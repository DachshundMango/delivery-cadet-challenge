"""
LLM Feedback Messages for SQL Generation Errors

This module contains feedback messages provided to the LLM when SQL generation fails.
Each function returns a specific feedback based on the error type to guide the LLM's correction.

Separating feedbacks from logic makes them easier to modify, translate, and version control.

Usage:
    from .feedbacks import get_unknown_tables_feedback, get_multiple_statements_feedback
"""


def get_unknown_tables_feedback(invalid_tables: set, allowed_tables: set, is_likely_alias: bool = False) -> str:
    """
    Generate feedback for "Unknown tables in query" error.

    Args:
        invalid_tables: Set of invalid table names that were used
        allowed_tables: Set of valid table names from schema
        is_likely_alias: True if invalid_tables are short names (1-2 chars) that look like aliases

    Returns:
        Formatted feedback string to append to SQL generation prompt
    """
    invalid_str = str(invalid_tables)

    if is_likely_alias:
        # Short names like 'it', 't', 'x' - likely subquery alias issue
        return f"""

**CRITICAL FIX REQUIRED:**
Your previous attempt used a subquery with alias {invalid_str}, which caused a validation error.

ALWAYS use CTE (WITH clause) instead of subqueries in FROM clause.

Example:
WITH ranked AS (
    SELECT *, RANK() OVER (PARTITION BY "category" ORDER BY "value" DESC) AS rank
    FROM data_table
)
SELECT * FROM ranked WHERE rank = 1

Do NOT use: FROM (SELECT ...) AS {list(invalid_tables)[0]}
"""
    else:
        # Longer names - actual non-existent table names
        allowed_list = ', '.join(f'"{t}"' for t in sorted(allowed_tables))
        return f"""

**CRITICAL FIX REQUIRED:**
Your previous attempt used invalid table(s): {invalid_str}

These tables DO NOT EXIST in the schema.

Use ONLY these exact table names: {allowed_list}

Rules:
- Do NOT abbreviate table names (e.g., 'cust' instead of 'customers')
- Do NOT invent new table names
- Do NOT use aliases without defining them as CTEs first
- Copy table names EXACTLY as shown above
"""


def get_multiple_statements_feedback() -> str:
    """
    Generate feedback for "Multiple SQL statements not allowed" error.

    Returns:
        Formatted feedback string
    """
    return """

**CRITICAL FIX REQUIRED:**
Your previous attempt had multiple SQL statements (separated by semicolons).

Generate EXACTLY ONE query. Use CTE (WITH clause) for multi-step logic:

Example:
WITH temp AS (
    SELECT "entity_id", SUM("amount") as total
    FROM transactions
    GROUP BY "entity_id"
)
SELECT e."name", t.total
FROM entities e
JOIN temp t ON e."id" = t."entity_id"

Do NOT use:
CREATE TEMP TABLE temp AS (...);
SELECT * FROM temp;
"""


def get_sql_comments_feedback() -> str:
    """
    Generate feedback for "SQL comments not allowed" error.

    Returns:
        Formatted feedback string
    """
    return """

**CRITICAL FIX REQUIRED:**
Your previous attempt had SQL comments (-- or /* */).

Remove ALL comments. Return ONLY the SQL query with no explanations.

Do NOT include:
- Line comments: -- This is a comment
- Block comments: /* This is a comment */
- Explanatory text before or after the query

Return ONLY valid SQL inside <sql></sql> tags.
"""


def get_forbidden_keyword_feedback(keyword: str = 'CREATE') -> str:
    """
    Generate feedback for "Forbidden SQL keyword" error.

    Args:
        keyword: The forbidden keyword that was used (e.g., 'CREATE', 'DELETE')

    Returns:
        Formatted feedback string
    """
    if keyword == 'CREATE':
        return """

**CRITICAL FIX REQUIRED:**
Your previous attempt used CREATE TEMP TABLE.

Use CTE (WITH clause) instead:

Example:
WITH temp AS (
    SELECT "item_id", COUNT(*) as record_count
    FROM transactions
    GROUP BY "item_id"
)
SELECT * FROM temp WHERE record_count > 10

CTEs are temporary and automatically cleaned up after the query.
"""
    else:
        return f"""

**CRITICAL FIX REQUIRED:**
Your previous attempt used forbidden keyword: {keyword}

This system only allows SELECT queries (read-only).

Forbidden operations:
- DROP (deleting tables)
- DELETE (deleting rows)
- UPDATE (modifying data)
- INSERT (adding data)
- CREATE (creating objects)
- ALTER (modifying structure)

Generate a SELECT query that retrieves the requested information without modifying data.
"""


def get_column_not_found_feedback(column_name: str = None) -> str:
    """
    Generate feedback for "column does not exist" error.

    Args:
        column_name: Optional column name that was not found

    Returns:
        Formatted feedback string
    """
    column_info = f" '{column_name}'" if column_name else ""
    return f"""

**CRITICAL FIX REQUIRED:**
Your previous attempt referenced a non-existent column{column_info}.

PostgreSQL column name rules:
1. Unquoted names are converted to LOWERCASE
   - customerName → customername (fails if actual column is "customerName")

2. ALWAYS use double quotes for exact matching:
   - ✓ SELECT t."customerName" FROM table t
   - ✗ SELECT t.customerName FROM table t

3. Column names are CASE-SENSITIVE when quoted:
   - "CustomerName" ≠ "customername" ≠ "CUSTOMERNAME"

4. Check the schema for exact column names and quote them correctly.

Example:
SELECT t."recordID", e."entityName", t."totalAmount"
FROM transactions t
JOIN entities e ON t."entityID" = e."id"
"""


def get_division_by_zero_feedback() -> str:
    """
    Generate feedback for "Division by zero" error.
    """
    return """
    **Fix: Division by Zero Error**
    - You are trying to divide by a value that is ZERO (likely STDDEV, SUM, or COUNT).
    - Use `NULLIF(column, 0)` to handle division by zero safely.
    - Example: `col_a / NULLIF(col_b, 0)` -> Returns NULL instead of error.
    - Particularly common when calculating SKEWNESS or normalisation where STDDEV can be 0.
    """

def get_datetime_format_feedback() -> str:
    """
    Generate feedback for datetime format errors.
    """
    return """
    **Fix: Datetime Format Error**
    - The 'dateTime' column is TEXT and may contain ISO formats (e.g., '2023-01-01T12:00:00').
    - Your format string in TO_TIMESTAMP() failed.
    - SOLUTION: Use direct casting instead: `"dateTime"::timestamp`
    - PostgreSQL handles ISO formats automatically when casting.
    """

def get_alias_reference_feedback(column_name: str) -> str:
    """
    Generate feedback for "column does not exist" when it's likely an alias issue.
    """
    return f"""
    **Fix: Alias Reference Error ("{column_name}" does not exist)**
    - You defined "{column_name}" as an ALIAS in the SELECT clause (e.g., `... AS {column_name}`).
    - You CANNOT use an alias in the same SELECT or WHERE clause.
    - **Solution:** Wrap the calculation in a CTE or Subquery first.
    - Example:
      WITH stats AS (SELECT a+b AS my_alias FROM table)
      SELECT * FROM stats WHERE my_alias > 10
    """

def get_parsing_error_feedback(error_message: str) -> str:
    """
    Generate feedback for general SQL parsing errors.

    Args:
        error_message: The parsing error message from database

    Returns:
        Formatted feedback string
    """
    return f"""

**CRITICAL FIX REQUIRED:**
Your previous attempt had a SQL syntax error: {error_message}

Common syntax issues:
1. Missing quotes around column names with special characters
2. Incorrect JOIN syntax
3. Missing GROUP BY for aggregated columns
4. Mismatched parentheses in subqueries/CTEs

Steps to fix:
1. Review the error message carefully
2. Check your SQL syntax against PostgreSQL standards
3. Ensure all column names are quoted: t."columnName"
4. Verify JOIN conditions are correct
5. Make sure GROUP BY includes all non-aggregated SELECT columns
"""


def get_generic_retry_feedback(retry_count: int, max_retries: int) -> str:
    """
    Generate a generic feedback when retry_count is approaching max.

    Args:
        retry_count: Current retry attempt number (1-based)
        max_retries: Maximum number of retries allowed

    Returns:
        Formatted feedback string
    """
    if retry_count >= max_retries - 1:
        # Last attempt
        return f"""

**FINAL ATTEMPT (Retry {retry_count}/{max_retries}):**
This is your last chance to generate a valid SQL query.

Review the error message carefully and:
1. Use ONLY exact table names from the schema
2. Quote ALL column names with double quotes: "columnName"
3. Use CTEs instead of subqueries
4. Generate exactly ONE SELECT query
5. Do NOT include comments or explanations

If you're uncertain, prefer a simpler query that you're confident will work.
"""
    else:
        return f"""

**RETRY ATTEMPT {retry_count}/{max_retries}:**
Your previous SQL query failed validation.

Carefully read the error message above and fix the specific issue mentioned.
"""
