"""
Helper utilities for agent nodes.

This module contains reusable helper functions that were extracted from nodes.py
to keep node logic focused and more maintainable.

Functions:
- get_cached_engine(): Database connection pool management
- load_schema_info(): Schema loading with caching
- apply_pii_masking(): PII data masking for privacy protection
"""

import os
import json
from typing import Optional
from sqlalchemy import Engine
from src.core.db import get_db_engine
from src.core.logger import setup_logger
from src.core.errors import SchemaLoadError

logger = setup_logger('cadet.helpers')

# File paths (exported for use in nodes.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_DIR = os.path.join(BASE_DIR, 'src')
SCHEMA_JSON_PATH = os.path.join(SRC_DIR, 'config', 'schema_info.json')

# Module-level caches
_SCHEMA_CACHE: Optional[str] = None
_DB_ENGINE: Optional[Engine] = None


def get_cached_engine() -> Engine:
    """
    Get or create cached database engine.
    
    Uses a module-level global variable `_DB_ENGINE` to store the connection pool,
    preventing overhead from recreating engines on every request.
    
    Returns:
        sqlalchemy.Engine: Active database engine instance
    """
    global _DB_ENGINE
    if _DB_ENGINE is None:
        _DB_ENGINE = get_db_engine()
    return _DB_ENGINE


def load_schema_info() -> str:
    """
    Load pre-generated schema info from schema_info.json with caching.
    
    The schema information is critical for the LLM to generate valid SQL.
    It includes table names, column names, types, and foreign key relationships.
    
    Returns:
        str: LLM-ready schema description string
    
    Raises:
        SchemaLoadError: If schema file not found or invalid
    """
    global _SCHEMA_CACHE

    if _SCHEMA_CACHE is not None:
        return _SCHEMA_CACHE

    if not os.path.exists(SCHEMA_JSON_PATH):
        raise SchemaLoadError(
            f"{SCHEMA_JSON_PATH} not found.\n"
            "Please run: python src/generate_schema.py"
        )

    try:
        with open(SCHEMA_JSON_PATH, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)

        _SCHEMA_CACHE = schema_data.get('llm_prompt', '')

        if not _SCHEMA_CACHE:
            raise SchemaLoadError("Empty llm_prompt in schema_info.json")

        logger.info("Schema info loaded and cached")
        return _SCHEMA_CACHE

    except json.JSONDecodeError as e:
        raise SchemaLoadError(f"Invalid JSON in schema file: {e}")


def apply_pii_masking(rows: list[dict]) -> list[dict]:
    """
    Apply deterministic PII masking to SQL results (Python-only, no LLM).

    Loads PII column names from schema_info.json and masks matching columns
    with "Person #N" format. Removes duplicate name fields (e.g., firstName + lastName).

    Args:
        rows: SQL query results as list of dicts

    Returns:
        Masked rows with PII replaced
    """
    if not rows:
        return rows

    # Load PII columns from schema_info.json
    try:
        with open(SCHEMA_JSON_PATH, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)
        pii_columns_config = schema_data.get('pii_columns', {})
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        logger.debug("No PII configuration found, skipping masking")
        return rows

    # Flatten all PII columns into a single set (table-agnostic matching)
    pii_columns = set()
    for table_pii in pii_columns_config.values():
        pii_columns.update(table_pii)

    if not pii_columns:
        return rows

    logger.info(f"Masking PII columns: {pii_columns}")

    # Apply masking
    masked_rows = []
    person_counter = 1

    for row in rows:
        masked_row = {}
        first_pii_found = False

        for col_name, value in row.items():
            if col_name in pii_columns:
                if not first_pii_found:
                    masked_row[col_name] = f"Person #{person_counter}"
                    first_pii_found = True
                # Skip other PII columns in same row (e.g., lastName after firstName)
            else:
                masked_row[col_name] = value

        if first_pii_found:
            person_counter += 1

        masked_rows.append(masked_row)

    logger.info(f"Masked {person_counter - 1} individuals")
    return masked_rows
