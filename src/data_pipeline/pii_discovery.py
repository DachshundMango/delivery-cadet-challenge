import os
import glob
import json
import pandas as pd
from dotenv import load_dotenv

from src.core.logger import setup_logger
from langchain_groq import ChatGroq

from src.agent.prompts import get_pii_detection_prompt

# ANSI Color Codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
SRC_DIR = os.path.join(BASE_DIR, 'src')
CONFIG_DIR = os.path.join(SRC_DIR, 'config')

load_dotenv()
logger = setup_logger('cadet.pii_discovery')

# LLM configuration (can be overridden by environment variable)
LLM_MODEL = os.getenv('LLM_MODEL', 'llama-3.1-8b-instant')
llm = ChatGroq(model=LLM_MODEL)


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
	print("\n" + "=" * 80)
	print(f"{CYAN}PII DETECTION REPORT{RESET}")
	print("=" * 80)
	print()

	# Display each table
	for table_name, columns in all_columns.items():
		print(f"{BLUE}[Table: {table_name}]{RESET}")

		pii_columns = detection_result.get(table_name, [])

		for column_name in columns.keys():
			if column_name in pii_columns:
				# PII column - show in RED
				print(f"  {RED}🔴 [PII]  {column_name}{RESET}")
			else:
				# Safe column - show in GREEN
				print(f"  {GREEN}🟢 [SAFE] {column_name}{RESET}")

		print()  # Blank line between tables

	print("=" * 80)
	print(f"{YELLOW}REVIEW THE ABOVE DETECTION RESULTS{RESET}")
	print()
	print("The detected PII columns will be saved to:")
	print(f"  {CYAN}src/config/schema_info.json{RESET}")
	print()
	print("If you need to modify the detection results:")
	print(f"  1. Edit {CYAN}src/config/schema_info.json{RESET} after this script completes")
	print(f"  2. Look for the {CYAN}'pii_columns'{RESET} field")
	print(f"  3. Add/remove columns as needed")
	print()
	print("=" * 80)
	print()

	# Wait for user confirmation (Option B: Verify-First)
	input(f"{YELLOW}Press ENTER to save and continue...{RESET} ")

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
	logger.info("=" * 80)
	logger.info("PII Discovery Script Started")
	logger.info("=" * 80)

	# Step 1: Load data profile
	data_profile_path = os.path.join(CONFIG_DIR, 'data_profile.json')

	if not os.path.exists(data_profile_path):
		logger.error(f"Data profile not found: {data_profile_path}")
		logger.error("Please run 'python -m src.data_pipeline.profiler' first.")
		return

	logger.info(f"Loading data profile from: {data_profile_path}")
	data_profile = load_data_profile(data_profile_path)

	# Step 2: Collect column samples
	logger.info("Collecting column samples...")
	column_data = collect_column_samples(data_profile)
	logger.info(f"Collected samples from {len(column_data)} tables")

	# Step 3: Detect PII using LLM (one-time call)
	detection_result = detect_pii_with_llm(column_data)

	# Step 4: Display report and wait for user confirmation
	display_report_and_confirm(detection_result, column_data)

	# Step 5: Save to schema_info.json
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
	logger.info(f"Saving PII detection results to: {schema_info_path}")
	with open(schema_info_path, 'w', encoding='utf-8') as f:
		json.dump(schema_info, f, indent=2, ensure_ascii=False)

	logger.info("=" * 80)
	logger.info(f"{GREEN}✓ PII Discovery Completed Successfully{RESET}")
	logger.info(f"PII columns saved to: {schema_info_path}")
	logger.info("=" * 80)
	print()
	print(f"{GREEN}✓ PII detection completed!{RESET}")
	print(f"Results saved to: {CYAN}{schema_info_path}{RESET}")
	print()


if __name__ == "__main__":
	main()