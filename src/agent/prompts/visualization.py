"""
Visualization and chart generation prompts.

This module contains prompts for:
- Determining if visualization is needed
- Generating chart titles
- Classifying chart types
"""


def get_chart_title_prompt(user_question: str, chart_type: str) -> str:
    """
    Generate minimal prompt for chart title generation (token-optimized).

    Uses minimal tokens (~30-60) while maintaining quality with Temperature 0.0.
    The llama-3.3-70b model is capable enough to understand brief instructions.

    Args:
        user_question: User's original question
        chart_type: Type of chart (bar, line, pie, scatter, area)

    Returns:
        Minimal prompt string optimised for token efficiency
    """
    return f"""Create chart title (max 60 chars, Title Case):
Q: {user_question}
Type: {chart_type}
Title:"""


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

    return f"""You are a strict visualization classifier. Your DEFAULT answer is "no".

**CRITICAL RULE: DEFAULT = NO**
Only return "yes" if the user EXPLICITLY requests a visualization using specific keywords.

**Question:** {user_question}
**Data sample:** {truncated_result}

**Decision Logic:**

**Return "yes" ONLY if user question contains EXPLICIT visualization keywords:**
- "chart", "graph", "plot", "visualize", "visualization", "draw", "create a chart", "make a graph", "show me a chart"

**Return "no" for ALL other cases, including:**
- Questions about trends, comparisons, distributions WITHOUT explicit chart keywords
  Example: "What are the sales trends?" → NO (no chart keyword)
  Example: "Show me top 10 customers" → NO (no chart keyword)
  Example: "Compare revenue across regions" → NO (no chart keyword)
- User explicitly says NOT to visualize
  Example: "Don't make a chart, just show the data" → NO
  Example: "No visualization needed" → NO
- Simple data requests (list, show, get, find)
  Example: "List all products" → NO
  Example: "Show me the total revenue" → NO

**Examples:**
"What are the top 10 products by sales?" → {{"visualise": "no"}}
"Show me revenue trends over time" → {{"visualise": "no"}}
"Create a bar chart of top 10 products" → {{"visualise": "yes", "chart_type": "bar"}}
"Visualize the sales by region" → {{"visualise": "yes", "chart_type": "bar"}}
"Don't make a chart, just show the numbers" → {{"visualise": "no"}}
"Compare A and B" → {{"visualise": "no"}}

**Chart Type Selection (only if visualise="yes"):**
- Comparison/ranking → "bar"
- Time series/trends → "line"
- Time series with cumulative/fill → "area"
- Proportions/breakdown → "pie"
- Correlation/relationship between two numeric variables → "scatter"

**OUTPUT FORMAT:**
Return ONLY valid JSON. NO explanations, NO text before/after:
{{"visualise": "yes", "chart_type": "bar"}}
OR
{{"visualise": "no"}}"""
