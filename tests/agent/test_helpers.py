"""
Tests for helper utility functions.

These tests validate caching, schema loading, and PII masking logic
that are used throughout the agent workflow.
"""

import pytest
import json
from unittest.mock import patch, mock_open, MagicMock
from src.agent.helpers import (
    get_cached_engine,
    load_schema_info,
    apply_pii_masking
)
from src.core.errors import SchemaLoadError


class TestGetCachedEngine:
    """Test suite for database engine caching."""
    
    @patch('src.agent.helpers.get_db_engine')
    def test_creates_engine_on_first_call(self, mock_get_db):
        """Should create engine on first call and cache it."""
        mock_engine = MagicMock()
        mock_get_db.return_value = mock_engine
        
        import src.agent.helpers as helpers
        helpers._DB_ENGINE = None
        
        engine = get_cached_engine()
        
        assert engine == mock_engine
        mock_get_db.assert_called_once()
    
    @patch('src.agent.helpers.get_db_engine')
    def test_uses_cached_engine_on_second_call(self, mock_get_db):
        """Should use cached engine on subsequent calls."""
        mock_engine = MagicMock()
        mock_get_db.return_value = mock_engine
        
        import src.agent.helpers as helpers
        helpers._DB_ENGINE = None
        
        engine1 = get_cached_engine()
        engine2 = get_cached_engine()
        
        assert engine1 == engine2
        assert mock_get_db.call_count == 1


class TestLoadSchemaInfo:
    """Test suite for schema loading and caching."""
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"llm_prompt": "test schema"}')
    @patch('os.path.exists', return_value=True)
    def test_loads_schema_successfully(self, mock_exists, mock_file):
        """Should load and cache schema from JSON file."""
        import src.agent.helpers as helpers
        helpers._SCHEMA_CACHE = None
        
        result = load_schema_info()
        
        assert result == "test schema"
        mock_file.assert_called_once()
    
    @patch('os.path.exists', return_value=False)
    def test_raises_error_when_schema_file_missing(self, mock_exists):
        """Should raise SchemaLoadError when file doesn't exist."""
        import src.agent.helpers as helpers
        helpers._SCHEMA_CACHE = None
        
        with pytest.raises(SchemaLoadError) as exc_info:
            load_schema_info()
        
        assert "not found" in str(exc_info.value)
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"llm_prompt": ""}')
    @patch('os.path.exists', return_value=True)
    def test_raises_error_when_prompt_empty(self, mock_exists, mock_file):
        """Should raise SchemaLoadError when llm_prompt is empty."""
        import src.agent.helpers as helpers
        helpers._SCHEMA_CACHE = None
        
        with pytest.raises(SchemaLoadError) as exc_info:
            load_schema_info()
        
        assert "Empty llm_prompt" in str(exc_info.value)
    
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    @patch('os.path.exists', return_value=True)
    def test_raises_error_on_invalid_json(self, mock_exists, mock_file):
        """Should raise SchemaLoadError on invalid JSON."""
        import src.agent.helpers as helpers
        helpers._SCHEMA_CACHE = None
        
        with pytest.raises(SchemaLoadError) as exc_info:
            load_schema_info()
        
        assert "Invalid JSON" in str(exc_info.value)
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"llm_prompt": "cached schema"}')
    @patch('os.path.exists', return_value=True)
    def test_uses_cached_schema_on_second_call(self, mock_exists, mock_file):
        """Should return cached schema without re-reading file."""
        import src.agent.helpers as helpers
        helpers._SCHEMA_CACHE = None
        
        result1 = load_schema_info()
        result2 = load_schema_info()
        
        assert result1 == result2 == "cached schema"
        assert mock_file.call_count == 1


class TestApplyPIIMasking:
    """Test suite for PII masking functionality."""
    
    @patch('builtins.open', new_callable=mock_open, 
           read_data='{"pii_columns": {"users": ["firstName", "lastName"]}}')
    def test_masks_pii_columns_correctly(self, mock_file):
        """Should mask PII columns with Person #N format."""
        rows = [
            {"firstName": "John", "lastName": "Doe", "revenue": 1000},
            {"firstName": "Jane", "lastName": "Smith", "revenue": 2000},
        ]
        
        masked = apply_pii_masking(rows)
        
        assert masked[0]["firstName"] == "Person #1"
        assert "lastName" not in masked[0]
        assert masked[0]["revenue"] == 1000
        
        assert masked[1]["firstName"] == "Person #2"
        assert masked[1]["revenue"] == 2000
    
    def test_returns_empty_list_for_empty_input(self):
        """Should return empty list when input is empty."""
        assert apply_pii_masking([]) == []
    
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_returns_original_when_no_pii_config(self, mock_file):
        """Should return original rows when PII config is missing."""
        rows = [{"name": "John", "revenue": 1000}]
        result = apply_pii_masking(rows)
        
        assert result == rows
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"pii_columns": {}}')
    def test_returns_original_when_pii_columns_empty(self, mock_file):
        """Should return original rows when no PII columns configured."""
        rows = [{"name": "John", "revenue": 1000}]
        result = apply_pii_masking(rows)
        
        assert result == rows
    
    @patch('builtins.open', new_callable=mock_open,
           read_data='{"pii_columns": {"users": ["name"]}}')
    def test_preserves_non_pii_columns(self, mock_file):
        """Should preserve all non-PII columns unchanged."""
        rows = [
            {"name": "Alice", "email": "test@example.com", "revenue": 1500, "city": "Sydney"}
        ]
        
        masked = apply_pii_masking(rows)
        
        assert masked[0]["name"] == "Person #1"
        assert masked[0]["email"] == "test@example.com"
        assert masked[0]["revenue"] == 1500
        assert masked[0]["city"] == "Sydney"
    
    @patch('builtins.open', new_callable=mock_open,
           read_data='{"pii_columns": {"users": ["firstName", "lastName", "email"]}}')
    def test_only_keeps_first_pii_column(self, mock_file):
        """Should only keep first PII column and remove others."""
        rows = [
            {"firstName": "Bob", "lastName": "Wilson", "email": "bob@test.com", "revenue": 2000}
        ]
        
        masked = apply_pii_masking(rows)
        
        assert masked[0]["firstName"] == "Person #1"
        assert "lastName" not in masked[0]
        assert "email" not in masked[0]
        assert masked[0]["revenue"] == 2000
