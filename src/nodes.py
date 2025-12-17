import os
from dotenv import load_dotenv
from state import SQLAgentState
from langchain.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langgraph.types import Command
from sqlalchemy import create_engine, text

llm = ChatGroq(model='llama-3.1-8b-instant')

def read_question(state: SQLAgentState) -> dict:
    
    return {
        "messages": [HumanMessage(content=f"User question: {state['user_question']}")]
    }

def generate_SQL(state: SQLAgentState) -> dict:
    
    user_question = state['user_question']

    schema_info = """
    
    1. Table 'sales_transactions'
       - Primary Key: transactionID
       - Foreign Keys: customerID -> sales_customers(customerID), franchiseID -> sales_franchises(franchiseID)
       
    2. Table 'sales_customers'
       - Primary Key: customerID
       
    3. Table 'sales_franchises'
       - Primary Key: franchiseID
       - Foreign Keys: supplierID -> sales_suppliers(supplierID)
       
    4. Table 'sales_suppliers'
       - Primary Key: supplierID
    """

    initial_prompt = f"""You are an expert data engineer.
    Your goal is to convert user questions into valid SQL queries for a PostgreSQL database.
    Here is the schema of the database:
    {schema_info}
    Rules:
    1. Return ONLY the SQL query.
    2. Do not include markdown formatting (like ```sql).
    3. Do not add explanations. 
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

    return {
        "sql_query": response.content
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