"""Input validation utilities for user inputs and SQL queries"""

import json
import os
from typing import Set
from src.core.errors import ValidationError, SQLGenerationError
from src.core.logger import setup_logger
import sqlparse
from sqlparse.sql import IdentifierList, Identifier
from sqlparse.tokens import Keyword

logger = setup_logger('cadet.validation')

MAX_QUESTION_LENGTH = 1000

# File paths for schema validation
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_DIR = os.path.join(BASE_DIR, 'src')
SCHEMA_JSON_PATH = os.path.join(SRC_DIR, 'config', 'schema_info.json')


def validate_user_input(user_input: str, field_name: str = "input") -> str:
    """Validate and sanitize user input

    Args:
        user_input: Raw user input string
        field_name: Field name for error messages

    Returns:
        Sanitized input string

    Raises:
        ValidationError: If input is invalid
    """
    if not isinstance(user_input, str):
        logger.error(f"{field_name} is not a string: {type(user_input)}")
        raise ValidationError(f"{field_name} must be a string")

    # Strip whitespace
    sanitized = user_input.strip()

    # Check if empty
    if not sanitized:
        logger.warning(f"{field_name} is empty after stripping")
        raise ValidationError(f"{field_name} cannot be empty")

    # Check length
    if len(sanitized) > MAX_QUESTION_LENGTH:
        logger.warning(f"{field_name} exceeds max length: {len(sanitized)} > {MAX_QUESTION_LENGTH}")
        raise ValidationError(
            f"{field_name} is too long (max {MAX_QUESTION_LENGTH} characters)"
        )

    # Check for null bytes
    if '\x00' in sanitized:
        logger.error(f"{field_name} contains null bytes")
        raise ValidationError(f"{field_name} contains invalid characters")

    logger.debug(f"{field_name} validated successfully: {len(sanitized)} chars")
    return sanitized


def _extract_cte_names(sql_query: str) -> Set[str]:
    """
    Extract CTE (Common Table Expression) names from SQL query.

    CTEs are defined with: WITH cte_name AS (...)

    Args:
        sql_query: SQL query string

    Returns:
        Set of CTE names (lowercase)
    """
    import re
    cte_names = set()

    # Pattern: WITH name AS or WITH name1 AS (...), name2 AS (...)
    # Match: WITH followed by identifier before AS
    pattern = r'\bWITH\s+(\w+)\s+AS\b'
    matches = re.findall(pattern, sql_query, re.IGNORECASE)
    cte_names.update(m.lower() for m in matches)

    # Also match subsequent CTEs after commas: , name AS
    pattern = r',\s*(\w+)\s+AS\b'
    matches = re.findall(pattern, sql_query, re.IGNORECASE)
    cte_names.update(m.lower() for m in matches)

    return cte_names


def _extract_table_names(parsed_query) -> Set[str]:
    """
    Extract table names from parsed SQL query.

    Args:
        parsed_query: sqlparse parsed SQL statement

    Returns:
        Set of table names (lowercase)
    """
    tables = set()
    from_seen = False

    for token in parsed_query.tokens:
        if from_seen:
            if isinstance(token, (IdentifierList, Identifier)):
                identifiers = token.get_identifiers() if isinstance(token, IdentifierList) else [token]
                for ident in identifiers:
                    # Get real table name (remove alias if present)
                    if isinstance(ident, Identifier):
                        table_name = ident.get_real_name()
                    else:
                        table_name = str(ident).split()[0]  # Take first word before alias
                    tables.add(table_name.strip('"').strip('`').lower())
                from_seen = False  # Only reset after finding identifier

        if token.ttype is Keyword and token.value.upper() == 'FROM':
            from_seen = True

    return tables


def validate_sql_query(sql_query: str, allowed_tables: Set[str]) -> bool:
    """
    Validate SQL query for safety and correctness.

    Prevents SQL injection by checking for:
    - Dangerous keywords (DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE)
    - Multiple statements (semicolon-separated)
    - Comments that might hide malicious code
    - Table names not in schema

    Args:
        sql_query: SQL query string to validate
        allowed_tables: Set of valid table names from schema

    Returns:
        True if query is safe

    Raises:
        SQLGenerationError: If query is unsafe or invalid
    """
    # Normalize query
    query_upper = sql_query.upper()

    # Check for dangerous keywords
    dangerous_keywords = {
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER',
        'TRUNCATE', 'CREATE', 'GRANT', 'REVOKE', 'EXECUTE', 'EXEC'
    }

    for keyword in dangerous_keywords:
        if f' {keyword} ' in f' {query_upper} ':
            raise SQLGenerationError(
                f"Forbidden SQL keyword: {keyword}",
                details={'query': sql_query}
            )

    # Check for multiple statements (SQL injection vector)
    # Allow trailing semicolon, but block multiple statements
    sql_stripped = sql_query.rstrip(';').strip()
    if ';' in sql_stripped:
        raise SQLGenerationError(
            "Multiple SQL statements not allowed",
            details={'query': sql_query}
        )

    # Check for SQL comments (-- or /* */)
    if '--' in sql_query or '/*' in sql_query:
        raise SQLGenerationError(
            "SQL comments not allowed",
            details={'query': sql_query}
        )

    # Parse and validate table names
    try:
        parsed = sqlparse.parse(sql_query)[0]

        # Extract CTE names (temporary tables defined with WITH clause)
        cte_names = _extract_cte_names(sql_query)

        # Extract table names from query
        query_tables = _extract_table_names(parsed)

        # Remove CTE names from validation (they are not schema tables)
        actual_tables = query_tables - cte_names

        # Check if all tables are in schema
        invalid_tables = actual_tables - allowed_tables
        if invalid_tables:
            raise SQLGenerationError(
                f"Unknown tables in query: {invalid_tables}",
                details={'query': sql_query, 'allowed': list(allowed_tables)}
            )

        logger.info(f"SQL validation passed: {len(actual_tables)} schema tables, {len(cte_names)} CTEs")
        return True

    except Exception as e:
        raise SQLGenerationError(f"SQL parsing failed: {e}", details={'query': sql_query})
