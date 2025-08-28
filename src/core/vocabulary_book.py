from enum import Enum
from dataclasses import dataclass

from src.utils.logger import Logger
from src.core.word_entry import WordEntry
from src.utils.database_manager import DatabaseManager
from src.core.word_entry_manager import WordEntryManager
from src.utils.exceptions import BaseError

logger = Logger("vocabulary_book")

class BookType(Enum):
    SYSTEM = 1
    USER = 2
    def __str__(self):
        return self.name

@dataclass
class VocabularyBookInfo:
    name: str
    type: BookType = BookType.USER
    description: str = ""
    signature: str = ""
    database_url: str = ""

    def to_dict(self):
        result = {
            "name": self.name,
            "type": str(self.type),
            "description": self.description,
            "signature": self.signature,
            "database_url": self.database_url
        }
        return result

class VocabularyBook:
    def __init__(self, vocabulary_book_info, word_entry_manager):
        self.vocabulary_book_info: VocabularyBookInfo = vocabulary_book_info
        self.word_entry_manager: WordEntryManager = word_entry_manager

    def get_book_info(self):
        return self.vocabulary_book_info

    def get_word(self, word: str):
        try:
            result = self.word_entry_manager.get_word_entry(word)
        except BaseError as e:
            logger.ERROR(f"Get word {word} error, message: {e}")
            result = "Unknown word"
        return result

    def get_all_words(self):
        try:
            result = self.word_entry_manager.get_word_dict()
        except BaseError as e:
            logger.ERROR(f"Get all words error, message: {e}")
            result = []
        return result

    def add_word(self, word: WordEntry):
        try:
            result = self.word_entry_manager.add_word_entry(word)
        except BaseError as e:
            logger.ERROR(f"Add word {word} error, message: {e}")
            result = False
        return result

