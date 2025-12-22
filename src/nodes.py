import os
from dotenv import load_dotenv
from state import SQLAgentState
from langchain.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langgraph.types import Command
from sqlalchemy import create_engine, text

load_dotenv()

llm = ChatGroq(model='llama-3.3-70b-versatile')

def read_question(state: SQLAgentState) -> dict:
    
    return {
        "messages": [HumanMessage(content=f"User question: {state['user_question']}")]
    }

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

    schema_info = """
    1. Table 'sales_transactions'
       - Primary Key: transactionID
       - Foreign Keys: 
         - customerID -> sales_customers(customerID)
         - franchiseID -> sales_franchises(franchiseID)
       - Columns: 
         - transactionID (Integer)
         - product (Text)  
         - quantity (Integer)
         - unitPrice (Integer)
         - totalPrice (Integer)
         - paymentMethod (Text)
         - dateTime (Text)
         - cardNumber (BigInt)

    2. Table 'sales_customers'
       - Primary Key: customerID
       - Columns: 
         - customerID (Integer)
         - first_name (Text), last_name (Text)
         - country (Text), continent (Text), city (Text), state (Text)
         - gender (Text)

    3. Table 'sales_franchises'
       - Primary Key: franchiseID
       - Foreign Keys:
         - supplierID -> sales_suppliers(supplierID)
       - Columns: 
         - franchiseID (Integer)
         - name (Text) <-- This is the Franchise Name
         - city (Text), country (Text)
         - size (Text)

    4. Table 'sales_suppliers'
       - Primary Key: supplierID
       - Columns: 
         - supplierID (Integer)
         - name (Text) <-- This is the Supplier Name
         - ingredient (Text)
         - continent (Text), city (Text)
         - approved (Text)

    5. Table 'media_customer_reviews'
       - Primary Key: new_id
       - Foreign Keys:
         - franchiseID -> sales_franchises(franchiseID)
       - Columns: 
         - new_id (Integer)
         - review (Text) <-- The full text content of the customer review
         - franchiseID (Integer)
         - review_date (Text)

    6. Table 'media_gold_reviews_chunked'
       - Primary Key: chunk_id
       - Foreign Keys:
         - franchiseID -> sales_franchises(franchiseID)
       - Columns: 
         - chunk_id (Text)
         - franchiseID (Integer)
         - review_date (Text)
         - chunked_text (Text) <-- Segmented or processed review text for analysis
         - review_uri (Text)
    """

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

    load_dotenv()

    DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@localhost:{5432}/{os.getenv('DB_NAME')}" 

    engine = create_engine(DB_URL)

    sql_query = state['sql_query']

    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            rows = result.fetchall()
            return {"query_result": str(rows)} 
    except Exception as e:
        return {"query_result": f"Error: {str(e)}"}

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
    Please answer the user's question using the SQL Result. 
    If the result is empty, say "No data found".
    """
    
    response = llm.invoke(response_prompt)
    
    return {"messages": [response]}