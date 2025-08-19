from src.core.word_entry import WordEntry

class WordEntryManager:
    def __init__(self):
        self.word_dict = {}

    def add_word_entry(self, word_entry: WordEntry):
        self.word_dict[word_entry.word] = word_entry

    def get_word_entries(self):
        return self.word_dict
    
    def get_word_entry(self, word: str):
        return self.word_dict.get(word)
    
    def remove_word_entry(self, word: str):
        self.word_dict.pop(word)

    def update_word_entry(self, word: str, word_entry: WordEntry):
        self.word_dict[word] = word_entry

    def get_all_words(self):
        return list(self.word_dict.keys())
    
    def get_all_word_entries(self):
        return list(self.word_dict.values())