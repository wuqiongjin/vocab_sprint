import json
import os
from dataclasses import asdict
from pathlib import Path
from platformdirs import user_data_dir

from src.core.vocabulary_book import VocabularyBook, VocabularyBookInfo, BookType
from src.utils.database_manager import DatabaseManager, DataType
from src.utils.logger import Logger, APP_NAME
from src.core.word_entry_manager import WordEntryManager
from src.core.word_entry import WordEntry
from src.utils.exceptions import BaseError

logger = Logger("vocabulary_book_manager")

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PATH = Path(user_data_dir("data", APP_NAME))
WORD_ENTRY_KEY = "WordEntries"
DATABASE_URL_KEY = "database_url"

class VocabularyBookManager:
    def __init__(self, user_name = "default"):
        self.vocabulary_books = {}
        self.user_name = user_name
        self.book_dir = DATA_PATH / "users" / self.user_name / "books"
        self.book_list_config = self.book_dir / "book_list.json"
        book_info_list = self.read_books_from_config()
        if book_info_list is not None:
            for book_info in book_info_list:
                self.load_vocabulary_book(book_info)

    def get_book(self, book_name: str):
        return self.vocabulary_books[book_name]

    def get_all_book(self):
        return self.vocabulary_books

    def create_vocabulary_book(self, book_info):
        logger.DEBUG("create_vocabulary_book in")
        book_name = book_info.name
        if book_name in self.vocabulary_books:
            logger.ERROR(f"There is already a book named {book_name}, create vocabulary book failed.")
            return False
        database_path = self.generate_database_url(book_name)
        if os.path.exists(database_path):
            logger.ERROR(f"Database file found: {database_path}, create vocabulary book failed.")
            return False

        logger.INFO(f"Database file not found: {database_path}, start to create vocabulary book.")
        try:
            database_manager = DatabaseManager(database_path, True)
            VocabularyBookManager.create_word_entry_table(database_manager)
            word_entry_manager = WordEntryManager(database_manager, WORD_ENTRY_KEY)
        except BaseError as e:
            logger.INFO(f"Create vocabulary book failed. errorMessage: {e}")
            return False

        book_info.database_url = str(database_path)
        vocabulary_book = VocabularyBook(book_info, word_entry_manager)
        self.vocabulary_books[book_name] = vocabulary_book
        if self.commit_books_to_config() is False:
            logger.ERROR("Write books to config failed.")
            return False
        logger.INFO("Create vocabulary book success.")
        return True

    def create_vocabulary_book_from_data(self, book_info, data_url):
        logger.DEBUG("create_vocabulary_book_from_data in")
        self.create_vocabulary_book(book_info)

        return self.load_vocabulary_book(book_info)

    def load_vocabulary_book(self, book_info):
        logger.DEBUG("load_vocabulary_book in")
        book_name = book_info.name
        if book_name in self.vocabulary_books:
            logger.ERROR(f"There is already a book named {book_name}, can't load again.")
            return False
        database_path = book_info.database_url
        if not os.path.exists(database_path):
            logger.INFO(f"Database file not found: {database_path}, load vocabulary book failed.")
            return False

        logger.INFO(f"Database file found: {database_path}, start to load vocabulary book.")
        try:
            database_manager = DatabaseManager(database_path)
            if not database_manager.check_table_exist(WORD_ENTRY_KEY):
                logger.ERROR(f"Database: {database_path} has no table called {WORD_ENTRY_KEY}.")
                return False
            word_entry_manager = WordEntryManager(database_manager, WORD_ENTRY_KEY)
        except BaseError as e:
            logger.ERROR(f"Load vocabulary book {book_name} failed, error: {e}")
            return False
        vocabulary_book = VocabularyBook(book_info, word_entry_manager)
        self.vocabulary_books[book_name] = vocabulary_book
        return True

    def delete_vocabulary_book(self, book_name, force_delete = False):
        logger.DEBUG("delete_vocabulary_book in")
        if book_name not in self.vocabulary_books:
            logger.INFO(f"No vocabulary book called {book_name}.")
            return False
        book = self.vocabulary_books[book_name]
        if book.get_book_info().type == BookType.SYSTEM and not force_delete:
            logger.INFO(f"Can not delete system book: {book_name}, delete vocabulary book failed.")
            return False
        database_path = Path(book.get_book_info().database_url)
        if not os.path.exists(database_path):
            logger.INFO(f"Database file not found: {database_path}, delete vocabulary book failed.")
            return False

        logger.INFO(f"Database file found: {database_path}, start to delete vocabulary book.")
        self.vocabulary_books.pop(book_name, None)
        if self.commit_books_to_config() is False:
            logger.ERROR("Write books to config failed.")
            return False
        try:
            book.word_entry_manager.database_manager.close()
            os.remove(database_path)
            logger.DEBUG(f"Delete '{database_path}' success.")
        except PermissionError:
            logger.ERROR(f"Delete '{database_path}' failed, no permission.")
            return False
        except Exception as e:
            logger.ERROR(f"Delete '{database_path}' failed, error: {e}.")
            return False
        return True

    @staticmethod
    def create_word_entry_table(database_manager):
        columns = [
            ("Word", DataType.TEXT),
            ("Phonetic_UK", DataType.TEXT),
            ("Phonetic_US", DataType.TEXT),
            ("Interp_Noun", DataType.TEXT),
            ("Interp_Verb", DataType.TEXT),
            ("Interp_Adj", DataType.TEXT),
            ("Interp_Adv", DataType.TEXT),
            ("Interp_Pron", DataType.TEXT),
            ("Interp_Prep", DataType.TEXT),
            ("Interp_Conj", DataType.TEXT),
            ("Interp_Intj", DataType.TEXT),
            ("Interp_Art", DataType.TEXT),
            ("Interp_Det", DataType.TEXT),
            ("Interp_Num", DataType.TEXT),
            ("Interp_Aux", DataType.TEXT),
            ("Interp_Others", DataType.TEXT),
        ]
        config = {
            "primary_key": "Word",
        }
        database_manager.create_table("WordEntries", columns, config)

    def commit_books_to_config(self):
        logger.DEBUG("commit_books_to_config in.")
        book_list = []
        try:
            for book in self.vocabulary_books.values():
                book_dict = book.get_book_info().to_dict()
                book_list.append(book_dict)
            logger.DEBUG("Open config...")
            with open(self.book_list_config, 'w', encoding='utf-8') as f:
                json.dump(book_list, f, ensure_ascii=False, indent=4)
            logger.INFO(f"Add book: {book_list} to config success")
            return True
        except Exception as e:
            logger.ERROR(f"Add book: {book_list} to config failed, message: {e}")
            return False

    def read_books_from_config(self):
        try:
            with open(self.book_list_config, 'r', encoding='utf-8') as f:
                books_dict_list = json.load(f)
                for books_dict in books_dict_list:
                    books_dict["type"] = BookType[books_dict["type"]]
                return [VocabularyBookInfo(** book_dict) for book_dict in books_dict_list]
        except Exception as e:
            logger.INFO(f"Load book_list.json failed. error: {e}")
            return None

    def generate_database_url(self, book_name):
        database_path = self.book_dir / (book_name + ".db")
        counter = 0
        while os.path.exists(database_path):
            database_path = self.book_dir / (book_name + f"_{counter}.db")
            counter += 1
        return database_path