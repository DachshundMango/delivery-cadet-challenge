import os
import json
import re
from dotenv import load_dotenv
from src.state import SQLAgentState
from langchain.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langgraph.types import Command
from sqlalchemy import create_engine, text

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
            rows = result.fetchall()
            result_str = str(rows)

            # Apply PII masking to query results
            #masked_result = mask_pii_in_query_result(sql_query, result_str)

            return {"query_result": result_str} #후에 result_str -> masked_result 변경 필요
    except Exception as e:
        return {"query_result": f"Error: {str(e)}"}

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
    {{
    "visualise": "yes" or "no",
    "chart_type": "bar" or "line" or "pie" or "scatter"
    }}

    **Chart Type Guidelines:**
    - bar: Comparisons, rankings, top N items (e.g., "top 10 products", "sales by region")
    - line: Time series, trends over time (e.g., "monthly revenue", "daily orders")
    - pie: Proportions, percentages, composition (e.g., "market share", "distribution")
    - scatter: Correlations, relationships between two variables (e.g., "price vs sales")

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

    return {
        "plotly_data": plotly_data.to_dict()
    }

def create_plotly_chart(sql_result, chart_type):
    pass


def generate_response(state: SQLAgentState) -> dict:

    question = state['user_question']
    sql = state['sql_query']
    result = state['query_result']

    if "Error:" in result:
        return {"messages": [HumanMessage(content=f"An error ocurrs in query processing.\n{result}")]}

    response_prompt = f"""
    User asked: {question}
    SQL query used: {sql}
    SQL Result: {result}

    If the result is empty, say "No data found".
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