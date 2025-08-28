from src.core.word_entry import WordEntry
from src.core.word_entry_manager import WordEntryManager
from src.utils.logger import Logger

from enum import Enum
from fuzzywuzzy import fuzz
import threading
import concurrent.futures
from typing import Callable, List
from queue import Queue

logger = Logger("word_query_service")

class InvertIndex(Enum):
    TRANSLATION = "translation"

class QueryResult:
    def __init__(self, word: str, entry: WordEntry, score: int):
        self.word = word
        self.entry = entry
        self.score = score

class WordQueryService:
    def __init__(self, word_entry_manager: WordEntryManager, debounce_delay: float = 0.3, max_workers: int = 3):
        self.word_entry_manager = word_entry_manager
        self.indexes: dict[InvertIndex, dict[str, List[WordEntry]]] = {
            InvertIndex.TRANSLATION: {},
        }
        # Real-time search attributes
        self.stop_search = False
        self.last_query = ""
        self.search_results_callback = None
        self.debounce_delay = debounce_delay  # Debounce delay time in seconds
        self.debounce_timer = None
        self.lock = threading.Lock()  # Thread safety lock

        # Thread pool execution attributes
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.future = None
        self.result_queue = Queue()

        # Result processing thread
        self.result_thread = None

        # Build indexes
        self.build_indexes()
        # register callback to rebuild indexes when word_entry_manager is updated
        self.word_entry_manager.add_callback(self.build_indexes())

    def build_indexes(self):
        """
        interpretations -> word
        """
        with self.lock:
            # Clear indexes
            self.indexes = {
                InvertIndex.TRANSLATION: {},
            }

            for entry in self.word_entry_manager.get_word_dict().values():
                # build translation index
                for meaning in entry.interpretations.values():
                    if meaning:
                        self._add_to_index(InvertIndex.TRANSLATION, meaning, entry)
            logger.INFO(f"Built translation index finished with {len(self.indexes[InvertIndex.TRANSLATION])} entries")

    def _add_to_index(self, index_type: InvertIndex, key: str, entry: WordEntry):
        if key not in self.indexes[index_type]:
            self.indexes[index_type][key] = []
        self.indexes[index_type][key].append(entry)


    def query(self, text: str) -> list[WordEntry]:
        """
        Query by word or translation
        """
        if not text.strip():
            return []

        results = []
        # 1. query by word
        exact_entry = self.word_entry_manager.get_word_entry(text)
        if exact_entry:
            results.append(exact_entry)

        # 2. query by translation
        translation_entries = self.indexes[InvertIndex.TRANSLATION].get(text)
        if translation_entries:
            results.extend(translation_entries)

        # 3. query by partial match
        partial_results = self.partial_search(text)
        results.extend(partial_results)

        # remove duplicates and preserve order
        unique_results = list({entry.word: entry for entry in results}.values())    # 
        if len(unique_results) >= 3:
            logger.INFO(f"Query '{text}' returned {len(unique_results)} results")
            return unique_results

        # 4. fuzzy search
        unique_results.extend(self.fuzzy_search(text))

        # remove duplicates and preserve order
        unique_results = list({entry.word: entry for entry in unique_results}.values())
        logger.INFO(f"Query '{text}' returned {len(unique_results)} results")
        return unique_results

    def partial_search(self, text: str) -> list[WordEntry]:
        """
        Partial search by word or translation
        """
        results = []

        # 1. partial search by word
        for word, entry in self.word_entry_manager.get_word_dict().items():
            if text.lower() in word.lower():
                results.append(entry)

        # 2. partial search by translation
        for meaning, entries in self.indexes[InvertIndex.TRANSLATION].items():
            if text in meaning:
                results.extend(entries)

        return results

    def fuzzy_search(self, text: str, threshold: int = 60) -> list[WordEntry]:
        """
        Fuzzy search by word or translation

        threshold: minimum similarity score (0-100) to consider a match (default: 60)
        """
        results = []
        text = text.strip()
        if not text:
            return results

        for word, entry in self.word_entry_manager.get_word_dict().items():
            # compute similarity
            ratio = fuzz.ratio(text.lower(), word.lower())
            if ratio >= threshold:
                results.append(QueryResult(word, entry, ratio))

        # order by score
        return [query_result.entry for query_result in sorted(results, key=lambda x: x.score, reverse=True)]

    def _execute_query_async(self, query_text: str):
        """Execute query in thread pool"""
        try:
            results = self.query(query_text)
            self.result_queue.put((query_text, results, None))
            logger.INFO(f"Executed query task for: '{query_text}' with {len(results)} results")
        except Exception as e:
            self.result_queue.put((query_text, None, e))
            logger.ERROR(f"Error executing query task for: '{query_text}' with error: {e}")

    def _process_query_results(self):
        """Process query results from the queue"""
        while not self.stop_search:
            try:
                # Non-blocking get from queue
                query_text, results, error = self.result_queue.get(timeout=0.1)

                with self.lock:
                    # Check if result is still relevant (user might have entered new query)
                    if query_text == self.last_query and not self.stop_search and self.search_results_callback:
                        if error:
                            # Handle error
                            print(f"Query error: {error}")
                        else:
                            # Call callback function
                            logger.INFO(f"Calling search results callback with {len(results)} results")
                            self.search_results_callback(results)
            except:
                # Timeout is expected, continue loop
                logger.DEBUG("No query results in queue")
                pass

    def start_realtime_search(self, callback: Callable[[List[WordEntry]], None]):
        """
        Start real-time search
        callback: callback function for search results
        """
        with self.lock:
            if self.result_thread and self.result_thread.is_alive():
                self.stop_realtime_search()

            self.stop_search = False
            self.search_results_callback = callback

            # Start result processing thread
            self.result_thread = threading.Thread(target=self._process_query_results)
            self.result_thread.daemon = True
            self.result_thread.start()

    def stop_realtime_search(self):
        """Stop real-time search"""
        with self.lock:
            self.stop_search = True
            
            # Cancel debounce timer
            if self.debounce_timer:
                self.debounce_timer.cancel()
                self.debounce_timer = None

            # Cancel ongoing query
            if self.future and not self.future.done():
                self.future.cancel()

            # Wait for result thread to finish
            if self.result_thread and self.result_thread.is_alive():
                self.result_thread.join(timeout=1.0)

    def update_query(self, query_text: str):
        """
        Update query text with debounce mechanism
        """
        with self.lock:
            # Check if real-time search is started
            if self.search_results_callback is None:
                print("Warning: Real-time search not started. Call start_realtime_search() first.")
                return

            self.last_query = query_text

            # Cancel previous timer
            if self.debounce_timer:
                self.debounce_timer.cancel()

            # Set new timer
            self.debounce_timer = threading.Timer(self.debounce_delay, self._submit_query_task)
            self.debounce_timer.start()

    def _submit_query_task(self):
        """Submit query task to thread pool"""
        with self.lock:
            # Additional check to prevent unnecessary query execution
            if self.stop_search or not self.last_query or self.search_results_callback is None:
                return

            # Cancel previous query task if still running
            if self.future and not self.future.done():
                self.future.cancel()

            # Submit new query task to thread pool
            self.future = self.executor.submit(self._execute_query_async, self.last_query)
            logger.INFO(f"Submitted query task for '{self.last_query}'")

    def shutdown(self):
        """Shutdown query service and release resources"""
        self.stop_realtime_search()
        self.executor.shutdown(wait=False)
        self.word_entry_manager.remove_callback(self.build_indexes())
        logger.INFO("WordQueryService shutdown")