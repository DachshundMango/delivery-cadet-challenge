import os
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_DIR = os.path.join(BASE_DIR, 'src')
CONFIG_DIR = os.path.join(SRC_DIR, 'config')

def print_title(input):
    print(f"\n{'='*50}")
    print(f"Table: {input}")
    print(f"{'='*50}\n")


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
        
        print("[Recommended]")
        for idx, candidate in enumerate(columns_list):
            if candidate[0] == "recommended":
                print(f"{idx}. {candidate[1]:<20} {candidate[2]}")

        print("\n[Others]")
        for idx, candidate in enumerate(columns_list):
            if candidate[0] == "other":
                print(f"{idx}. {candidate[1]:<20} {candidate[2]}")
                
        while True:
            user_select = input("\nSelect PRIMARY KEY (or 'q'): ")
            
            if user_select.lower() == 'q':
                print(f"Skipped: {table_name}")
                pk_select_result[table_name] = None
                break

            if not user_select.isdigit():
                print("Invalid")
                continue

            user_select_int = int(user_select)

            if user_select_int >= len(columns_list):
                print("Invalid")
                continue

            selected_pk = columns_list[user_select_int][1]
            print(f"Selected: {table_name}.{selected_pk}")
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
        
        print("Available columns:")
        for i, col in enumerate(available_cols):
            hint = ""
            for ref_table in pk_select_result.keys():
                if ref_table != table_name:
                    col_core = col.replace("_id", "").replace("_", "")
                    table_core = ref_table.replace("sales_", "").replace("media_", "").replace("_", "")
                    if col_core.lower() in table_core.lower():
                        hint = f" → {ref_table}? (suggested)"
                        break
            print(f"  [{i}] {col}{hint}")
        
        while True:
            choice = input("\nSelect FK (or 'q'): ")
            
            if choice.lower() == 'q':
                break
            
            if not choice.isdigit() or int(choice) >= len(available_cols):
                print("Invalid")
                continue
            
            fk_col = available_cols[int(choice)]
            
            print(f"\nFK: {fk_col}")
            print("Select target table:")
            
            target_tables = [(t, pk) for t, pk in pk_select_result.items() 
                           if t != table_name and pk is not None]
            
            for i, (t_table, t_pk) in enumerate(target_tables):
                print(f"  [{i}] {t_table} (PK: {t_pk})")
            
            t_choice = input("Target: ")
            
            if not t_choice.isdigit() or int(t_choice) >= len(target_tables):
                print("Invalid")
                continue
            
            target_table, target_pk = target_tables[int(t_choice)]
            
            fk_relationships.append({
                "table": table_name,
                "column": fk_col,
                "references_table": target_table,
                "references_column": target_pk
            })

            print(f"Added FK: {table_name}.{fk_col} -> {target_table}.{target_pk}")
    
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

    print(f"\nSaved to {output_path}")
    return output_path


def main():

    profile_path = os.path.join(CONFIG_DIR, 'data_profile.json')

    if not os.path.exists(profile_path):
        print(f"Error: {profile_path} not found")
        print("Run profiler.py first")
        return

    data_profile = load_data_profile(profile_path)
    pk_select_result = interactive_pk_selection(data_profile)
    fk_relationships = interactive_fk_matching(data_profile, pk_select_result)

    save_keys_config(pk_select_result, fk_relationships)

if __name__ == '__main__':
    main()
