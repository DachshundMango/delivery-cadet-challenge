from graph import app
from pprint import pprint

inputs = {"user_question": "전체 데이터 개수가 몇 개야?"}

print("🚀 에이전트 출발! (Agent Started)\n")

for output in app.stream(inputs):
    for key, value in output.items():
        print(f"✅ Finished Node: {key}")
        pprint(value)
        print("---")

print("\n🏁 도착! (Finished)")