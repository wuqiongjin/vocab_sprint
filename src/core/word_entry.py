from src.utils.logger import Logger

from dataclasses import dataclass, field
from enum import Enum

logger = Logger('WordEntry')

class PartOfSpeech(Enum):
    NOUN = "Interp_Noun"
    VERB = "Interp_Verb"
    ADJ = "Interp_Adj"
    ADV = "Interp_Adv"
    PRON = "Interp_Pron"
    PREP = "Interp_Prep"
    CONJ = "Interp_Conj"
    INTJ = "Interp_Intj"
    ART = "Interp_Art"
    DET = "Interp_Det"
    NUM = "Interp_Num"
    AUX = "Interp_Aux"
    OTHERS = "Interp_Others"

    @classmethod
    def get_all_enums(cls) -> list:
        return [pos for pos in cls]

    @classmethod
    def get_all_values(cls) -> list[str]:
        return [pos.value for pos in cls]

@dataclass
class WordEntry:
    word: str                                                                   # required
    phonetic_UK: str = ""                                                       # Optional
    phonetic_US: str = ""                                                       # Optional
    interpretations: dict[PartOfSpeech, str] = field(default_factory=dict)      # Optional

    @classmethod
    def get_database_columns(cls):
        return ["Word", "Phonetic_UK", "Phonetic_US"] + PartOfSpeech.get_all_values()

    def to_dict(self):
        """create a dict from WordEntry"""
        return {
            "Word": self.word,
            "Phonetic_UK": self.phonetic_UK,
            "Phonetic_US": self.phonetic_US,
            "Interpretations": {
                pos.value: meaning for pos, meaning in self.interpretations.items()
            }
        }

    def to_flat_dict(self):
        """
        interpretations fields will be expanded into separate fields

        Returns:
            Dict[str, str]: a flat dict with base fields and interpretations fields
        """
        # base fields
        flat_dict = {
            "Word": self.word,
            "Phonetic_UK": self.phonetic_UK,
            "Phonetic_US": self.phonetic_US
        }

        # expand interpretations dict
        for pos in PartOfSpeech:
            # use Part of Speech as field name. such as "Interp_Noun, Interp_Verb,..."
            field_name = pos.value
            flat_dict[field_name] = self.interpretations.get(pos, "")

        return flat_dict

    @classmethod
    def from_dict(cls, data):
        """
        create a WordEntry instance from a dict

        Args:
            data: (Dict[PartOfSpeech | str, str]): a dict with base fields and interpretations fields
        """
        entry = cls(
            word=data["Word"],
            phonetic_UK=data.get("Phonetic_UK", ""),
            phonetic_US=data.get("Phonetic_US", "")
        )

        interpretations_dict = {}
        interpretations_data = data.get("Interpretations", {})

        # convert interpretations data to PartOfSpeech enum
        for key, meaning in interpretations_data.items():
            if not isinstance(meaning, str) or not meaning.strip():
                continue

            # if key is already a PartOfSpeech enum, use it directly
            if isinstance(key, PartOfSpeech):
                interpretations_dict[key] = meaning.strip()
            # if key is a string, try to find a matching PartOfSpeech value
            elif isinstance(key, str):
                try:
                    pos_enum = PartOfSpeech(key)
                    interpretations_dict[pos_enum] = meaning.strip()
                except ValueError:
                    # try to find a matching PartOfSpeech value
                    found = False
                    for pos in PartOfSpeech:
                        if pos.value == key:
                            interpretations_dict[pos] = meaning.strip()
                            found = True
                            break
                    
                    if not found:
                        logger.WARN(f"Invalid Part of Speech: {key}")
                        continue
            else:
                logger.WARN(f"Invalid key type in interpretations: {type(key)}")
                continue

        entry.interpretations = interpretations_dict
        return entry

    @classmethod
    def from_flat_dict(cls, flat_dict):
        """
        create a WordEntry instance from a flat dict

        Returns:
            flat_dict: (Dict[PartOfSpeech | str, str]): a flat dict with base fields and interpretations fields
        """
        # extract base fields
        word = flat_dict["Word"]
        phonetic_UK = flat_dict.get("Phonetic_UK", "")
        phonetic_US = flat_dict.get("Phonetic_US", "")

        # rebuild interpretations dict
        interpretations = {}
        for key, value in flat_dict.items():
            if not isinstance(value, str) or not value.strip():
                continue

            # Skip base fields
            if key in ["Word", "Phonetic_UK", "Phonetic_US"]:
                continue

            if key in PartOfSpeech.get_all_enums():
                # key is PartOfSpeech enum, use it directly
                interpretations[PartOfSpeech(key)] = value.strip()
            elif key in PartOfSpeech.get_all_values():
                # key is a string, try to find a matching PartOfSpeech value
                found = False
                for pos in PartOfSpeech:
                    if pos.value == key:
                        interpretations[pos] = value.strip()
                        found = True
                        break

                if not found:
                    logger.WARN(f"Unexpected field in flat dict: {key}")
            else:
                logger.WARN(f"Invalid key in flat dict: {key}")

        return cls(
            word=word,
            phonetic_UK=phonetic_UK,
            phonetic_US=phonetic_US,
            interpretations=interpretations
        )