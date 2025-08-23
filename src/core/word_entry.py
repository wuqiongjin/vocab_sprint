from dataclasses import dataclass

@dataclass
class WordEntry:
    Word: str
    Phonetic_UK: str
    Phonetic_US: str
    Interp_Noun: str = ""
    Interp_Verb: str = ""
    Interp_Adj: str = ""
    Interp_Adv: str = ""
    Interp_Pron: str = ""
    Interp_Prep: str = ""
    Interp_Conj: str = ""
    Interp_Intj: str = ""
    Interp_Art: str = ""
    Interp_Det: str = ""
    Interp_Num: str = ""
    Interp_Aux: str = ""
    Interp_Others: str = ""