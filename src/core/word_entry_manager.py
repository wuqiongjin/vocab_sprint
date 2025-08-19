from .word_entry import WordEntry
from utils.database_manager import DatabaseManager

class WordEntryManager:
    def __init__(self, database_path: str, table_name: str):
        self.database_path = database_path
        self.database_manager = DatabaseManager(database_path)
        self.word_dict = self.database_manager.export_table_data(table_name)

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


# # test
# if __name__ == "__main__":
#     word_entry_manager = WordEntryManager("../../resource/vacab_sprint_test.db", "WordEntry")
#     print(word_entry_manager.get_all_words())
#     print(word_entry_manager.get_all_word_entries())
#     print(word_entry_manager.get_word_entry("hello"))
#     print(word_entry_manager.get_word_entries())
#     print(word_entry_manager.get_word_entry("hello2"))
#     print(word_entry_manager.get_word_entries())