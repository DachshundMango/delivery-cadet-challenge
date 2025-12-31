import os
import glob
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
SRC_DIR = os.path.join(BASE_DIR, 'src')
CONFIG_DIR = os.path.join(SRC_DIR, 'config')


def analyse_csv_file(file_path) -> dict:

	df = pd.read_csv(file_path)

	row_count = len(df)

	table_metadata = {
		"file_path": file_path,
		"row_count": row_count,
		"columns": {}
	}

	columns_list = df.columns.tolist()

	for column in columns_list:

		table_metadata["columns"][column] = {}

		null_count = df[column].isna().sum()
		null_ratio = null_count / row_count if row_count > 0 else 0.0
		unique_count = df[column].nunique()
		unique_ratio = unique_count / row_count if row_count > 0 else 0.0
		sample_values = df[column].fillna("NULL").head(5).tolist()
		is_unique = unique_count == row_count
		has_nulls = null_count > 0
		has_id_pattern = "id" in column.lower()

		table_metadata["columns"][column]["dtype"] = str(df[column].dtype)
		table_metadata["columns"][column]["null_count"] = null_count
		table_metadata["columns"][column]["null_ratio"] = null_ratio
		table_metadata["columns"][column]["unique_count"] = unique_count
		table_metadata["columns"][column]["unique_ratio"] = unique_ratio
		table_metadata["columns"][column]["is_unique"] = is_unique
		table_metadata["columns"][column]["has_nulls"] = has_nulls
		table_metadata["columns"][column]["has_id_pattern"] = has_id_pattern
		table_metadata["columns"][column]["sample_values"] = sample_values
		
	return table_metadata

def analyse_all_csv(data_dir):

	data_profile = {}
	csv_files = glob.glob(os.path.join(data_dir, '*.csv'))

	for file_path in csv_files:
		table_name = os.path.basename(file_path).replace('.csv','')
		data_profile[table_name] = analyse_csv_file(file_path)

	output_path = os.path.join(CONFIG_DIR, 'data_profile.json')
	with open(output_path, 'w', encoding='utf-8') as f:
		json.dump(data_profile, f, indent=2, ensure_ascii=False)

	print(f"Profiled {len(data_profile)} tables")
	print(f"Saved to {output_path}")


def main():
	"""Profile all CSV files in data directory"""
	analyse_all_csv(DATA_DIR)


if __name__ == '__main__':
	main()