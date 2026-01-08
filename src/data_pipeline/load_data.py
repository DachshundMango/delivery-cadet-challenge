import os
import glob
import json
import pandas as pd
from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.core.db import get_db_engine
from src.core.console import Console

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')
SRC_DIR = os.path.join(BASE_DIR, 'src')
CONFIG_DIR = os.path.join(SRC_DIR, 'config')

def load_csv_to_db(file_path: str, table_name: str, engine: Engine) -> None:

    try:
        Console.info(f"Loading {table_name}...")
        df = pd.read_csv(file_path)
        df.to_sql(name=table_name, con=engine, if_exists='replace', index=False)
        Console.info(f"{table_name}: {len(df)} rows loaded")

    except (pd.errors.ParserError, pd.errors.EmptyDataError, SQLAlchemyError) as e:
        Console.error(f"Failed to load {table_name}", str(e)[:100])

def add_primary_key(keys: dict, table_name: str, engine: Engine) -> bool:

    table = str(table_name)

    if table not in keys:
        Console.info(f"Skipped PK for {table} (not in configuration)")
        return False

    pk = keys[table]['pk']

    if not pk:
        Console.info(f"{table_name} has no primary key")
        return False

    sql = f'ALTER TABLE "{table}" ADD PRIMARY KEY ("{pk}")'

    try:
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
        Console.success(f"Primary key: {table}.{pk}")
        return False
    except SQLAlchemyError as e:
        Console.warning(f"Primary key {table}.{pk} failed", f"Reason: {str(e)[:100]}")
        return True

def add_foreign_key(keys: dict, table_name: str, engine: Engine) -> bool:

    table = str(table_name)

    if table not in keys:
        Console.info(f"Skipped FK for {table} (not in configuration)")
        return False

    fks = keys[table]['fks']

    failed = False

    if not fks:
        Console.info(f"{table_name} has no foreign keys")
        return False

    for fk in fks:
        col = fk['col']
        ref_table = fk['ref_table']
        ref_col = fk['ref_col']

        try:
            sql = f'ALTER TABLE "{table}" ADD CONSTRAINT "{col}" FOREIGN KEY ("{col}") REFERENCES "{ref_table}"("{ref_col}")'
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            Console.success(f"Foreign key: {table}.{col} -> {ref_table}.{ref_col}")
        except SQLAlchemyError as e:
            failed = True
            Console.warning(f"Foreign key {table}.{col} -> {ref_table} failed", f"Reason: {str(e)[:100]}")
            continue

    return failed

def main() -> None:
    Console.header("Load Data - CSV to PostgreSQL")

    engine = get_db_engine()
    files = glob.glob(os.path.join(DATA_DIR, '*.csv'))
    keys_json = os.path.join(CONFIG_DIR, 'keys.json')

    if not files:
        Console.error("No CSV files found in data directory")
        return

    if not os.path.exists(keys_json):
        Console.error("keys.json not found", "Run relationship_discovery.py first")
        return

    Console.info(f"Found {len(files)} CSV files")

    with open(keys_json, 'r', encoding='utf-8') as f:
        keys = json.load(f)

    # Step 1: Load CSV data
    Console.step(1, 3, "Loading CSV data to database")
    for file in files:
        file_path = os.path.join(DATA_DIR, file)
        file_name = os.path.basename(file_path)
        table_name = file_name.replace('.csv','')
        load_csv_to_db(file_path=file_path, table_name=table_name, engine=engine)

    # Step 2: Add primary keys
    Console.step(2, 3, "Setting primary key constraints")
    pk_failed = False
    for file in files:
        file_path = os.path.join(DATA_DIR, file)
        file_name = os.path.basename(file_path)
        table_name = file_name.replace('.csv','')
        result = add_primary_key(keys=keys, table_name=table_name, engine=engine)
        if result:
            pk_failed = True

    # Step 3: Add foreign keys
    Console.step(3, 3, "Setting foreign key constraints")
    fk_failed = False
    for file in files:
        file_path = os.path.join(DATA_DIR, file)
        file_name = os.path.basename(file_path)
        table_name = file_name.replace('.csv','')
        result = add_foreign_key(keys=keys, table_name=table_name, engine=engine)
        if result:
            fk_failed = True

    # Final status
    if pk_failed or fk_failed:
        print()
        if pk_failed:
            Console.warning("Some primary key constraints failed")
        if fk_failed:
            Console.warning("Some foreign key constraints failed")
        Console.info("\nRun integrity checker for detailed diagnosis:", indent=0)
        Console.info("  python -m src.data_pipeline.integrity_checker", indent=0)
        Console.footer("Load completed with warnings", success=False)
    else:
        Console.footer("Load completed successfully")


if __name__ == "__main__":
    main()