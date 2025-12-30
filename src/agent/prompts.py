"""
Prompt templates for the SQL Agent

This module contains all LLM prompts used by the agent nodes.
Separating prompts from logic makes them easier to modify and version control.

All prompts are implemented as functions for consistency and flexibility.

Usage:
    from .prompts import get_intent_classification_prompt, get_sql_generation_prompt
"""

# ===============================================================
# Intent Classification
# ===============================================================

def get_intent_classification_prompt() -> str:
    """
    Generate prompt for classifying user intent (sql vs general).

    Returns:
        Prompt string for intent classification
    """
    return """Classify user input into: sql or general

**Few-Shot Examples:**

User: "Show me top 10 records"
Classification: sql

User: "What is the total count?"
Classification: sql

User: "Which item has the highest value?"
Classification: sql

User: "Hello"
Classification: general

User: "What can you do?"
Classification: general

User: "Create a chart"
Classification: sql

User: "Compare A and B"
Classification: sql

**Rules:**
- ANY question about data, numbers, rankings, comparisons → sql
- ONLY greetings (hello/hi) or capability questions (what can you do) → general
- DEFAULT → sql

Return ONLY the word sql or general - no markdown, no explanations, no punctuation."""


# ===============================================================
# General Response (Non-SQL queries)
# ===============================================================

def get_general_response_prompt(user_question: str) -> str:
    """
    Generate prompt for general conversation responses.

    Args:
        user_question: The user's input question

    Returns:
        Formatted prompt string
    """
    return f"""You are a database query assistant. You ONLY answer questions using the connected database.

User question: "{user_question}"

**Critical Rules:**
- You can ONLY answer questions based on data in the database
- NEVER use web search or general knowledge
- If the user asks about capabilities, explain you analyze data from the connected database
- If greeting (hello/hi), respond politely and offer to help with database queries
- For any other question, respond: "I can only answer questions based on the database. Please ask a data-related question."

Respond briefly and clearly."""


# ===============================================================
# SQL Generation
# ===============================================================

def get_sql_generation_prompt(schema_info: str, user_question: str) -> str:
    """
    Generate prompt for SQL query generation.

    Args:
        schema_info: Database schema information (tables, columns, relationships)
        user_question: The user's natural language question

    Returns:
        Formatted prompt string
    """
    return f"""Generate PostgreSQL SELECT query.

**Database Schema:**
{schema_info}

**CRITICAL PostgreSQL Quoting Rules:**
- PostgreSQL converts unquoted identifiers to LOWERCASE
- ALWAYS use double quotes around ALL column names in EVERY clause
- This includes: SELECT, WHERE, JOIN, GROUP BY, ORDER BY, HAVING
- Quote every column reference: alias."columnName" NOT alias.columnName

**Examples of CORRECT quoting:**
✓ SELECT: SELECT s."first_name", s."customerID" FROM "sales_customers" s
✓ JOIN: JOIN "sales_transactions" t ON s."customerID" = t."customerID"
✓ GROUP BY: GROUP BY t."product", t."paymentMethod"
✓ ORDER BY: ORDER BY t."dateTime" DESC

**Common Mistakes to AVOID:**
❌ WRONG: SELECT t.paymentMethod, COUNT(*) FROM ... GROUP BY t.paymentMethod
   Error: column t.paymentmethod does not exist (lowercase!)
✓ CORRECT: SELECT t."paymentMethod", COUNT(*) FROM ... GROUP BY t."paymentMethod"

❌ WRONG: ORDER BY t.dateTime DESC
   Error: column t.datetime does not exist (lowercase!)
✓ CORRECT: ORDER BY t."dateTime" DESC

**CRITICAL: Schema-Only Constraint**
- NEVER reference tables that are NOT explicitly listed in the schema above
- NEVER assume additional tables exist (e.g., products, items, categories)
- ALWAYS verify every table you reference appears in the schema

**Common Mistake to AVOID:**
WRONG: SELECT p."product", SUM(t."quantity") FROM products p JOIN "sales_transactions" t ...
  ❌ This assumes a 'products' table exists - it does NOT
CORRECT: SELECT t."product", SUM(t."quantity") FROM "sales_transactions" t ...
  ✓ Uses the 'product' column directly from sales_transactions table

**Query Rules:**
1. Use ONLY tables/columns from schema above - verify EVERY table exists
2. Use GROUP BY with aggregate functions (SUM, COUNT, AVG)
3. ORDER BY aliases or column position for aggregates
4. Return ONLY SQL query - no markdown, no explanations

**User Question:** {user_question}

**SQL Query:**"""


# ===============================================================
# Visualization Classification
# ===============================================================

def get_visualization_prompt(user_question: str, sql_result: str) -> str:
    """
    Generate prompt to determine if visualization is needed.

    Args:
        user_question: The user's original question
        sql_result: JSON string of SQL query results

    Returns:
        Formatted prompt string
    """
    # Truncate result to prevent prompt overflow
    truncated_result = sql_result[:200] + "..." if len(sql_result) > 200 else sql_result

    return f"""Analyze if result needs visualization.

**Question:** {user_question}
**Result:** {truncated_result}

**Criteria:**
- Keywords: "chart", "visualize", "compare", "trend" → yes
- 3+ rows + aggregated data → yes
- Single value → no

**Chart Types:**
- bar: Rankings, comparisons
- line: Time series, trends
- pie: Proportions

Return ONLY JSON - no markdown, no explanations:
{{"visualise": "yes" or "no", "chart_type": "bar" or "line" or "pie"}}"""


# ===============================================================
# Pyodide (Python Analysis)
# ===============================================================

def get_pyodide_analysis_prompt(user_question: str, sql_result: str) -> str:
    """
    Generate prompt for Pyodide-based Python analysis.

    Args:
        user_question: The user's question requesting analysis
        sql_result: JSON string of SQL query results to analyze

    Returns:
        Formatted prompt string
    """
    return f"""You are a Python Data Analyst using pandas in a browser environment (Pyodide).

User Question: "{user_question}"

Database Result (JSON format):
{sql_result}

Generate Python code to analyze this data. CRITICAL RULES:

1. MANDATORY: Use the JSON data provided above - DO NOT create sample data
2. Import pandas: import pandas as pd
3. Load the actual data: df = pd.DataFrame({sql_result})
4. Perform ONLY the analysis requested (correlation, statistics, grouping, etc.)
5. Print the result using print() - this is what the user will see
6. DO NOT use matplotlib or plotting libraries - only pandas operations
7. Keep output concise and readable
8. Return ONLY executable Python code, NO markdown, NO explanations

Example for "show statistics":
import pandas as pd
df = pd.DataFrame({sql_result})
print(df.describe())
"""


# ===============================================================
# Response Generation
# ===============================================================

def get_response_generation_prompt(question: str, result: str) -> str:
    """
    Generate prompt for natural language response from SQL results.

    Args:
        question: The user's original question
        result: JSON string of SQL query results

    Returns:
        Formatted prompt string
    """
    # Truncate result to prevent prompt overflow
    truncated_result = result[:1000] if len(result) > 1000 else result

    return f"""Answer the user's question using the query results.

**Question:** {question}
**Results:** {truncated_result}

**Guidelines:**
- Direct, clear answer
- Natural, readable format
- NO SQL code or technical details
- Summarize if many results
- Use bullet points for readability

**Answer:**"""


# ===============================================================
# Export all prompts
# ===============================================================

__all__ = [
    'get_intent_classification_prompt',
    'get_general_response_prompt',
    'get_sql_generation_prompt',
    'get_visualization_prompt',
    'get_pyodide_analysis_prompt',
    'get_response_generation_prompt',
]
