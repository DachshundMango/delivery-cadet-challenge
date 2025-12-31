import os
import glob
import json
import pandas as pd
from sqlalchemy import Engine, text
from dotenv import load_dotenv
from src.core.db import get_db_engine

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')
SRC_DIR = os.path.join(BASE_DIR, 'src')
CONFIG_DIR = os.path.join(SRC_DIR, 'config')

def load_csv_to_db(file_path: str, table_name: str, engine: Engine) -> None:

    try:
        print(f"Loading {table_name}...")
        df = pd.read_csv(file_path)
        df.to_sql(name=table_name, con=engine, if_exists='replace', index=False)
        print(f"   -> {table_name}: {len(df)} rows loaded")

    except Exception as e:
        print(f"Error loading {table_name}: {e}")

def add_primary_key(keys: dict, table_name: str, engine: Engine) -> bool:

    table = str(table_name)

    if table not in keys:
        print(f"Skipped PK set for {table} - not in key configuration.")
        return False

    pk = keys[table]['pk']

    if not pk:
        print(f"{table_name} does not have a primary key.")
        return False

    sql = f'ALTER TABLE "{table}" ADD PRIMARY KEY ("{pk}")'

    try:
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
        print(f"Primary key set for {table}")
        return False
    except Exception as e:
        print(f"Warning: Primary key {table}.{pk} is skipped.")
        print(f" Reason: {str(e)[:100]}")
        print(f" Table loaded without PK")
        return True

def add_foreign_key(keys: dict, table_name: str, engine: Engine) -> bool:

    table = str(table_name)
    
    if table not in keys:
        print(f"Skipped FK set for {table} - not in key configuration.")
        return False
    
    fks = keys[table]['fks']

    failed = False

    if not fks:
        print(f"{table_name} does not have any foreign keys.")
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
            print(f"Foreign key {table}.{col} -> {ref_table}")
        except Exception as e:
            failed = True
            print(f"Warning: Foreign key {table}.{col} -> {ref_table} is skipped. Please recheck data file.")
            print(f" Reason: {str(e)[:100]}")
            print(f" Edit and run scripts/transform_data.py to fix")
            continue

    return failed

def main() -> None:
    engine = get_db_engine()
    files = glob.glob(os.path.join(DATA_DIR, '*.csv'))
    keys_json = os.path.join(CONFIG_DIR, 'keys.json')

    if not files:
        print('csv file does not exist in the data directory.')
        return

    if not os.path.exists(keys_json):
        print('key configuration file does not exist.')
        return
        
    with open(keys_json, 'r', encoding='utf-8') as f:
        keys = json.load(f)

    pk_failed = False

    for file in files:
        file_path = os.path.join(DATA_DIR, file)
        file_name = os.path.basename(file_path)
        table_name = file_name.replace('.csv','')
        load_csv_to_db(file_path=file_path, table_name=table_name, engine=engine)
        result = add_primary_key(keys=keys, table_name=table_name, engine=engine)
        if result:
            pk_failed = True

    fk_failed = False

    for file in files:
        file_path = os.path.join(DATA_DIR, file)
        file_name = os.path.basename(file_path)
        table_name = file_name.replace('.csv','')
        result = add_foreign_key(keys=keys, table_name=table_name, engine=engine)
        if result:
            fk_failed = True
    
    if pk_failed or fk_failed:
        print("\n" + "="*60)
        if pk_failed:
            print("WARNING: Primary key constraints failed")
        if fk_failed:
            print("WARNING: Foreign key constraints failed")
        print("\nRun integrity checker for detailed diagnosis:")
        print("  python -m src.data_pipeline.integrity_checker")
        print("="*60)


if __name__ == "__main__":
    main()