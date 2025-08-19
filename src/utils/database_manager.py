import os
import sqlite3
from enum import Enum

from src.utils.logger import Logger

logger = Logger("database_manager")

class DataType(Enum):
    """SQLite Data Type"""
    TEXT = "TEXT"
    INTEGER = "INTEGER"
    REAL = "REAL"
    BLOB = "BLOB"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    DATETIME = "DATETIME"
    NUMERIC = "NUMERIC"

class DatabaseManager:
    def __init__(self, database_path):
        if not os.path.exists(database_path):
            logger.INFO(f"Database file not found: {database_path}, creating...")
        self.conn = sqlite3.connect(database_path)
        self.cursor = self.conn.cursor()

    def __del__(self):
        self.close()

    def create_table(self, table_name: str, columns: list[tuple[str, DataType]]):
        # columns is a list of tuples, each tuple contains (column name, data type)
        column_definitions = ', '.join([f"{col_name} {data_type.value}" for col_name, data_type in columns])
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({column_definitions})"
        logger.DEBUG(f"Creating table: {sql}")
        self.cursor.execute(sql)
        self.conn.commit()

    def insert_data(self, table_name: str, data: dict):
        if not data:
            logger.ERROR(f"No data to insert into table: {table_name}")
            return

        # verify table exists
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not self.cursor.fetchone():
            raise ValueError(f"Table '{table_name}' does not exist")

        # get table columns
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        table_columns = [row[1] for row in self.cursor.fetchall()]
        
        # verify if the columns in the data are valid
        invalid_columns = [col for col in data.keys() if col not in table_columns]
        if invalid_columns:
            raise ValueError(f"Invalid columns: {invalid_columns}. Valid columns are: {table_columns}")

        # use placeholder and parameterized query
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        values = list(data.values())

        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        logger.DEBUG(f"Inserting data: {query}")
        
        try:
            self.cursor.execute(query, values)
            self.conn.commit()
            logger.INFO(f"Successfully inserted data into {table_name}")
        except sqlite3.Error as e:
            logger.ERROR(f"Error inserting data: {e}")
            self.conn.rollback()
            raise

    def export_table_data(self, table_name: str) -> dict:
        """
        export all data from the database, return a dictionary, the key is word, the value is the row data
        """
        self.cursor.execute(f"SELECT * FROM {table_name}")
        rows = self.cursor.fetchall()
        data = {}
        for row in rows:
            data[row[0]] = row[:]
        return data

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()



# # 测试
# if __name__ == "__main__":
#     # test create table, insert data, export table data
#     database_manager = DatabaseManager("./test.db")
#     colmns = [
#         ("word", DataType.TEXT),
#         ("phonetic_UK", DataType.TEXT),
#         ("phonetic_US", DataType.TEXT),
#         ("interp_Noun", DataType.TEXT),
#         ("interp_Verb", DataType.TEXT),
#         ("interp_Adj", DataType.TEXT),
#         ("interp_Adv", DataType.TEXT),
#     ]
#     database_manager.create_table("WordEntry", colmns)
#     database_manager.insert_data("WordEntry", {
#         "word": "hello",
#         "phonetic_UK": "həˈləʊ",
#         "phonetic_US": "həˈləʊ",
#         "interp_Noun": "a greeting",
#         "interp_Verb": "to greet",
#     })
#     data = database_manager.export_table_data("WordEntry")
#     print(data)


    # test insert WordEntry to database
#     from dataclasses import dataclass

#     @dataclass
#     class WordEntry:
#         word: str
#         phonetic_UK: str
#         phonetic_US: str
#         interp_Noun: str = ""
#         interp_Verb: str = ""
#         interp_Adj: str = ""
#         interp_Adv: str = ""
#         interp_Pron: str = ""
#         interp_Prep: str = ""
#         interp_Conj: str = ""
#         interp_Intj: str = ""
#         interp_Art: str = ""
#         interp_Det: str = ""
#         interp_Num: str = ""
#         interp_Aux: str = ""
#         interp_Others: str = ""

#     database_manager.insert_data("WordEntry", WordEntry(
#         word="hello2",
#         phonetic_UK="həˈləʊ",
#         phonetic_US="həˈləʊ",
#         interp_Noun="a greeting",
#         interp_Verb="to greet",
#         interp_Adj="friendly",
#         interp_Adv="gently",
#     ).__dict__)

#     print(database_manager.export_table_data("WordEntry"))