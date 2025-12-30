import os
import json
from dotenv import load_dotenv
from sqlalchemy import Engine, text
from src.core.db import get_db_engine

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_DIR = os.path.join(BASE_DIR, 'src')
CONFIG_DIR = os.path.join(SRC_DIR, 'config')
KEYS_PATH = os.path.join(CONFIG_DIR, 'keys.json')
SCHEMA_JSON_PATH = os.path.join(CONFIG_DIR, 'schema_info.json')
SCHEMA_MD_PATH = os.path.join(CONFIG_DIR, 'schema_info.md')


def load_keys_config() -> dict:
    """Load keys.json configuration"""
    if not os.path.exists(KEYS_PATH):
        raise FileNotFoundError(f"{KEYS_PATH} not found. Run transform_data.py first.")

    with open(KEYS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_column_info(engine: Engine, table_name: str) -> list[tuple[str, str]]:
    """Get column information from database"""
    query = """
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = :table_name
    ORDER BY ordinal_position;
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), {"table_name": table_name})
            return [(row[0], row[1]) for row in result]
    except Exception as e:
        print(f"Warning: Could not get columns for {table_name}: {e}")
        return []


def generate_schema_json(keys_config: dict, engine: Engine) -> dict:
    """Generate structured schema as JSON"""
    schema = {}

    for table_name, config in keys_config.items():
        pk = config.get('pk', '')
        fks = config.get('fks', [])
        columns = get_column_info(engine, table_name)

        schema[table_name] = {
            'pk': pk,
            'fks': fks,
            'columns': [
                {'name': col_name, 'type': col_type}
                for col_name, col_type in columns
            ]
        }

    return schema


def generate_schema_markdown(schema: dict) -> str:
    """Generate human-readable schema as Markdown"""
    lines = ["# Database Schema\n"]
    lines.append("Generated from keys.json and PostgreSQL information_schema\n")
    lines.append("---\n")

    for idx, (table_name, info) in enumerate(schema.items(), 1):
        lines.append(f"\n## {idx}. Table `{table_name}`\n")

        # Primary Key
        if info['pk']:
            lines.append(f"**Primary Key:** `{info['pk']}`\n")
        else:
            lines.append("**Primary Key:** None\n")

        # Foreign Keys
        if info['fks']:
            lines.append("\n**Foreign Keys:**\n")
            for fk in info['fks']:
                lines.append(f"- `{fk['col']}` → `{fk['ref_table']}.{fk['ref_col']}`\n")

        # Columns
        if info['columns']:
            lines.append("\n**Columns:**\n")
            lines.append("| Column | Type |\n")
            lines.append("|--------|------|\n")
            for col in info['columns']:
                lines.append(f"| `{col['name']}` | {col['type']} |\n")

    return "".join(lines)


def generate_schema_text_for_llm(schema: dict) -> str:
    """Generate text format schema for LLM consumption"""
    lines = []

    for idx, (table_name, info) in enumerate(schema.items(), 1):
        lines.append(f'{idx}. Table "{table_name}"')

        # Primary Key
        if info['pk']:
            lines.append(f'   - Primary Key: "{info["pk"]}"')

        # Foreign Keys
        if info['fks']:
            lines.append(f"   - Foreign Keys:")
            for fk in info['fks']:
                lines.append(f'     - "{fk["col"]}" -> "{fk["ref_table"]}"("{fk["ref_col"]}")')

        # Columns
        if info['columns']:
            lines.append(f"   - Columns:")
            for col in info['columns']:
                lines.append(f'     - "{col["name"]}" ({col["type"]})')

        lines.append("")  # Empty line between tables

    return "\n".join(lines)


def main() -> None:
    """Generate schema files from keys.json and database"""
    print("="*60)
    print("SCHEMA GENERATION")
    print("="*60)

    try:
        # Load keys.json
        print("\n[1/4] Loading keys.json...")
        keys_config = load_keys_config()
        print(f"✓ Loaded {len(keys_config)} tables")

        # Connect to DB
        print("\n[2/4] Connecting to database...")
        engine = get_db_engine()
        print("✓ Connected")

        # Generate schema
        print("\n[3/4] Generating schema...")
        schema = generate_schema_json(keys_config, engine)

        # Add LLM-friendly text to schema JSON
        schema_with_text = {
            'tables': schema,
            'llm_prompt': generate_schema_text_for_llm(schema)
        }

        # Generate markdown
        markdown = generate_schema_markdown(schema)
        print("✓ Schema generated")

        # Write files
        print("\n[4/4] Writing schema files...")

        with open(SCHEMA_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(schema_with_text, f, indent=2)
        print(f"✓ {SCHEMA_JSON_PATH}")

        with open(SCHEMA_MD_PATH, 'w', encoding='utf-8') as f:
            f.write(markdown)
        print(f"✓ {SCHEMA_MD_PATH}")

        print("\n" + "="*60)
        print("✓ SCHEMA GENERATION COMPLETE")
        print("="*60)
        print(f"\nGenerated files:")
        print(f"  - {SCHEMA_JSON_PATH} (for SQL Agent)")
        print(f"  - {SCHEMA_MD_PATH} (for human review)")

    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print("\nPlease run the pipeline in order:")
        print("  1. python src/profiler.py")
        print("  2. python src/relationship_discovery.py")
        print("  3. python src/load_data.py")
        print("  4. python src/transform_data.py")
        print("  5. python src/generate_schema.py  ← You are here")
    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == '__main__':
    main()
