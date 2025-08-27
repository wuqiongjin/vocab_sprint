import csv
from src.core.word_entry import WordEntry, PartOfSpeech
from src.utils.exceptions import BaseError
from src.utils.logger import Logger

logger = Logger("file_reader")

class FileManager:
    @staticmethod
    def parse_word_entries_from_csv(csv_path):
        list_dict = csv_to_dict_list(csv_path)
        list_word_entry = []
        for dicts in list_dict:
            if check_keys_required_for_raw_file(dicts):
                try:
                    word = dicts["word"]
                    phonetic = dicts["phonetic"]
                    definition = dicts["definition"]
                    uk_phonetic, us_phonetic = split_phonetics(phonetic)
                    definition_dict = split_definition(definition)
                    word_entry = WordEntry(word, uk_phonetic, us_phonetic, definition_dict)
                    list_word_entry.append(word_entry)
                except BaseError as e:
                    logger.ERROR(f"Data Invalid: {dicts['word']}, error: {e}")
                    continue
            elif check_keys_required_for_standard_file(dicts):
                try:
                    word = dicts["Word"]
                    uk_phonetic = dicts["Phonetic_UK"]
                    us_phonetic = dicts["Phonetic_US"]
                    definition_dict = {}
                    for key in dicts:
                        if key != "Word" or "Phonetic_UK" or "Phonetic_US":
                            definition_dict[key] = dicts[key]
                    word_entry = WordEntry(word, uk_phonetic, us_phonetic, definition_dict)
                    list_word_entry.append(word_entry)
                except BaseError as e:
                    logger.ERROR(f"Data Invalid: {dicts['Word']}, error: {e}")
                    continue
        return list_word_entry

def check_keys_required_for_standard_file(dicts) -> bool:
    required_keys = PartOfSpeech.get_all_values() + ["Word", "Phonetic_UK", "Phonetic_US"]
    return all(key in dicts for key in required_keys)

def check_keys_required_for_raw_file(dicts) -> bool:
    required_keys = ["word", "phonetic", "definition"]
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

def detect_definition(text: str):
    type_mapping = {
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
        "aux": PartOfSpeech.AUX
    }
    text = text.strip()
    for prefix, definition_type in type_mapping.items():
        if text.startswith(prefix):
            return definition_type
    return PartOfSpeech.OTHERS

def split_definition(text: str):
    list_def = text.split('||')
    dict_def = {}
    for definition in list_def:
        dict_def[detect_definition(definition)] = definition
    return dict_def