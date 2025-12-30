import sys
import os

# Add project root to path for consistent imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import START, StateGraph, END
from src.state import SQLAgentState, is_error_result
from src.nodes import read_question, intent_classification, generate_SQL, execute_SQL, generate_general_response, generate_response, visualisation_request_classification, generate_pyodide_analysis, pyodide_request_classification
from src.logger import setup_logger

logger = setup_logger('cadet.graph')
MAX_SQL_RETRIES = 3

workflow = StateGraph(SQLAgentState)

def check_intent_classification(state: SQLAgentState) -> str:
    return state['intent']

def check_query_validation(state: SQLAgentState) -> str:
    """Route based on query result. Prevents infinite loops with retry limit."""
    result = state.get('query_result')

    if result is None:
        logger.warning("Query result is None, retrying")
        return "retry"

    if is_error_result(result):
        # Count previous errors in messages
        messages = state.get('messages', [])
        error_count = sum(1 for msg in messages
                         if 'Error:' in str(getattr(msg, 'content', '')))

        if error_count >= MAX_SQL_RETRIES:
            logger.error(f"Max SQL retries ({MAX_SQL_RETRIES}) exceeded, routing to response")
            return "success"  # Route to response node with error message

        logger.warning(f"SQL error detected, retry {error_count + 1}/{MAX_SQL_RETRIES}")
        return "retry"

    logger.info("Query executed successfully")
    return "success"

def check_pyodide_classification(state: SQLAgentState) -> str:
    return "pyodide" if state['needs_pyodide'] else "skip"
    
workflow.add_node("read_question", read_question)
workflow.add_node("intent_classification", intent_classification)
workflow.add_node("generate_SQL", generate_SQL)
workflow.add_node("execute_SQL", execute_SQL)
workflow.add_node("visualisation_request_classification", visualisation_request_classification)
workflow.add_node("pyodide_request_classification", pyodide_request_classification)
workflow.add_node("generate_response", generate_response)
workflow.add_node("generate_general_response", generate_general_response)
workflow.add_node("generate_pyodide_analysis", generate_pyodide_analysis)
workflow.add_edge(START, "read_question")
workflow.add_edge("read_question", "intent_classification")

workflow.add_conditional_edges(
    "intent_classification", 
    check_intent_classification,
    {"sql":"generate_SQL", "general": "generate_general_response"}
)

workflow.add_edge("generate_SQL", "execute_SQL")

workflow.add_conditional_edges(
    "execute_SQL",
    check_query_validation,
    {"retry":"generate_SQL", "success": "visualisation_request_classification"}
)

workflow.add_edge("visualisation_request_classification", "pyodide_request_classification")

workflow.add_conditional_edges(
    "pyodide_request_classification",
    check_pyodide_classification,
    {"pyodide":"generate_pyodide_analysis", "skip":"generate_response"}
)

workflow.add_edge("generate_pyodide_analysis", "generate_response")
workflow.add_edge("generate_response", END)
workflow.add_edge("generate_general_response", END)

app = workflow.compile()