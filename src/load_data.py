import os
import glob
import json
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from sqlalchemy.sql.expression import table


load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@localhost:{5432}/{os.getenv('DB_NAME')}" 

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
SRC_DIR = os.path.join(BASE_DIR, 'src')

def get_engine():
    """Generate and return SQLAlchemy Engine instance"""
    try:
        engine = create_engine(DB_URL)
        print("✅ DB connection succeeded.")
        return engine
    except Exception as e:
        print(f"❌ DB connection failed: {e}")
        raise e

def load_csv_to_db(file_path, table_name, engine):
    
    try:
        print(f"📂 Loading {table_name}...")
        df = pd.read_csv(file_path)
        df.to_sql(name=table_name, con=engine, if_exists='replace', index=False)       
        print(f"   -> {table_name} : {len(df)} rows loaded.")

    except Exception as e:
        print(f"❌ Error loading {table_name}: {e}")

def add_primary_key(keys, table_name, engine):
    
    table = str(table_name)
    
    if table not in keys:
        print(f"Skipped PK set for {table} - not in key configuration.")
        return
    
    pk = keys[table]['pk']
    
    if not pk:
        print(f"{table_name} does not have a primary key.")
        return

    sql = f'ALTER TABLE "{table}" ADD PRIMARY KEY ("{pk}")'
    
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    print(f"Primary key set for {table}")

def add_foreign_key(keys, table_name, engine):

    table = str(table_name)
    
    if table not in keys:
        print(f"Skipped FK set for {table} - not in key configuration.")
        return
    
    fks = keys[table]['fks']

    if not fks:
        print(f"{table_name} does not have any foreign keys.")
        return

    for fk in fks:
        col = fk['col']
        ref_table = fk['ref_table']
        ref_col = fk['ref_col']
        
        # clean_sql = f'DELETE FROM "{table}" WHERE "{col}" NOT IN (SELECT "{ref_col}" FROM "{ref_table}")'
        
        alter_sql = f'ALTER TABLE "{table}" ADD CONSTRAINT "{col}" FOREIGN KEY ("{col}") REFERENCES "{ref_table}"("{ref_col}")'
        with engine.connect() as conn:
            # conn.execute(text(clean_sql))
            conn.execute(text(alter_sql))
            conn.commit()
        print(f"Foreign key {table}.{col} -> {ref_table}")

def main():
    engine = get_engine()
    files = glob.glob(os.path.join(DATA_DIR, '*.csv'))
    keys_json = os.path.join(SRC_DIR, 'keys.json')

    if not files:
        print('csv file does not exist in the data directory.')
        return

    if not os.path.exists(keys_json):
        print('key configuration file does not exist.')
        return
        
    with open(keys_json, 'r', encoding='utf-8') as f:
        keys = json.load(f)

    for file in files:
        file_path = os.path.join(DATA_DIR, file)
        file_name = os.path.basename(file_path)
        table_name = file_name.replace('.csv','')
        load_csv_to_db(file_path=file_path, table_name=table_name, engine=engine)
        add_primary_key(keys=keys, table_name=table_name, engine=engine)

    for file in files:
        file_path = os.path.join(DATA_DIR, file)
        file_name = os.path.basename(file_path)
        table_name = file_name.replace('.csv','')
        add_foreign_key(keys=keys, table_name=table_name, engine=engine)

if __name__ == "__main__":
    main()