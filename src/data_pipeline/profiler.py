import os
import glob
import json
import pandas as pd
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.core.console import Console
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')
SRC_DIR = os.path.join(BASE_DIR, 'src')
CONFIG_DIR = os.path.join(SRC_DIR, 'config')

# LLM configuration (Cerebras via OpenAI-compatible API)
LLM_MODEL = os.getenv('LLM_MODEL', 'llama-3.3-70b')
CEREBRAS_API_KEY = os.getenv('CEREBRAS_API_KEY')
CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"
llm = ChatOpenAI(model=LLM_MODEL, api_key=CEREBRAS_API_KEY, base_url=CEREBRAS_BASE_URL)


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

		null_count = int(df[column].isna().sum())
		null_ratio = null_count / row_count if row_count > 0 else 0.0
		unique_count = int(df[column].nunique())
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

def summarize_for_llm(data_profile: dict) -> dict:
	"""
	Summarize data_profile.json for LLM analysis.
	Removes verbose details and focuses on key statistics.
	"""
	summary = {
		"total_tables": len(data_profile),
		"tables": []
	}

	for table_name, table_info in data_profile.items():
		# Skip if table is empty
		if table_info['row_count'] == 0:
			continue

		table_summary = {
			"name": table_name,
			"rows": table_info['row_count'],
			"columns": []
		}

		for col_name, col_info in table_info['columns'].items():
			# Skip ID columns and unique identifiers
			if col_info['has_id_pattern'] or (col_info['is_unique'] and table_info['row_count'] > 50):
				continue

			# Include only relevant columns
			col_summary = {
				"name": col_name,
				"type": col_info['dtype'],
				"unique_values": col_info['unique_count'],
				"unique_ratio": round(col_info['unique_ratio'], 3),
				"null_ratio": round(col_info['null_ratio'], 3),
				"sample_values": col_info['sample_values'][:3]
			}

			table_summary['columns'].append(col_summary)

		# Only include tables with analyzable columns
		if table_summary['columns']:
			summary['tables'].append(table_summary)

	return summary


def generate_insights(data_profile: dict) -> dict:
	"""
	Generate data-agnostic insights using LLM analysis.

	This approach is completely dataset-agnostic - it works with any CSV data
	by letting the LLM understand the data structure and find interesting patterns.
	"""
	Console.info("Generating insights with LLM...")

	# Summarize profile for LLM
	summary = summarize_for_llm(data_profile)

	# Create prompt for LLM
	prompt = f"""You are a data analyst. Analyze this dataset profile and identify 3-5 interesting patterns or insights.

Dataset Profile:
{json.dumps(summary, indent=2)}

Instructions:
1. Look for high concentration patterns (e.g., top 20% accounts for 80% - Pareto principle)
2. Look for category dominance (one value dominates a field)
3. Look for imbalanced distributions
4. Look for data quality issues (high null ratios)
5. Focus on patterns that would be valuable for decision-making

CRITICAL RULES:
- Base insights ONLY on the metadata provided (unique_ratio, null_ratio, sample_values)
- Do NOT make assumptions about data you cannot see
- AVOID technical/system columns (URIs, status flags like 'approved', review dates)
- Prioritize business-relevant fields (categories, types, amounts, locations)
- Express findings in percentages or concrete numbers where possible
- Be specific: mention table names and column names
- Keep descriptions concise and actionable (one sentence each)

Return ONLY a JSON object in this exact format:
{{
  "summary": {{
    "total_rows": <sum of all rows across tables>,
    "total_tables": <number of tables>,
    "key_stats": "<brief one-line summary of dataset>"
  }},
  "insights": [
    {{
      "type": "concentration|dominance|imbalance|quality",
      "description": "<specific finding with numbers and business context>",
      "table": "<table_name>",
      "column": "<column_name>"
    }}
  ]
}}

Return 3-5 most interesting and actionable insights. Be concise and data-driven."""

	try:
		response = llm.invoke(prompt)
		content = response.content.strip()

		# Clean markdown formatting
		content = content.replace("```json", "").replace("```", "").strip()

		# Parse JSON
		insights = json.loads(content)

		Console.info(f"Generated {len(insights.get('insights', []))} insights")
		return insights

	except json.JSONDecodeError as e:
		Console.info(f"Failed to parse LLM response as JSON: {e}")
		# Return fallback insights
		return {
			"summary": {
				"total_rows": sum(t['row_count'] for t in data_profile.values()),
				"total_tables": len(data_profile),
				"key_stats": "Dataset analysis in progress"
			},
			"insights": []
		}
	except Exception as e:
		Console.info(f"Insight generation failed: {e}")
		return {
			"summary": {
				"total_rows": sum(t['row_count'] for t in data_profile.values()),
				"total_tables": len(data_profile),
				"key_stats": "Dataset loaded successfully"
			},
			"insights": []
		}


def analyse_all_csv(data_dir):

	# Step 1: Scan CSV files
	Console.step(1, 4, "Scanning CSV files")
	csv_files = glob.glob(os.path.join(data_dir, '*.csv'))
	Console.info(f"Found {len(csv_files)} tables")

	# Step 2: Analyze each file
	Console.step(2, 4, "Analyzing data structure")
	data_profile = {}
	for file_path in csv_files:
		table_name = os.path.basename(file_path).replace('.csv','')
		data_profile[table_name] = analyse_csv_file(file_path)

		# Show info for each table
		table_info = data_profile[table_name]
		Console.info(f"{table_name}: {table_info['row_count']} rows, {len(table_info['columns'])} columns")

	# Step 3: Save profile results
	Console.step(3, 4, "Saving data profile")
	profile_path = os.path.join(CONFIG_DIR, 'data_profile.json')
	with open(profile_path, 'w', encoding='utf-8') as f:
		json.dump(data_profile, f, indent=2, ensure_ascii=False, default=str)
	Console.info(f"Saved to {profile_path}")

	# Step 4: Generate insights
	Console.step(4, 4, "Discovering insights")
	insights = generate_insights(data_profile)
	insights_path = os.path.join(CONFIG_DIR, 'insights.json')
	with open(insights_path, 'w', encoding='utf-8') as f:
		json.dump(insights, f, indent=2, ensure_ascii=False)
	Console.info(f"Saved to {insights_path}")


def main():
	"""Profile all CSV files in data directory"""
	Console.header("Profiler - Data Analysis")
	analyse_all_csv(DATA_DIR)
	Console.footer("Profiler completed")


if __name__ == '__main__':
	main()