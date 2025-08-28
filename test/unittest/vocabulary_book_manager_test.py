import sys
import io
import os
from pathlib import Path
from platformdirs import user_data_dir
from src.core.vocabulary_book_manager import VocabularyBookManager, ExportType
from src.core.vocabulary_book import *
from src.utils.logger import APP_NAME

ROOT = Path(__file__).resolve().parent.parent.parent

TEST_USER_NAME = "test_user"

TEST_BOOK_NAME = "new test Book"
TEST_BOOK_DESCRIPTION = "This is a new test book."

TEST_BOOK_50A_NAME = "50A_words"
TEST_BOOK_50A_DESCRIPTION = "50 words start with A."
TEST_CSV_50A_URL = ROOT / "resource"/ "csv" / "50_A.csv"
TEST_CSV_50A_OUTPUT_STANDARD_URL = "50_A_STANDARD.csv"
TEST_CSV_50A_OUTPUT_RAW_URL = "50_A_RAW.csv"

CLEAR_PATH = Path(user_data_dir("data", APP_NAME)) / "users" / TEST_USER_NAME / "books"

def test_create_vocabulary_book():
    book_mgr = VocabularyBookManager(TEST_USER_NAME)
    book_info = VocabularyBookInfo(TEST_BOOK_NAME, type=BookType.SYSTEM, description=TEST_BOOK_DESCRIPTION)
    assert book_mgr.create_vocabulary_book(book_info) == True, "Create test book success."

def test_load_vocabulary_book():
    book_mgr = VocabularyBookManager(TEST_USER_NAME)
    assert len(book_mgr.vocabulary_books) == 1
    book = book_mgr.vocabulary_books[TEST_BOOK_NAME]
    assert book.get_book_info().name == TEST_BOOK_NAME
    assert book.get_book_info().description == TEST_BOOK_DESCRIPTION

def test_delete_vocabulary_book():
    book_mgr = VocabularyBookManager(TEST_USER_NAME)
    assert book_mgr.delete_vocabulary_book(TEST_BOOK_NAME) == False
    assert len(book_mgr.vocabulary_books) == 1
    assert book_mgr.delete_vocabulary_book(TEST_BOOK_NAME, True) == True
    new_book_mgr = VocabularyBookManager(TEST_USER_NAME)
    assert len(new_book_mgr.vocabulary_books) == 0

def test_create_vocabulary_book_from_csv():
    book_mgr = VocabularyBookManager(TEST_USER_NAME)
    book_info = VocabularyBookInfo(TEST_BOOK_50A_NAME, BookType.SYSTEM, TEST_BOOK_50A_DESCRIPTION)
    assert book_mgr.create_vocabulary_book_from_data(book_info, TEST_CSV_50A_URL)
    book = book_mgr.get_book(TEST_BOOK_50A_NAME)
    list_words = book.get_all_words()
    assert len(list_words) == 50
    assert book_mgr.delete_vocabulary_book(TEST_BOOK_50A_NAME, True) == True

def test_export_vocabulary_book_to_csv():
    book_mgr = VocabularyBookManager(TEST_USER_NAME)
    book_info = VocabularyBookInfo(TEST_BOOK_50A_NAME, BookType.SYSTEM, TEST_BOOK_50A_DESCRIPTION)
    assert book_mgr.create_vocabulary_book_from_data(book_info, TEST_CSV_50A_URL)
    book_mgr.export_vocabulary_book(TEST_BOOK_50A_NAME, TEST_CSV_50A_OUTPUT_STANDARD_URL, export_type=ExportType.CSV_STANDARD)
    book_mgr.export_vocabulary_book(TEST_BOOK_50A_NAME, TEST_CSV_50A_OUTPUT_RAW_URL, export_type=ExportType.CSV_RAW)
    assert book_mgr.delete_vocabulary_book(TEST_BOOK_50A_NAME, True) == True
    assert os.path.exists(TEST_CSV_50A_OUTPUT_STANDARD_URL)
    assert os.path.exists(TEST_CSV_50A_OUTPUT_RAW_URL)
    os.remove(TEST_CSV_50A_OUTPUT_STANDARD_URL)
    os.remove(TEST_CSV_50A_OUTPUT_RAW_URL)

if __name__ == "__main__":
    test_create_vocabulary_book()

    test_load_vocabulary_book()

    test_delete_vocabulary_book()

    test_create_vocabulary_book_from_csv()

    test_export_vocabulary_book_to_csv()