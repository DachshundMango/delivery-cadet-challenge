from langgraph.graph import START, StateGraph, END
from src.agent.state import SQLAgentState, is_error_result
from src.agent.nodes import (
    read_question,
    intent_classification,
    generate_SQL,
    execute_SQL,
    generate_general_response,
    generate_response,
    visualisation_request_classification,
    generate_pyodide_analysis,
    pyodide_request_classification,
    enable_pyodide_fallback,
)
from src.core.logger import setup_logger

logger = setup_logger('cadet.graph')
MAX_SQL_RETRIES = 3


# Defined state is put into the StateGraph -> workflow is a StateGraph object
workflow = StateGraph(SQLAgentState)

def check_intent_classification(state: SQLAgentState) -> str:
    return state['intent']

def check_query_validation(state: SQLAgentState) -> str:
    """Route based on query result. Supports Pyodide fallback after max retries."""
    result = state.get('query_result')

    if result is None:
        logger.warning("Query result is None, retrying")
        return "retry"

    if is_error_result(result):
        # Get retry count from dedicated counter (NOT messages - prevents token overflow)
        retry_count = state.get('sql_retry_count', 0) or 0

        if retry_count >= MAX_SQL_RETRIES:
            # Check if Pyodide fallback has already been attempted
            fallback_attempted = state.get('pyodide_fallback_attempted', False)
            
            if not fallback_attempted:
                # First time hitting max retries: try Pyodide fallback
                logger.warning(f"Max SQL retries ({MAX_SQL_RETRIES}) exceeded. Attempting Pyodide fallback.")
                return "fallback"
            else:
                # Pyodide fallback also failed: give up
                logger.error(f"Pyodide fallback also failed. Routing to response with error.")
                return "success"  # Route to response node with error message

        logger.warning(f"SQL error detected, retry {retry_count + 1}/{MAX_SQL_RETRIES}")
        return "retry"

    logger.info("Query executed successfully")
    return "success"

def check_pyodide_classification(state: SQLAgentState) -> str:
    return "pyodide" if state['needs_pyodide'] else "skip"
    

# Add NODES to the workflow
workflow.add_node("read_question", read_question)
workflow.add_node("intent_classification", intent_classification)
workflow.add_node("generate_SQL", generate_SQL)
workflow.add_node("execute_SQL", execute_SQL)
workflow.add_node("visualisation_request_classification", visualisation_request_classification)
workflow.add_node("pyodide_request_classification", pyodide_request_classification)
workflow.add_node("generate_response", generate_response)
workflow.add_node("generate_general_response", generate_general_response)
workflow.add_node("generate_pyodide_analysis", generate_pyodide_analysis)
workflow.add_node("enable_pyodide_fallback", enable_pyodide_fallback)

# Add EDGES to the workflow
workflow.add_edge(START, "read_question")
workflow.add_edge("read_question", "intent_classification")

workflow.add_conditional_edges(
    "intent_classification",
    check_intent_classification,
    {"sql":"pyodide_request_classification", "general": "generate_general_response"}
)

workflow.add_conditional_edges(
    "pyodide_request_classification",
    check_pyodide_classification,
    {"pyodide":"generate_SQL", "skip":"generate_SQL"}
)

workflow.add_edge("generate_SQL", "execute_SQL")

workflow.add_conditional_edges(
    "execute_SQL",
    check_query_validation,
    {
        "retry": "generate_SQL",
        "success": "visualisation_request_classification",
        "fallback": "enable_pyodide_fallback"
    }
)

# Pyodide fallback: reset state and retry with simple SQL
workflow.add_edge("enable_pyodide_fallback", "generate_SQL")

workflow.add_conditional_edges(
    "visualisation_request_classification",
    check_pyodide_classification,
    {"pyodide":"generate_pyodide_analysis", "skip":"generate_response"}
)

workflow.add_edge("generate_pyodide_analysis", "generate_response")
workflow.add_edge("generate_response", END)
workflow.add_edge("generate_general_response", END)

app = workflow.compile()