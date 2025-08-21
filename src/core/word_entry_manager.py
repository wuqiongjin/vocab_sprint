from src.core.word_entry import WordEntry
from src.utils.database_manager import DatabaseManager, DataType
from src.utils.logger import Logger

logger = Logger(__name__)

class WordEntryManager:
    def __init__(self, database_manager: DatabaseManager, table_name: str):
        self.database_manager = database_manager
        # check table exist
        if not self.database_manager.check_table_exist(table_name):
            raise Exception(f"table {table_name} not exist")

        # load data from database
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
#     database_manager = DatabaseManager("./test.db", True)
#     colmns = [
#         ("word", DataType.TEXT),
#         ("phonetic_UK", DataType.TEXT),
#         ("phonetic_US", DataType.TEXT),
#         ("interp_Noun", DataType.TEXT),
#         ("interp_Verb", DataType.TEXT),
#         ("interp_Adj", DataType.TEXT),
#         ("interp_Adv", DataType.TEXT),
#     ]
#     print(f"create status: {database_manager.create_table('WordEntry', colmns)}")
#     database_manager.insert_data("WordEntry", {
#         "word": "goods",
#         "phonetic_UK": "gʊdz",
#         "phonetic_US": "ɡʊdz",
#         "interp_Noun": "商品",
#     })
#     word_entry_manager = WordEntryManager(database_manager, "WordEntry")
#     print(word_entry_manager.get_all_words())
#     print(word_entry_manager.get_all_word_entries())
#     print(word_entry_manager.get_word_entry("hello"))
#     print(word_entry_manager.get_word_entries())
#     print(word_entry_manager.get_word_entry("hello2"))
#     print(word_entry_manager.get_word_entries())