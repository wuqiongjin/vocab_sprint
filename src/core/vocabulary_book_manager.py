import json
import os
import csv
from enum import Enum
from pathlib import Path
from platformdirs import user_data_dir

from src.core.vocabulary_book import VocabularyBook, VocabularyBookInfo, BookType
from src.utils.database_manager import DatabaseManager, DataType
from src.utils.logger import Logger, APP_NAME
from src.core.word_entry_manager import WordEntryManager
from src.core.word_entry import WordEntry, PartOfSpeech
from src.utils.exceptions import BaseError

logger = Logger("vocabulary_book_manager")

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PATH = Path(user_data_dir("data", APP_NAME))
WORD_ENTRY_KEY = "WordEntries"
DATABASE_URL_KEY = "database_url"

EXPORT_FIELD_KEY_RAW_WORD = "word"
EXPORT_FIELD_KEY_RAW_PHONETIC = "phonetic"
EXPORT_FIELD_KEY_RAW_DEFINITION = "definition"

EXPORT_FIELD_KEY_STANDARD_WORD = "Word"
EXPORT_FIELD_KEY_STANDARD_PHONETIC_UK = "Phonetic_UK"
EXPORT_FIELD_KEY_STANDARD_PHONETIC_US = "Phonetic_US"

class ExportType(Enum):
    CSV_STANDARD = "csv_standard",
    CSV_RAW = "csv_raw"

    @classmethod
    def get_all_name(cls) -> list[str]:
        return [pos.name for pos in cls]

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
        if not self.create_vocabulary_book(book_info):
            logger.ERROR(f"Create book {book_info.name} failed.")
            return False
        book = self.get_book(book_info.name)

        try:
            list_words = self.parse_word_entries_from_csv(data_url)
        except Exception as e:
            self.delete_vocabulary_book(book_info.name, True)
            logger.ERROR(f"Parse data failed, create book from data failed. error: {e}")
            return False

        for word in list_words:
            book.add_word(word)
        return True

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

    def export_vocabulary_book(self, book_name, output_path, export_type = ExportType.CSV_STANDARD):
        logger.DEBUG("export_vocabulary_book in")
        if book_name not in self.vocabulary_books:
            logger.INFO(f"No vocabulary book called {book_name}.")
            return False
        book = self.vocabulary_books[book_name]
        word_entries = book.word_entry_manager.get_word_dict().values()
        self.generate_csv_from_word_entries(word_entries, output_path, export_type)
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
            (EXPORT_FIELD_KEY_STANDARD_WORD, DataType.TEXT),
            (EXPORT_FIELD_KEY_STANDARD_PHONETIC_UK, DataType.TEXT),
            (EXPORT_FIELD_KEY_STANDARD_PHONETIC_US, DataType.TEXT),
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
            "primary_key": EXPORT_FIELD_KEY_STANDARD_WORD,
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

    @staticmethod
    def parse_word_entries_from_csv(csv_path):
        list_dict = csv_to_dict_list(csv_path)
        list_word_entry = []
        for dicts in list_dict:
            if check_keys_required_for_raw_file(dicts):
                try:
                    word = dicts[EXPORT_FIELD_KEY_RAW_WORD]
                    phonetic = dicts[EXPORT_FIELD_KEY_RAW_PHONETIC]
                    definition = dicts[EXPORT_FIELD_KEY_RAW_DEFINITION]
                    uk_phonetic, us_phonetic = split_phonetics(phonetic)
                    definition_dict = split_definition(definition)
                    word_entry = WordEntry(word, uk_phonetic, us_phonetic, definition_dict)
                    list_word_entry.append(word_entry)
                except BaseError as e:
                    logger.ERROR(f"Data Invalid: {dicts['word']}, error: {e}")
                    continue
            elif check_keys_required_for_standard_file(dicts):
                try:
                    word = dicts[EXPORT_FIELD_KEY_STANDARD_WORD]
                    uk_phonetic = dicts[EXPORT_FIELD_KEY_STANDARD_PHONETIC_UK]
                    us_phonetic = dicts[EXPORT_FIELD_KEY_STANDARD_PHONETIC_US]
                    definition_dict = {}
                    for key in dicts:
                        if key != EXPORT_FIELD_KEY_STANDARD_WORD or EXPORT_FIELD_KEY_STANDARD_PHONETIC_UK or EXPORT_FIELD_KEY_STANDARD_PHONETIC_US:
                            definition_dict[key] = dicts[key]
                    word_entry = WordEntry(word, uk_phonetic, us_phonetic, definition_dict)
                    list_word_entry.append(word_entry)
                except BaseError as e:
                    logger.ERROR(f"Data Invalid: {dicts['Word']}, error: {e}")
                    continue
        return list_word_entry

    @staticmethod
    def generate_csv_from_word_entries(list_word_entry: list[WordEntry], csv_path, export_type):
        if export_type == ExportType.CSV_STANDARD:
            list_dict = word_entry_to_dict_standard(list_word_entry)
        elif export_type == ExportType.CSV_RAW:
            list_dict = word_entry_to_dict_raw(list_word_entry)
        else:
            list_dict = []
        if not list_dict:
            logger.ERROR("empty data.")
            return False
        fieldnames = list_dict[0].keys()
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for row in list_dict:
                    writer.writerow(row)
            return True
        except BaseError as e:
            return False

def word_entry_to_dict_standard(list_word_entry: list[WordEntry]):
    list_dict = []
    for word_entry in list_word_entry:
        list_dict.append(word_entry.to_flat_dict())
    return list_dict

def word_entry_to_dict_raw(list_word_entry: list[WordEntry]):
    list_dict = []
    for word_entry in list_word_entry:
        output_dict = {
            EXPORT_FIELD_KEY_RAW_WORD: word_entry.word,
            EXPORT_FIELD_KEY_RAW_PHONETIC: "英" + word_entry.phonetic_UK + "美" + word_entry.phonetic_US,
            EXPORT_FIELD_KEY_RAW_DEFINITION: "||".join(str(v) for v in word_entry.interpretations.values())
        }
        list_dict.append(output_dict)
    return list_dict

def check_keys_required_for_standard_file(dicts) -> bool:
    required_keys = PartOfSpeech.get_all_values() + [EXPORT_FIELD_KEY_STANDARD_WORD, EXPORT_FIELD_KEY_STANDARD_PHONETIC_UK, EXPORT_FIELD_KEY_STANDARD_PHONETIC_US]
    return all(key in dicts for key in required_keys)

def check_keys_required_for_raw_file(dicts) -> bool:
    required_keys = [EXPORT_FIELD_KEY_RAW_WORD, EXPORT_FIELD_KEY_RAW_PHONETIC, EXPORT_FIELD_KEY_RAW_DEFINITION]
    return all(key in dicts for key in required_keys)

def csv_to_dict_list(csv_path: str, encoding: str = "utf-8"):
    dict_list = []
    with open(csv_path, "r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dict_list.append(row)
    return dict_list

def split_phonetics(text: str):
    parts = [p for p in text.split('/') if p.strip()]
    if len(parts) >= 4:
        uk_phonetic = f"/{parts[1]}/"
        us_phonetic = f"/{parts[3]}/"
        return uk_phonetic, us_phonetic
    else:
        raise ValueError(f"Invalid phonetic format：{text}")

InterpretationsMap = {
    "n": PartOfSpeech.NOUN,
    "v": PartOfSpeech.VERB,
    "adj": PartOfSpeech.ADJ,
    "adv": PartOfSpeech.ADV,
    "prep": PartOfSpeech.PREP,
    "conj": PartOfSpeech.CONJ,
    "pron": PartOfSpeech.PRON,
    "num": PartOfSpeech.NUM,
    "int": PartOfSpeech.INTJ,
    "art": PartOfSpeech.ART,
    "det": PartOfSpeech.DET,
    "aux": PartOfSpeech.AUX,
    "other": PartOfSpeech.OTHERS
}

def detect_definition(text: str):
    text = text.strip()
    for prefix, definition_type in InterpretationsMap.items():
        if text.startswith(prefix):
            return definition_type
    return PartOfSpeech.OTHERS

def split_definition(text: str):
    list_def = text.split('||')
    dict_def = {}
    for definition in list_def:
        dict_def[detect_definition(definition)] = definition
    return dict_def