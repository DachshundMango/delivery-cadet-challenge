"""
Pyodide (Python analysis) prompts.

This module contains prompts for:
- Generating Python code for statistical analysis
- Performing advanced data analysis in Pyodide
"""


def get_pyodide_analysis_prompt(user_question: str, data_sample: str) -> str:
    """
    Generate prompt for Pyodide-based Python analysis.

    Args:
        user_question: The user's question requesting analysis
        data_sample: JSON string showing ONE row of data to understand structure (NOT the full dataset)

    Returns:
        Formatted prompt string
    """
    return f"""You are a Python Data Analyst using pandas in a browser environment (Pyodide).

User Question: "{user_question}"

Data Structure (Sample Row):
{data_sample}

Generate Python code to analyse this data. CRITICAL RULES:

1. **Dynamic Data Loading**:
   - The full dataset is ALREADY loaded in a string variable named `csv_data` (CSV format).
   - Your code must start by loading it: `df = pd.read_csv(io.StringIO(csv_data))`
   - DO NOT define the `csv_data` variable yourself. It is injected automatically.

2. **No Hardcoding**:
   - NEVER hardcode values or results.
   - ❌ BAD: `print("Correlation is 0.85")`
   - ✅ GOOD: `print(f"Correlation: {{df['quantity'].corr(df['total']).round(2)}}")`
   - The code must calculate values dynamically from the DataFrame.

3. **Handle Missing Values**:
   - Check for NaN/None values programmatically.
   - Example: `if df['col'].notna().any(): ...`

4. **Use Actual Columns Only (CRITICAL)**:
   - CHECK the "Data Structure" above carefully.
   - If the data is ALREADY aggregated (contains 'mean', 'count', 'std_dev'), DO NOT try to aggregate it again.
   - Just print/format the existing data nicely.
   - ❌ BAD: `df.groupby('size')['value'].mean()` (when 'mean' column already exists)
   - ✅ GOOD: `print(df[['size', 'mean', 'std_dev']])`

5. **Data Type Conversion (CRITICAL)**:
   - SQL results often come as strings (e.g., "123.45") to preserve precision.
   - You MUST convert numeric columns using `pd.to_numeric(df['col'])` before doing ANY maths or comparison.
   - Example: `df['mean'] = pd.to_numeric(df['mean'])`

6. **Output Format**:
   - Use `print()` to show the final analysis.
   - Do NOT use matplotlib or plotting libraries - text output only.
   - Import pandas as pd.

Return ONLY executable Python code below. NO markdown, NO explanations:
"""
