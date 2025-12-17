from langgraph.graph import END, START, StateGraph
from state import SQLAgentState
from nodes import read_question, generate_SQL, execute_SQL, generate_response

workflow = StateGraph(SQLAgentState)

workflow.add_node("read_question", read_question)
workflow.add_node("generate_SQL", generate_SQL)
workflow.add_node("execute_SQL", execute_SQL)
workflow.add_node("generate_response", generate_response)

def check_query_validation(state: SQLAgentState) -> str:
    result = state['query_result']
    return "retry" if "Error" in result else "success"

workflow.add_edge(START, "read_question")
workflow.add_edge("read_question", "generate_SQL")
workflow.add_edge("generate_SQL", "execute_SQL")

workflow.add_conditional_edges(
    "execute_SQL", 
    check_query_validation, 
    {"retry":"generate_SQL", "success": "generate_response"}
)

workflow.add_edge("generate_response", END)


app = workflow.compile()