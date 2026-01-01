import sys
import os
import logging

# Add project root to path for consistent imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.graph import app
from pprint import pprint
from langchain_core.messages import HumanMessage

# Disable INFO and DEBUG logging globally for clean CLI output
logging.disable(logging.INFO)

while True:
    user_input = input("Ask questions (enter q if you want to exit): ")

    if user_input.lower() == 'q':
        print("Agent finished. See you!")
        break

    inputs = {"messages": [HumanMessage(content=user_input)]}

    print("\nProcessing...\n")

    for output in app.stream(inputs):
        for key, value in output.items():
            # KEY = "generate_SQL" -> Show generated SQL
            if str(key) == "generate_SQL":
                sql = value.get('sql_query', '')
                if sql:
                    print("Generated SQL:")
                    print("-" * 60)
                    print(sql)
                    print("-" * 60)

            # KEY = "execute_SQL" -> Show query results
            elif str(key) == "execute_SQL":
                result = value.get('query_result', '')
                if result and not result.startswith("Error:"):
                    # Count rows if result is a list
                    try:
                        import json
                        data = json.loads(result) if isinstance(result, str) else result
                        if isinstance(data, list):
                            print(f"Query executed: {len(data)} rows returned\n")
                    except:
                        print("Query executed successfully\n")
                elif result and result.startswith("Error:"):
                    print(f"Query error: {result}\n")

            # KEY = "generate_response" or "generate_general_response" -> Show final answer
            elif str(key) in ["generate_response", "generate_general_response"]:
                ai_message = value['messages'][-1].content
                print("Answer:")
                print(ai_message)

    print()