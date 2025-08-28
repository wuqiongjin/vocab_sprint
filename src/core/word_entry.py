from dataclasses import dataclass, field
from enum import Enum

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
        entry = cls(
            word=data["Word"],
            phonetic_UK=data.get("Phonetic_UK", ""),
            phonetic_US=data.get("Phonetic_US", "")
        )
        
        interpretations_dict = {}
        for pos_str, meaning in data.get("Interpretations", {}).items():
            if not meaning:
                continue
            # find the corresponding enum value from string
            for pos_enum in PartOfSpeech:
                if pos_enum.value == pos_str:
                    interpretations_dict[pos_enum] = meaning
                    break
        
        entry.interpretations = interpretations_dict
        return entry
    
    @classmethod
    def from_flat_dict(cls, flat_dict):
        """
        create a WordEntry instance from a flat dict
        """
        # extract base fields
        word = flat_dict["Word"]
        phonetic_UK = flat_dict.get("Phonetic_UK", "")
        phonetic_US = flat_dict.get("Phonetic_US", "")
        
        # rebuild interpretations dict
        interpretations = {}
        for pos in PartOfSpeech:
            pos_value = pos.value
            if not flat_dict.get(pos_value, ""):
                continue
            if pos_value in flat_dict and flat_dict[pos_value]:
                interpretations[pos] = flat_dict[pos_value]
        
        return cls(
            word=word,
            phonetic_UK=phonetic_UK,
            phonetic_US=phonetic_US,
            interpretations=interpretations
        )