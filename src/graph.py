from langgraph.graph import START, StateGraph, END
from src.state import SQLAgentState
from src.nodes import read_question, intent_classification, generate_SQL, execute_SQL, generate_general_response, generate_response, visualisation_request_classification

workflow = StateGraph(SQLAgentState)

def check_intent_classification(state: SQLAgentState) -> str:
    return state['intent']

def check_query_validation(state: SQLAgentState) -> str:
    result = state['query_result']
    if result is None:
        return "retry"
    return "retry" if "Error" in result else "success"

workflow.add_node("read_question", read_question)
workflow.add_node("intent_classification", intent_classification)
workflow.add_node("generate_SQL", generate_SQL)
workflow.add_node("execute_SQL", execute_SQL)
workflow.add_node("visualisation_request_classification", visualisation_request_classification)
workflow.add_node("generate_response", generate_response)
workflow.add_node("generate_general_response", generate_general_response)

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
workflow.add_edge("visualisation_request_classification", "generate_response")

workflow.add_edge("generate_response", END)
workflow.add_edge("generate_general_response", END)

app = workflow.compile()