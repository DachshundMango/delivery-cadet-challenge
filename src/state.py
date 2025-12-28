from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage
import operator

class SQLAgentState(TypedDict):

	"""
	- This class is inherited from TypedDict. 
	- Only declared keys below are available keys in the class.
	- Each key has its own fixed type for values.
	- Messages
		1) All elements in the list must be BaseMessage type. 
		2) Newly generated message is appended to the existing list, instead of overwriting.
		3) BaseMessage: The parent class of HumanMessage, AIMessage, SystemMessage, ToolMessage
	"""

	user_question: str | None
	intent: str | None

	sql_query: str | None
	query_result: str | None
    
	messages: Annotated[List[BaseMessage], operator.add]
