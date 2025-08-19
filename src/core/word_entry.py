from dataclasses import dataclass

@dataclass
class WordEntry:
    word: str
    phonetic_UK: str
    phonetic_US: str
    interp_Noun: str
    interp_Verb: str
    interp_Adj: str
    interp_Adv: str
    interp_Pron: str
    interp_Prep: str
    interp_Conj: str
    interp_Intj: str
    interp_Art: str
    interp_Det: str
    interp_Num: str
    interp_Aux: str
    interp_Others: str