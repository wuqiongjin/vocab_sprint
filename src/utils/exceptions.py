from enum import Enum
from typing import Optional, Any

class ErrorCode(Enum):
    SUCCESS = 0
    UNKNOWN_ERROR = 1
    INVALID_ARGUMENT = 2
    VALIDATION_ERROR = 3
    RESOURCE_NOT_FOUND = 4
    INTERNAL_ERROR = 5
    DATABASE_ERROR = 6
    NETWORK_ERROR = 7
    TIMEOUT_ERROR = 8
    PERMISSION_DENIED = 9
    CONFIGURATION_ERROR = 10

class BaseError(Exception):
    """
    Base error class for all custom exceptions.
    """
    DEFAULT_CODE = ErrorCode.UNKNOWN_ERROR

    def __init__(
            self,
            message: str,
            code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
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
    DEFAULT_CODE = ErrorCode.INVALID_ARGUMENT
    
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
    DEFAULT_CODE = ErrorCode.INTERNAL_ERROR
    
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
        operation: str = None,
        details: dict[str, Any] = None,
        cause: Exception = None
    ):
        if operation:
            message = f"Database operation '{operation}' failed: {message}"
        super().__init__(message, self.DEFAULT_CODE, details, cause)


# # test
# if __name__ == '__main__':
#     try:
#         raise ValidationError("Invalid input", {"field": "value"})
#     except BaseError as e:
#         print(e)