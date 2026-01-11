"""
Tests for routing logic in the LangGraph workflow.

These tests validate the routing decisions made by RouteDecider class,
which determines the flow through the agent state machine.
"""

import pytest
from src.agent.routing import RouteDecider
from src.agent.state import SQLAgentState


class TestDecideIntentRoute:
    """Test suite for intent classification routing."""
    
    def test_sql_intent_returns_sql(self):
        """Should return 'sql' when intent is sql."""
        state = {"intent": "sql"}
        assert RouteDecider.decide_intent_route(state) == "sql"
    
    def test_general_intent_returns_general(self):
        """Should return 'general' when intent is general."""
        state = {"intent": "general"}
        assert RouteDecider.decide_intent_route(state) == "general"


class TestDecideSQLRetryRoute:
    """Test suite for SQL retry routing logic with Pyodide fallback."""
    
    def test_success_when_no_error(self):
        """Should route to success when query succeeds without errors."""
        state = {
            "query_result": '[{"count": 5}]',
            "sql_retry_count": 0
        }
        assert RouteDecider.decide_sql_retry_route(state) == "success"
    
    def test_retry_when_result_is_none(self):
        """Should retry when query_result is None."""
        state = {
            "query_result": None,
            "sql_retry_count": 0
        }
        assert RouteDecider.decide_sql_retry_route(state) == "retry"
    
    def test_retry_on_first_error(self):
        """Should retry on first SQL error."""
        state = {
            "query_result": "Error: column not found",
            "sql_retry_count": 1
        }
        assert RouteDecider.decide_sql_retry_route(state) == "retry"
    
    def test_retry_on_second_error(self):
        """Should retry on second SQL error."""
        state = {
            "query_result": "Error: syntax error",
            "sql_retry_count": 2
        }
        assert RouteDecider.decide_sql_retry_route(state) == "retry"
    
    def test_fallback_after_max_retries(self):
        """Should route to fallback after reaching max retries."""
        state = {
            "query_result": "Error: table not found",
            "sql_retry_count": 3,
            "pyodide_fallback_attempted": False
        }
        assert RouteDecider.decide_sql_retry_route(state) == "fallback"
    
    def test_success_when_fallback_also_failed(self):
        """Should route to success (with error) when fallback also fails."""
        state = {
            "query_result": "Error: still failing",
            "sql_retry_count": 3,
            "pyodide_fallback_attempted": True
        }
        assert RouteDecider.decide_sql_retry_route(state) == "success"
    
    def test_custom_max_retries_parameter(self):
        """Should respect custom max_retries parameter."""
        state = {
            "query_result": "Error: test error",
            "sql_retry_count": 2,
            "pyodide_fallback_attempted": False
        }
        result = RouteDecider.decide_sql_retry_route(state, max_retries=2)
        assert result == "fallback"
    
    def test_handles_none_retry_count(self):
        """Should handle None retry count gracefully."""
        state = {
            "query_result": "Error: test",
            "sql_retry_count": None
        }
        assert RouteDecider.decide_sql_retry_route(state) == "retry"
    
    def test_handles_missing_retry_count(self):
        """Should handle missing retry count (defaults to 0)."""
        state = {
            "query_result": "Error: test"
        }
        assert RouteDecider.decide_sql_retry_route(state) == "retry"
    
    def test_success_with_empty_result(self):
        """Should route to success even with empty result array."""
        state = {
            "query_result": "[]",
            "sql_retry_count": 0
        }
        assert RouteDecider.decide_sql_retry_route(state) == "success"
    
    def test_error_detection_is_case_sensitive(self):
        """Should detect errors starting with 'Error:' prefix."""
        state = {
            "query_result": "Error: column does not exist",
            "sql_retry_count": 1
        }
        assert RouteDecider.decide_sql_retry_route(state) == "retry"


class TestDecidePyodideRoute:
    """Test suite for Pyodide analysis routing."""
    
    def test_pyodide_when_needed(self):
        """Should route to pyodide when needs_pyodide is True."""
        state = {"needs_pyodide": True}
        assert RouteDecider.decide_pyodide_route(state) == "pyodide"
    
    def test_skip_when_not_needed(self):
        """Should skip pyodide when needs_pyodide is False."""
        state = {"needs_pyodide": False}
        assert RouteDecider.decide_pyodide_route(state) == "skip"
    
    def test_skip_when_needs_pyodide_missing(self):
        """Should skip pyodide when needs_pyodide key is missing."""
        state = {}
        assert RouteDecider.decide_pyodide_route(state) == "skip"
    
    def test_skip_when_needs_pyodide_is_none(self):
        """Should skip pyodide when needs_pyodide is None."""
        state = {"needs_pyodide": None}
        assert RouteDecider.decide_pyodide_route(state) == "skip"
