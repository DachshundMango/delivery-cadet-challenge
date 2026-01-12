"""
Tests for agent configuration settings.

These tests validate that LLM instances and configuration constants
are properly initialised with correct values.
"""

import pytest
from src.agent.config import (
    llm_intent,
    llm_sql,
    llm_vis,
    llm_response,
    llm,
    MAX_SQL_RETRIES,
    VALID_CHART_TYPES,
    LLM_MODEL,
    CEREBRAS_BASE_URL
)


class TestLLMInstances:
    """Test suite for LLM instance configuration."""
    
    def test_all_llm_instances_exist(self):
        """Should have all required LLM instances initialised."""
        assert llm_intent is not None
        assert llm_sql is not None
        assert llm_vis is not None
        assert llm_response is not None
    
    def test_llm_intent_temperature_is_deterministic(self):
        """Intent LLM should use temperature 0.0 for deterministic classification."""
        assert llm_intent.temperature == 0.0
    
    def test_llm_sql_temperature_is_accurate(self):
        """SQL LLM should use temperature 0.1 for accurate query generation."""
        assert llm_sql.temperature == 0.1
    
    def test_llm_vis_temperature_is_deterministic(self):
        """Visualisation LLM should use temperature 0.0 for strict decisions."""
        assert llm_vis.temperature == 0.0
    
    def test_llm_response_temperature_is_natural(self):
        """Response LLM should use temperature 0.7 for natural language."""
        assert llm_response.temperature == 0.7
    
    def test_default_llm_is_sql(self):
        """Default llm should be the SQL generation instance."""
        assert llm == llm_sql
    
    def test_all_llms_use_same_model(self):
        """All LLM instances should use the same base model."""
        assert llm_intent.model_name == llm_sql.model_name
        assert llm_sql.model_name == llm_vis.model_name
        assert llm_vis.model_name == llm_response.model_name
    
    def test_all_llms_use_cerebras_base_url(self):
        """All LLM instances should use Cerebras API endpoint."""
        expected_url = "https://api.cerebras.ai/v1"
        assert CEREBRAS_BASE_URL == expected_url


class TestConfigurationConstants:
    """Test suite for workflow configuration constants."""
    
    def test_max_sql_retries_value(self):
        """MAX_SQL_RETRIES should be set to 3."""
        assert MAX_SQL_RETRIES == 3
    
    def test_valid_chart_types_contains_bar(self):
        """Valid chart types should include 'bar'."""
        assert 'bar' in VALID_CHART_TYPES
    
    def test_valid_chart_types_contains_line(self):
        """Valid chart types should include 'line'."""
        assert 'line' in VALID_CHART_TYPES
    
    def test_valid_chart_types_contains_pie(self):
        """Valid chart types should include 'pie'."""
        assert 'pie' in VALID_CHART_TYPES

    def test_valid_chart_types_contains_scatter(self):
        """Valid chart types should include 'scatter'."""
        assert 'scatter' in VALID_CHART_TYPES

    def test_valid_chart_types_contains_area(self):
        """Valid chart types should include 'area'."""
        assert 'area' in VALID_CHART_TYPES

    def test_valid_chart_types_count(self):
        """Should have exactly 5 valid chart types."""
        assert len(VALID_CHART_TYPES) == 5
    
    def test_valid_chart_types_is_set(self):
        """VALID_CHART_TYPES should be a set for efficient lookup."""
        assert isinstance(VALID_CHART_TYPES, set)
    
    def test_invalid_chart_types_not_included(self):
        """Invalid chart types should not be in VALID_CHART_TYPES."""
        assert 'histogram' not in VALID_CHART_TYPES
        assert 'bubble' not in VALID_CHART_TYPES
        assert 'heatmap' not in VALID_CHART_TYPES
    
    def test_llm_model_is_llama(self):
        """Should use llama-3.3-70b model by default."""
        assert 'llama' in LLM_MODEL.lower()
