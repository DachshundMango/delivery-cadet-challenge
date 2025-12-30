import os
import json
from collections import defaultdict
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, 'src')
KEYS_PATH = os.path.join(SRC_DIR, 'keys.json')

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@localhost:5432/{os.getenv('DB_NAME')}"


def get_engine():
    """Create database engine"""
    return create_engine(DB_URL)


def load_keys_config():
    """Load keys.json configuration"""
    if os.path.exists(KEYS_PATH):
        with open(KEYS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def execute_query(engine, query):
    """Execute a single SQL query"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            conn.commit()
        return True, result.rowcount
    except Exception as e:
        return False, str(e)


def update_keys_from_db(engine):
    """Read actual PK/FK constraints from DB and update keys.json"""
    print("\n[Updating keys.json from DB]")

    # Get all tables first
    tables_query = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_type = 'BASE TABLE';
    """

    # Query for PKs
    pk_query = """
    SELECT tc.table_name, kcu.column_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name
    WHERE tc.constraint_type = 'PRIMARY KEY'
      AND tc.table_schema = 'public';
    """

    # Query for FKs (with proper join to avoid duplicates)
    fk_query = """
    SELECT DISTINCT
        kcu.table_name,
        kcu.column_name,
        ccu.table_name AS ref_table,
        ccu.column_name AS ref_col
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.referential_constraints rc
      ON tc.constraint_name = rc.constraint_name
      AND tc.table_schema = rc.constraint_schema
    JOIN information_schema.key_column_usage ccu
      ON rc.unique_constraint_name = ccu.constraint_name
      AND rc.unique_constraint_schema = ccu.table_schema
      AND kcu.ordinal_position = ccu.ordinal_position
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_schema = 'public';
    """

    try:
        with engine.connect() as conn:
            # Get all tables
            tables_result = conn.execute(text(tables_query))
            tables = {row[0] for row in tables_result}

            # Get PKs
            pk_result = conn.execute(text(pk_query))
            pks = {row[0]: row[1] for row in pk_result}

            # Get FKs with deduplication
            fk_result = conn.execute(text(fk_query))
            fks = defaultdict(list)
            for row in fk_result:
                fk_entry = {
                    'col': row[1],
                    'ref_table': row[2],
                    'ref_col': row[3]
                }
                # Avoid duplicates
                if fk_entry not in fks[row[0]]:
                    fks[row[0]].append(fk_entry)

        # Build new keys config
        new_keys = {}
        for table in sorted(tables):
            new_keys[table] = {
                'pk': pks.get(table, ''),
                'fks': fks.get(table, [])
            }

        # Save to keys.json
        with open(KEYS_PATH, 'w', encoding='utf-8') as f:
            json.dump(new_keys, f, indent=2)

        print(f"✓ keys.json updated with {len(new_keys)} tables")
        return True

    except Exception as e:
        print(f"✗ Failed to update keys.json: {str(e)[:100]}")
        return False


def verify_transformation(engine, keys_config):
    """Verify transformation by checking FK relationships in DB"""
    print("\n[Verifying Transformation]")

    issue_count = 0

    for table_name, config in keys_config.items():
        fks = config.get('fks', [])

        for fk in fks:
            col = fk['col']
            ref_table = fk['ref_table']
            ref_col = fk['ref_col']

            sql = f"""
            SELECT COUNT(*) as orphan_count
            FROM "{table_name}"
            WHERE "{col}" NOT IN (
                SELECT "{ref_col}" FROM "{ref_table}"
            ) AND "{col}" IS NOT NULL;
            """

            try:
                with engine.connect() as conn:
                    result = conn.execute(text(sql)).fetchone()
                    orphan_count = result[0]

                if orphan_count > 0:
                    print(f"⚠️  {table_name}.{col}: {orphan_count} orphans remain")
                    issue_count += 1
            except Exception as e:
                print(f"⚠️  Could not verify {table_name}.{col}: {str(e)[:60]}")
                issue_count += 1

    if issue_count == 0:
        print("✓ All integrity issues resolved!")
        return True
    else:
        print(f"\n⚠️  {issue_count} issues still remain")
        return False


def main():
    """
    Interactive data transformation tool
    """
    print("="*60)
    print("DATA TRANSFORMATION TOOL")
    print("="*60)
    print("\nEnter SQL queries to transform your data.")
    print("Type 'done' when finished to verify and update keys.json.")
    print("Type 'quit' to exit without verification.\n")

    engine = get_engine()
    query_count = 0

    while True:
        try:
            query = input("SQL> ").strip()

            if not query:
                continue

            if query.lower() == 'quit':
                print("Exiting without verification.")
                return

            if query.lower() == 'done':
                break

            success, result = execute_query(engine, query)

            if success:
                print(f"✓ Query executed: {result} rows affected")
                query_count += 1
            else:
                print(f"✗ Query failed: {result}")

        except KeyboardInterrupt:
            print("\n\nExiting...")
            return
        except EOFError:
            break

    print(f"\n{query_count} queries executed successfully.")

    # Update keys.json from DB
    update_keys_from_db(engine)

    # Load updated keys and verify
    keys_config = load_keys_config()
    if keys_config:
        success = verify_transformation(engine, keys_config)

        if success:
            print("\n" + "="*60)
            print("✓ TRANSFORMATION COMPLETE - ALL VERIFIED")
            print("="*60)
            print("\nYou can now run the SQL Agent:")
            print("  python src/main.py")
        else:
            print("\n" + "="*60)
            print("⚠️  TRANSFORMATION COMPLETE - VERIFICATION FAILED")
            print("="*60)
            print("Some issues remain. Manual review required.")
    else:
        print("\n" + "="*60)
        print("✓ TRANSFORMATION COMPLETE")
        print("="*60)


if __name__ == '__main__':
    main()
