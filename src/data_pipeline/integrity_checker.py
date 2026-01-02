import os
import glob
import json
import pandas as pd
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.console import Console

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')
CLEAN_DATA_DIR = os.path.join(BASE_DIR, 'clean_data')
SRC_DIR = os.path.join(BASE_DIR, 'src')
CONFIG_DIR = os.path.join(SRC_DIR, 'config')
KEYS = os.path.join(CONFIG_DIR, 'keys.json')


def load_keys_config(keys_path) -> dict:
    
	with open(keys_path, 'r', encoding='utf-8') as f:
		keys_config = json.load(f)
    
	return keys_config

def load_csv_data(data_dir) -> dict:

    tables = dict()

    csv_files = glob.glob(os.path.join(data_dir, '*.csv'))

    for file_path in csv_files:
        table_name = os.path.basename(file_path).replace('.csv','')
        tables[table_name] = pd.read_csv(file_path)

    return tables

def detect_pk_issues(tables, keys_config) -> list:
    """
    Detect PK issues (duplicates, NULLs)

    Returns: list of issues
    """
    issues = []

    for table_name, keys in keys_config.items():
        pk = keys.get('pk')

        if not pk:
            continue

        if table_name not in tables:
            continue

        df = tables[table_name]

        if pk not in df.columns:
            continue

        # Check for NULLs
        null_count = df[pk].isna().sum()

        # Check for duplicates
        total_count = len(df)
        unique_count = df[pk].nunique()
        duplicate_count = total_count - unique_count

        if null_count > 0 or duplicate_count > 0:
            hint_parts = []
            if duplicate_count > 0:
                hint_parts.append(f"{duplicate_count} duplicate values")
            if null_count > 0:
                hint_parts.append(f"{null_count} NULL values")

            hint = "PK column has " + " and ".join(hint_parts)

            # Get duplicate samples
            duplicate_samples = []
            if duplicate_count > 0:
                duplicated_values = df[df.duplicated(subset=[pk], keep=False)][pk].unique()
                duplicate_samples = sorted(list(duplicated_values))[:5]

            issues.append({
                "table": table_name,
                "pk_column": pk,
                "duplicate_count": duplicate_count,
                "null_count": null_count,
                "duplicate_samples": duplicate_samples,
                "hint": hint
            })

    return issues

def detect_fk_issues(tables, keys_config) -> list:

    issues = []

    for table_name, keys in keys_config.items():
        if table_name not in tables:
            continue

        pd_fk = tables[table_name]
        fks_list = keys['fks']

        for fk in fks_list:
            fk_col = fk['col']
            ref_table = fk['ref_table']
            ref_col = fk['ref_col']

            if ref_table not in tables:
                continue

            pd_ref = tables[ref_table]
            
            # 차집합
            fk_values = set(pd_fk[fk_col].dropna())
            pk_values = set(pd_ref[ref_col].dropna())
            missing = fk_values - pk_values
            
            if missing:
                total_fk = len(fk_values)
                missing_count = len(missing)
                missing_ratio = missing_count / total_fk
                
                # 힌트 생성
                if missing_ratio > 0.9:
                    hint = "Systematic offset suspected (90%+ affected)"
                else:
                    hint = "Orphan records detected"
                
                issues.append({
                    "fk_table": table_name,
                    "fk_column": fk_col,
                    "ref_table": ref_table,
                    "ref_column": ref_col,
                    "missing_count": missing_count,
                    "missing_ratio": missing_ratio,
                    "missing_samples": sorted(list(missing))[:10],  # 샘플
                    "hint": hint
                })
    
    return issues

def print_report(pk_issues, fk_issues):

    total_issues = len(pk_issues) + len(fk_issues)

    if total_issues == 0:
        Console.success("No integrity issues found", indent=0)
        return

    Console.warning(f"Found {total_issues} integrity issue(s)")

    issue_num = 1

    # Print PK issues
    if pk_issues:
        print(f"\n{Console.THIN_LINE}")
        print("PRIMARY KEY ISSUES")
        print(f"{Console.THIN_LINE}")
        for issue in pk_issues:
            print(f"\nIssue #{issue_num}:")
            Console.info(f"Table: {issue['table']}", indent=0)
            Console.info(f"PK Column: {issue['pk_column']}", indent=0)
            Console.info(f"Duplicates: {issue['duplicate_count']}", indent=0)
            Console.info(f"NULLs: {issue['null_count']}", indent=0)
            Console.info(f"Hint: {issue['hint']}", indent=0)
            if issue['duplicate_samples']:
                Console.info(f"Samples: {issue['duplicate_samples']}", indent=0)
            issue_num += 1

    # Print FK issues
    if fk_issues:
        print(f"\n{Console.THIN_LINE}")
        print("FOREIGN KEY ISSUES")
        print(f"{Console.THIN_LINE}")
        for issue in fk_issues:
            print(f"\nIssue #{issue_num}:")
            Console.info(f"Table: {issue['fk_table']}.{issue['fk_column']}", indent=0)
            Console.info(f"Reference: {issue['ref_table']}.{issue['ref_column']}", indent=0)
            Console.info(f"Missing: {issue['missing_count']} values ({issue['missing_ratio']:.1%})", indent=0)
            Console.info(f"Hint: {issue['hint']}", indent=0)
            Console.info(f"Samples: {issue['missing_samples']}", indent=0)
            issue_num += 1

def main():

    Console.header("Integrity Checker - Data Validation")

    if not os.path.exists(KEYS):
        Console.error(f"{KEYS} not found", "Run relationship_discovery.py first")
        return

    Console.step(1, 3, "Loading configuration and data")
    keys_config = load_keys_config(KEYS)
    tables = load_csv_data(DATA_DIR)

    if not tables:
        Console.error(f"No CSV files found in {DATA_DIR}")
        return

    Console.info(f"Loaded {len(tables)} tables")

    Console.step(2, 3, "Checking primary key constraints")
    pk_issues = detect_pk_issues(tables, keys_config)
    if pk_issues:
        Console.warning(f"Found {len(pk_issues)} PK issue(s)")
    else:
        Console.success("No PK issues")

    Console.step(3, 3, "Checking foreign key constraints")
    fk_issues = detect_fk_issues(tables, keys_config)
    if fk_issues:
        Console.warning(f"Found {len(fk_issues)} FK issue(s)")
    else:
        Console.success("No FK issues")

    print()
    print_report(pk_issues, fk_issues)

    total_issues = len(pk_issues) + len(fk_issues)
    if total_issues > 0:
        Console.footer(f"Validation completed - {total_issues} issue(s) found", success=False)
    else:
        Console.footer("Validation completed - no issues found")

if __name__ == '__main__':
    main()
