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
    Generate prompt for classifying user intent (sql vs general) with reasoning.

    Returns:
        Prompt string for intent classification
    """
    return """You are an intent classifier for a database query assistant. Analyze the user's input carefully.

**Classification Task:** Determine if the user wants to query data (sql) or have general conversation (general).

**Decision Process:**
1. Check if the input is a greeting or meta-question about the system itself → general
2. Check if the input requests data, statistics, analysis, or visualization → sql
3. When in doubt, default to sql (users mainly want data queries)

**Few-Shot Examples:**

User: "Show me top 10 records"
Reasoning: Requests data retrieval
Classification: sql

User: "What is the total count?"
Reasoning: Requests numerical aggregation
Classification: sql

User: "Which item has the highest value?"
Reasoning: Requests ranking/comparison from data
Classification: sql

User: "Hello"
Reasoning: Simple greeting, no data request
Classification: general

User: "What can you do?"
Reasoning: Meta-question about system capabilities
Classification: general

User: "Create a chart"
Reasoning: Requests data visualization (requires data query)
Classification: sql

User: "Compare A and B"
Reasoning: Requests data comparison
Classification: sql

**Classification Rules:**
- ANY question about data, numbers, rankings, comparisons, trends → sql
- ANY request for charts, visualizations, analysis → sql
- ONLY greetings (hello/hi/hey) or capability questions (what can you do) → general
- DEFAULT → sql (assume user wants data)

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
    Generate prompt for SQL query generation with Chain-of-Thought reasoning.

    Args:
        schema_info: Database schema information (tables, columns, relationships)
        user_question: The user's natural language question

    Returns:
        Formatted prompt string with structured reasoning steps
    """
    return f"""You are an expert PostgreSQL query generator. Analyze the question carefully before generating SQL.

**Database Schema:**
{schema_info}

**User Question:** {user_question}

**STEP-BY-STEP APPROACH:**
Before writing the query, think through:
1. Which tables from the schema contain the data needed?
2. What foreign key relationships connect these tables?
3. What columns should be selected, filtered, or aggregated?
4. Is this a simple query or does it need CTEs/window functions?

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

After thinking through the steps above, return ONLY the SQL query below. NO explanations, NO markdown, NO text before or after the query:
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

    return f"""You are a data visualization specialist. Analyze whether this data would benefit from a chart.

**Question:** {user_question}
**Data sample:** {truncated_result}

**Analysis Steps:**
1. Examine the user's question - do they explicitly request a chart?
2. Look at the data structure - how many rows and columns?
3. Identify the data type - is it categorical, numerical, time-series?
4. Consider if visualization adds value beyond text

**Decision Criteria:**

**Return "yes" if:**
1. User EXPLICITLY asks for: "chart", "visualize", "plot", "graph", "visualization"
2. Question implies visual comparison would be helpful (e.g., "compare across...", "trends over time", "distribution of...")
3. Data has multiple categories/time points that benefit from visual representation

**Return "no" if:**
1. Simple lookup or count ("how many", "what is the total")
2. User asks to "list" or "show" without visual intent
3. Single value answer
4. Only 1-2 rows of data (insufficient for meaningful chart)

**Be conservative:** When in doubt, prefer "no". Only suggest visualization when it clearly adds value.

**Chart Type Selection:**
- Comparison/ranking data (e.g., top 10, by category) → "bar"
- Time series/trends (e.g., daily, monthly, over time) → "line"
- Parts of whole/proportions (e.g., percentage breakdown) → "pie"

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

    return f"""You are a data analyst converting SQL results into natural language. Think step-by-step before responding.

**Question:** {question}
**Data (JSON):** {truncated_result}

**ANALYSIS STEPS:**
Before writing your answer:
1. First, parse the JSON structure - identify what columns are present
2. Understand what each row represents in relation to the question
3. Identify the key insight or pattern that answers the question
4. Check for any surprising trends or outliers in the data
5. Formulate a clear, concise natural language response

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
- **CRITICAL: Escape ALL dollar signs with backslash: \$100 (NEVER use $100 directly)**
- This prevents LaTeX rendering issues in the frontend

**WRONG examples to AVOID:**
❌ "19,983thanaveragetransactionsvalue128.55" - NO SPACES
❌ "XXL19983128.55" - VALUES CONCATENATED
❌ "categoryArevenue19983" - COLUMN NAMES MIXED
❌ "Total revenue: $19,983" - DOLLAR SIGN NOT ESCAPED (will render as LaTeX)

**CORRECT examples:**
✓ "Category A has a revenue of \$19,983 with average value of \$128.55"
✓ "- Category: A\n- Revenue: \$19,983\n- Average: \$128.55"
✓ "Total sales: \$50,000" - DOLLAR SIGN PROPERLY ESCAPED

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

**Proactive Insight Discovery (MANDATORY):**
After answering the question, you MUST analyze the data and provide 1-2 additional insights that the user didn't explicitly ask for.

Look for:
1. **Concentration patterns**: Top N items account for large portion (e.g., "Top 3 items account for 75% of total")
2. **Outliers/Anomalies**: Values significantly higher/lower than average (e.g., "One value is 5x higher than average")
3. **Imbalances**: Uneven distribution across categories (e.g., "One category dominates with 80% share")
4. **Correlations**: Interesting relationships between fields (e.g., "Field X shows 3x higher values when Field Y is larger")

**Format your response in TWO sections:**

**Answer:**
[Your direct answer to the question]

💡 **Interesting Insight:**
[1-2 sentences about a pattern you discovered in the data that the user didn't ask about]

**Rules for insights:**
- Base insights ONLY on the actual data shown in the results
- Be specific with numbers and percentages
- Keep it brief (1-2 sentences max)
- Focus on actionable or surprising patterns
- If no interesting pattern exists, write "No significant patterns detected"

**Example structure:**
Answer: The top 3 entries are Person #1 with \$5,000, Person #2 with \$4,200, and Person #3 with \$3,800.

💡 **Interesting Insight:** These top 3 entries account for 65% of the total, showing a high concentration pattern."""


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
