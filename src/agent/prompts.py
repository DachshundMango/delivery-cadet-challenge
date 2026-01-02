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

**CRITICAL - Privacy Protection:**
- Replace ONLY individual person names with "Person #N" (with numbering)
- Keep organization names, company names, business names unchanged

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
    return f"""Generate PostgreSQL SELECT query for the user's question using ONLY the tables in the schema below.

**Database Schema:**
{schema_info}

**CRITICAL RULES:**

1. **Use EXACT table names from schema** - Never abbreviate or invent names
   ✓ CORRECT: FROM "table_name_from_schema"
   ✗ WRONG: FROM abbreviated_name (no such table)
   ✗ WRONG: FROM invented_table (no such table)

2. **Keep queries simple** - Use ORDER BY + LIMIT for "top N", not window functions

3. **Quote ALL columns** - PostgreSQL is case-sensitive: t."columnName" not t.columnName

4. **Single query only** - No semicolons in middle, NO comments (-- or /* */), no temp tables

5. **Advanced features ONLY when necessary:**
   - Window Functions: for ranking WITHIN groups (PARTITION BY)
   - CTEs (WITH clause): ALWAYS use CTE instead of subqueries in FROM clause
   - Example: WITH ranked AS (SELECT ... RANK() OVER ...) SELECT * FROM ranked WHERE rank = 1

**User Question:** {user_question}

Return ONLY the SQL query below. NO explanations, NO markdown, NO text before or after the query:
"""


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

    return f"""Should this question be answered with a visualization?

**Question:** {user_question}
**Data sample:** {truncated_result}

**Return "yes" if:**
1. User EXPLICITLY asks for: "chart", "visualize", "plot", "graph", "visualization"
2. Question implies visual comparison would be helpful (e.g., "compare across...", "trends over time", "distribution of...")
3. Data has multiple categories/time points that benefit from visual representation

**Return "no" if:**
1. Simple lookup or count ("how many", "what is the total")
2. User asks to "list" or "show" without visual intent
3. Single value answer

**Be conservative:** When in doubt, prefer "no". Only suggest visualization when it clearly adds value.

**Chart type:**
- Comparison/ranking data → "bar"
- Time series/trends → "line"
- Parts of whole/proportions → "pie"

Return ONLY the JSON below. NO explanations, NO text before or after. Just the JSON object:
{{"visualise": "yes", "chart_type": "bar"}}
OR
{{"visualise": "no"}}"""


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

Return ONLY executable Python code below. NO markdown code blocks, NO explanations, NO text before or after the code:
"""


# ===============================================================
# Data Masking (for charts and privacy)
# ===============================================================

def get_data_masking_prompt(sql_result: str) -> str:
    """
    Generate prompt to mask personal names in SQL result data.

    Args:
        sql_result: JSON string of SQL query results

    Returns:
        Formatted prompt string
    """
    return f"""You are a data privacy filter. Your task is to identify and mask INDIVIDUAL PERSON NAMES while preserving business/organization names.

**Input Data:**
{sql_result}

**Task:**
Look at each value in the data. If it appears to be an INDIVIDUAL PERSON'S NAME (like "John Smith", "Alice", "Robert Johnson"), replace it with "Person #N" with sequential numbering.

**What to MASK (individual person names):**
- Typical human first names: John, Sarah, Michael, Emily, David
- Full names with first + last: "John Smith", "Alice Brown"
- Single person names in name fields

**What NOT to mask (business/organizational names):**
- Business names: "Acme Corp", "Global Services Inc."
- Stores/organizations: "Downtown Shop", "City Center"
- Brands/products: "Product A", "Brand X"
- Companies: "ABC Corporation", "XYZ Supplies"
- Locations: "New York", "London", "Main Street"

**Key distinction:**
- Person names sound like individual humans (John, Sarah, Michael)
- Business names sound like organizations/places/brands (Palace, Corner, Foods, Inc.)

**IMPORTANT:** If the same person has multiple name fields, keep only the FIRST field as "Person #N" and DELETE the others.

**Examples:**

Example 1 - Mask person names:
Input: [{{"name": "John Smith", "spending": 1000}}, {{"name": "Emily Davis", "spending": 500}}]
Output: [{{"name": "Person #1", "spending": 1000}}, {{"name": "Person #2", "spending": 500}}]

Example 2 - Keep business names:
Input: [{{"name": "Acme Corp", "reviews": 100}}, {{"name": "Global Services", "reviews": 80}}]
Output: [{{"name": "Acme Corp", "reviews": 100}}, {{"name": "Global Services", "reviews": 80}}]

Example 3 - Mixed data:
Input: [{{"customer": "Alice Brown", "store": "Downtown Shop", "amount": 50}}]
Output: [{{"customer": "Person #1", "store": "Downtown Shop", "amount": 50}}]

Return ONLY the modified JSON array below. NO markdown, NO explanations, NO text before or after:
"""


def get_pii_detection_prompt(column_data: dict) -> str:
    """
    Generate prompt to detect which columns contain personal identifiable information (PII).

    Args:
        column_data: Dictionary of {table_name: {column_name: [sample_values]}}

    Returns:
        Formatted prompt string
    """
    # Format column data into readable text
    formatted_data = ""
    for table_name, columns in column_data.items():
        formatted_data += f"\n[Table: {table_name}]\n"
        for column_name, sample_values in columns.items():
            # Truncate samples to prevent prompt overflow
            samples_str = str(sample_values)[:150]
            formatted_data += f"  - {column_name}: {samples_str}\n"

    return f"""You are a data privacy expert. Analyze the following database columns and identify which ones contain INDIVIDUAL PERSON NAMES (PII).

**Database Column Information:**
{formatted_data}

**Your Task:**
Identify columns that contain INDIVIDUAL HUMAN NAMES ONLY.

**MUST Include (PII - Personal Names):**
- Person first names, last names, full names (e.g., customer names, employee names, user names)
- Reviewer names, user names (when they are individual people)
- Any column with individual person identifiers like "John", "Sarah", "Michael Smith"

**MUST Exclude (NOT PII):**
- Organization names ("Acme Corp", "Global Services")
- Company names, business names ("ABC Corporation", "XYZ Industries Inc.")
- City names, location names ("New York", "Boston", "Main Street")
- Product names ("Product A", "Brand X")
- Store names ("Downtown Shop", "City Center")
- IDs, numbers, dates, amounts

**Key Distinction:**
- Person names: Sound like individual humans (John, Alice, Smith, Emily Davis)
- Business names: Sound like organizations/places/brands (Palace, Corner, Inc., Bakery, Foods)

**Examples:**

Example 1 - Include these:
Table: customers
- firstName: ["John", "Alice", "Bob"] ✓ PII (person names)
- lastName: ["Smith", "Brown", "Johnson"] ✓ PII (person names)

Example 2 - Exclude these:
Table: organizations
- organizationName: ["Acme Corp", "Global Services"] ✗ NOT PII (business names)
- city: ["New York", "Boston"] ✗ NOT PII (location names)

Example 3 - Mixed:
Table: reviews
- reviewerName: ["Sarah Johnson", "Mike Davis"] ✓ PII (person names)
- organizationName: ["Acme Corp", "Global Services"] ✗ NOT PII (business names)

**CRITICAL:** Only return columns that contain INDIVIDUAL PERSON NAMES. Be conservative - when in doubt, exclude it.

If a table has no PII columns, omit it from the result or use empty array.

Return ONLY the JSON object below. NO markdown, NO explanations, NO text before or after:
{{
  "table_name1": ["pii_column1", "pii_column2"],
  "table_name2": ["pii_column3"]
}}"""


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

    return f"""You are answering a data question. Parse the JSON results carefully and write a natural language response.

**Question:** {question}
**Data (JSON):** {truncated_result}

**CRITICAL INSTRUCTIONS:**
1. Parse the JSON properly - each object has key-value pairs
2. For each row, extract values separately: row["key1"], row["key2"], etc.
3. Write complete sentences with proper spacing between words and numbers
4. NEVER concatenate values without spaces or punctuation
5. Use bullet points for lists (one item per line)

**Response format:**
- Start each item with a bullet point or number
- Use natural language: "Category A" not "categoryA"
- Add spaces: "revenue of $19,983" not "revenue19983"
- Add commas in numbers: "19,983" not "19983"

**WRONG examples to AVOID:**
❌ "19,983thanaveragetransactionsvalue128.55" - NO SPACES
❌ "XXL19983128.55" - VALUES CONCATENATED
❌ "categoryArevenue19983" - COLUMN NAMES MIXED

**CORRECT examples:**
✓ "Category A has a revenue of $19,983 with average value of $128.55"
✓ "- Category: A\n- Revenue: $19,983\n- Average: $128.55"

**CRITICAL - Privacy Protection (MANDATORY):**
⚠️ YOU MUST NEVER SHOW ANY INDIVIDUAL PERSON NAMES IN YOUR RESPONSE ⚠️

- SCAN the entire query result for ANY individual person names
- Replace EVERY SINGLE occurrence with "Person #N" using sequential numbering
- This applies to: firstName, lastName, fullName, name fields (when referring to people)
- DO NOT mask: organization names, company names, business names, product names, location names

**Examples:**
❌ WRONG: "The top person is John Smith with $1000"
✅ CORRECT: "The top person is Person #1 with $1000"

❌ WRONG: "1. Alice Johnson - $800, 2. Bob Williams - $500"
✅ CORRECT: "1. Person #1 - $800, 2. Person #2 - $500"

❌ WRONG: "People include Sarah, Michael, and David"
✅ CORRECT: "People include Person #1, Person #2, and Person #3"

✅ CORRECT: "Top organization: Acme Corp" (business name, keep as-is)
✅ CORRECT: "Company: Global Services Inc." (company name, keep as-is)

**BEFORE you write your answer, VERIFY that no individual person names appear in your response.**

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
    'get_data_masking_prompt',
    'get_response_generation_prompt',
]
