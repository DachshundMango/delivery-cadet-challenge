"""
Routing Decision Logic for LangGraph Workflow

This module contains routing decision functions that were extracted from graph.py
to make them testable, maintainable, and reusable.

The RouteDecider class provides static methods for conditional edge routing in the
LangGraph state machine.

Routing Functions:
- decide_intent_route: Route between SQL and general conversation
- decide_sql_retry_route: Handle SQL retry logic with Pyodide fallback
- decide_pyodide_route: Route based on Pyodide analysis requirement
"""

from src.agent.state import SQLAgentState, is_error_result
from src.core.logger import setup_logger

logger = setup_logger('cadet.routing')


class RouteDecider:
    """
    Centralized routing decisions for the agent workflow.
    
    All methods are static since they don't require instance state.
    This makes them easy to test and use directly in graph.py.
    """
    
    @staticmethod
    def decide_intent_route(state: SQLAgentState) -> str:
        """
        Route based on intent classification.
        
        Args:
            state: Current workflow state with 'intent' key
            
        Returns:
            'sql': Question requires database query
            'general': Question is general conversation
        """
        return state['intent']
    
    @staticmethod
    def decide_sql_retry_route(state: SQLAgentState, max_retries: int = 3) -> str:
        """
        Route based on query result. Supports Pyodide fallback after max retries.
        
        This is the most complex routing logic, handling:
        - Successful queries
        - Failed queries with retry
        - Max retries exceeded with Pyodide fallback
        - Fallback also failed (give up)
        
        Args:
            state: Current workflow state with query_result and retry counters
            max_retries: Maximum number of SQL generation attempts (default: 3)
            
        Returns:
            'retry': Try SQL generation again with error feedback
            'success': Continue to visualization (or error response if all failed)
            'fallback': Enable Pyodide fallback mode (simple SQL + Python analysis)
        """
        result = state.get('query_result')
        
        if result is None:
            logger.warning("Query result is None, retrying")
            return "retry"
        
        if is_error_result(result):
            # Get retry count from dedicated counter (NOT messages - prevents token overflow)
            retry_count = state.get('sql_retry_count', 0) or 0
            
            if retry_count >= max_retries:
                # Check if Pyodide fallback has already been attempted
                fallback_attempted = state.get('pyodide_fallback_attempted', False)
                
                if not fallback_attempted:
                    # First time hitting max retries: try Pyodide fallback
                    logger.warning(f"Max SQL retries ({max_retries}) exceeded. Attempting Pyodide fallback.")
                    return "fallback"
                else:
                    # Pyodide fallback also failed: give up
                    logger.error(f"Pyodide fallback also failed. Routing to response with error.")
                    return "success"  # Route to response node with error message
            
            logger.warning(f"SQL error detected, retry {retry_count + 1}/{max_retries}")
            return "retry"
        
        logger.info("Query executed successfully")
        return "success"
    
    @staticmethod
    def decide_pyodide_route(state: SQLAgentState) -> str:
        """
        Route based on Pyodide analysis requirement.
        
        Args:
            state: Current workflow state with 'needs_pyodide' key
            
        Returns:
            'pyodide': Generate Pyodide analysis code
            'skip': Skip Pyodide analysis
        """
        return "pyodide" if state.get('needs_pyodide') else "skip"
