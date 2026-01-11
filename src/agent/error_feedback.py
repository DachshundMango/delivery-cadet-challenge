"""
Error feedback routing for SQL generation retry logic.

This module analyzes SQL error messages and returns targeted feedback strings
to help the LLM correct its query generation on retry attempts.

The error feedback system provides specific guidance based on:
- Unknown table names (with alias detection)
- Multiple SQL statements
- SQL comments
- Forbidden keywords
- Column not found errors (with alias detection)
- Division by zero
- Datetime format issues
- Generic parsing errors (catch-all)
"""

import re
import ast
from typing import Set
from src.agent.feedbacks import (
    get_unknown_tables_feedback,
    get_multiple_statements_feedback,
    get_sql_comments_feedback,
    get_forbidden_keyword_feedback,
    get_column_not_found_feedback,
    get_parsing_error_feedback,
    get_division_by_zero_feedback,
    get_datetime_format_feedback,
    get_alias_reference_feedback,
)
from src.core.logger import setup_logger

logger = setup_logger('cadet.error_feedback')


def get_sql_error_feedback(error_message: str, allowed_tables: Set[str]) -> str:
    """
    Analyze SQL error message and return targeted feedback.
    
    This function routes error messages to appropriate feedback generators,
    providing specific guidance to help the LLM correct SQL generation errors.
    
    Args:
        error_message: Error string from query_result (e.g., "Error: column not found")
        allowed_tables: Set of valid table names from schema
        
    Returns:
        Feedback string to append to SQL generation prompt
        
    Example:
        >>> feedback = get_sql_error_feedback("Error: Unknown tables: {'foo'}", {'users'})
        >>> "FEEDBACK:" in feedback
        True
    
    Note:
        This function is called during SQL retry attempts to provide
        error-specific guidance to the LLM for correction.
    """
    
    # Case 1: Unknown tables in query
    if 'Unknown tables in query' in error_message:
        match = re.search(r"Unknown tables in query: (\{.*?\})", error_message)
        if match:
            invalid_tables_str = match.group(1)
            # Safe parsing: use ast.literal_eval instead of eval
            try:
                invalid_tables_set = ast.literal_eval(invalid_tables_str)
            except (ValueError, SyntaxError):
                logger.warning(f"Failed to parse invalid tables: {invalid_tables_str}")
                return get_parsing_error_feedback(error_message)
            
            # Check if it's likely a subquery alias issue (short names)
            is_likely_alias = any(len(t) <= 2 for t in invalid_tables_set)
            
            return get_unknown_tables_feedback(
                invalid_tables=invalid_tables_set,
                allowed_tables=allowed_tables,
                is_likely_alias=is_likely_alias
            )
    
    # Case 2: Multiple SQL statements
    if 'Multiple SQL statements not allowed' in error_message:
        return get_multiple_statements_feedback()
    
    # Case 3: SQL comments
    if 'SQL comments not allowed' in error_message:
        return get_sql_comments_feedback()
    
    # Case 4: Forbidden keywords (e.g., CREATE, DROP)
    if 'Forbidden SQL keyword: CREATE' in error_message:
        return get_forbidden_keyword_feedback('CREATE')
    
    # Case 5: Column not found (with alias detection)
    if 'column' in error_message.lower() and 'does not exist' in error_message.lower():
        match = re.search(r'column "(.+?)" does not exist', error_message)
        if match:
            column = match.group(1)
            return get_alias_reference_feedback(column)
        else:
            return get_column_not_found_feedback()
    
    # Case 6: Division by zero
    if 'division by zero' in error_message.lower():
        return get_division_by_zero_feedback()
    
    # Case 7: Datetime format issues
    if 'datetime' in error_message.lower() and 'format' in error_message.lower():
        return get_datetime_format_feedback()
    
    # Default: Generic parsing error (catch-all)
    logger.debug(f"No specific error handler matched. Using generic feedback for: {error_message[:100]}...")
    return get_parsing_error_feedback(error_message)
