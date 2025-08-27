import sys
import io
import os

from src.core.vocabulary_book_manager import VocabularyBookManager
from src.core.vocabulary_book import *

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

TEST_USER_NAME = "test_user"
TEST_BOOK_NAME = "new test Book"
TEST_BOOK_DESCRIPTION = "This is a new test book."

def test_create_vocabulary_book():
    book_mgr = VocabularyBookManager(TEST_USER_NAME)
    book_info = VocabularyBookInfo(TEST_BOOK_NAME, type=BookType.SYSTEM, description=TEST_BOOK_DESCRIPTION)
    assert book_mgr.create_vocabulary_book(book_info) is True, "Create test book success."

def test_load_vocabulary_book():
    book_mgr = VocabularyBookManager(TEST_USER_NAME)
    assert len(book_mgr.vocabulary_books) is 1
    book = book_mgr.vocabulary_books[TEST_BOOK_NAME]
    assert book.get_book_info().name == TEST_BOOK_NAME
    assert book.get_book_info().description == TEST_BOOK_DESCRIPTION

def test_delete_vocabulary_book():
    book_mgr = VocabularyBookManager(TEST_USER_NAME)
    assert book_mgr.delete_vocabulary_book(TEST_BOOK_NAME) is False
    assert len(book_mgr.vocabulary_books) is 1
    assert book_mgr.delete_vocabulary_book(TEST_BOOK_NAME, True) is True
    new_book_mgr = VocabularyBookManager(TEST_USER_NAME)
    assert len(new_book_mgr.vocabulary_books) is 0

if __name__ == "__main__":
    test_create_vocabulary_book()

    test_load_vocabulary_book()

    test_delete_vocabulary_book()