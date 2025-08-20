from enum import Enum
from dataclasses import dataclass

from src.utils.database_manager import DatabaseManager
from src.core.word_entry_manager import WordEntryManager

class BookType(Enum):
    SYSTEM = 1
    USER = 2

@dataclass
class VocabularyBookInfo:
    name: str
    type: BookType = BookType.USER
    description: str = ""
    signature: str = ""

class VocabularyBook:
    def __init__(self, vocabulary_book_info, word_entry_manager):
        self.vocabulary_book_info: VocabularyBookInfo = vocabulary_book_info
        self.word_entry_manager: WordEntryManager = word_entry_manager

    def get_book_info(self):
        return self.vocabulary_book_info

    def get_word(self, word: str):
        return self.word_entry_manager.get_word_entry(word)