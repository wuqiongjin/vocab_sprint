from enum import Enum
from typing import Optional, Any

class ErrorCode(Enum):
    SUCCESS = 0
    # General errors (1-99)
    UNKNOWN_ERROR = 1
    VALIDATION_ERROR = 2
    INVALID_ARGUMENT = 3
    RESOURCE_NOT_FOUND = 4
    PERMISSION_DENIED = 5

    # Internal errors (100-199)
    INTERNAL_ERROR = 100
    CONFIGURATION_ERROR = 101

    # Database errors (200-299)
    DATABASE_ERROR = 200
    DATABASE_CONNECTION_ERROR = 201
    DATABASE_QUERY_ERROR = 202
    DATABASE_TIMEOUT_ERROR = 203
    TABLE_NOT_FOUND = 204
    COLUMN_NOT_FOUND = 205
    INVALID_TABLE_STRUCTURE = 206

    # Network errors (300-399)
    NETWORK_ERROR = 300
    NETWORK_CONNECTION_ERROR = 301
    NETWORK_TIMEOUT_ERROR = 302

    # Timeout errors (400-499)
    TIMEOUT_ERROR = 400

    # Add more as needed...

class BaseError(Exception):
    """
    Base error class for all custom exceptions.
    """
    DEFAULT_CODE = ErrorCode.UNKNOWN_ERROR

    def __init__(
            self,
            message: str,
            code: ErrorCode = None,
            details: Optional[dict[str, Any]] = None,   # provide additional details about the error
            cause: Exception = None                     # save the original exception
    ):
        self.message = message
        self.code = code or self.DEFAULT_CODE
        self.details = details or {}
        self.cause = cause

        # construct the full error message
        full_message = f"{self.code.name}: {self.message}"
        if self.details:
            full_message += f" | Details: {self.details}"
        if self.cause:
            full_message += f" | Caused by: {type(self.cause).__name__}: {str(self.cause)}"

        super().__init__(full_message)

    def __str__(self):
        return self.args[0] if self.args else f"{self.code.name}: {self.message}"

    def __repr__(self):
        return f"{self.__class__.__name__}(message={self.message!r}, code={self.code}, details={self.details!r})"

    def to_dict(self) -> dict[str, Any]:
        """convert the error to a dict"""
        return {
            "type": self.__class__.__name__,
            "code": self.code.value,
            "message": self.message,
            "details": self.details,
            "cause": str(self.cause) if self.cause else None
        }

class ValidationError(BaseError):
    """
    Raised when data validation fails.
    """
    DEFAULT_CODE = ErrorCode.VALIDATION_ERROR
    
    def __init__(
        self, 
        message: str, 
        details: dict[str, Any] = None,
        cause: Exception = None
    ):
        super().__init__(message, self.DEFAULT_CODE, details, cause)

class InvalidArgumentError(BaseError):
    """
    Raised when an argument is invalid.
    """
    DEFAULT_CODE = ErrorCode.INVALID_ARGUMENT
    
    def __init__(
        self, 
        message: str, 
        details: dict[str, Any] = None,
        cause: Exception = None
    ):
        super().__init__(message, self.DEFAULT_CODE, details, cause)

class ResourceNotFoundError(BaseError):
    """
    Raised when a requested resource is not found.
    """
    DEFAULT_CODE = ErrorCode.RESOURCE_NOT_FOUND
    
    def __init__(
        self, 
        message: str,
        resource_type: str, 
        resource_id: str | int,
        details: dict[str, Any] = None,
        cause: Exception = None
    ):
        message = f"{message}. {resource_type} with ID {resource_id} not found"
        super().__init__(message, self.DEFAULT_CODE, details, cause)

class InternalError(BaseError):
    """
    Raised when an internal error occurs.
    """
    DEFAULT_CODE = ErrorCode.INTERNAL_ERROR
    
    def __init__(
        self, 
        message: str, 
        details: dict[str, Any] = None,
        cause: Exception = None
    ):
        super().__init__(message, self.DEFAULT_CODE, details, cause)

class DatabaseError(BaseError):
    """
    Raised when a database error occurs.
    """
    DEFAULT_CODE = ErrorCode.DATABASE_ERROR
    
    def __init__(
        self, 
        message: str, 
        code: ErrorCode = None,
        operation: str = None,
        details: dict[str, Any] = None,
        cause: Exception = None
    ):
        # if code is not provided, use the default code
        code = code or self.DEFAULT_CODE

        if operation:
            message = f"Database operation '{operation}' failed: {message}"
        super().__init__(message, code, details, cause)

class DatabaseConnectionError(DatabaseError):
    """
    Raised when database connection fails.
    """
    DEFAULT_CODE = ErrorCode.DATABASE_CONNECTION_ERROR

    def __init__(
        self, 
        message: str, 
        database_path: str = None,
        details: dict[str, Any] = None,
        cause: Exception = None
    ):
        if database_path:
            message = f"Failed to connect to database '{database_path}': {message}"
        super().__init__(message, self.DEFAULT_CODE, "connect", details, cause)

class TableNotFoundError(DatabaseError):
    """
    Raised when a table is not found in the database.
    """
    DEFAULT_CODE = ErrorCode.TABLE_NOT_FOUND

    def __init__(
        self, 
        table_name: str,
        details: dict[str, Any] = None,
        cause: Exception = None
    ):
        message = f"Table '{table_name}' not found in database"
        super().__init__(message, self.DEFAULT_CODE, "table_check", details, cause)

class ColumnNotFoundError(DatabaseError):
    """
    Raised when a column is not found in a table.
    """
    DEFAULT_CODE = ErrorCode.COLUMN_NOT_FOUND

    def __init__(
        self, 
        table_name: str,
        column_name: str,
        details: dict[str, Any] = None,
        cause: Exception = None
    ):
        message = f"Column '{column_name}' not found in table '{table_name}'"
        super().__init__(message, self.DEFAULT_CODE, "column_check", details, cause)

class InvalidTableStructureError(DatabaseError):
    """
    Raised when table structure is invalid.
    """
    DEFAULT_CODE = ErrorCode.INVALID_TABLE_STRUCTURE

    def __init__(
        self, 
        table_name: str,
        message: str,
        details: dict[str, Any] = None,
        cause: Exception = None
    ):
        full_message = f"Invalid structure for table '{table_name}': {message}"
        super().__init__(full_message, self.DEFAULT_CODE, "table_structure", details, cause)

# # test
# if __name__ == '__main__':
#     try:
#         raise ValidationError("Invalid input", {"field": "value"})
#     except BaseError as e:
#         print(e)