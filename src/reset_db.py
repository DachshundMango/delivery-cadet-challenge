"""
Database and Pipeline Reset Utility

Completely resets the database and all pipeline configuration files.
Use this when you want to start fresh with new data.
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import glob

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.console import Console
from src.core.logger import setup_logger

logger = setup_logger('cadet.reset_db')

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, 'src', 'config')


def delete_config_files():
    """Delete all pipeline configuration files in src/config/"""
    Console.step(1, 2, "Cleaning configuration files")

    config_files = [
        'keys.json',
        'schema_info.json',
        'schema_info.md',
        'data_profile.json'
    ]

    deleted_count = 0
    for filename in config_files:
        filepath = os.path.join(CONFIG_DIR, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                Console.info(f"Deleted: {filename}")
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete {filename}: {e}")
                Console.warning(f"Failed to delete {filename}", str(e)[:50])
        else:
            Console.info(f"Skipped: {filename} (not found)", indent=1)

    if deleted_count > 0:
        Console.success(f"Deleted {deleted_count} config file(s)", indent=0)
    else:
        Console.info("No config files to delete", indent=1)


def reset_database():
    """Drop all tables from the database"""
    Console.step(2, 2, "Resetting database tables")

    load_dotenv()

    # Get database connection from environment
    DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@localhost:5432/{os.getenv('DB_NAME')}"

    try:
        engine = create_engine(DB_URL)

        with engine.connect() as conn:
            # Get all tables in public schema
            result = conn.execute(text("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
            """))

            tables = [row[0] for row in result]

            if not tables:
                Console.info("No tables to drop", indent=1)
                return

            # Drop all tables with CASCADE
            for table in tables:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
                Console.info(f"Dropped: {table}")

            conn.commit()
            Console.success(f"Dropped {len(tables)} table(s)", indent=0)

    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        Console.error("Database reset failed", str(e))
        raise


def main():
    """Main reset function"""
    Console.header("Reset Database and Pipeline")

    Console.warning("This will DELETE all data and configuration!")
    Console.info("  - All database tables will be dropped", indent=0)
    Console.info("  - All config files will be deleted", indent=0)
    Console.info("  - You will need to run setup.py again\n", indent=0)

    response = input("Are you sure you want to continue? [y/N]: ").strip().lower()
    if response not in ['y', 'yes']:
        Console.warning("Reset cancelled by user")
        return

    try:
        # Delete config files
        delete_config_files()

        # Reset database
        reset_database()

        Console.footer("Reset completed successfully")
        Console.info("Run 'python src/setup.py' to set up the pipeline again", indent=0)

    except Exception as e:
        logger.error(f"Reset failed: {e}")
        Console.footer("Reset failed", success=False)
        sys.exit(1)


if __name__ == "__main__":
    main()
