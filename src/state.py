from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage
import operator


class SQLAgentState(TypedDict):
	"""
	State schema for SQL Agent workflow.

	This TypedDict defines the complete state that flows through all nodes
	in the LangGraph workflow. Each key has a fixed type and purpose.

	Attributes:
		user_question: Original user input extracted from messages
		intent: Classification result ('sql' for data queries, 'general' for conversation)
		sql_query: Generated PostgreSQL query string
		query_result: JSON string of query results or error message starting with "Error:"
		plotly_data: JSON string containing Plotly chart specification (not dict!)
		needs_pyodide: Whether Pyodide (Python) analysis is required
		messages: List of messages accumulated via operator.add
			- HumanMessage: User input
			- AIMessage: LLM responses
			- SystemMessage: System prompts
			- ToolMessage: Tool call results (charts, Python code)

	Notes:
		- Messages are accumulated (not replaced) due to operator.add annotation
		- query_result format: JSON array string like '[{"col": "val"}]' or "Error: <message>"
		- plotly_data format: JSON string with 'type', 'data', 'layout' keys
	"""

	user_question: Optional[str]
	intent: Optional[str]  # 'sql' | 'general'

	sql_query: Optional[str]
	query_result: Optional[str]

	plotly_data: Optional[str]  # JSON string, NOT dict!
	needs_pyodide: Optional[bool]

	messages: Annotated[List[BaseMessage], operator.add]


def is_error_result(query_result: Optional[str]) -> bool:
	"""
	Check if query result contains an error.

	Args:
		query_result: Query result string from execute_SQL node

	Returns:
		True if result contains an error, False otherwise

	Example:
		>>> is_error_result("Error: column not found")
		True
		>>> is_error_result('[{"count": 5}]')
		False
	"""
	return query_result is not None and query_result.startswith("Error:")
