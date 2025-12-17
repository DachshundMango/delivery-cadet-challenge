from graph import app
from pprint import pprint

inputs = {"user_question": "What are the top 3 most popular products by total quantity sold?"}

print("🚀 Agent starts! (Agent Started)\n")

for output in app.stream(inputs):
    for key, value in output.items():
        print(f"✅ Finished Node: {key}")
        pprint(value)
        print("---")

print("\n🏁 Finished!")