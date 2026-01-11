"""
Agent Configuration

This module contains LLM instances and configuration constants for the agent workflow.
Separating configuration makes it easier to:
- Switch between different LLM providers
- Adjust temperature settings per task
- Manage environment-specific settings

LLM Instances:
- llm_intent: Temperature 0.0 (deterministic intent classification)
- llm_sql: Temperature 0.1 (accurate SQL generation)
- llm_vis: Temperature 0.0 (strict visualization decisions)
- llm_response: Temperature 0.7 (natural language responses)
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

# LLM Configuration
LLM_MODEL = os.getenv('LLM_MODEL', 'llama-3.3-70b')
CEREBRAS_API_KEY = os.getenv('CEREBRAS_API_KEY')
CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"

# Task-specific LLMs with optimized temperature settings (using Cerebras via OpenAI-compatible API)
llm_intent = ChatOpenAI(
    model=LLM_MODEL,
    temperature=0.0,
    api_key=CEREBRAS_API_KEY,
    base_url=CEREBRAS_BASE_URL
)  # Intent classification: deterministic

llm_sql = ChatOpenAI(
    model=LLM_MODEL,
    temperature=0.1,
    api_key=CEREBRAS_API_KEY,
    base_url=CEREBRAS_BASE_URL
)  # SQL generation: accurate & safe

llm_vis = ChatOpenAI(
    model=LLM_MODEL,
    temperature=0.0,
    api_key=CEREBRAS_API_KEY,
    base_url=CEREBRAS_BASE_URL
)  # Visualization: deterministic (strict keyword detection)

llm_response = ChatOpenAI(
    model=LLM_MODEL,
    temperature=0.7,
    api_key=CEREBRAS_API_KEY,
    base_url=CEREBRAS_BASE_URL
)  # Response: natural & varied

# Default LLM (for backward compatibility)
llm = llm_sql

# Workflow configuration constants
MAX_RETRY_COUNT = 3  # Used internally by nodes (deprecated name, use MAX_SQL_RETRIES)
MAX_SQL_RETRIES = 3  # Used by routing logic
VALID_CHART_TYPES = {'bar', 'line', 'pie'}
