"""
Data Pipeline Utilities

ETL tools for loading CSV data, generating schemas, and validating data integrity.

Note: Modules in this package import each other, so we avoid importing main functions
here to prevent circular import issues. Run scripts directly as modules:
  python -m src.data_pipeline.profiler
  python -m src.data_pipeline.relationship_discovery
  python -m src.data_pipeline.load_data
  python -m src.data_pipeline.transform_data
  python -m src.data_pipeline.generate_schema
"""

__all__ = []
