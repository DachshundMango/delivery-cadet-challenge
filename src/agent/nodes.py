"""
LangGraph Agent Nodes

This module defines the core logic nodes for the SQL Agent workflow.
Each function represents a node in the LangGraph state machine, processing
the state and returning updates.

Key Components:
- Intent Classification: Routes between SQL generation and general conversation
- SQL Generation: Converts natural language to PostgreSQL queries (with retries)
- Execution: Runs queries against the database
- Visualization: Determines if and how to chart the results
- Analysis: Optional Python-based statistical analysis using Pyodide
- Response Generation: Formats final answers in natural language
"""

import ast
import os
import json
import csv
import io
from typing import Optional
from dotenv import load_dotenv
from src.agent.state import SQLAgentState
from src.agent.prompts import (
    get_intent_classification_prompt,
    get_general_response_prompt,
    get_sql_generation_prompt,
    get_simple_sql_for_pyodide_prompt,
    get_visualization_prompt,
    get_pyodide_analysis_prompt,
    get_response_generation_prompt,
)
from src.agent.feedbacks import (
    get_unknown_tables_feedback,
    get_multiple_statements_feedback,
    get_sql_comments_feedback,
    get_forbidden_keyword_feedback,
    get_column_not_found_feedback,
    get_parsing_error_feedback,
    get_division_by_zero_feedback,
    get_datetime_format_feedback,
    get_alias_reference_feedback,
)
from src.core.logger import setup_logger
from src.core.db import get_db_engine
from src.core.validation import validate_sql_query
from src.core.errors import (
    ValidationError,
    SQLGenerationError,
    SchemaLoadError,
    LLMError
)
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.types import Command
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.exc import SQLAlchemyError
import plotly.express as px

# Automatically find .env file in the project root and load environment variables
load_dotenv()
logger = setup_logger('cadet.nodes')

# LLM configuration
LLM_MODEL = os.getenv('LLM_MODEL', 'llama-3.3-70b')
CEREBRAS_API_KEY = os.getenv('CEREBRAS_API_KEY')
CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"

# Task-specific LLMs with optimized temperature settings (using Cerebras via OpenAI-compatible API)
llm_intent = ChatOpenAI(model=LLM_MODEL, temperature=0.0, api_key=CEREBRAS_API_KEY, base_url=CEREBRAS_BASE_URL)    # Intent classification: deterministic
llm_sql = ChatOpenAI(model=LLM_MODEL, temperature=0.1, api_key=CEREBRAS_API_KEY, base_url=CEREBRAS_BASE_URL)       # SQL generation: accurate & safe
llm_vis = ChatOpenAI(model=LLM_MODEL, temperature=0.0, api_key=CEREBRAS_API_KEY, base_url=CEREBRAS_BASE_URL)       # Visualization: deterministic (strict keyword detection)
llm_response = ChatOpenAI(model=LLM_MODEL, temperature=0.7, api_key=CEREBRAS_API_KEY, base_url=CEREBRAS_BASE_URL)  # Response: natural & varied

# Default LLM (for backward compatibility)
llm = llm_sql

# File paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_DIR = os.path.join(BASE_DIR, 'src')
SCHEMA_JSON_PATH = os.path.join(SRC_DIR, 'config', 'schema_info.json')

# Module-level caches
_SCHEMA_CACHE: Optional[str] = None
_DB_ENGINE: Optional[Engine] = None

# Configuration constants
MAX_RETRY_COUNT = 3
VALID_CHART_TYPES = {'bar', 'line', 'pie'}


def get_cached_engine() -> Engine:
    """
    Get or create cached database engine.
    
    Uses a module-level global variable `_DB_ENGINE` to store the connection pool,
    preventing overhead from recreating engines on every request.
    
    Returns:
        sqlalchemy.Engine: Active database engine instance
    """
    global _DB_ENGINE
    if _DB_ENGINE is None:
        _DB_ENGINE = get_db_engine()
    return _DB_ENGINE


def load_schema_info() -> str:
    """
    Load pre-generated schema info from schema_info.json with caching.
    
    The schema information is critical for the LLM to generate valid SQL.
    It includes table names, column names, types, and foreign key relationships.
    
    Returns:
        str: LLM-ready schema description string
    
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


def apply_pii_masking(rows: list[dict]) -> list[dict]:
    """
    Apply deterministic PII masking to SQL results (Python-only, no LLM).

    Loads PII column names from schema_info.json and masks matching columns
    with "Person #N" format. Removes duplicate name fields (e.g., firstName + lastName).

    Args:
        rows: SQL query results as list of dicts

    Returns:
        Masked rows with PII replaced
    """
    if not rows:
        return rows

    # Load PII columns from schema_info.json
    try:
        with open(SCHEMA_JSON_PATH, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)
        pii_columns_config = schema_data.get('pii_columns', {})
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        logger.debug("No PII configuration found, skipping masking")
        return rows

    # Flatten all PII columns into a single set (table-agnostic matching)
    pii_columns = set()
    for table_pii in pii_columns_config.values():
        pii_columns.update(table_pii)

    if not pii_columns:
        return rows

    logger.info(f"Masking PII columns: {pii_columns}")

    # Apply masking
    masked_rows = []
    person_counter = 1

    for row in rows:
        masked_row = {}
        first_pii_found = False

        for col_name, value in row.items():
            if col_name in pii_columns:
                if not first_pii_found:
                    masked_row[col_name] = f"Person #{person_counter}"
                    first_pii_found = True
                # Skip other PII columns in same row (e.g., lastName after firstName)
            else:
                masked_row[col_name] = value

        if first_pii_found:
            person_counter += 1

        masked_rows.append(masked_row)

    logger.info(f"Masked {person_counter - 1} individuals")
    return masked_rows


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

    except (AttributeError, KeyError, TypeError) as e:
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

    try:
        # Get prompt from prompts module
        intent_prompt = get_intent_classification_prompt()

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "{intent_prompt}"),
            ("human", "{user_question}")
        ])

        final_prompt_value = prompt_template.invoke({
            "intent_prompt": intent_prompt,
            "user_question": user_question
        })

        response = llm_intent.invoke(final_prompt_value)  # Temperature: 0.0 (deterministic)

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

    # Get prompt from prompts module
    general_prompt = get_general_response_prompt(user_question)

    response = llm_response.invoke(general_prompt)  # Temperature: 0.7 (natural language)

    return {
        "messages": [response]
    }


def generate_SQL(state: SQLAgentState) -> dict:
    """
    Generate validated PostgreSQL query from user question.

    Loads database schema and prompts LLM to create a valid SQL query.
    Validates the generated query for safety before returning.
    On retry, provides specific hints based on previous error.

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

        # Load allowed tables for validation to prevent hallucinations
        with open(SCHEMA_JSON_PATH, 'r') as f:
            schema_data = json.load(f)
        allowed_tables = set(schema_data['tables'].keys())

        # Check if pyodide analysis is needed
        needs_pyodide = state.get('needs_pyodide', False)

        logger.info(f"SQL Generation: needs_pyodide={needs_pyodide}")

        # Get base prompt from prompts module
        # If pyodide is needed, use simpler SQL prompt to just fetch raw data
        if needs_pyodide:
            logger.info("Using simple SQL prompt for Pyodide analysis")
            sql_prompt = get_simple_sql_for_pyodide_prompt(schema_info, user_question)
        else:
            logger.info("Using complex SQL prompt for direct analysis")
            sql_prompt = get_sql_generation_prompt(schema_info, user_question)

        # Check if this is a retry (look for previous errors in message history)
        messages = state.get('messages', [])
        retry_count = sum(1 for msg in messages if 'Error:' in str(getattr(msg, 'content', '')))

        if retry_count > 0:
            # Get previous error from query_result to generate targeted feedbacks
            previous_error = state.get('query_result', '')

            # Add specific feedbacks based on error type to guide the LLM's correction
            if 'Unknown tables in query' in previous_error:
                # Extract invalid table names from error
                import re
                match = re.search(r"Unknown tables in query: (\{.*?\})", previous_error)
                if match:
                    invalid_tables_str = match.group(1)
                    # Check if it's a subquery alias issue (single letter or short name)
                    invalid_tables_set = eval(invalid_tables_str)  # Convert string set to actual set
                    is_likely_alias = any(len(t) <= 2 for t in invalid_tables_set)

                    # Use feedback module
                    sql_prompt += get_unknown_tables_feedback(
                        invalid_tables=invalid_tables_set,
                        allowed_tables=allowed_tables,
                        is_likely_alias=is_likely_alias
                    )

            elif 'Multiple SQL statements not allowed' in previous_error:
                sql_prompt += get_multiple_statements_feedback()

            elif 'SQL comments not allowed' in previous_error:
                sql_prompt += get_sql_comments_feedback()

            elif 'Forbidden SQL keyword: CREATE' in previous_error:
                sql_prompt += get_forbidden_keyword_feedback('CREATE')

            elif 'column' in previous_error.lower() and 'does not exist' in previous_error.lower():
                # Check if it's an alias reference issue (UndefinedColumn)
                import re
                match = re.search(r'column "(.+?)" does not exist', previous_error)
                if match:
                    column = match.group(1)
                    # If the column is NOT in allowed_tables, it's likely an alias
                    # (Simplified check: just provide the alias feedback as a hint)
                    sql_prompt += get_alias_reference_feedback(column)
                else:
                    sql_prompt += get_column_not_found_feedback()

            elif 'division by zero' in previous_error.lower():
                sql_prompt += get_division_by_zero_feedback()

            elif 'datetime' in previous_error.lower() and 'format' in previous_error.lower():
                 sql_prompt += get_datetime_format_feedback()

            else:
                # Catch-all for other SQL errors (GroupingError, SyntaxError, etc.)
                sql_prompt += get_parsing_error_feedback(previous_error)

            logger.info(f"Retry {retry_count}: Added specific feedback for error type")

        response = llm_sql.invoke(sql_prompt)  # Temperature: 0.1 (accurate & safe queries)
        raw_content = response.content.strip()

        # Try XML parsing first (new structured format)
        import re
        sql_match = re.search(r'<sql>(.*?)</sql>', raw_content, re.DOTALL | re.IGNORECASE)

        if sql_match:
            # Extract SQL from XML tags
            sql_query = sql_match.group(1).strip()

            # Optional: Extract reasoning for logging (not used in validation)
            reasoning_match = re.search(r'<reasoning>(.*?)</reasoning>', raw_content, re.DOTALL | re.IGNORECASE)
            if reasoning_match:
                reasoning = reasoning_match.group(1).strip()
                logger.debug(f"LLM reasoning: {reasoning[:200]}...")
        else:
            # Fallback to legacy parsing (markdown format)
            sql_query = raw_content.replace("```sql", "").replace("```", "").strip()
            logger.debug("Using fallback parsing (no XML tags found)")

        # CRITICAL: Validate query safety
        validate_sql_query(sql_query, allowed_tables)

        logger.info(f"SQL generated and validated: {sql_query[:100]}...")
        # Clear previous error in query_result so execute_SQL runs the new query
        return {"sql_query": sql_query, "query_result": None}

    except SQLGenerationError as e:
        # Validation failed - store error in state for retry logic
        error_msg = f"Error: {str(e)}"
        logger.error(f"SQL validation failed: {e}")
        logger.debug(f"Failed SQL query: {sql_query if 'sql_query' in locals() else 'N/A'}")

        # Return error in query_result AND messages so retry logic can process it
        # messages is needed for retry_count tracking
        return {
            "sql_query": sql_query if 'sql_query' in locals() else None,
            "query_result": error_msg,
            "messages": [AIMessage(content=error_msg)]
        }

    except (SchemaLoadError, ValidationError) as e:
        # Other errors - still raise
        logger.error(f"SQL generation failed: {e}")
        raise

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
    query_result = state.get('query_result')

    # Calculate retry count first
    messages = state.get('messages', [])
    retry_count = sum(1 for msg in messages
                      if 'Error:' in str(getattr(msg, 'content', '')))

    # If query_result already has an error (from validation failure), pass it through
    if query_result and 'Error:' in query_result:
        # Check retry limit only if we are still in error state
        if retry_count >= MAX_RETRY_COUNT:
            error_msg = f"Error: Maximum retry limit ({MAX_RETRY_COUNT}) exceeded. Query failed."
            logger.error(f"Max retries exceeded for query: {sql_query}")
            return {
                "query_result": error_msg,
                "messages": [AIMessage(content=error_msg)]
            }

        logger.info("Skipping execution - validation error already in query_result")
        return {}  # Don't overwrite query_result, just pass through

    if not sql_query:
        raise ValidationError("Missing sql_query in state")

    # If we get here, either it's the first try OR generate_SQL succeeded (query_result is None)
    # So we execute regardless of retry_count history

    try:
        engine = get_cached_engine()
        logger.info(f"Executing SQL (attempt {retry_count + 1}): {sql_query[:100]}...")

        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            rows = [dict(row._mapping) for row in result.fetchall()]

        # Apply PII masking (deterministic, Python-only)
        masked_rows = apply_pii_masking(rows)

        result_str = json.dumps(masked_rows, default=str, ensure_ascii=False)
        logger.info(f"Query succeeded: {len(masked_rows)} rows")
        return {"query_result": result_str}

    except SQLAlchemyError as e:
        # Database errors (syntax, connection, data type, etc.)
        error_msg = f"Error: {str(e)}"
        logger.warning(f"Database error: {e}")
        return {
            "query_result": error_msg,
            "messages": [AIMessage(content=error_msg)]
        }

    except Exception as e:
        # Unexpected errors
        error_msg = f"Error: {str(e)}"
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {
            "query_result": error_msg,
            "messages": [AIMessage(content=error_msg)]
        }

def visualisation_request_classification(state: SQLAgentState) -> dict:
    """
    Determine if a chart is needed and select the appropriate type.
    
    Analyzes the user's question and the SQL results to decide if visualization
    adds value. If yes, it generates the Plotly JSON configuration.
    
    Args:
        state: Current workflow state (requires query_result, intent)
        
    Returns:
        dict: Updates to state with 'plotly_data' (JSON string or None) 
              and optional ToolMessage.
    """
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

    try:
        # Get prompt from prompts module
        vis_prompt = get_visualization_prompt(user_question, sql_result)

        response = llm_vis.invoke(vis_prompt)  # Temperature: 0.2 (consistent decisions)

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

        # sql_result is already PII-masked by execute_SQL node
        plotly_data = create_plotly_chart(sql_result, chart_type, user_question)

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

def create_plotly_chart(sql_result, chart_type, user_question=""):
    """Generate Plotly chart JSON from SQL results with proper titles and labels"""
    try:
        sql_list = json.loads(sql_result)
    except json.JSONDecodeError:
        try:
            sql_list = ast.literal_eval(sql_result)
        except (ValueError, SyntaxError) as e:
            logger.warning(f"Failed to parse SQL result for charting: {e}")
            return None

    if not sql_list:
        return None

    # Extract column names from first row
    first_row = sql_list[0]
    if isinstance(first_row, dict):
        columns = list(first_row.keys())
    else:
        columns = []

    # Determine axis labels from column names
    x_label = columns[0] if len(columns) >= 1 else "Category"
    y_label = columns[-1] if len(columns) >= 1 else "Value"

    # Generate chart title from user question
    if user_question:
        # Clean up common phrases
        title = user_question.replace("show me", "").replace("Show me", "")
        title = title.replace("create a chart", "").replace("Create a chart", "")
        title = title.replace("create a bar chart", "").replace("Create a bar chart", "")
        title = title.replace("visualize", "").replace("Visualize", "")
        title = title.replace("make a graph", "").replace("Make a graph", "")
        title = title.strip()

        # Take only first sentence (up to . or ?)
        if '.' in title:
            title = title.split('.')[0]
        if '?' in title:
            title = title.split('?')[0]

        # Remove "showing" or "of" at the start
        if title.lower().startswith("showing "):
            title = title[8:]
        if title.lower().startswith("of "):
            title = title[3:]

        # Limit length to prevent overflow
        if len(title) > 60:
            title = title[:57] + "..."

        # Capitalize first letter
        if title:
            title = title[0].upper() + title[1:]
    else:
        title = f"{y_label} by {x_label}"

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
            x_value = ' '.join(x_string_parts)
        else:
            x_value = str(row_values[0])

        y_value = row_values[-1]

        x_data.append(x_value)
        y_data.append(y_value)

    # Try to convert y_data to numbers if they are strings representing numbers
    try:
        # Check if all values can be converted to float
        numeric_y_data = [float(str(y).replace(',', '')) for y in y_data if y is not None]
        if len(numeric_y_data) == len(y_data):
            y_data = numeric_y_data
    except (ValueError, TypeError):
        # Keep as is if conversion fails
        pass

    # Chart generation with layout customization
    if chart_type == "bar":
        fig = px.bar(x=x_data, y=y_data, text=y_data)
        fig.update_layout(
            xaxis_title=x_label,
            yaxis_title=y_label,
            showlegend=False
        )
        fig.update_traces(textposition='outside')
    elif chart_type == "line":
        fig = px.line(x=x_data, y=y_data, markers=True)
        fig.update_layout(
            xaxis_title=x_label,
            yaxis_title=y_label,
            showlegend=False
        )
    elif chart_type == "pie":
        fig = px.pie(names=x_data, values=y_data, hole=0.3)
        fig.update_traces(textposition='inside', textinfo='percent+label')
    else:
        # Fallback to bar chart for unknown types
        fig = px.bar(x=x_data, y=y_data)
        fig.update_layout(
            xaxis_title=x_label,
            yaxis_title=y_label,
            showlegend=False
        )

    # Apply common layout settings to all chart types
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center'
        },
        font=dict(size=12),
        height=500,
        margin=dict(l=50, r=50, t=80, b=50)
    )

    return json.dumps({
        "type": "plotly",
        "data": json.loads(fig.to_json())['data'],
        "layout": json.loads(fig.to_json())['layout']
    })

def pyodide_request_classification(state: SQLAgentState) -> dict:

    user_question = state['user_question']

    # Safety check: ensure user_question is a string
    if not user_question or not isinstance(user_question, str):
        logger.warning("Pyodide classification: invalid user_question")
        return {
            "needs_pyodide": False
        }

    # Only trigger for advanced statistical analysis that SQL cannot handle
    pyodide_keywords = [
        'correlation',
        'statistical analysis',
        'standard deviation',
        'variance',
        'distribution',  # Covers "distribution analysis", "price distribution", etc.
        'skewness',
        'kurtosis',
        'outlier',
        'outliers',
        'percentile',
        'quartile',
        'time series'  # Covers "time series analysis"
    ]

    needs_pyodide = any(keyword in user_question.lower() for keyword in pyodide_keywords)

    logger.info(f"Pyodide classification: needs_pyodide={needs_pyodide} for question: {user_question[:50]}...")

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

    # Extract schema (first row) to show LLM the structure without full data
    try:
        data_list = json.loads(sql_result)
        if data_list and len(data_list) > 0:
            # Pass only the first row as sample to keep prompt light and data-agnostic
            data_sample = json.dumps([data_list[0]])
            
            # Convert to CSV for efficient injection
            output = io.StringIO()
            if isinstance(data_list[0], dict):
                keys = data_list[0].keys()
                writer = csv.DictWriter(output, fieldnames=keys)
                writer.writeheader()
                # Handle None values as empty strings
                for row in data_list:
                    clean_row = {k: (v if v is not None else "") for k, v in row.items()}
                    writer.writerow(clean_row)
            csv_data = output.getvalue()
        else:
            data_sample = "[]"
            csv_data = ""
    except json.JSONDecodeError:
        return {}

    # Get prompt from prompts module (passing sample only)
    pyodide_prompt = get_pyodide_analysis_prompt(user_question, data_sample)

    response = llm_sql.invoke(pyodide_prompt)  # Temperature: 0.1
    generated_code = response.content.replace("```python", "").replace("```", "").strip()

    # Inject the CSV data into the code dynamically
    final_code = f"""import pandas as pd
import io

# Injected data (CSV format)
csv_data = {repr(csv_data)}

# Analysis Code
{generated_code}"""
    
    tool_message = ToolMessage(
        content=final_code,
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

    # Get prompt from prompts module
    needs_pyodide = state.get('needs_pyodide', False)
    response_prompt = get_response_generation_prompt(question, result, needs_pyodide)

    response = llm_response.invoke(response_prompt)  # Temperature: 0.7 (natural & varied)
    raw_content = response.content.strip()

    # Try XML parsing first (new structured format)
    import re
    answer_match = re.search(r'<answer>(.*?)</answer>', raw_content, re.DOTALL | re.IGNORECASE)
    insight_match = re.search(r'<insight>(.*?)</insight>', raw_content, re.DOTALL | re.IGNORECASE)

    if answer_match:
        # Extract structured response
        answer_text = answer_match.group(1).strip()
        insight_text = insight_match.group(1).strip() if insight_match else ""

        # Combine answer and insight
        if insight_text:
            final_response = f"{answer_text}\n\n{insight_text}"
        else:
            final_response = answer_text

        logger.info("Response generated successfully (XML format)")
        # Create new message with parsed content
        from langchain_core.messages import AIMessage
        return {"messages": [AIMessage(content=final_response)]}
    else:
        # Fallback to legacy format (use response as-is)
        logger.info("Response generated successfully (legacy format)")
        return {"messages": [response]}