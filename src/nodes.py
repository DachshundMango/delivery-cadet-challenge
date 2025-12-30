import ast
import os
import json
import re
from typing import Set, Optional
from dotenv import load_dotenv
from src.state import SQLAgentState
from src.logger import setup_logger
from src.db import get_db_engine
from src.errors import (
    ValidationError,
    SQLGenerationError,
    SchemaLoadError,
    LLMError
)
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langgraph.types import Command
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.exc import SQLAlchemyError
import sqlparse
from sqlparse.sql import IdentifierList, Identifier
from sqlparse.tokens import Keyword
import plotly.express as px

load_dotenv()
logger = setup_logger('cadet.nodes')

# LLM configuration (can be overridden by environment variable)
LLM_MODEL = os.getenv('LLM_MODEL', 'llama-3.1-8b-instant')
llm = ChatGroq(model=LLM_MODEL)

# File paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, 'src')
SCHEMA_JSON_PATH = os.path.join(SRC_DIR, 'schema_info.json')

# Module-level caches
_SCHEMA_CACHE: Optional[str] = None
_DB_ENGINE: Optional[Engine] = None

# Configuration constants
MAX_RETRY_COUNT = 3
VALID_CHART_TYPES = {'bar', 'line', 'pie'}


def get_cached_engine() -> Engine:
    """Get or create cached database engine"""
    global _DB_ENGINE
    if _DB_ENGINE is None:
        _DB_ENGINE = get_db_engine()
    return _DB_ENGINE


def load_schema_info() -> str:
    """
    Load pre-generated schema info from schema_info.json with caching.

    Returns:
        LLM-ready schema description string

    Raises:
        SchemaLoadError: If schema file not found or invalid
    """
    global _SCHEMA_CACHE

    if _SCHEMA_CACHE is not None:
        return _SCHEMA_CACHE

    if not os.path.exists(SCHEMA_JSON_PATH):
        raise SchemaLoadError(
            f"{SCHEMA_JSON_PATH} not found.\n"
            "Please run: python src/generate_schema.py"
        )

    try:
        with open(SCHEMA_JSON_PATH, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)

        _SCHEMA_CACHE = schema_data.get('llm_prompt', '')

        if not _SCHEMA_CACHE:
            raise SchemaLoadError("Empty llm_prompt in schema_info.json")

        logger.info("Schema info loaded and cached")
        return _SCHEMA_CACHE

    except json.JSONDecodeError as e:
        raise SchemaLoadError(f"Invalid JSON in schema file: {e}")

# def mask_pii_in_query_result(sql_query: str, result_str: str) -> str:
#     """
#     Always apply name pattern matching, regardless of column names.
#     Dataset-agnostic approach.
#     """
#     # 조건 체크 없이 항상 패턴 매칭 적용
#     masked_result = re.sub(r"'([A-Z][a-z]+)'", "'[NAME_REDACTED]'", result_str)
#     return masked_result

def read_question(state: SQLAgentState) -> dict:
    """
    Extract user question from the last message in state.

    Handles both simple string messages and multimodal content blocks
    (text, images, etc.). This is the entry point of the workflow.

    Args:
        state: Current workflow state

    Returns:
        Dictionary with 'user_question' key

    Raises:
        ValidationError: If message format is invalid

    Node Position: START → read_question → intent_classification
    """
    messages = state.get("messages", [])

    if not messages:
        logger.warning("No messages in state")
        return {"user_question": None}

    last_message = messages[-1]

    try:
        # Extract content from message
        if isinstance(last_message, dict):
            content = last_message.get('content')
        else:
            content = last_message.content

        # Handle multimodal content (list of blocks)
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get('type') == 'text':
                    content = block.get('text', '')
                    break
                elif isinstance(block, str):
                    content = block
                    break
            else:
                # No text block found
                content = str(content[0]) if content else ''

        # Validate content type
        if not isinstance(content, str):
            raise ValidationError(
                f"Invalid message content type: {type(content)}",
                details={'content': str(content)[:100]}
            )

        logger.info(f"Question extracted: {content[:50]}...")
        return {"user_question": content}

    except Exception as e:
        logger.error(f"Failed to extract question: {e}")
        raise ValidationError(f"Message extraction failed: {e}")

def intent_classification(state: SQLAgentState) -> dict:
    """
    Classify user intent as 'sql' or 'general'.

    Determines whether the question requires database query (sql)
    or general conversation (general). This routing decision affects
    the entire workflow path.

    Args:
        state: Current workflow state (requires user_question)

    Returns:
        Dictionary with 'intent' key ('sql' or 'general')

    Raises:
        ValidationError: If user_question is missing or invalid

    Node Position: read_question → intent_classification → [sql/general branch]
    """
    user_question = state.get('user_question')

    if not user_question:
        raise ValidationError("Missing user_question in state")

    # Improved prompt with few-shot examples
    intent_prompt = """Classify user input into: sql or general

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

    try:
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "{intent_prompt}"),
            ("human", "{user_question}")
        ])

        final_prompt_value = prompt_template.invoke({
            "intent_prompt": intent_prompt,
            "user_question": user_question
        })

        response = llm.invoke(final_prompt_value)

        # Clean markdown formatting (remove **, `, ', etc.)
        intent = response.content.strip().lower()
        intent = intent.replace("*", "").replace("`", "").replace("'", "").replace('"', "").strip()

        # Validate intent
        if intent not in ['sql', 'general']:
            logger.warning(f"Invalid intent '{response.content.strip()}', defaulting to 'general'")
            intent = 'general'

        logger.info(f"Intent classified: {intent} for question: {user_question[:50]}")
        return {"intent": intent}

    except Exception as e:
        logger.error(f"Intent classification failed: {e}")
        # Fallback to general intent on error
        logger.warning("Falling back to 'general' intent due to error")
        return {"intent": "general"}

def generate_general_response(state: SQLAgentState) -> dict:

    user_question = state['user_question']

    general_prompt = f"""You are a database query assistant. You ONLY answer questions using the connected database.

User question: "{user_question}"

**Critical Rules:**
- You can ONLY answer questions based on data in the database
- NEVER use web search or general knowledge
- If the user asks about capabilities, explain you analyze data from the connected database
- If greeting (hello/hi), respond politely and offer to help with database queries
- For any other question, respond: "I can only answer questions based on the database. Please ask a data-related question."

Respond briefly and clearly."""

    response = llm.invoke(general_prompt)

    return {
        "messages": [response]
    }


def _extract_table_names(parsed_query) -> Set[str]:
    """
    Extract table names from parsed SQL query.

    Args:
        parsed_query: sqlparse parsed SQL statement

    Returns:
        Set of table names (lowercase)
    """
    tables = set()
    from_seen = False

    for token in parsed_query.tokens:
        if from_seen:
            if isinstance(token, (IdentifierList, Identifier)):
                identifiers = token.get_identifiers() if isinstance(token, IdentifierList) else [token]
                for ident in identifiers:
                    # Get real table name (remove alias if present)
                    if isinstance(ident, Identifier):
                        table_name = ident.get_real_name()
                    else:
                        table_name = str(ident).split()[0]  # Take first word before alias
                    tables.add(table_name.strip('"').strip('`').lower())
                from_seen = False  # Only reset after finding identifier

        if token.ttype is Keyword and token.value.upper() == 'FROM':
            from_seen = True

    return tables


def validate_sql_query(sql_query: str, allowed_tables: Set[str]) -> bool:
    """
    Validate SQL query for safety and correctness.

    Prevents SQL injection by checking for:
    - Dangerous keywords (DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE)
    - Multiple statements (semicolon-separated)
    - Comments that might hide malicious code
    - Table names not in schema

    Args:
        sql_query: SQL query string to validate
        allowed_tables: Set of valid table names from schema

    Returns:
        True if query is safe

    Raises:
        SQLGenerationError: If query is unsafe or invalid
    """
    # Normalize query
    query_upper = sql_query.upper()

    # Check for dangerous keywords
    dangerous_keywords = {
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER',
        'TRUNCATE', 'CREATE', 'GRANT', 'REVOKE', 'EXECUTE', 'EXEC'
    }

    for keyword in dangerous_keywords:
        if f' {keyword} ' in f' {query_upper} ':
            raise SQLGenerationError(
                f"Forbidden SQL keyword: {keyword}",
                details={'query': sql_query}
            )

    # Check for multiple statements (SQL injection vector)
    # Allow trailing semicolon, but block multiple statements
    sql_stripped = sql_query.rstrip(';').strip()
    if ';' in sql_stripped:
        raise SQLGenerationError(
            "Multiple SQL statements not allowed",
            details={'query': sql_query}
        )

    # Check for SQL comments (-- or /* */)
    if '--' in sql_query or '/*' in sql_query:
        raise SQLGenerationError(
            "SQL comments not allowed",
            details={'query': sql_query}
        )

    # Parse and validate table names
    try:
        parsed = sqlparse.parse(sql_query)[0]

        # Extract table names from query
        query_tables = _extract_table_names(parsed)

        # Check if all tables are in schema
        invalid_tables = query_tables - allowed_tables
        if invalid_tables:
            raise SQLGenerationError(
                f"Unknown tables in query: {invalid_tables}",
                details={'query': sql_query, 'allowed': list(allowed_tables)}
            )

        logger.info(f"SQL validation passed: {len(query_tables)} tables")
        return True

    except Exception as e:
        raise SQLGenerationError(f"SQL parsing failed: {e}", details={'query': sql_query})


def generate_SQL(state: SQLAgentState) -> dict:
    """
    Generate validated PostgreSQL query from user question.

    Loads database schema and prompts LLM to create a valid SQL query.
    Validates the generated query for safety before returning.

    Args:
        state: Current workflow state (requires user_question)

    Returns:
        Dictionary with 'sql_query' key

    Raises:
        ValidationError: If user_question missing
        SchemaLoadError: If schema info unavailable
        SQLGenerationError: If generated SQL is invalid/unsafe

    Node Position: intent_classification[sql] → generate_SQL → execute_SQL
    """
    user_question = state.get('user_question')

    if not user_question:
        raise ValidationError("Missing user_question in state")

    try:
        # Load schema (cached after first call)
        schema_info = load_schema_info()

        # Load allowed tables for validation
        with open(SCHEMA_JSON_PATH, 'r') as f:
            schema_data = json.load(f)
        allowed_tables = set(schema_data['tables'].keys())

        # Concise prompt with PostgreSQL-specific quoting rules
        sql_prompt = f"""Generate PostgreSQL SELECT query.

**Database Schema:**
{schema_info}

**CRITICAL PostgreSQL Quoting Rules:**
- PostgreSQL converts unquoted identifiers to LOWERCASE
- ALWAYS use double quotes around ALL column names, even after table aliases
- Quote every column reference: alias."columnName" NOT alias.columnName

**Examples:**
CORRECT: SELECT s."first_name", s."customerID" FROM "sales_customers" s JOIN "sales_transactions" t ON s."customerID" = t."customerID"
WRONG: SELECT s.first_name, s.customerID FROM "sales_customers" s JOIN "sales_transactions" t ON s.customerID = t.customerID

**Query Rules:**
1. Use ONLY tables/columns from schema above
2. Use GROUP BY with aggregate functions (SUM, COUNT, AVG)
3. ORDER BY aliases or column position for aggregates
4. Return ONLY SQL query - no markdown, no explanations

**User Question:** {user_question}

**SQL Query:**"""

        response = llm.invoke(sql_prompt)
        sql_query = response.content.strip()

        # Clean markdown formatting
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

        # CRITICAL: Validate query safety
        validate_sql_query(sql_query, allowed_tables)

        logger.info(f"SQL generated and validated: {sql_query[:100]}...")
        return {"sql_query": sql_query}

    except (SchemaLoadError, SQLGenerationError, ValidationError) as e:
        logger.error(f"SQL generation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in SQL generation: {e}")
        raise LLMError(f"SQL generation failed: {e}")

def execute_SQL(state: SQLAgentState) -> dict:
    """
    Execute validated SQL query against PostgreSQL database.

    Executes the validated SQL query and returns results as JSON.
    Handles various SQL errors with specific error messages.
    Prevents infinite retry loops by tracking retry count.

    Args:
        state: Current workflow state (requires sql_query)

    Returns:
        Dictionary with 'query_result' key (JSON string or error message)

    Raises:
        ValidationError: If sql_query missing

    Node Position: generate_SQL → execute_SQL → [retry/success]
    """
    sql_query = state.get('sql_query')

    if not sql_query:
        raise ValidationError("Missing sql_query in state")

    # Check retry count to prevent infinite loops
    messages = state.get('messages', [])
    retry_count = sum(1 for msg in messages
                      if 'Error:' in str(getattr(msg, 'content', '')))

    if retry_count >= MAX_RETRY_COUNT:
        error_msg = f"Error: Maximum retry limit ({MAX_RETRY_COUNT}) exceeded. Query failed."
        logger.error(f"Max retries exceeded for query: {sql_query}")
        return {"query_result": error_msg}

    try:
        engine = get_cached_engine()
        logger.info(f"Executing SQL (attempt {retry_count + 1}): {sql_query[:100]}...")

        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            rows = [dict(row._mapping) for row in result.fetchall()]

        result_str = json.dumps(rows, default=str, ensure_ascii=False)
        logger.info(f"Query succeeded: {len(rows)} rows")
        return {"query_result": result_str}

    except SQLAlchemyError as e:
        # Database errors (syntax, connection, data type, etc.)
        error_msg = f"Error: {str(e)}"
        logger.warning(f"Database error: {e}")
        return {"query_result": error_msg}

    except Exception as e:
        # Unexpected errors
        error_msg = f"Error: {str(e)}"
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {"query_result": error_msg}

def visualisation_request_classification(state: SQLAgentState) -> dict:
    """Determine if chart is needed and select type"""
    user_question = state.get('user_question', '')
    sql_result = state.get('query_result', '')
    intent = state.get('intent', '')

    # Skip visualization for non-SQL queries or errors
    if intent != 'sql' or not sql_result or 'Error:' in sql_result:
        logger.info("Skipping visualization (non-SQL or error)")
        return {"plotly_data": None}

    if sql_result in ['[]', '', 'null']:
        logger.info("Skipping visualization (empty result)")
        return {"plotly_data": None}

    # Concise prompt
    vis_prompt = f"""Analyze if result needs visualization.

**Question:** {user_question}
**Result:** {sql_result[:200]}...

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

    try:
        response = llm.invoke(vis_prompt)

        # Clean markdown formatting (similar to SQL generation)
        content = response.content.strip()
        content = content.replace("```json", "").replace("```", "").strip()

        response_json = json.loads(content)

        if response_json.get('visualise') != 'yes':
            return {"plotly_data": None}

        chart_type = response_json.get('chart_type', 'bar')
        if chart_type not in VALID_CHART_TYPES:
            logger.warning(f"Invalid chart type '{chart_type}', using 'bar'")
            chart_type = 'bar'

        plotly_data = create_plotly_chart(sql_result, chart_type)

        if plotly_data is None:
            return {"plotly_data": None}

        tool_message = ToolMessage(
            content=plotly_data,
            tool_call_id="call_visualisation_1",
            name="create_plotly_chart"
        )

        logger.info(f"Chart created: {chart_type}")
        return {"messages": [tool_message], "plotly_data": plotly_data}

    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM response as JSON")
        return {"plotly_data": None}
    except Exception as e:
        logger.error(f"Visualization failed: {e}")
        return {"plotly_data": None}

def create_plotly_chart(sql_result, chart_type):
    """Generate Plotly chart JSON from SQL results"""
    try:
        sql_list = json.loads(sql_result)
    except json.JSONDecodeError:
        try:
            sql_list = ast.literal_eval(sql_result)
        except Exception as e:
            logger.warning(f"Failed to parse SQL result for charting: {e}")
            return None
    
    if not sql_list:
        return None
    
    x_data = []
    y_data = []
    
    for data in sql_list:


        if isinstance(data, dict):
            row_values = list(data.values())
        elif isinstance(data, (list, tuple)):
            row_values = list(data)
        else:
            continue

        x_string_parts = [str(x) for x in row_values[:-1]]

        if x_string_parts:
            x_label = ' '.join(x_string_parts)
        else:
            x_label = str(row_values[0])
        
        y_label = row_values[-1]

        x_data.append(x_label)
        y_data.append(y_label)

    # Chart generation
    if chart_type == "bar":
        fig = px.bar(x=x_data, y=y_data, text=y_data, color=x_data)
    elif chart_type == "line":
        fig = px.line(x=x_data, y=y_data, markers=True)
    elif chart_type == "pie":
        fig = px.pie(names=x_data, values=y_data, hole=0.3)
    else:
        # Fallback to bar chart for unknown types
        fig = px.bar(x=x_data, y=y_data)

    return json.dumps({
        "type": "plotly",
        "data": json.loads(fig.to_json())['data'],
        "layout": json.loads(fig.to_json())['layout']
    })

def pyodide_request_classification(state: SQLAgentState) -> dict:

    user_question = state['user_question']

    # Safety check: ensure user_question is a string
    if not user_question or not isinstance(user_question, str):
        return {
            "needs_pyodide": False
        }

    pyodide_keywords = [
        'correlation', 'statistics', 'analyze', 'analyse', 'describe', 'summary',
        'std', 'mean', 'median', 'variance', 'average', 'distribution'
    ]

    needs_pyodide = any(keyword in user_question.lower() for keyword in pyodide_keywords)

    return {
        "needs_pyodide": needs_pyodide
    }


def generate_pyodide_analysis(state: SQLAgentState) -> dict:

    user_question = state['user_question']
    sql_result = state['query_result']

    # Safety check: ensure sql_result is valid
    if not sql_result or not isinstance(sql_result, str):
        return {}

    if "Error:" in sql_result or sql_result in ["[]", ""]:
        return {}

    pyodide_prompt = f"""You are a Python Data Analyst using pandas in a browser environment (Pyodide).

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
    
    response = llm.invoke(pyodide_prompt)
    code = response.content.replace("```python", "").replace("```", "").strip()
    
    tool_message = ToolMessage(
        content=code,
        tool_call_id="call_python_interpreter",
        name="python_interpreter"
    )
    
    return {
        "messages": [tool_message]
    }


def generate_response(state: SQLAgentState) -> dict:
    """Generate natural language response from SQL results"""
    question = state.get('user_question', '')
    result = state.get('query_result', '')

    # Handle errors
    if "Error:" in result:
        logger.warning("Generating error response for user")
        return {"messages": [HumanMessage(
            content=f"I encountered an error while processing your query:\n{result}\n\nPlease try rephrasing your question."
        )]}

    # Handle empty results
    if result in ['[]', '', 'null']:
        logger.info("Empty result, notifying user")
        return {"messages": [HumanMessage(
            content="No data found for your question. Please try a different query."
        )]}

    # Generate response with concise prompt
    response_prompt = f"""Answer the user's question using the query results.

**Question:** {question}
**Results:** {result[:1000]}

**Guidelines:**
- Direct, clear answer
- Natural, readable format
- NO SQL code or technical details
- Summarize if many results
- Use bullet points for readability

**Answer:**"""

    response = llm.invoke(response_prompt)
    logger.info("Response generated successfully")

    return {"messages": [response]}