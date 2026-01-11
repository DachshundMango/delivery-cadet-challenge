from langgraph.graph import START, StateGraph, END
from src.agent.state import SQLAgentState
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
from src.agent.routing import RouteDecider
from src.agent.config import MAX_SQL_RETRIES


# Defined state is put into the StateGraph -> workflow is a StateGraph object
workflow = StateGraph(SQLAgentState)


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
    RouteDecider.decide_intent_route,
    {"sql": "pyodide_request_classification", "general": "generate_general_response"}
)

workflow.add_conditional_edges(
    "pyodide_request_classification",
    RouteDecider.decide_pyodide_route,
    {"pyodide": "generate_SQL", "skip": "generate_SQL"}
)

workflow.add_edge("generate_SQL", "execute_SQL")

workflow.add_conditional_edges(
    "execute_SQL",
    lambda state: RouteDecider.decide_sql_retry_route(state, MAX_SQL_RETRIES),
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
    RouteDecider.decide_pyodide_route,
    {"pyodide": "generate_pyodide_analysis", "skip": "generate_response"}
)

workflow.add_edge("generate_pyodide_analysis", "generate_response")
workflow.add_edge("generate_response", END)
workflow.add_edge("generate_general_response", END)

app = workflow.compile()