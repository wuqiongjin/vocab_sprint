from src.core.word_entry import WordEntry
from src.utils.database_manager import DatabaseManager
from src.utils.logger import Logger
from src.utils.exceptions import TableNotFoundError, ColumnNotFoundError, InvalidTableStructureError

logger = Logger("word_entry_manager")

class WordEntryManager:
    def __init__(self, database_manager: DatabaseManager, table_name: str):
        self.database_manager = database_manager
        # check table exist
        if not self.database_manager.check_table_exist(table_name):
            raise TableNotFoundError(table_name)
        
        word_entry_columns = WordEntry.get_database_columns()
        table_columns = [col["name"] for col in self.database_manager.get_table_columns(table_name)]

        try:
            # check table structure (Must exactly match WordEntry class)
            # 1. check if all columns in WordEntry class are in the database table
            self.database_manager.check_columns_valid(table_name, word_entry_columns, table_columns)
            # 2. check if all columns in the database table are in WordEntry class
            self.database_manager.check_columns_valid(table_name, table_columns, word_entry_columns)
        except ColumnNotFoundError as e:
            raise InvalidTableStructureError(
                f"Table {table_name} structure is invalid",
                {
                    "word_entry_columns": word_entry_columns,
                    "actual_columns": table_columns,
                },
                e
            )

        self.table_name = table_name
        # load data from database
        self.word_dict = {entry_dict['Word']: WordEntry.from_flat_dict(entry_dict) for entry_dict in self.database_manager.export_table_data(table_name)}

    def add_word_entry(self, word_entry: WordEntry) -> bool:
        if word_entry.word in self.word_dict:
            logger.ERROR(f"add_word_entry failed! word: {word_entry.word} already exists")
            return False
        self.word_dict[word_entry.word] = word_entry
        self.database_manager.insert_data(self.table_name, word_entry.to_flat_dict())
        return True

    def get_word_entries(self):
        return self.word_dict
    
    def get_word_entry(self, word: str):
        return self.word_dict.get(word)

    def remove_word_entry(self, word: str) -> bool:
        if word not in self.word_dict:
            logger.ERROR(f"remove_word_entry failed! word: {word} not found in {self.table_name}")
            return False
        self.word_dict.pop(word)
        self.database_manager.delete_data(self.table_name, f"word='{word}'")
        return True
         
    def update_word_entry(self, word: str, word_entry: WordEntry) -> bool:
        if word not in self.word_dict:
            logger.ERROR(f"update_word_entry failed! word: {word} not found in {self.table_name}")
            return False
        self.word_dict[word] = word_entry
        self.database_manager.update_data(self.table_name, word_entry.to_flat_dict(), f"word='{word}'")
        return True

    def get_all_words(self):
        return list(self.word_dict.keys())
    
    def get_all_word_entries(self):
        return list(self.word_dict.values())