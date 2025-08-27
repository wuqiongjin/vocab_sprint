import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Union, Dict, Any, TypedDict

from src.utils.exceptions import (
    ErrorCode, DatabaseError, DatabaseConnectionError, TableNotFoundError, 
    ColumnNotFoundError, ValidationError, NoRowsAffectedError
)
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

class TableConfig(TypedDict, total=False):
    """
    Table configuration (all parameters are optional)

    Attributes:
        primary_key: Column name or list of column names for primary key.
        foreign_keys: List of foreign key definitions as (column, referenced_table, referenced_column).
        not_null_keys: List of column names that should have NOT NULL constraint.
        unique_keys: List of column names or lists of column names for unique constraints.
        default_values: Dictionary of default values for columns.
        check_constraints: List of check constraints as (column_name, condition).

    Usage:
        config = {"primary_key": "id", "not_null_keys": ["id", "name"]}
        or:
        config = {}  # empty config will create a table without any constraints
    """

    primary_key: Union[str, List[str]]
    foreign_keys: List[tuple[str, str, str]]
    not_null_keys: List[str]
    unique_keys: List[Union[str, List[str]]]
    default_values: Dict[str, Any]
    check_constraints: List[tuple[str, str]]

class OrderDirection(Enum):
    ASC = "ASC"
    DESC = "DESC"

@dataclass
class JoinClause:
    table: str
    on: str
    join_type: str = "INNER"  # INNER, LEFT, RIGHT, FULL

@dataclass
class SelectQuery:
    """Query builder for select operations"""
    table: str
    columns: Optional[List[str]] = None
    where_clause: Optional[str] = None              # where = "age > ? AND status = ?"
    where_args: Optional[tuple] = None              # where_args = (25, "active")
    order_by: Optional[str] = None
    order_direction: OrderDirection = OrderDirection.ASC
    limit: Optional[int] = None
    offset: Optional[int] = None
    group_by: Optional[str] = None
    having: Optional[str] = None
    joins: Optional[List[JoinClause]] = None

    def __post_init__(self):
        """Basic validation"""
        if not self.table or not self.table.strip():
            raise ValidationError("Table name cannot be empty", {"parameter": "table"})

class DatabaseManager:
    def __init__(self, database_path: str, create_if_not_exist=False):
        """
        Initialize database manager.

        Args:
            database_path: Path to the SQLite database file.
            create_if_not_exist: If True, create database file if it doesn't exist.

        Raises:
            DatabaseConnectionError: If database connection fails.
            ValidationError: If database_path is invalid.
        """
        if not database_path:
            raise ValidationError("Database path cannot be empty", {"parameter": "database_path"})
        self.database_path = database_path
        self.create_if_not_exist = create_if_not_exist
        self.conn = None
        self.cursor = None
        self.__connect()

    def __connect(self):
        """Establish database connection."""
        try:
            if not os.path.exists(self.database_path):
                if not self.create_if_not_exist:
                    raise DatabaseConnectionError(
                        "Database file not found", 
                        self.database_path,
                        {"create_if_not_exist": False}
                    )
                else:
                    logger.INFO(f"Database file not found, creating new database: {self.database_path}")
                    os.makedirs(os.path.dirname(self.database_path), exist_ok=True)


            self.conn = sqlite3.connect(self.database_path)
            # set row factory to return dict instead of tuple
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            logger.INFO(f"Connected to database: {self.database_path}")
            
        except sqlite3.Error as e:
            raise DatabaseConnectionError(
                f"SQLite connection error: {str(e)}",
                self.database_path,
                {"error_type": "sqlite3.Error"},
                e
            )
        except OSError as e:
            raise DatabaseConnectionError(
                f"OS error while accessing database: {str(e)}",
                self.database_path,
                {"error_type": "OSError"},
                e
            )
        except Exception as e:
            raise DatabaseConnectionError(
                f"Unexpected error during connection: {str(e)}",
                self.database_path,
                {"error_type": type(e).__name__},
                e
            )

    def __del__(self):
        try:
            self.close()
        except:
            Logger.ERROR("Error while closing database connection.")
            pass  # ignore any exception in destructor

    def create_table(self, table_name: str, columns: list[tuple[str, DataType]],
                    config: Optional[TableConfig] = None) -> bool:
        """
        Create a new table if it doesn't exist.

        Args:
            table_name: Name of the table to create.
            columns: List of column definitions, each as a tuple of (column_name, DataType).
            config: Table configuration.

        Returns:
            True if the table was created, False if it already exists.

        Raises:
            ValidationError: If table_name or columns are invalid.
            DatabaseError: If table creation fails.
        """
        if not table_name or not table_name.strip():
            raise ValidationError("Table name cannot be empty", 
                                {"parameter": "table_name"})
        
        if not columns:
            raise ValidationError("Columns list cannot be empty", 
                                {"parameter": "columns"})

        if self.check_table_exist(table_name):
            logger.INFO(f"Table '{table_name}' already exists, skipping creation")
            return False

        # get table configuration
        config = config or {}
        primary_key = config.get('primary_key') # if not provided, will be None
        foreign_keys = config.get('foreign_keys', [])
        not_null_keys = config.get('not_null_keys', [])
        unique_keys = config.get('unique_keys', [])
        default_values = config.get('default_values', {})
        check_constraints = config.get('check_constraints', [])

        # get all column names
        column_names = [col_name for col_name, _ in columns]

        # validate primary_key values
        if primary_key:
            if isinstance(primary_key, list):
                self.check_columns_valid(table_name, primary_key, column_names)
            else:
                self.check_columns_valid(table_name, [primary_key], column_names)

        # validate foreign_keys values
        fk_columns = [fk[0] for fk in foreign_keys]
        self.check_columns_valid(table_name, fk_columns, column_names)

        # validate not_null_keys values
        self.check_columns_valid(table_name, not_null_keys, column_names)
        
        # validate unique_keys values (composite keys are allowed. It should be flattened first!)
        flat_unique_keys = []
        for key in unique_keys:
            if isinstance(key, list):
                flat_unique_keys.extend(key)
            else:
                flat_unique_keys.append(key)
        self.check_columns_valid(table_name, flat_unique_keys, column_names)

        # validate default values
        self.check_columns_valid(table_name, default_values.keys(), column_names)

        # validate check_constraints values
        check_columns = [cc[0] for cc in check_constraints]
        self.check_columns_valid(table_name, check_columns, column_names)


        # column definitions (contains NOT NULL constraint and default value)
        column_definitions = []
        for col_name, data_type in columns:
            # add column definition
            not_null = " NOT NULL" if col_name in not_null_keys else ""

            # add default value
            default = ""
            if col_name in default_values:
                default_val = default_values[col_name]
                if isinstance(default_val, str) and data_type != DataType.TEXT:
                    default = f" DEFAULT {default_val}"
                else:
                    default = f" DEFAULT '{default_val}'"

            column_definitions.append(f"{col_name} {data_type.value}{not_null}{default}")


        # add primary key constraint
        if primary_key:
            if isinstance(primary_key, str):
                primary_key = [primary_key]
            pk_columns = ', '.join(primary_key)
            column_definitions.append(f"PRIMARY KEY ({pk_columns})")

        # add foreign key constraints
        for fk_column, ref_table, ref_column in foreign_keys:
            column_definitions.append(f"FOREIGN KEY ({fk_column}) REFERENCES {ref_table}({ref_column})")

        # add unique constraints
        for key in unique_keys:
            if isinstance(key, list):
                # composite unique key
                unique_columns = ', '.join(key)
                column_definitions.append(f"UNIQUE ({unique_columns})")
            else:
                # single unique key
                column_definitions.append(f"UNIQUE ({key})")

        # add extra check constraints
        for column_name, condition in check_constraints:
            column_definitions.append(f"CHECK ({column_name} {condition})")

        try:
            # build complete SQL statement
            sql = f"CREATE TABLE {table_name} ({', '.join(column_definitions)})"
            logger.DEBUG(f"Creating table: {sql}")

            self.cursor.execute(sql)
            self.conn.commit()
            logger.INFO(f"Created new table successfully: {table_name}")
            return True

        except sqlite3.Error as e:
            self.conn.rollback()
            raise DatabaseError(
                f"Failed to create table '{table_name}': {str(e)}",
                ErrorCode.DATABASE_ERROR,
                "create_table",
                {
                    "table_name": table_name, 
                    "columns": str(columns),
                    "sql": sql
                },
                e
            )

    def check_table_exist(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Raises:
            DatabaseError: If database query fails.
        """
        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            return self.cursor.fetchone() is not None
        except sqlite3.Error as e:
            raise DatabaseError(
                f"Failed to check table existence: {str(e)}",
                ErrorCode.DATABASE_ERROR,
                "check_table_exist",
                {"table_name": table_name},
                e
            )

    def check_columns_valid(self, table_name: str, columns_to_check: list[str],
                            table_columns: Optional[list[str]] = None) -> bool:
        """
        check if all the data keys are valid for the table

        Args:
            table_name: Name of the table to check. (the table may not exist yet!)
            columns_to_check: List of column names to check.
            table_columns: List of column names in the table. If not provided, it will be fetched from the database.

        Returns:
            bool: True if all the data keys are valid, False otherwise

        Raises:
            DatabaseError: If database query fails.
            TableNotFoundError: If table doesn't exist.
            ValidationError: If data is invalid.
        """
        if not columns_to_check:
            logger.DEBUG(f"No columns to check for table: {table_name}")
            return True

        # get all the table columns
        if not table_columns:
            table_columns = [col["name"] for col in self.get_table_columns(table_name)]

        invalid_columns = [col for col in columns_to_check if col not in table_columns]
        if invalid_columns:
            raise ColumnNotFoundError(
                table_name,
                invalid_columns,
                {
                    "table_name": table_name,
                    "invalid_columns": invalid_columns,
                    "valid_columns": table_columns
                }
            )
        return invalid_columns == []

    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get detailed information about all columns in a table.

        Returns:
            List of dictionaries with column information.

        Raises:
            TableNotFoundError: If table doesn't exist.
            DatabaseError: If database query fails.
        """
        try:
            if not self.check_table_exist(table_name):
                raise TableNotFoundError(table_name)

            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = []
            for row in self.cursor.fetchall():
                columns.append({
                    "cid": row[0],              # column id
                    "name": row[1],             # column name
                    "type": row[2],             # data type
                    "notnull": bool(row[3]),    # is 'not null' constraint
                    "dflt_value": row[4],       # default value
                    "pk": bool(row[5])          # is primary key
                })
            return columns

        except sqlite3.Error as e:
            raise DatabaseError(
                f"Failed to get table columns: {str(e)}",
                ErrorCode.DATABASE_ERROR,
                "get_table_columns",
                {"table_name": table_name},
                e
            )

    def insert_data(self, table_name: str, data: dict) -> int:
        """
        Insert data into a table.

        Returns:
            The rowid of the inserted row.

        Raises:
            TableNotFoundError: If table doesn't exist.
            ValidationError: If data is invalid.
            DatabaseError: If insertion fails.
        """
        if not data:
            raise ValidationError("No data to insert", 
                                {"table_name": table_name})

        # verify table exists
        if not self.check_table_exist(table_name):
            raise TableNotFoundError(table_name)

        # check columns are valid
        if not self.check_columns_valid(table_name, data):
            raise ValidationError("Invalid data", {"table_name": table_name})

        try:
            # use placeholder and parameterized query
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            values = list(data.values())

            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            logger.DEBUG(f"Inserting data: {query} with values {values}")

            self.cursor.execute(query, values)
            self.conn.commit()
            logger.INFO(f"Successfully inserted data into {table_name}")

            # Return the last inserted rowid
            return self.cursor.lastrowid

        except sqlite3.Error as e:
            self.conn.rollback()
            raise DatabaseError(
                f"Failed to insert data into table '{table_name}': {str(e)}",
                "insert_data",
                {"table_name": table_name, "data_keys": list(data.keys())},
                e
            )

    def update_data(self, table_name: str, data: dict, where_clause: str, where_args: tuple = None,
                    raise_if_no_rows: bool = False) -> int:
        """
        Update data in a table.

        Args:
            table_name: Name of the table to update.
            data: Dictionary of column-value pairs to update.
            where_clause: SQL WHERE clause (without the WHERE keyword).
            where_args: Parameters for the WHERE clause.

        Returns:
            Number of rows affected.

        Raises:
            TableNotFoundError: If table doesn't exist.
            ValidationError: If data or where clause is invalid.
            DatabaseError: If update fails.
            NoRowsAffectedError: If no rows are updated and raise_if_no_rows is True.
        """
        if not data:
            raise ValidationError("No data to update", 
                                {"table_name": table_name})

        if not where_clause:
            raise ValidationError("Where clause is required for update", 
                                {"table_name": table_name})

        # verify table exists
        if not self.check_table_exist(table_name):
            raise TableNotFoundError(table_name)

        # check columns are valid
        if not self.check_columns_valid(table_name, data):
            raise ValidationError("Invalid data", {"table_name": table_name})

        try:
            # build SET clause
            set_clause = ', '.join([f"{col} = ?" for col in data.keys()])
            values = list(data.values())

            # add WHERE clause parameters if provided
            if where_args:
                values.extend(where_args)

            query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
            logger.DEBUG(f"Updating data: {query} with values {values}")

            self.cursor.execute(query, values)
            self.conn.commit()
            affected_rows = self.cursor.rowcount
            logger.INFO(f"Successfully updated {affected_rows} rows in {table_name}")

            # Check if no rows were updated and raise error if requested
            if affected_rows == 0 and raise_if_no_rows:
                raise NoRowsAffectedError(
                    "No rows were updated. Possible reasons: no matching records or identical data.",
                    {"table_name": table_name, "where_clause": where_clause, "where_args": where_args}
                )

            return affected_rows

        except sqlite3.Error as e:
            self.conn.rollback()
            raise DatabaseError(
                f"Failed to update data in table '{table_name}': {str(e)}",
                "update_data",
                {"table_name": table_name, "data_keys": list(data.keys())},
                e
            )

    def delete_data(self, table_name: str, where_clause: str, where_args: tuple = None,
                    raise_if_no_rows: bool = False) -> int:
        """
        Delete data from a table.

        Args:
            table_name: Name of the table to delete from.
            where_clause: SQL WHERE clause (without the WHERE keyword).
            where_args: Parameters for the WHERE clause.

        Returns:
            Number of rows affected.

        Raises:
            TableNotFoundError: If table doesn't exist.
            ValidationError: If where clause is invalid.
            DatabaseError: If deletion fails.
            NoRowsAffectedError: If no rows are updated and raise_if_no_rows is True.
        """
        if not where_clause:
            raise ValidationError("Where clause is required for delete", 
                                {"table_name": table_name})

        try:
            # verify table exists
            if not self.check_table_exist(table_name):
                raise TableNotFoundError(table_name)

            query = f"DELETE FROM {table_name} WHERE {where_clause}"
            logger.DEBUG(f"Deleting data: {query}")

            if where_args:
                self.cursor.execute(query, where_args)
            else:
                self.cursor.execute(query)
 
            self.conn.commit()
            affected_rows = self.cursor.rowcount
            logger.INFO(f"Successfully deleted {affected_rows} rows from {table_name}")

            # Check if no rows were deleted and raise error if requested
            if affected_rows == 0 and raise_if_no_rows:
                raise NoRowsAffectedError(
                    "No rows were deleted. Possible reasons: no matching records or identical data.",
                    {"table_name": table_name, "where_clause": where_clause, "where_args": where_args}
                )

            return affected_rows

        except sqlite3.Error as e:
            self.conn.rollback()
            raise DatabaseError(
                f"Failed to delete data from table '{table_name}': {str(e)}",
                "delete_data",
                {"table_name": table_name, "where_clause": where_clause},
                e
            )

    def select_data(self, query: SelectQuery) -> List[Dict]:
        """
        select data from a table

        Args:
            query: SelectQuery contains all the information needed to select data from a table

        Returns:
            List of dictionaries representing the selected rows.

        Raises:
            TableNotFoundError: If table doesn't exist.
            DatabaseError: If selection fails.
        """
        try:
            # verify table exists
            if not self.check_table_exist(query.table):
                raise TableNotFoundError(query.table)

            # build SELECT clause
            select_clause = '*'
            if query.columns:
                select_clause = ', '.join(query.columns)

            # build base query
            sql_parts = [f"SELECT {select_clause} FROM {query.table}"]

            # add JOIN clauses
            if query.joins:
                for join in query.joins:
                    sql_parts.append(f"{join.join_type} JOIN {join.table} ON {join.on}")

            # add WHERE clause
            if query.where_clause:
                sql_parts.append(f"WHERE {query.where_clause}")

            # add GROUP BY clause
            if query.group_by:
                sql_parts.append(f"GROUP BY {query.group_by}")

                # add HAVING clause
                if query.having:
                    sql_parts.append(f"HAVING {query.having}")

            # add ORDER BY clause
            if query.order_by:
                direction = query.order_direction.value
                sql_parts.append(f"ORDER BY {query.order_by} {direction}")

            # add LIMIT and OFFSET clauses
            if query.limit is not None:
                sql_parts.append(f"LIMIT {query.limit}")
                if query.offset is not None:
                    sql_parts.append(f"OFFSET {query.offset}")

            # build final SQL
            sql = " ".join(sql_parts)
            logger.INFO(f"Executing query: {sql} with args: {query.where_args}")

            # execute query
            if query.where_args:
                self.cursor.execute(sql, query.where_args)
            else:
                self.cursor.execute(sql)

            # fetch results and convert to list of dictionaries
            rows = self.cursor.fetchall()
            result = [dict(row) for row in rows]

            logger.INFO(f"Successfully selected {len(result)} rows from {query.table}")
            return result

        except sqlite3.Error as e:
            raise DatabaseError(
                f"Failed to select data from table '{query.table}': {str(e)}",
                "select",
                {"table": query.table, "sql": sql},
                e
            )

    def select_one(self, query: SelectQuery) -> Optional[Dict]:
        """
        execute select query and return the first row

        Args:
            query: select query

        Returns:
            first row of the query or None if no row is found.
        """
        query.limit = 1
        results = self.select_data(query)
        return results[0] if results else None

    def count(self, table: str, where: Optional[str] = None, where_args: Optional[tuple] = None) -> int:
        """
        count the number of records which meet the condition in a table

        Args:
            table: table name
            where: where clause
            where_args: where clause parameters

        Returns:
            Number of records.
        """
        query = SelectQuery(
            table=table,
            columns=["COUNT(*) as count"],
            where=where,
            where_args=where_args
        )

        result = self.select_one(query)
        return result["count"] if result else 0

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

    def execute_raw_sql(self, sql: str, params: tuple = None) -> List[Dict]:
        """
        Execute raw SQL query.

        Args:
            sql: SQL query to execute.
            params: Parameters for the query.

        Returns:
            List of dictionaries representing the query results.

        Raises:
            DatabaseError: If query execution fails.
        """
        try:
            logger.DEBUG(f"Executing raw SQL: {sql}")

            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)

            # Check if this is a query that returns results
            if self.cursor.description is not None:
                # this is a SELECT statement
                rows = self.cursor.fetchall()
                result = [dict(row) for row in rows]
                logger.INFO(f"Raw SQL executed successfully, returned {len(result)} rows")
                return result
            else:
                # this is an INSERT, UPDATE, or DELETE statement
                self.conn.commit()
                affected_rows = self.cursor.rowcount
                logger.INFO(f"Raw SQL executed successfully, affected {affected_rows} rows")
                return [{"affected_rows": affected_rows}]

        except sqlite3.Error as e:
            self.conn.rollback()
            raise DatabaseError(
                f"Failed to execute raw SQL: {str(e)}",
                "execute_raw_sql",
                {"sql": sql},
                e
            )

    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.
        
        Example:
            with db.transaction():
                db.insert_data(...)
                db.update_data(...)
        """
        try:
            yield
            self.conn.commit()
            logger.DEBUG("Transaction committed successfully")
        except Exception as e:
            self.conn.rollback()
            logger.ERROR(f"Transaction rolled back due to error: {e}")
            raise

    def is_connected(self) -> bool:
        return self.conn is not None
    
    def reconnect(self):
        self.close()
        self.__connect()

    def close(self):
        if hasattr(self, "cursor") and self.cursor:
            self.cursor.close()
            self.cursor = None
        if hasattr(self, "conn") and self.conn:
            self.conn.close()
            self.conn = None
        logger.INFO(f"Database connection closed: {self.database_path}")



# # 测试
# if __name__ == "__main__":
#  #   # test create table, insert data, export table data
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

    # @dataclass
    # class WordEntry:
    #     word: str
    #     phonetic_UK: str
    #     phonetic_US: str
    #     interp_Noun: str = ""
    #     interp_Verb: str = ""
    #     interp_Adj: str = ""
    #     interp_Adv: str = ""
    #     interp_Pron: str = ""
    #     interp_Prep: str = ""
    #     interp_Conj: str = ""
    #     interp_Intj: str = ""
    #     interp_Art: str = ""
    #     interp_Det: str = ""
    #     interp_Num: str = ""
    #     interp_Aux: str = ""
    #     interp_Others: str = ""

    # database_manager.insert_data("WordEntry", WordEntry(
    #     word="hello2",
    #     phonetic_UK="həˈləʊ",
    #     phonetic_US="həˈləʊ",
    #     interp_Noun="a greeting",
    #     interp_Verb="to greet",
    #     interp_Adj="friendly",
    #     interp_Adv="gently",
    # ).__dict__)

    # print(database_manager.export_table_data("WordEntry"))