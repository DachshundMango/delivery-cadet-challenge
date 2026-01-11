"""
Prompt templates for the SQL Agent.

This module organises all LLM prompts by functional category.

Usage:
    from src.agent.prompts import get_intent_classification_prompt
    from src.agent.prompts.sql import get_sql_generation_prompt
"""

# Re-export commonly used prompts for convenience
from .intent import get_intent_classification_prompt, get_general_response_prompt
from .sql import get_sql_generation_prompt, get_simple_sql_for_pyodide_prompt
from .visualization import get_chart_title_prompt, get_visualization_prompt
from .analysis import get_pyodide_analysis_prompt
from .privacy import get_data_masking_prompt, get_pii_detection_prompt, get_response_generation_prompt

__all__ = [
    # Intent & General
    'get_intent_classification_prompt',
    'get_general_response_prompt',
    
    # SQL Generation
    'get_sql_generation_prompt',
    'get_simple_sql_for_pyodide_prompt',
    
    # Visualization
    'get_chart_title_prompt',
    'get_visualization_prompt',
    
    # Analysis
    'get_pyodide_analysis_prompt',
    
    # Privacy & Response
    'get_data_masking_prompt',
    'get_pii_detection_prompt',
    'get_response_generation_prompt',
]
