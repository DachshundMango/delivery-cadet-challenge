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
         - product (Text)  <-- ⭐ IMPORTANT: Use this for product names. There is NO 'productID'.
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
    """

    initial_prompt = f"""You are an expert data engineer.
    Convert user questions into valid PostgreSQL queries.
    
    Here is the ACTUAL schema of the database:
    {schema_info}
    
    Rules:
    1. Use ONLY the columns explicitly listed above. 
    2. **CRITICAL**: The product column is named 'product', NOT 'productID'.
    3. Return ONLY the SQL query string.
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