import ast
import os
import json
import re
from dotenv import load_dotenv
from src.state import SQLAgentState
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langgraph.types import Command
from sqlalchemy import create_engine, text
import plotly.express as px

load_dotenv()

#llm = ChatGroq(model='llama-3.3-70b-versatile')
llm = ChatGroq(model='llama-3.1-8b-instant')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, 'src')
SCHEMA_JSON_PATH = os.path.join(SRC_DIR, 'schema_info.json')

def get_db_engine():
    """Create database engine"""
    DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@localhost:5432/{os.getenv('DB_NAME')}"
    return create_engine(DB_URL)

def load_schema_info():
    """Load pre-generated schema info from schema_info.json"""
    if not os.path.exists(SCHEMA_JSON_PATH):
        raise FileNotFoundError(
            f"{SCHEMA_JSON_PATH} not found.\n"
            "Please run: python src/generate_schema.py"
        )

    with open(SCHEMA_JSON_PATH, 'r', encoding='utf-8') as f:
        schema_data = json.load(f)

    return schema_data.get('llm_prompt', '')

# def mask_pii_in_query_result(sql_query: str, result_str: str) -> str:
#     """
#     Always apply name pattern matching, regardless of column names.
#     Dataset-agnostic approach.
#     """
#     # 조건 체크 없이 항상 패턴 매칭 적용
#     masked_result = re.sub(r"'([A-Z][a-z]+)'", "'[NAME_REDACTED]'", result_str)
#     return masked_result

def read_question(state: SQLAgentState) -> dict:
    
    messages = state.get("messages", [])

    if messages:
        last_message = messages[-1]
        
        if isinstance(last_message, dict):
            content = last_message.get('content')
        
        else:
            content = last_message.content
        
        return {"user_question": content}

    return {}

def intent_classification(state: SQLAgentState) -> dict:
    
    user_question = state['user_question']

    intent_prompt = """Analyze the following input and classify it into one of two categories:

    sql - If the user wants to fetch, count, analyze, or look up specific data from a database.
    general - If the input is a greeting, a clarifying question, a coding request, or casual chat.

    **Rules:**
    - Even if the user does not use the word "SQL", if the intent requires data retrieval (e.g., "Who bought the most items?"), classify as [SQL].
    - If the request is ambiguous but leans towards asking for information likely stored in a table, classify as [SQL].

    **Output:**
    Return ONLY the class label `sql` or `general`. Do not provide explanations."""
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "{intent_prompt}"),
        ("human", "{user_question}")
    ])

    final_prompt_value = prompt_template.invoke({
        "intent_prompt": intent_prompt,
        "user_question": user_question
    })

    response = llm.invoke(final_prompt_value)
    
    intent = response.content
    intent = intent.replace("'", "").strip()
    
    return {
        "intent": intent
    }

def generate_general_response(state: SQLAgentState) -> dict:
    
    user_question = state['user_question']

    general_prompt = f"""You are a helpful data analyst assistant.
    User said: "{user_question}"
    
    Respond politely. If they ask about your capability, say you can help analyze sales data.
    """

    response = llm.invoke(general_prompt)

    return {
        "messages": [response]
    }

def generate_SQL(state: SQLAgentState) -> dict:

    user_question = state['user_question']

    # Load pre-generated schema info
    schema_info = load_schema_info()

    initial_prompt = f"""You are an expert data engineer.
    Convert user questions into valid PostgreSQL queries.

    Here is the ACTUAL schema of the database:
    {schema_info}

    Rules:
    1. Use ONLY the column names explicitly listed above.
    2. Return ONLY the SQL query string.
    3. If a table or column name contains mixed case letters (camelCase), you MUST enclose it in double quotes.
    4. Example: Do not write `SELECT paymentMethod ...`. Write `SELECT "paymentMethod" ...`.
    5. When the question asks for "total", "sum", or aggregated values, use appropriate aggregate functions (SUM, COUNT, AVG) with GROUP BY.
    6. Example: "total quantity sold by product" requires `SELECT product, SUM(quantity) as total_quantity FROM table GROUP BY product`.
    7. When ordering by an aggregated column, use the alias or column position in ORDER BY.
    8. Always think about whether the question requires aggregation before writing the query.
    """
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "{initial_prompt}"),
        ("human", "{user_question}")
    ])

    final_prompt_value = prompt_template.invoke({
        "initial_prompt": initial_prompt,
        "user_question": user_question
    })

    response = llm.invoke(final_prompt_value)
    
    sql_query = response.content
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
    return {
        "sql_query": sql_query
    }

def execute_SQL(state: SQLAgentState) -> dict:

    engine = get_db_engine()
    sql_query = state['sql_query']

    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            rows = [dict(row._mapping) for row in result.fetchall()]
            result_str = json.dumps(rows, default=str, ensure_ascii=False)
            # Apply PII masking to query results
            #masked_result = mask_pii_in_query_result(sql_query, result_str)
            return {
                "query_result": result_str
            } #후에 result_str -> masked_result 변경 필요
    
    except Exception as e:
        return {
            "query_result": f"Error: {str(e)}"
        }

def visualisation_request_classification(state: SQLAgentState) -> dict:
    
    user_question = state['user_question']
    sql_result = state['query_result']

    if state['intent'] == 'general' or \
        ("Error:" in sql_result) or \
        (sql_result in [None, '[]', '']):
        return {
        "plotly_data": None
        }
    
    visualisation_request_prompt = f"""
    
    You are a data visualisation expert. Analyze the user's question and SQL result to determine if visualisation is needed.

    **Output Format (JSON only):**
    {{{{
    "visualise": "yes" or "no",
    "chart_type": "bar" or "line" or "pie"
    }}}}

    **Chart Type Guidelines:**
    - bar: Comparisons, rankings, top N items (e.g., "top 10 products", "sales by region")
    - line: Time series, trends over time (e.g., "monthly revenue", "daily orders")
    - pie: Proportions, percentages, composition (e.g., "market share", "distribution")

    **Decision Rules:**
    - If the question explicitly mentions "chart", "plot", "visualize", "visualise", "graph", or "show" → visualise: yes
    - However, if the question explicitly denies or prohibits visualisation → visualise: no
    - If SQL result has only 1 row or is a simple count → visualise: no
    - If the question asks for comparisons, trends, or distributions → visualise: yes
    - If the question only needs a single number or text answer → visualise: no
    - If SQL result shows multiple data points (3+ rows) and involves aggregation → visualise: yes
    
    **IMPORTANT:**
    - Return ONLY valid JSON
    - No explanations, no additional text
    - If unsure about chart_type, default to "bar"

    The SQL query returned the following result:
    {sql_result}
    """
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", visualisation_request_prompt),
        ("human", "{user_question}")
    ])

    final_prompt_value = prompt_template.invoke({
        "user_question": user_question
    })

    response = llm.invoke(final_prompt_value)
    
    try:
        response_json = json.loads(response.content)
    except Exception as e:
        return {
        "plotly_data": None
        }
    
    if response_json['visualise'] == 'no':
        return {
        "plotly_data": None
        }

    chart_type = response_json['chart_type']

    plotly_data = create_plotly_chart(
        sql_result, 
        chart_type
    )

    if plotly_data is None:
        return {
        "plotly_data": None
        }
    
    tool_message = ToolMessage(
        content=plotly_data,
        tool_call_id="call_visulisaion_1",
        name="create_plotly_chart"
    )

    return {
        "messages": [tool_message],
        "plotly_data": plotly_data
        
    }

def create_plotly_chart(sql_result, chart_type):
    
    try:
        sql_list = json.loads(sql_result)
    except Exception:
        try:
            sql_list = ast.literal_eval(sql_result)
        except Exception as e:
            print(f"Error: {e}")
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

    pyodide_keywords = ['correlation', 'statistics', 'analyze', 'describe', 'summary', 'std', 'mean', 'median']

    needs_pyodide = any(keyword in user_question.lower() for keyword in pyodide_keywords)

    return {
        "needs_pyodide": needs_pyodide
    }


def generate_pyodide_analysis(state: SQLAgentState) -> dict:

    user_question = state['user_question']
    sql_result = state['query_result']

    if "Error:" in sql_result or sql_result in [None, "[]", ""]:
        return {}

    pyodide_prompt = f"""
    You are a Python Data Analyst. 
    The user asked: "{user_question}"
    
    I have retrieved data from the database in JSON format:
    {sql_result}
    
    Write a Python script to analyze this data using 'pandas'.
    
    **Requirements:**
    1. Create a DataFrame directly from the JSON data provided above.
    2. Example: 
       import pandas as pd
       data = {sql_result} 
       df = pd.DataFrame(data)
    3. Perform the analysis requested (e.g., correlation, description, math).
    4. PRINT the final result using `print()`. The user will see the standard output.
    5. Return ONLY the Python code. No markdown formatting.
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

    question = state['user_question']
    sql = state['sql_query']
    result = state['query_result']

    if "Error:" in result:
        return {"messages": [HumanMessage(content=f"An error ocurrs in query processing.\n{result}")]}

    response_prompt = f"""
    You are a helpful data assistant. Answer the user's question based on the SQL result provided.

    User asked: {question}
    SQL Result: {result}

    **Instructions:**
    - Provide a clear, concise answer to the user's question
    - Present the data in a natural, easy-to-read format
    - DO NOT explain the SQL query or show the SQL code
    - DO NOT provide Python code or implementation details
    - DO NOT give unnecessary technical explanations
    - If the result is empty, say "No data found"
    - Keep your response brief and focused on answering the question

    Answer the question directly using the SQL result.
    """


    # **CRITICAL PRIVACY REQUIREMENT:** -> To be included in response_prompt above 
    # - DO NOT include any personal names (first names, last names) in your response
    # - If the data contains [NAME_REDACTED], acknowledge that personal information has been protected for privacy
    # - Focus on aggregate statistics, counts, and trends rather than individual identities
    # Please answer the user's question using the SQL Result while respecting privacy.
    
    
    response = llm.invoke(response_prompt)

    # Additional safety check: mask any names that might have slipped through (Defense in Depth)
    # final_response = re.sub(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', '[NAME_REDACTED]', response.content)
    # response.content = final_response 

    return {"messages": [response]}