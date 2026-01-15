# Error Handling & SQL Validation

This document explains how Delivery Cadet handles SQL validation errors, the retry mechanism, and how to debug validation failures.

## Table of Contents
- [Overview](#overview)
- [SQL Validation Pipeline](#sql-validation-pipeline)
- [Error Types](#error-types)
- [Retry Mechanism](#retry-mechanism)
- [Recent Improvements](#recent-improvements)
- [Debugging Guide](#debugging-guide)
- [Common Issues](#common-issues)

---

## Overview

Delivery Cadet uses a multi-layered approach to ensure SQL queries are safe and valid before execution:

1. **LLM generates SQL** from natural language
2. **Validation layer** checks for safety and correctness
3. **If validation fails**, error is stored and passed to retry logic
4. **LLM receives error hints** and regenerates SQL (up to 3 attempts)
5. **Execute validated query** against PostgreSQL

This document focuses on steps 2-4: validation, error handling, and retry logic.

---

## SQL Validation Pipeline

### Location
[src/core/validation.py](../src/core/validation.py) - `validate_sql_query()`

### Validation Steps

#### 1. Safety Checks
Prevents SQL injection and dangerous operations:

```python
# Forbidden keywords
dangerous_keywords = {
    'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER',
    'TRUNCATE', 'CREATE', 'GRANT', 'REVOKE', 'EXECUTE', 'EXEC'
}
```

**Error:** `"Forbidden SQL keyword: {keyword}"`

#### 2. Multiple Statement Prevention
Blocks queries with multiple statements (SQL injection vector):

```python
if ';' in sql_stripped:
    raise SQLGenerationError("Multiple SQL statements not allowed")
```

**Error:** `"Multiple SQL statements not allowed"`

#### 3. Comment Blocking
Prevents comments that could hide malicious code:

```python
if '--' in sql_query or '/*' in sql_query:
    raise SQLGenerationError("SQL comments not allowed")
```

**Error:** `"SQL comments not allowed"`

#### 4. Table Name Validation
Ensures all table references exist in the schema:

**Process:**
1. Extract CTE names (e.g., `WITH customer_data AS (...)`)
2. Extract subquery aliases (e.g., `FROM (SELECT ...) AS temp`)
3. Extract all table names from `FROM` and `JOIN` clauses
4. Filter out CTEs and subquery aliases
5. Check remaining tables against allowed schema tables

**Error:** `"Unknown tables in query: {invalid_tables}"`

---

## Error Types

### 1. Unknown Tables Error

**Example:**
```
Error: Unknown tables in query: {'it'}
```

**Causes:**
- LLM invents non-existent table names
- LLM uses abbreviations (e.g., `'it'` instead of `'items'`)
- CTE defined but referenced with wrong name
- Parsing failure (CTE not detected)

**LLM Hint (Short names ≤2 chars):**
```
Your previous attempt used a subquery with alias {'it'}, which caused a validation error.
ALWAYS use CTE (WITH clause) instead of subqueries in FROM clause.
Example: WITH ranked AS (SELECT ... RANK() OVER (...) FROM ...) SELECT * FROM ranked WHERE rank = 1
```

**LLM Hint (Long names):**
```
Your previous attempt used invalid table(s): {'unknown_table'}
These tables DO NOT EXIST in the schema.
Use ONLY these exact table names: customers, orders, products, ...
Do NOT abbreviate or invent table names.
```

### 2. Multiple Statements Error

**Example:**
```
Error: Multiple SQL statements not allowed
```

**Cause:**
LLM generated multiple queries separated by semicolons:
```sql
CREATE TEMP TABLE temp AS (...);
SELECT * FROM temp;
```

**LLM Hint:**
```
Your previous attempt had multiple SQL statements (separated by semicolons).
Generate EXACTLY ONE query. Use CTE (WITH clause) for multi-step logic:
WITH temp AS (SELECT ...) SELECT ... FROM temp
```

### 3. SQL Comments Error

**Example:**
```
Error: SQL comments not allowed
```

**Cause:**
LLM included comments in SQL:
```sql
SELECT * FROM orders -- Get all orders
WHERE status = 'active'
```

**LLM Hint:**
```
Your previous attempt had SQL comments (-- or /* */).
Remove ALL comments. Return ONLY the SQL query with no explanations.
```

### 4. Column Does Not Exist

**Example:**
```
Error: column "customername" does not exist
```

**Cause:**
PostgreSQL is case-sensitive. Unquoted column names are lowercased:
```sql
-- Wrong
SELECT customerName FROM customers

-- Correct
SELECT "customerName" FROM customers
```

**LLM Hint:**
```
Your previous attempt referenced a non-existent column.
Remember: PostgreSQL converts unquoted column names to lowercase.
ALWAYS use double quotes: t."columnName" not t.columnName
```

### 5. Forbidden Keyword Error

**Example:**
```
Error: Forbidden SQL keyword: CREATE
```

**Cause:**
LLM tried to create temporary tables:
```sql
CREATE TEMP TABLE temp AS (...)
```

**LLM Hint:**
```
Your previous attempt used CREATE TEMP TABLE.
Use CTE (WITH clause) instead: WITH temp AS (SELECT ...) SELECT ... FROM temp
```

---

## Retry Mechanism

### Maximum Retries
`MAX_SQL_RETRIES = 3` ([src/agent/graph.py:17](../src/agent/graph.py#L17))

### Workflow

```
User Question
    ↓
generate_SQL (LLM generates SQL)
    ↓
validate_sql_query()
    ↓
┌─ Validation PASS → execute_SQL → Success
│
└─ Validation FAIL → Error stored in query_result
                         ↓
                     execute_SQL (skips execution)
                         ↓
                     check_query_validation (detects error)
                         ↓
                     ┌─ retry_count < 3 → generate_SQL (with hints)
                     │
                     └─ retry_count >= 3 → Return error message
```

### Retry Count Tracking

**Location:** [src/agent/graph.py:36-38](../src/agent/graph.py#L36-L38)

```python
messages = state.get('messages', [])
error_count = sum(1 for msg in messages
                 if 'Error:' in str(getattr(msg, 'content', '')))
```

Errors are counted by checking messages for `"Error:"` prefix.

### Error Hint Generation

**Location:** [src/agent/nodes.py:367-403](../src/agent/nodes.py#L367-L403)

When `retry_count > 0`, the system:
1. Reads previous error from `state['query_result']`
2. Matches error pattern (e.g., `'Unknown tables in query'`)
3. Appends specific hint to SQL generation prompt
4. Invokes LLM with updated prompt

**Example:**
```python
if 'Unknown tables in query' in previous_error:
    sql_prompt += "\n\n**CRITICAL FIX REQUIRED:**\n..."
```

---

## Recent Improvements

### Problem (Before)
Validation errors caused workflow termination without retry:

```
generate_SQL
    ↓
validate_sql_query() fails
    ↓
raise SQLGenerationError  ← Workflow stops here!
    ↓
🛑 Never reaches execute_SQL
🛑 Retry logic never triggered
🛑 User sees error, no recovery
```

### Solution (After - 2026-01-09)

**Change 1: Store validation errors instead of raising**

[src/agent/nodes.py:432-447](../src/agent/nodes.py#L432-L447)

```python
except SQLGenerationError as e:
    # Validation failed - store error in state for retry logic
    error_msg = f"Error: {str(e)}"
    logger.error(f"SQL validation failed: {e}")

    # Return error in query_result so retry logic can process it
    return {
        "sql_query": sql_query if 'sql_query' in locals() else None,
        "query_result": error_msg  # ← Key change!
    }
```

**Change 2: Skip execution if error already present**

[src/agent/nodes.py:470-474](../src/agent/nodes.py#L470-L474)

```python
# If query_result already has an error (from validation failure), pass it through
query_result = state.get('query_result')
if query_result and 'Error:' in query_result:
    logger.info("Skipping execution - validation error already in query_result")
    return {}  # Don't overwrite query_result, just pass through
```

**Change 3: Enhanced debug logging**

[src/core/validation.py:296-305](../src/core/validation.py#L296-L305)

```python
if invalid_tables:
    logger.error(f"=== SQL Validation Failed ===")
    logger.error(f"Invalid tables: {invalid_tables}")
    logger.error(f"CTE names found: {cte_names}")
    logger.error(f"Subquery aliases found: {subquery_aliases}")
    logger.error(f"All extracted tables: {query_tables}")
    logger.error(f"Actual tables (after filtering): {actual_tables}")
    logger.error(f"Allowed tables: {sorted(allowed_tables)}")
    logger.error(f"SQL query:\n{sql_query}")
    logger.error(f"===========================")
```

### Impact
- ✅ Validation errors now trigger retry (up to 3 attempts)
- ✅ LLM receives error-specific hints
- ✅ Detailed logs for debugging
- ✅ User gets answer after retry (instead of error)

### Removed: Fuzzy Matching

**Previous behavior** ([validation.py:279-289](../src/core/validation.py#L279-L289)):
```python
# Fuzzy check: if table is a prefix of any CTE name
for cte in cte_names:
    if table in cte or cte in table:
        is_cte_variant = True
```

**Problem:**
- False positives: `'it' in 'website'` → True (unintended match)
- Masked real issues: CTE parsing failures not detected
- Inconsistent: Substring matching instead of prefix matching

**Solution:**
Removed fuzzy matching (commented out). Now uses exact matching only:
```python
if table in cte_names or table in subquery_aliases:
    continue  # Only exact matches filtered
```

This makes validation stricter but more predictable. If LLM uses wrong CTE name, it fails validation → retry with hint → LLM corrects it.

---

## Debugging Guide

### Step 1: Check Logs

**Log file:** `log.txt` (root directory)

**Look for validation failures:**
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
SELECT "item", SUM("amount") as total
FROM sales_orders
WHERE "region" = 'North'
GROUP BY "item"
ORDER BY total DESC
LIMIT 5
===========================
```

### Step 2: Analyze the Error

**Questions to ask:**
1. **Is the invalid table a typo?** (e.g., `'oder'` instead of `'orders'`)
2. **Is it a CTE?** Check if CTE names are empty but query has `WITH` clause
3. **Is it a short alias?** (e.g., `'it'`, `'t'`, `'x'`) → Likely subquery issue
4. **Does it match a real table?** (e.g., `'customer'` vs `'customers'`)

### Step 3: Test CTE Extraction

**Run in Python console:**
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

If empty set but CTE exists → regex pattern issue.

### Step 4: Check sqlparse Output

```python
import sqlparse
from src.core.validation import _extract_table_names

sql = "SELECT * FROM (SELECT ...) AS temp"
parsed = sqlparse.parse(sql)[0]

tables = _extract_table_names(parsed)
print(tables)  # Check if 'temp' is included
```

### Step 5: Manual Validation Test

```python
from src.core.validation import validate_sql_query

sql_query = "SELECT * FROM unknown_table"
allowed_tables = {'customers', 'orders', 'products'}

try:
    validate_sql_query(sql_query, allowed_tables)
except Exception as e:
    print(f"Error: {e}")
```

---

## Common Issues

### Issue 1: "Unknown tables: {'it'}"

**Root cause:**
LLM generated table name/alias 'it' without defining it as a CTE or using a real table.

**Possible queries:**
```sql
-- Case 1: No CTE definition
SELECT * FROM it  -- ❌ Where is 'it' defined?

-- Case 2: CTE name mismatch
WITH item_totals AS (...)
SELECT * FROM it  -- ❌ Should be 'item_totals'

-- Case 3: Parsing failure
WITH it AS (...)
SELECT * FROM it  -- ✅ Should work, but regex might fail
```

**Solution:**
1. Check logs for actual SQL query
2. If CTE exists but not detected → fix `_extract_cte_names()` regex
3. If no CTE → LLM error, retry will fix it

### Issue 2: Validation passes but execution fails

**Symptom:**
```
logger.info("SQL validation passed")
...
Error: column "customerName" does not exist
```

**Cause:**
Validation only checks table names, not column names. PostgreSQL validates columns at execution time.

**Solution:**
This is expected behavior. Column errors trigger retry through `execute_SQL` error handling.

### Issue 3: Retry not working

**Symptom:**
Validation error shown to user, no retry attempted.

**Check:**
1. Is error in `query_result`? (Should be after 2026-01-09 update)
2. Is `check_query_validation` being called?
3. Is retry count already at max (3)?

**Debug:**
```bash
grep "Retry" log.txt
# Should see: "Retry 1/3", "Retry 2/3", etc.
```

### Issue 4: CTE not detected

**Symptom:**
```
CTE names found: set()
SQL query:
WITH customer_data AS (...)
```

**Cause:**
Regex pattern `r'\b(\w+)\s+AS\s*\('` doesn't match the SQL format.

**Possible reasons:**
- Extra spaces/newlines: `WITH\n    customer_data\nAS (`
- Comments: `WITH /* temp */ customer_data AS (`
- Lowercase 'as': Pattern is case-insensitive, so should work

**Test regex:**
```python
import re
sql = "WITH customer_data AS (SELECT ...)"
matches = re.findall(r'\b(\w+)\s+AS\s*\(', sql, re.IGNORECASE)
print(matches)  # Should be: ['customer_data']
```

---

## Best Practices

### 1. Always Check Logs First
Don't guess - look at the actual SQL query in `log.txt`.

### 2. Test Validation Locally
Before deploying validation changes, test with real queries from logs.

### 3. Update Retry Hints
When adding new validation rules, update hint generation in `nodes.py:generate_SQL`.

### 4. Monitor Retry Success Rate
Track how often retries succeed vs. fail (metrics idea for future).

### 5. Keep Validation Strict
Don't add fuzzy matching to "help" the LLM - it masks real issues. Let retry mechanism fix errors.

---

## Related Documentation

- [Architecture Guide](ARCHITECTURE.md) - System design and workflow
- [Setup Guide](../SETUP_GUIDE.md) - Interactive data pipeline setup guide
- [README](../README.md) - User setup and usage

---

**Last Updated:** 2026-01-11
