from graph import app
from pprint import pprint


while True:
    user_input = input("Ask questions (enter q if you want to exit): ")

    if user_input.lower() == 'q':
        print("Agent finished. See you!")
        break 

    inputs = {"user_question": user_input}

    # Easy Questions:
    # What are the top 3 most popular products by total quantity sold?
    # How many customers are there in each continent?
    # What payment methods are used and how often is each one used?

    # Medium Questions:
    # Which country generates the highest total revenue? Show all countries ranked by revenue?
    # Who are the top 5 customers by total spending? Show their names and total amount spent?
    # Which franchises have received the most customer reviews? List the top 5 franchise names with their review counts?

    print("Agent starts! (Agent Started)\n")

    for output in app.stream(inputs):
        for key, value in output.items():
            print(f"Node: {key}")
            #pprint(value)

            # DEBUG: SQL 실행 결과 타입 확인
            # if str(key) == "execute_SQL":
            #     query_result = value.get('query_result')
            #     print(f"\n=== DEBUG: execute_SQL output ===")
            #     print(f"Raw query_result type: {type(query_result)}")
            #     print(f"Raw query_result value: {query_result}")
            #     print(f"=================================\n")

            if str(key) in  ["generate_response", "generate_general_response"]:
                ai_message = value['messages'][-1].content
                print(f"\nAgent answers:\n{ai_message}")
    
    print()