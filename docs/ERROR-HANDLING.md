# Error Handling & SQL Validation

This document explains how Delivery Cadet handles SQL validation errors, the retry mechanism with intelligent error feedback, and the Pyodide fallback strategy.

## Table of Contents
- [Error Handling Philosophy](#error-handling-philosophy)
- [SQL Retry Mechanism](#sql-retry-mechanism)
- [Error Feedback System Architecture](#error-feedback-system-architecture)
- [Pyodide Fallback](#pyodide-fallback)
- [Security Guardrails](#security-guardrails)
- [Error Types Reference](#error-types-reference)
- [Debugging Guide](#debugging-guide)
- [Reference Architecture Summary](#reference-architecture-summary)

---

## Error Handling Philosophy

Delivery Cadet is designed with **self-correction** at its core. When SQL generation or execution fails, the system doesn't simply return an error to the user—it analyses the failure, generates targeted feedback, and retries with specific guidance for the LLM.

**Key principles:**
- **Fail gracefully**: Errors are opportunities for correction, not termination points
- **Targeted feedback**: Each error type receives specific corrective guidance (not generic "try again" messages)
- **Fallback strategy**: When SQL approaches fail after 3 attempts, the system pivots to a simpler SQL + Python analysis approach
- **Security first**: All queries pass through validation before execution, regardless of retry count

This creates a resilient system that can handle ambiguous questions, correct its own mistakes, and still provide accurate answers even when the initial approach fails.

## SQL Retry Mechanism

### Overview

When SQL generation or execution fails, Delivery Cadet automatically retries up to **3 times** with progressively refined guidance. This retry mechanism is orchestrated across multiple modules working in concert.

### Retry Flow

```
User Question
    ↓
generate_SQL (LLM generates SQL)
    ↓
validate_sql_query() — Module: src/core/validation.py
    ↓
    ├─ PASS → execute_SQL → Success
    │
    └─ FAIL → Store error in state['query_result']
              Increment state['sql_retry_count']
                  ↓
              execute_SQL (skips execution)
                  ↓
              decide_sql_retry_route() — Module: src/agent/routing.py
                  ↓
                  ├─ retry_count < 3 → generate_SQL (with error feedback)
                  │                        ↑
                  │                        │
                  │         get_sql_error_feedback() — Module: src/agent/error_feedback.py
                  │                        │
                  │                 Analyses error pattern
                  │                        │
                  │            Routes to specific feedback template
                  │                        │
                  │              feedback templates — Module: src/agent/feedbacks.py
                  │
                  └─ retry_count >= 3 → Check Pyodide fallback eligibility
                                            ↓
                                      enable_pyodide_fallback (if not attempted)
                                            or
                                      Return error to user (if fallback also failed)
```

### Retry Count Tracking

**Module:** `src/agent/state.py`

The system uses a dedicated `sql_retry_count` state variable (not message counting) to track retry attempts. This prevents token overflow and ensures consistent retry logic:

```python
# State definition
sql_retry_count: Optional[int]  # Incremented on each failure
```

**Key operations:**
- **Increment:** When `generate_SQL` validation fails or `execute_SQL` encounters database errors
- **Reset:** When transitioning to Pyodide fallback (fresh start with simpler approach)
- **Check:** In `decide_sql_retry_route()` to determine whether to retry or fallback

### Retry Decision Logic

**Module:** `src/agent/routing.py` — Function: `decide_sql_retry_route()`

After each SQL execution attempt, the routing logic examines:
1. **Query result status**: Does it contain "Error:"?
2. **Retry count**: How many attempts have been made?
3. **Fallback status**: Has Pyodide fallback already been attempted?

**Decision tree:**
- Result is None → Retry immediately
- Error present + retry_count < 3 → Retry with error feedback
- Error present + retry_count >= 3 + no fallback yet → Enable Pyodide fallback
- Error present + retry_count >= 3 + fallback attempted → Return error to user
- No error → Proceed to visualisation

### Error Analysis and Feedback Generation

**Module:** `src/agent/error_feedback.py` — Function: `get_sql_error_feedback()`

When a retry is triggered, this module:
1. **Parses the error message** using regex patterns
2. **Identifies error category** (unknown tables, forbidden keywords, column issues, etc.)
3. **Routes to appropriate feedback template** from `src/agent/feedbacks.py`
4. **Returns targeted guidance** appended to the SQL generation prompt

**Example flow:**
```python
# Error: "Unknown tables in query: {'it'}"
error_feedback.get_sql_error_feedback(error, allowed_tables)
    ↓
Detects: "Unknown tables in query"
    ↓
Checks: Is 'it' likely a subquery alias? (length <= 2 chars)
    ↓
Routes to: get_unknown_tables_feedback(is_likely_alias=True)
    ↓
Returns: "CRITICAL FIX: Always use CTE (WITH clause) instead of subqueries..."
```

This feedback is appended to the SQL generation prompt, guiding the LLM to correct the specific issue.

## Error Feedback System Architecture

### Module Roles

The error feedback system is split into two specialised modules for maintainability and clarity:

#### 1. Error Analysis Router (`src/agent/error_feedback.py`)

**Responsibility:** Analyse error messages and route to appropriate feedback generators.

**Key function:** `get_sql_error_feedback(error_message, allowed_tables)`

**Workflow:**
1. Receives error message from `state['query_result']`
2. Uses regex patterns to identify error category
3. Extracts relevant details (e.g., invalid table names, column names)
4. Routes to specific feedback function in `feedbacks.py`
5. Returns formatted feedback string

**Supported error categories:**
- Unknown tables in query
- Multiple SQL statements
- SQL comments
- Forbidden keywords (CREATE, DROP, etc.)
- Column not found
- Division by zero
- Datetime format issues
- Generic parsing errors (catch-all)

#### 2. Feedback Templates (`src/agent/feedbacks.py`)

**Responsibility:** Provide concrete correction guides for each error type.

**Available templates (9+):**
- `get_unknown_tables_feedback()` — Guides LLM to use correct table names or CTEs
- `get_multiple_statements_feedback()` — Instructs use of CTEs instead of multiple statements
- `get_sql_comments_feedback()` — Reminds LLM to remove comments
- `get_forbidden_keyword_feedback()` — Suggests CTE alternative to CREATE TEMP TABLE
- `get_column_not_found_feedback()` — Explains PostgreSQL case sensitivity
- `get_alias_reference_feedback()` — Specific guidance for column alias issues
- `get_parsing_error_feedback()` — Generic fallback guidance
- `get_division_by_zero_feedback()` — Suggests NULLIF or CASE protection
- `get_datetime_format_feedback()` — Guides proper datetime casting

**Example template:**
```python
def get_unknown_tables_feedback(invalid_tables, allowed_tables, is_likely_alias):
    if is_likely_alias:
        return """
        **CRITICAL FIX REQUIRED:**
        Your previous attempt used a subquery with alias {invalid_tables}, which caused a validation error.

        ALWAYS use CTE (WITH clause) instead of subqueries in FROM clause.
        Example: WITH ranked AS (SELECT ... RANK() OVER (...) FROM ...) SELECT * FROM ranked WHERE rank = 1
        """
    else:
        return f"""
        **CRITICAL FIX REQUIRED:**
        Your previous attempt used invalid table(s): {invalid_tables}
        These tables DO NOT EXIST in the schema.

        Use ONLY these exact table names: {', '.join(sorted(allowed_tables))}
        Do NOT abbreviate or invent table names.
        """
```

### Integration with Retry Flow

**In `generate_SQL` node:**
1. Check if `sql_retry_count > 0`
2. If yes, call `get_sql_error_feedback(previous_error, allowed_tables)`
3. Append returned feedback to SQL generation prompt
4. Invoke LLM with enhanced prompt

This ensures each retry attempt receives specific, actionable guidance rather than generic "try again" messages.

---

## Pyodide Fallback

### When It Activates

After **3 failed SQL retry attempts**, if the question originally required SQL analysis (not general conversation), the system automatically transitions to **Pyodide fallback mode**.

**Trigger conditions:**
- `sql_retry_count >= 3`
- `query_result` contains "Error:"
- `pyodide_fallback_attempted == False`

### Strategy

Instead of attempting complex analytical SQL, the system pivots to a **two-step approach**:

1. **Simple SELECT query:** Fetch raw data with minimal transformations (avoid window functions, complex aggregations, CTEs that caused failures)
2. **Browser-side Python analysis:** Use Pyodide (Python runtime in WebAssembly) to perform pandas operations directly in the user's browser

**Example scenario:**
```
Original question: "For each country, rank products by total revenue and show only the top-selling product"

Failed SQL approach (3 attempts):
- Attempt 1: Window function with RANK() → Syntax error
- Attempt 2: CTE with ROW_NUMBER() → Unknown table error
- Attempt 3: Subquery approach → Validation failed

Pyodide fallback approach:
- SQL: SELECT country, product, SUM(revenue) as total FROM sales GROUP BY country, product
- Python (Pandas):
  df.groupby('country').apply(lambda x: x.nlargest(1, 'total')).reset_index(drop=True)
```

### Implementation

**Module:** `src/agent/nodes.py` — Function: `enable_pyodide_fallback()`

**Workflow:**
1. Sets `needs_pyodide = True` in state
2. Sets `pyodide_fallback_attempted = True` to prevent loops
3. Clears previous error state (`query_result = None`, `sql_query = None`)
4. Resets `sql_retry_count = 0` for fresh attempt
5. Returns to `generate_SQL` with Pyodide mode enabled

**Result:**
- LLM generates simpler SQL focused on data retrieval
- `generate_pyodide_analysis` node creates pandas code for analysis
- Pyodide executes Python code in browser, returns final result

### Preventing Infinite Loops

The `pyodide_fallback_attempted` flag ensures the system doesn't retry indefinitely:
- If Pyodide approach also fails after retries → System returns error to user
- No further fallback attempts beyond Pyodide

---

## Security Guardrails

### Validation Layer

**Module:** `src/core/validation.py` — Function: `validate_sql_query()`

All SQL queries pass through security validation **before execution**, regardless of whether it's the first attempt or a retry. This ensures compromised or malicious queries cannot reach the database.

### Four-Layer Security

#### 1. Forbidden Keyword Detection

Blocks dangerous SQL operations:
```python
dangerous_keywords = {
    'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER',
    'TRUNCATE', 'CREATE', 'GRANT', 'REVOKE', 'EXECUTE', 'EXEC'
}
```

**Raises:** `SQLGenerationError("Forbidden SQL keyword: {keyword}")`

#### 2. Multiple Statement Prevention

Prevents SQL injection via statement chaining:
- Strips trailing semicolon (allowed)
- Checks for additional semicolons in query body
- Rejects queries with multiple statements

**Raises:** `SQLGenerationError("Multiple SQL statements not allowed")`

#### 3. Comment Blocking

Prevents comments that could hide malicious code:
- Blocks `--` (single-line comments)
- Blocks `/* */` (multi-line comments)

**Raises:** `SQLGenerationError("SQL comments not allowed")`

#### 4. Table Whitelist Validation

Ensures all table references exist in the schema:

**Process:**
1. Extract CTE names using regex: `WITH <name> AS (`
2. Extract subquery aliases using `sqlparse` AST traversal
3. Extract all table names from `FROM` and `JOIN` clauses
4. Filter out CTEs and subquery aliases (temporary, not schema tables)
5. Validate remaining tables against allowed schema tables

**Raises:** `SQLGenerationError("Unknown tables in query: {invalid_tables}")`

### Impact on Retry Logic

When validation fails:
- Error is **stored** in `state['query_result']` (not raised immediately)
- `sql_retry_count` is incremented
- Execution is skipped (`execute_SQL` detects error and passes through)
- Retry logic triggers with targeted feedback

This ensures security checks remain active while allowing self-correction.

---

## Error Types Reference

This section provides a quick reference for common error patterns. For detailed feedback logic, see `src/agent/feedbacks.py`.

### 1. Unknown Tables Error

**Error message:** `"Unknown tables in query: {'table_name'}"`

**Common causes:**
- LLM invents non-existent table names
- Uses abbreviations (e.g., `'it'` instead of `'items'`)
- CTE defined but referenced with wrong name
- Short aliases from subqueries (e.g., `'t'`, `'x'`)

**System response:**
- If table name ≤2 chars → Assumes subquery alias issue → Instructs use of CTE
- Otherwise → Provides list of valid table names from schema

### 2. Multiple Statements Error

**Error message:** `"Multiple SQL statements not allowed"`

**Cause:** LLM generated multiple queries separated by semicolons

**System response:** Instructs use of CTE (WITH clause) for multi-step logic

### 3. SQL Comments Error

**Error message:** `"SQL comments not allowed"`

**Cause:** LLM included `--` or `/* */` comments in query

**System response:** Reminds to return only SQL with no explanations

### 4. Column Does Not Exist

**Error message:** `"column 'columnname' does not exist"`

**Cause:** PostgreSQL case sensitivity—unquoted column names are lowercased

**System response:** Instructs use of double quotes for case-sensitive columns: `"columnName"`

### 5. Forbidden Keyword Error

**Error message:** `"Forbidden SQL keyword: CREATE"`

**Cause:** LLM attempted to use CREATE TEMP TABLE or other dangerous operations

**System response:** Suggests CTE alternative

### 6. Division by Zero

**Error message:** Contains `"division by zero"`

**System response:** Suggests NULLIF or CASE protection around division operations

### 7. Datetime Format Issues

**Error message:** Contains `"datetime"` and `"format"`

**System response:** Guides proper datetime casting and format strings

### 8. Parsing Errors

**Catch-all category** for syntax errors not matching specific patterns

**System response:** Generic guidance to review SQL syntax and structure

## Debugging Guide

### Log Analysis

**Primary log file:** `log.txt` (root directory)

The validation module (`src/core/validation.py`) logs detailed debugging information when validation fails. Look for the banner:

```bash
grep "=== SQL Validation Failed ===" log.txt -A 10
```

**Example output:**
```
=== SQL Validation Failed ===
Invalid tables: {'it'}
CTE names found: set()
Subquery aliases found: set()
All extracted tables: {'sales_orders', 'it'}
Actual tables (after filtering): {'it'}
Allowed tables: ['customers', 'orders', 'products', 'sales_orders']
SQL query:
SELECT "item", SUM("amount") as total FROM sales_orders
===========================
```

### Diagnostic Questions

When analysing a validation failure:

1. **Is it a typo?** Compare invalid table name with allowed tables list
2. **Is it a CTE?** If query has `WITH` clause but CTE names are empty → Regex parsing issue
3. **Is it a short alias?** Names ≤2 chars (`'it'`, `'t'`) → Likely subquery without CTE
4. **Case mismatch?** PostgreSQL lowercases unquoted identifiers

### Testing Validation Components

**Test CTE extraction:**
```python
from src.core.validation import _extract_cte_names

sql = """
WITH item_totals AS (
    SELECT "item", SUM("amount") as total
    FROM sales_orders
    GROUP BY "item"
)
SELECT * FROM item_totals
"""

cte_names = _extract_cte_names(sql)
print(cte_names)  # Should be: {'item_totals'}
```

If empty set but CTE exists → Check regex pattern in `_extract_cte_names()`.

**Test subquery alias extraction:**
```python
from src.core.validation import _extract_subquery_aliases

sql = "SELECT * FROM (SELECT id FROM orders) AS order_subset"
aliases = _extract_subquery_aliases(sql)
print(aliases)  # Should include: {'order_subset'}
```

**Manual validation test:**
```python
from src.core.validation import validate_sql_query

sql_query = "SELECT * FROM unknown_table"
allowed_tables = {'customers', 'orders', 'products'}

try:
    validate_sql_query(sql_query, allowed_tables)
except Exception as e:
    print(f"Error: {e}")
```

### Tracking Retry Attempts

Search logs for retry indicators:

```bash
grep "Retry" log.txt
# Expected output: "Retry 1: Added specific feedback for error type"
```

```bash
grep "sql_retry_count" log.txt
# Shows retry counter increments
```

### Common Debugging Scenarios

**Scenario 1: Validation passes but execution fails**

This is expected—validation only checks table names and safety. Column errors are caught at execution time and trigger retry with column-specific feedback.

**Scenario 2: Retry not triggered**

Check if:
- Error is stored in `query_result` state (not raised immediately)
- `sql_retry_count` is incrementing
- Retry count hasn't exceeded 3

**Scenario 3: CTE not detected**

Possible causes:
- Extra whitespace: `WITH\n    name\nAS (`
- SQL comments interfering with regex
- Test the CTE extraction function directly (see above)

**Scenario 4: Pyodide fallback not activating**

Verify:
- `sql_retry_count >= 3`
- `pyodide_fallback_attempted == False`
- Original intent was 'sql' (not 'general')

## Reference Architecture Summary

### Module Breakdown

**Core workflow orchestration:**
- `src/agent/graph.py` — Defines the StateGraph workflow, nodes, and conditional edges
- `src/agent/state.py` — State schema including `sql_retry_count` and `pyodide_fallback_attempted`
- `src/agent/config.py` — Configuration constants including `MAX_SQL_RETRIES = 3`

**Node implementations:**
- `src/agent/nodes.py` — All workflow nodes:
  - `generate_SQL()` — LLM SQL generation with retry feedback integration
  - `execute_SQL()` — Query execution with error detection
  - `enable_pyodide_fallback()` — Fallback mode activation
  - Other nodes (intent classification, visualisation, response generation)

**Routing logic:**
- `src/agent/routing.py` — Contains `RouteDecider` class:
  - `decide_sql_retry_route()` — Determines retry vs. fallback vs. success
  - Other routing decisions (intent, visualisation, pyodide)

**Error feedback system:**
- `src/agent/error_feedback.py` — Error analysis router:
  - `get_sql_error_feedback()` — Analyses error messages and routes to appropriate feedback
- `src/agent/feedbacks.py` — Feedback template library:
  - 9+ specialised feedback generators for different error types
  - Returns formatted strings appended to SQL prompts

**Validation and security:**
- `src/core/validation.py` — SQL validation functions:
  - `validate_sql_query()` — Four-layer security validation
  - `_extract_cte_names()` — CTE name extraction via regex
  - `_extract_subquery_aliases()` — Subquery alias extraction via sqlparse
  - `_extract_table_names()` — Table name extraction from parsed SQL

**Error definitions:**
- `src/core/errors.py` — Custom exception classes:
  - `SQLGenerationError` — Raised for validation failures
  - `ValidationError` — Raised for input validation issues

### Key Workflow Paths

**Success path:**
```
generate_SQL → validate (pass) → execute_SQL → visualisation → response
```

**Retry path:**
```
generate_SQL → validate (fail) → execute_SQL (skip) → routing (retry)
  ↓
generate_SQL (with feedback from error_feedback.py) → retry up to 3 times
```

**Fallback path:**
```
generate_SQL → validate (fail) → ... → retry 3 times (all fail)
  ↓
routing (fallback) → enable_pyodide_fallback
  ↓
generate_SQL (simple mode) → execute_SQL → generate_pyodide_analysis → response
```

---

## Related Documentation

- [Architecture Guide](ARCHITECTURE.md) - Complete system design and LangGraph workflow
- [Setup Guide](../SETUP_GUIDE.md) - Interactive data pipeline setup guide
- [README](../README.md) - Installation, setup, and usage

---

**Last Updated:** 2026-01-15
