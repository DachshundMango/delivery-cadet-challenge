"""Database reset utility"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def reset_database():
    load_dotenv()

    # Get database connection from environment
    DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@localhost:5432/{os.getenv('DB_NAME')}"
    engine = create_engine(DB_URL)

    print(f"Resetting database '{os.getenv('DB_NAME')}'...")

    try:
        with engine.connect() as conn:
            # Drop all tables with CASCADE option
            tables = ["sales_transactions", "sales_customers", "sales_franchises", "sales_suppliers", "media_customer_reviews", "media_gold_reviews_chunked"]
            for table in tables:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
                print(f"   Dropped table: {table}")
            conn.commit()
            print("\nDatabase reset complete")
    except Exception as e:
        print(f"Database reset failed: {e}")

if __name__ == "__main__":
    reset_database()