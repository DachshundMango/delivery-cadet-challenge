"""
Core Utilities

Shared utilities for database connections, logging, validation, and error handling.
"""

# Import in dependency order to avoid circular imports
from .logger import setup_logger
from .errors import (
    ValidationError,
    SQLGenerationError,
    SchemaLoadError,
    LLMError,
)
from .db import get_db_engine
from .validation import validate_user_input

__all__ = [
    # Logging
    'setup_logger',
    # Errors
    'ValidationError',
    'SQLGenerationError',
    'SchemaLoadError',
    'LLMError',
    # Database
    'get_db_engine',
    # Validation
    'validate_user_input',
]
