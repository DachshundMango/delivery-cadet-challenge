"""
Relationship Discovery

This interactive tool assists users in defining Primary Keys (PK) and Foreign Keys (FK)
for the dataset. It analyses column names and statistics to suggest likely relationships,
which are then confirmed by the user and saved to `keys.json`.

Workflow:
1. Load data profile (from profiler.py)
2. Interactive PK selection: Suggests PKs based on uniqueness and patterns
3. Interactive FK matching: Suggests FKs based on column name similarity
4. Save configuration: Generates keys.json for use by load_data.py
"""

import os
import json
import pandas as pd
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.console import Console

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_DIR = os.path.join(BASE_DIR, 'src')
CONFIG_DIR = os.path.join(SRC_DIR, 'config')

def print_title(input):
    print(f"\n{Console.THIN_LINE}")
    print(f"Table: {input}")
    print(f"{Console.THIN_LINE}\n")


def load_data_profile(file_path) -> dict:
    
    with open(file_path, 'r', encoding='utf-8') as f:
      data_profile = json.load(f)
    
    return data_profile

def interactive_pk_selection(data_profile) -> dict:
    
    pk_select_result = dict()

    for table_name, table_info in data_profile.items():
        
        columns = table_info['columns']
        columns_list = []

        for column_name, column_info in columns.items():
            is_unique = column_info['is_unique']
            has_nulls = column_info['has_nulls']
            has_id_pattern = column_info['has_id_pattern']
            sample_values = column_info['sample_values']
            sample_str = str(sample_values)[:50]

            if is_unique and not has_nulls and has_id_pattern:
                columns_list.insert(0, ("recommended", column_name, sample_str))
            else:
                columns_list.append(("other", column_name, sample_str))

        print_title(table_name)

        Console.info("[Recommended]", indent=0)
        for idx, candidate in enumerate(columns_list):
            if candidate[0] == "recommended":
                Console.info(f"{idx}. {candidate[1]:<20} {candidate[2]}", indent=0)

        Console.info("\n[Others]", indent=0)
        for idx, candidate in enumerate(columns_list):
            if candidate[0] == "other":
                Console.info(f"{idx}. {candidate[1]:<20} {candidate[2]}", indent=0)

        while True:
            user_select = input("\nSelect PRIMARY KEY (or 'q'): ")

            if user_select.lower() == 'q':
                Console.info(f"Skipped: {table_name}", indent=0)
                pk_select_result[table_name] = None
                break

            if not user_select.isdigit():
                Console.warning("Invalid input", "Enter a number or 'q' to skip")
                continue

            user_select_int = int(user_select)

            if user_select_int >= len(columns_list):
                Console.warning("Invalid input", "Number out of range")
                continue

            selected_pk = columns_list[user_select_int][1]
            Console.success(f"Selected: {table_name}.{selected_pk}", indent=0)
            pk_select_result[table_name] = selected_pk
            break

    return pk_select_result

def interactive_fk_matching(data_profile, pk_select_result) -> dict:
    
    fk_relationships = []
    
    for table_name, table_info in data_profile.items():
        
        selected_pk = pk_select_result.get(table_name)
        if not selected_pk:
            continue
        
        columns = table_info['columns']
        available_cols = [col for col in columns.keys() if col != selected_pk]
        
        if not available_cols:
            continue
        
        print_title(table_name)

        Console.info("Available columns:", indent=0)
        for i, col in enumerate(available_cols):
            hint = ""
            for ref_table in pk_select_result.keys():
                if ref_table != table_name:
                    # Generalized matching: remove common id suffixes and check if column name part is in table name
                    # e.g., "customerID" -> "customer" which is in "sales_customers"
                    col_core = col.lower().replace("_id", "").replace("id", "")
                    if col_core and col_core in ref_table.lower():
                        hint = f" → {ref_table}? (suggested)"
                        break
            Console.info(f"[{i}] {col}{hint}", indent=0)

        while True:
            choice = input("\nSelect FK (or 'q'): ")

            if choice.lower() == 'q':
                break

            if not choice.isdigit() or int(choice) >= len(available_cols):
                Console.warning("Invalid input", "Enter a valid number or 'q' to skip")
                continue

            fk_col = available_cols[int(choice)]

            Console.info(f"\nFK: {fk_col}", indent=0)
            Console.info("Select target table:", indent=0)

            target_tables = [(t, pk) for t, pk in pk_select_result.items()
                           if t != table_name and pk is not None]

            for i, (t_table, t_pk) in enumerate(target_tables):
                Console.info(f"[{i}] {t_table} (PK: {t_pk})", indent=0)

            t_choice = input("Target: ")

            if not t_choice.isdigit() or int(t_choice) >= len(target_tables):
                Console.warning("Invalid input", "Enter a valid number")
                continue

            target_table, target_pk = target_tables[int(t_choice)]

            fk_relationships.append({
                "table": table_name,
                "column": fk_col,
                "references_table": target_table,
                "references_column": target_pk
            })

            Console.success(f"Added FK: {table_name}.{fk_col} -> {target_table}.{target_pk}", indent=0)
    
    return fk_relationships


def save_keys_config(pk_select_result, fk_relationships, output_path=None):

    if output_path is None:
        output_path = os.path.join(CONFIG_DIR, 'keys.json')

    keys_config = {}

    for table_name, pk_column in pk_select_result.items():

        keys_config[table_name] = {
            "pk": pk_column if pk_column else [],
            "fks": []
        }

    for fk_rel in fk_relationships:
        table_name = fk_rel["table"]

        if table_name not in keys_config:
            keys_config[table_name] = {"pk": [], "fks": []}

        keys_config[table_name]["fks"].append({
            "col": fk_rel["column"],
            "ref_table": fk_rel["references_table"],
            "ref_col": fk_rel["references_column"]
        })

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(keys_config, f, indent=2, ensure_ascii=False)

    Console.success(f"Saved to {output_path}", indent=0)
    return output_path


def main():

    Console.header("Relationship Discovery - PK/FK Configuration")

    profile_path = os.path.join(CONFIG_DIR, 'data_profile.json')

    if not os.path.exists(profile_path):
        Console.error(f"{profile_path} not found", "Run profiler.py first")
        return

    Console.step(1, 2, "Selecting primary keys")
    data_profile = load_data_profile(profile_path)
    pk_select_result = interactive_pk_selection(data_profile)

    Console.step(2, 2, "Configuring foreign key relationships")
    fk_relationships = interactive_fk_matching(data_profile, pk_select_result)

    print()  # Add blank line before save message
    save_keys_config(pk_select_result, fk_relationships)

    Console.footer("Relationship discovery completed")

if __name__ == '__main__':
    main()
