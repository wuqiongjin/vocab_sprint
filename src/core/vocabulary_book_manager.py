import os
from pathlib import Path
from src.core.vocabulary_book import VocabularyBook, VocabularyBookInfo, BookType
from src.utils.database_manager import DatabaseManager, DataType
from src.utils.logger import Logger
from src.core.word_entry_manager import WordEntryManager
from src.core.word_entry import WordEntry

ROOT = Path(__file__).resolve().parent.parent.parent
logger = Logger("vocabulary_book_manager")

class VocabularyBookManager:

    def __init__(self, user_name = "default"):
        self.vocabulary_books = {}
        self.user_name = user_name
        self.book_dir = ROOT / "data/users" / self.user_name / "books"
        book_files = list(self.book_dir.rglob('*.db'))
        for book_file in book_files:
            self.load_vocabulary_book(book_file)

    def get_book(self, book_name: str):
        return self.vocabulary_books[book_name]

    def get_all_book(self):
        return self.vocabulary_books

    def create_vocabulary_book(self, book_info):
        logger.INFO("create_vocabulary_book in")
        book_name = book_info.name
        database_path = self.book_dir / (book_name + ".db")
        if os.path.exists(database_path):
            logger.ERROR(f"Database file found: {database_path}, create vocabulary book failed.")
            return False
        logger.INFO(f"Database file not found: {database_path}, start to create vocabulary book.")
        database_manager = DatabaseManager(database_path)
        VocabularyBookManager.create_word_entry_table(database_manager)
        word_entry_manager = WordEntryManager(database_manager, "WordEntries")
        vocabulary_book = VocabularyBook(book_info, word_entry_manager)
        logger.INFO("Create vocabulary book success.")
        self.vocabulary_books[book_name] = vocabulary_book
        return True

    def load_vocabulary_book(self, database_path):
        if not os.path.exists(database_path):
            logger.INFO(f"Database file not found: {database_path}, load vocabulary book failed.")
            return
        book_name = Path(database_path).stem
        book_info = VocabularyBookInfo(book_name)
        database_manager = DatabaseManager(database_path)
        word_entry_manager = WordEntryManager(database_manager, "WordEntries")
        vocabulary_book = VocabularyBook(book_info, word_entry_manager)
        self.vocabulary_books[book_name] = vocabulary_book

    @staticmethod
    def create_word_entry_table(database_manager):
        columns = [
            ("word", DataType.TEXT),
            ("phonetic_UK", DataType.TEXT),
            ("phonetic_US", DataType.TEXT),
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
            ("Interp_OTHERS", DataType.TEXT),
        ]
        database_manager.create_table("WordEntries", columns)


# 测试
# if __name__ == '__main__':
#     mgr = VocabularyBookManager()
#     info = VocabularyBookInfo("new Book", type=BookType.SYSTEM, description="This is a book.")
#     mgr.create_vocabulary_book(info)
#
#     word = mgr.get_book("Book").get_word("apple")
#     print(word)
