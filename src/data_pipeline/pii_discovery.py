import os
import glob
import json
import pandas as pd
from dotenv import load_dotenv
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.logger import setup_logger
from src.core.console import Console
from langchain_openai import ChatOpenAI

from src.agent.prompts import get_pii_detection_prompt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')
SRC_DIR = os.path.join(BASE_DIR, 'src')
CONFIG_DIR = os.path.join(SRC_DIR, 'config')

load_dotenv()
logger = setup_logger('cadet.pii_discovery')

# LLM configuration (Cerebras via OpenAI-compatible API)
LLM_MODEL = os.getenv('LLM_MODEL', 'llama-3.3-70b')
CEREBRAS_API_KEY = os.getenv('CEREBRAS_API_KEY')
CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"
llm = ChatOpenAI(model=LLM_MODEL, api_key=CEREBRAS_API_KEY, base_url=CEREBRAS_BASE_URL)


def load_data_profile(file_path) -> dict:
    
    with open(file_path, 'r', encoding='utf-8') as f:
      data_profile = json.load(f)
    
    return data_profile

def collect_column_samples(data_profile) -> dict:
	
	column_data = dict()

	for table_name, table_info in data_profile.items():
        
		columns = table_info['columns']
		column_data[table_name] = dict()
		for column_name, column_info in columns.items():
			column_data[table_name][column_name] = column_info['sample_values']

	return column_data
	
def detect_pii_with_llm(column_data) -> dict:
	"""
	Use LLM to detect which columns contain PII (personal names).

	Args:
		column_data: Dictionary of {table_name: {column_name: [sample_values]}}

	Returns:
		Dictionary of {table_name: [pii_column_list]}
	"""
	logger.info("Starting PII detection with LLM...")

	# Get prompt from prompts module
	pii_detection_prompt = get_pii_detection_prompt(column_data)

	# Invoke LLM
	response = llm.invoke(pii_detection_prompt)

	# Clean response (remove markdown formatting)
	result_text = response.content.strip()
	result_text = result_text.replace("```json", "").replace("```", "").strip()

	# Parse JSON
	try:
		detection_result = json.loads(result_text)
		logger.info(f"PII detection completed. Found PII in {len(detection_result)} tables.")
	except json.JSONDecodeError as e:
		logger.error(f"Failed to parse LLM response as JSON: {e}")
		logger.error(f"Raw response: {result_text}")
		detection_result = {}

	return detection_result

def display_report_and_confirm(detection_result: dict, all_columns: dict) -> None:
	"""
	Display PII detection report with color coding and wait for user confirmation.

	Args:
		detection_result: Dictionary of {table_name: [pii_column_list]}
		all_columns: Dictionary of {table_name: {column_name: [samples]}}
	"""
	print(f"\n{Console.THICK_LINE}")
	print("PII DETECTION REPORT")
	print(f"{Console.THICK_LINE}\n")

	# Display each table
	for table_name, columns in all_columns.items():
		Console.info(f"[Table: {table_name}]", indent=0)

		pii_columns = detection_result.get(table_name, [])

		for column_name in columns.keys():
			if column_name in pii_columns:
				# PII column - show in RED
				print(f"  {Console.RED}[PII]  {column_name}{Console.RESET}")
			else:
				# Safe column - show in GREEN
				print(f"  {Console.GREEN}[SAFE] {column_name}{Console.RESET}")

		print()  # Blank line between tables

	print(f"{Console.THICK_LINE}")
	Console.warning("Review the above detection results")
	print()
	Console.info("The detected PII columns will be saved to:", indent=0)
	Console.info("  src/config/schema_info.json", indent=0)
	print()
	Console.info("If you need to modify the detection results:", indent=0)
	Console.info("  1. Edit src/config/schema_info.json after this script completes", indent=0)
	Console.info("  2. Look for the 'pii_columns' field", indent=0)
	Console.info("  3. Add/remove columns as needed", indent=0)
	print()
	print(f"{Console.THICK_LINE}\n")

	# Wait for user confirmation (Option B: Verify-First)
	input("Press ENTER to save and continue... ")

def main():
	"""
	Main function to discover PII columns and save to schema_info.json.

	This follows Option B (Verify-First) strategy:
	1. Load data profile
	2. Detect PII columns using LLM (one-time call)
	3. Display visual report
	4. Wait for user confirmation
	5. Save to schema_info.json
	"""
	Console.header("PII Discovery - Personal Information Detection")

	# Step 1: Load data profile
	Console.step(1, 5, "Loading data profile")
	data_profile_path = os.path.join(CONFIG_DIR, 'data_profile.json')

	if not os.path.exists(data_profile_path):
		logger.error(f"Data profile not found: {data_profile_path}")
		Console.error(f"Data profile not found: {data_profile_path}", "Run profiler.py first")
		return

	data_profile = load_data_profile(data_profile_path)
	Console.info(f"Loaded from {data_profile_path}")

	# Step 2: Collect column samples
	Console.step(2, 5, "Collecting column samples")
	column_data = collect_column_samples(data_profile)
	Console.info(f"Collected samples from {len(column_data)} tables")

	# Step 3: Detect PII using LLM (one-time call)
	Console.step(3, 5, "Detecting PII columns with LLM")
	detection_result = detect_pii_with_llm(column_data)

	# Step 4: Display report and wait for user confirmation
	Console.step(4, 5, "Reviewing detection results")
	display_report_and_confirm(detection_result, column_data)

	# Step 5: Save to schema_info.json
	Console.step(5, 5, "Saving results")
	schema_info_path = os.path.join(CONFIG_DIR, 'schema_info.json')

	# Load existing schema_info or create new one
	if os.path.exists(schema_info_path):
		logger.info(f"Loading existing schema_info from: {schema_info_path}")
		with open(schema_info_path, 'r', encoding='utf-8') as f:
			schema_info = json.load(f)
	else:
		logger.warning(f"schema_info.json not found. Creating new file.")
		schema_info = {}

	# Add pii_columns field
	schema_info['pii_columns'] = detection_result

	# Save updated schema_info
	with open(schema_info_path, 'w', encoding='utf-8') as f:
		json.dump(schema_info, f, indent=2, ensure_ascii=False)

	Console.footer("PII discovery completed")
	Console.info(f"Results saved to: {schema_info_path}", indent=0)


if __name__ == "__main__":
	main()