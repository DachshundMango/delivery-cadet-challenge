"""
SQL generation prompts.

This module contains prompts for:
- Generating complex SQL queries with reasoning
- Generating simple SQL queries for Pyodide analysis
"""


def get_sql_generation_prompt(schema_info: str, user_question: str) -> str:
    """
    Generate prompt for SQL query generation with Chain-of-Thought reasoning.

    Args:
        schema_info: Database schema information (tables, columns, relationships)
        user_question: The user's natural language question

    Returns:
        Formatted prompt string with structured reasoning steps
    """
    return f"""You are an expert PostgreSQL query generator. Analyze the question carefully before generating SQL.

<database_schema>
{schema_info}
</database_schema>

<user_question>
{user_question}
</user_question>

<instructions>
**STEP-BY-STEP APPROACH:**
Before writing the query, think through:
1. Which tables from the schema contain the data needed?
2. What foreign key relationships connect these tables?
3. What columns should be selected, filtered, or aggregated?
4. Is this a simple query or does it need CTEs/window functions?

**CRITICAL RULES:**

1. **Use EXACT table names from schema** - Never abbreviate or invent
   ✓ FROM transactions t (exact + alias)
   ✗ FROM trans (no abbreviation)

2. **Table aliases ALLOWED** - Use short aliases (t, e, r) for readability
   ✓ FROM transactions t JOIN entities e ON t."entity_id" = e."id"

3. **Quote ALL columns** - PostgreSQL case-sensitive: t."columnName"

4. **Single query only** - No semicolons, NO comments (-- or /**/), no temp tables

5. **Use CTEs, NOT subqueries**
   ✓ WITH temp AS (SELECT ...) SELECT * FROM temp
   ✗ SELECT * FROM (SELECT ...) AS temp

6. **Query complexity:**
   a) **Simple "top N" globally**: ORDER BY + LIMIT
      "Show top 10 items" → SELECT "item", SUM("amount") FROM fact_table GROUP BY "item" ORDER BY SUM("amount") DESC LIMIT 10

   b) **Ranking per group**: PARTITION BY + window functions
      "Show top item PER REGION" → WITH ranked AS (SELECT "region", "item", RANK() OVER (PARTITION BY "region" ORDER BY SUM("amount") DESC) ...) SELECT * FROM ranked WHERE rank = 1

   c) **Running totals**: SUM() OVER (ORDER BY ...)
      "Cumulative total per day" → SELECT "date", SUM("amount"), SUM(SUM("amount")) OVER (ORDER BY "date") as cumulative FROM fact_table GROUP BY "date"

   d) **Multi-step logic**: CTE (WITH clause)
      WITH temp AS (SELECT ...) SELECT * FROM temp

   7. **Common Pitfalls (CRITICAL):**
      - **Dates**: If date/time columns are stored as TEXT, use `::timestamp` casting for auto-parsing.
        ✓ CORRECT: column_name::timestamp (works with ISO 8601 and other standard formats)
        ✗ WRONG: TO_DATE(column_name, 'format') or TO_TIMESTAMP(column_name, 'format')
        Example: EXTRACT(DOW FROM date_column::timestamp)
      - **Division**: Prevent zero division errors: `x / NULLIF(y, 0)`.
      - **Aliases**: Do NOT reference aliases in the same level.

   8. **Honor user requests** - Use explicitly requested SQL features
</instructions>

<output_format>
First, write your reasoning inside <reasoning> tags:
- Which tables you'll use
- What joins are needed
- What the query structure will be

Then, provide ONLY the SQL query inside <sql> tags.

Example:
<reasoning>
Tables: "entities", "transactions"
Joins: entities.id = transactions.entity_id
Aggregation: SUM by entity
Structure: Simple GROUP BY with ORDER BY LIMIT
</reasoning>

<sql>
SELECT e."name", SUM(t."amount") as total
FROM "entities" e
JOIN "transactions" t ON e."id" = t."entity_id"
GROUP BY e."name"
ORDER BY total DESC
LIMIT 10
</sql>
</output_format>

Now generate your response following the format above:
"""


def get_simple_sql_for_pyodide_prompt(schema_info: str, user_question: str) -> str:
    """
    Generate prompt for creating simple SELECT queries for Pyodide analysis.

    When statistical analysis is needed, we want to fetch raw data rather than
    performing complex aggregations in SQL. Pyodide will handle the analysis.

    Args:
        schema_info: Database schema information
        user_question: The user's question

    Returns:
        Formatted prompt string for simple SQL generation
    """
    return f"""You are an expert PostgreSQL query generator. The user wants statistical analysis that will be performed by Python/Pandas.

<database_schema>
{schema_info}
</database_schema>

<user_question>
{user_question}
</user_question>

**TASK**: Generate a SIMPLE SELECT query to fetch the RAW DATA needed for analysis.

**CRITICAL RULES:**
1. **DO NOT perform statistical calculations** (no AVG, STDDEV, percentile functions, etc.)
2. **DO NOT use window functions** (no PARTITION BY, RANK, etc.)
3. **DO NOT use date functions** (no EXTRACT, TO_DATE, DATE_TRUNC, etc.)
4. **Just SELECT the relevant columns AS-IS** from the appropriate table(s)
5. **You MAY use JOINs** if multiple tables are needed
6. **You MAY use WHERE** to filter irrelevant data
7. **Keep it simple** - Pandas will do ALL analysis (statistical, temporal, etc.)

**Examples:**
Question: "Calculate correlation between price and quantity"
✓ GOOD: SELECT "unitPrice", "quantity" FROM "sales_transactions"
✗ BAD:  WITH stats AS (SELECT AVG("unitPrice")...) SELECT correlation...

Question: "Time series analysis of transactions by day of week"
✓ GOOD: SELECT "dateTime", "transactionID" FROM "sales_transactions"
✗ BAD:  SELECT EXTRACT(DOW FROM "dateTime"::timestamp) AS day_of_week...

Return ONLY the SQL query. NO explanations, NO markdown:"""
