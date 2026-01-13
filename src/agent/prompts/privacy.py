"""
Privacy protection and response generation prompts.

This module contains prompts for:
- Data masking (PII protection)
- PII detection in database columns
- Natural language response generation with privacy controls
"""


def get_data_masking_prompt(sql_result: str) -> str:
    """
    Generate prompt to mask personal names in SQL result data.

    Args:
        sql_result: JSON string of SQL query results

    Returns:
        Formatted prompt string
    """
    return f"""You are a data privacy filter. Your task is to identify and mask INDIVIDUAL PERSON NAMES while preserving business/organisation names.

**Input Data:**
{sql_result}

**Task:**
Look at each value in the data. If it appears to be an INDIVIDUAL PERSON'S NAME (like "John Smith", "Alice", "Robert Johnson"), replace it with "Person #N" with sequential numbering.

**What to MASK (individual person names):**
- Typical human first names: John, Sarah, Michael, Emily, David
- Full names with first + last: "John Smith", "Alice Brown"
- Single person names in name fields

**What NOT to mask (business/organisational names):**
- Business names: "Acme Corp", "Global Services Inc."
- Stores/organisations: "Downtown Shop", "City Centre"
- Brands/products: "Product A", "Brand X"
- Companies: "ABC Corporation", "XYZ Supplies"
- Locations: "New York", "London", "Main Street"

**Key distinction:**
- Person names sound like individual humans (John, Sarah, Michael)
- Business names sound like organisations/places/brands (Palace, Corner, Foods, Inc.)

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

    return f"""You are a data privacy expert. Analyse the following database columns and identify which ones contain INDIVIDUAL PERSON NAMES (PII).

**Database Column Information:**
{formatted_data}

**Your Task:**
Identify columns that contain INDIVIDUAL HUMAN NAMES ONLY.

**MUST Include (PII - Personal Names):**
- Person first names, last names, full names (e.g., customer names, employee names, user names)
- Reviewer names, user names (when they are individual people)
- Any column with individual person identifiers like "John", "Sarah", "Michael Smith"

**MUST Exclude (NOT PII):**
- Organisation names ("Acme Corp", "Global Services")
- Company names, business names ("ABC Corporation", "XYZ Industries Inc.")
- City names, location names ("New York", "Boston", "Main Street")
- Product names ("Product A", "Brand X")
- Store names ("Downtown Shop", "City Centre")
- IDs, numbers, dates, amounts

**Key Distinction:**
- Person names: Sound like individual humans (John, Alice, Smith, Emily Davis)
- Business names: Sound like organisations/places/brands (Palace, Corner, Inc., Bakery, Foods)

**Examples:**

Example 1 - Include these:
Table: customers
- firstName: ["John", "Alice", "Bob"] ✓ PII (person names)
- lastName: ["Smith", "Brown", "Johnson"] ✓ PII (person names)

Example 2 - Exclude these:
Table: organisations
- organisationName: ["Acme Corp", "Global Services"] ✗ NOT PII (business names)
- city: ["New York", "Boston"] ✗ NOT PII (location names)

Example 3 - Mixed:
Table: reviews
- reviewerName: ["Sarah Johnson", "Mike Davis"] ✓ PII (person names)
- organisationName: ["Acme Corp", "Global Services"] ✗ NOT PII (business names)

**CRITICAL:** Only return columns that contain INDIVIDUAL PERSON NAMES. Be conservative - when in doubt, exclude it.

If a table has no PII columns, omit it from the result or use empty array.

Return ONLY the JSON object below. NO markdown, NO explanations, NO text before or after:
{{
  "table_name1": ["pii_column1", "pii_column2"],
  "table_name2": ["pii_column3"]
}}"""


def get_response_generation_prompt(question: str, result: str, needs_pyodide: bool = False) -> str:
    """
    Generate prompt for natural language response from SQL results.

    Args:
        question: The user's original question
        result: JSON string of SQL query results
        needs_pyodide: Whether Python analysis is being performed

    Returns:
        Formatted prompt string
    """
    # For Pyodide: result is metadata. For normal: truncate to 1000 chars
    truncated_result = result if needs_pyodide else (result[:1000] if len(result) > 1000 else result)

    pyodide_instruction = ""
    if needs_pyodide:
        pyodide_instruction = """
        **PYTHON ANALYSIS MODE:**
        Data format: {"row_count": N, "columns": [...], "sample_rows": [2 examples]}

        ANSWER RULES:
        - Use row_count for total records (NOT the sample_rows length!)
        - List columns, mention row_count, then say: "Advanced statistical analysis is being generated in the Python console below."
        - DO NOT count, calculate percentages, or analyze patterns from sample_rows

        INSIGHT RULES (Pyodide mode):
        - Keep it to ONE sentence only
        - Comment ONLY on data structure (e.g., "The dataset includes timestamp and ID fields enabling temporal analysis.")
        - DO NOT use speculative words: "may", "could", "might", "suggests"
        - DO NOT analyze sample_rows or mention "no patterns detected"
        - Focus on what columns exist and what type of analysis they enable
        """

    return f"""You are a data analyst converting SQL results into natural language. Think step-by-step before responding.

    **Question:** {question}
    **Data (JSON):** {truncated_result}

    {pyodide_instruction}

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

**Formatting:**
- Use bullet points/numbers, natural language, proper spacing
- Add commas in numbers: "19,983" not "19983"
- **CRITICAL: Escape dollar signs: \$100 NOT $100** (prevents LaTeX rendering)

**Examples:**
✓ "Category A: \$19,983 with average \$128.55"
❌ "categoryA19983" (no spaces, no formatting)

**CRITICAL - Privacy Protection:**
⚠️ NEVER show individual person names - Replace with "Person #N"

- Mask: firstName, lastName, fullName (individual people)
- Keep: organisation names, company names, locations

**Examples:**
❌ "John Smith - \$1000"
✅ "Person #1 - \$1000"
✅ "Acme Corp - \$1000" (business name, keep)

**Proactive Insight Discovery (MANDATORY):**
After answering the question, you MUST analyse the data and provide 1-2 additional insights that the user didn't explicitly ask for.

Look for:
1. **Concentration patterns**: Top N items account for large portion (e.g., "Top 3 items account for 75% of total")
2. **Outliers/Anomalies**: Values significantly higher/lower than average (e.g., "One value is 5x higher than average")
3. **Imbalances**: Uneven distribution across categories (e.g., "One category dominates with 80% share")
4. **Correlations**: Interesting relationships between fields (e.g., "Field X shows 3x higher values when Field Y is larger")

**Rules for insights:**
- Base insights ONLY on the actual data shown in the results
- Be specific with numbers and percentages
- Keep it brief (1-2 sentences max)
- Focus on actionable or surprising patterns
- If no interesting pattern exists, write "No significant patterns detected"

<output_format>
Structure your response using XML tags:

<answer>
Your direct answer to the question here.
</answer>

<insight>
💡 **Interesting Insight:** 1-2 sentences about a pattern you discovered in the data that the user didn't ask about.
</insight>

Example:
<answer>
The top 3 entries are Person #1 with \$5,000, Person #2 with \$4,200, and Person #3 with \$3,800.
</answer>

<insight>
💡 **Interesting Insight:** These top 3 entries account for 65% of the total, showing a high concentration pattern.
</insight>
</output_format>

Now generate your response following the XML format above:"""
