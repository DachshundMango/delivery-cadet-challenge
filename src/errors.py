from typing import Optional, Dict, Any


class CadetError(Exception):
    """
    Base exception for CADET application.

    All custom exceptions should inherit from this class.
    """
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DatabaseError(CadetError):
    """Database operation failures"""
    pass


class SQLGenerationError(CadetError):
    """LLM failed to generate valid SQL query"""
    pass


class SQLExecutionError(DatabaseError):
    """
    SQL execution failures.

    Includes information about the failed query and original error.
    """
    def __init__(self, message: str, sql_query: str, original_error: Exception):
        super().__init__(
            message=message,
            details={
                'sql_query': sql_query,
                'original_error': str(original_error),
                'error_type': type(original_error).__name__
            }
        )


class SchemaLoadError(CadetError):
    """Schema information loading failures"""
    pass


class ValidationError(CadetError):
    """Input validation failures"""
    pass


class LLMError(CadetError):
    """LLM API call failures"""
    pass
