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
    
    # Remove comments to avoid false positives
    sql_clean = re.sub(r'--.*', '', sql_query)
    sql_clean = re.sub(r'/\*.*?\*/', '', sql_clean, flags=re.DOTALL)
    
    # Find CTE definitions directly
    # Pattern: identifier AS (
    # This captures "name" in "WITH name AS (" or ", name AS ("
    # It is robust because "AS (" is distinctive for CTEs and some function calls
    # Even if it matches function aliases like "generate_series(...) AS x(id)", 
    # treating 'x' as a CTE/temporary name is actually correct for validation purposes.
    cte_pattern = r'\b(\w+)\s+AS\s*\('
    matches = re.findall(cte_pattern, sql_clean, re.IGNORECASE)
    cte_names.update(m.lower() for m in matches)
        
    return cte_names


def _extract_subquery_aliases(sql_query: str) -> Set[str]:
    """
    Extract subquery aliases from SQL query using sqlparse.
    
    This function traverses the parsed SQL tree to find identifiers that act as aliases
    for subqueries. It handles complex nested queries better than regex.
    
    Example:
        SELECT * FROM (SELECT ...) AS my_alias
        -> Returns {'my_alias'}
    
    Args:
        sql_query: SQL query string
        
    Returns:
        Set of subquery alias names (lowercase)
    """
    import sqlparse
    from sqlparse.sql import Identifier, IdentifierList, Parenthesis
    from sqlparse.tokens import Keyword, DML
    
    aliases = set()
    
    try:
        parsed = sqlparse.parse(sql_query)[0]
    except:
        return aliases

    def _extract_from_token(token):
        # If token is an identifier (e.g., "(SELECT ...) AS alias")
        if isinstance(token, Identifier):
            # Check if it has an alias
            if token.has_alias():
                # Check if the real name is a subquery (starts with parenthesis)
                # This is a heuristic because sqlparse doesn't always strictly type subqueries
                real_name = token.get_real_name()
                # If real_name is None, it might be a subquery structure
                if real_name is None or real_name.strip().startswith('('):
                    aliases.add(token.get_alias().lower())
        
        # If token is a list of identifiers (e.g. "table1, table2")
        elif isinstance(token, IdentifierList):
            for identifier in token.get_identifiers():
                _extract_from_token(identifier)
        
        # Recursively check children to find nested subqueries
        if hasattr(token, 'tokens'):
            for child in token.tokens:
                _extract_from_token(child)

    _extract_from_token(parsed)
    return aliases


def _extract_table_names(parsed_query) -> Set[str]:
    """
    Extract table names from parsed SQL query.
    Handles FROM clauses, JOIN clauses, and subqueries.

    Improved logic to distinguish table references from column references
    in function contexts (e.g., EXTRACT(field FROM column)).

    Args:
        parsed_query: sqlparse parsed SQL statement

    Returns:
        Set of table names (lowercase)
    """
    from sqlparse.sql import Function, Parenthesis

    tables = set()
    from_or_join_seen = False

    for token in parsed_query.tokens:
        # Skip FROM keywords inside function calls
        # Functions are parsed as Function or Parenthesis tokens
        # This prevents EXTRACT(DOW FROM column) from being parsed as a table reference
        if isinstance(token, (Function, Parenthesis)):
            # Do NOT recursively process - skip entirely to avoid false positives
            # FROM inside functions (like EXTRACT(DOW FROM column)) should be ignored
            continue

        # Check for FROM or JOIN keywords (only at statement level, not inside functions)
        if token.ttype is Keyword and token.value.upper() in ('FROM', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'CROSS'):
            from_or_join_seen = True
            continue

        # Skip keywords like OUTER, ON
        if token.ttype is Keyword:
            if from_or_join_seen and token.value.upper() in ('OUTER', 'ON', 'USING'):
                from_or_join_seen = False
            continue

        # Extract table names when we've seen FROM or JOIN
        if from_or_join_seen:
            if isinstance(token, (IdentifierList, Identifier)):
                identifiers = token.get_identifiers() if isinstance(token, IdentifierList) else [token]
                for ident in identifiers:
                    # Get real table name (remove alias if present)
                    if isinstance(ident, Identifier):
                        # get_real_name() returns the table name without alias
                        table_name = ident.get_real_name()
                        if table_name:  # Only add if not empty
                            tables.add(table_name.strip('"').strip('`').lower())
                    else:
                        # Fallback: take first word before alias
                        table_str = str(ident).strip()
                        if table_str and not table_str.upper() in ('SELECT', 'WHERE', 'GROUP', 'ORDER', 'HAVING'):
                            table_name = table_str.split()[0]
                            tables.add(table_name.strip('"').strip('`').lower())
                from_or_join_seen = False

        # Recursively handle subqueries (non-function parentheses already handled above)
        if hasattr(token, 'tokens') and not isinstance(token, (Function, Parenthesis)):
            subtables = _extract_table_names(token)
            tables.update(subtables)

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

        # Extract subquery aliases (FROM (SELECT ...) AS alias)
        subquery_aliases = _extract_subquery_aliases(sql_query)

        # Extract table names from query
        query_tables = _extract_table_names(parsed)

        # Remove CTE names and subquery aliases from validation (they are not schema tables)
        # Handle fuzzy matching for CTEs (e.g. LLM generated "name_cte" but used "name")
        actual_tables = set()
        
        for table in query_tables:
            # Check if it's a known CTE or subquery alias
            if table in cte_names or table in subquery_aliases:
                # Skip this table because it is a CTE or subquery alias
                continue
            
            # # Fuzzy check: if table is a prefix of any CTE name (e.g. "supplier" in "supplier_cte")
            # # or if any CTE name is a prefix of table (e.g. "supplier_cte" in "supplier_cte_1")
            # is_cte_variant = False
            # for cte in cte_names:
            #     if table in cte or cte in table:
            #         is_cte_variant = True
            #         break
            
            # if is_cte_variant:
            #     # Skip this table because it is a CTE variant
            #     continue
                
            actual_tables.add(table)

        # Check if all tables are in schema
        invalid_tables = actual_tables - allowed_tables
        if invalid_tables:
            # Debug logging to understand what went wrong
            logger.error(f"=== SQL Validation Failed ===")
            logger.error(f"Invalid tables: {invalid_tables}")
            logger.error(f"CTE names found: {cte_names}")
            logger.error(f"Subquery aliases found: {subquery_aliases}")
            logger.error(f"All extracted tables: {query_tables}")
            logger.error(f"Actual tables (after filtering): {actual_tables}")
            logger.error(f"Allowed tables: {sorted(allowed_tables)}")
            logger.error(f"SQL query:\n{sql_query}")
            logger.error(f"===========================")

            raise SQLGenerationError(
                f"Unknown tables in query: {invalid_tables}",
                details={'query': sql_query, 'allowed': list(allowed_tables)}
            )

        logger.info(f"SQL validation passed: {len(actual_tables)} schema tables, {len(cte_names)} CTEs, {len(subquery_aliases)} subquery aliases")
        return True

    except (IndexError, ValueError, AttributeError) as e:
        raise SQLGenerationError(f"SQL parsing failed: {e}", details={'query': sql_query})
