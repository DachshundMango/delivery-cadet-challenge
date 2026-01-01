import os
from typing import Optional
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from src.core.logger import setup_logger

# Automatically find .env file in the project root and load environment variables
load_dotenv()

logger = setup_logger('cadet.db')


class DatabaseConfig:
    """Centralized database configuration"""

    @staticmethod
    def get_db_url() -> str:
        """
        Construct PostgreSQL connection URL from environment variables.

        Returns:
            Database connection URL string

        Raises:
            ValueError: If required environment variables are missing
        """
        user = os.getenv('DB_USER')
        password = os.getenv('DB_PASSWORD')
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        name = os.getenv('DB_NAME')

        if not all([user, password, name]):
            raise ValueError(
                "Missing required DB environment variables: DB_USER, DB_PASSWORD, DB_NAME"
            )

        return f"postgresql://{user}:{password}@{host}:{port}/{name}"


def get_db_engine(pool_size: int = 5, max_overflow: int = 10) -> Engine:
    """
    Create and return a SQLAlchemy engine with connection pooling.

    Args:
        pool_size: Number of connections to maintain in the pool
        max_overflow: Maximum number of connections beyond pool_size

    Returns:
        SQLAlchemy Engine instance

    Raises:
        ValueError: If required environment variables are missing
        SQLAlchemyError: If database connection fails

    Example:
        >>> engine = get_db_engine()
        >>> with engine.connect() as conn:
        ...     result = conn.execute(text("SELECT COUNT(*) FROM sales"))
    """
    try:
        db_url = DatabaseConfig.get_db_url()
        engine = create_engine(
            db_url,
            pool_pre_ping=True,  # Verify connections before using
            pool_size=pool_size,
            max_overflow=max_overflow,
            echo=False  # Set to True for SQL debugging
        )

        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        logger.info("Database connection established successfully")
        return engine

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {e}")
        raise
