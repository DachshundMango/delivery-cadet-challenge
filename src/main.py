from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langserve import add_routes
import uvicorn
from graph import app as graph_app

app = FastAPI(title="Delivery Cadet Agent")

# CORS 허용 (UI 접속용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LangGraph 연결
add_routes(app, graph_app, path="/agent")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


# from graph import app
# from pprint import pprint

# while True:
#     user_input = input("Ask questions (enter q if you want to exit): ")

#     if user_input.lower() == 'q':
#         print("Agent finished. See you!")
#         break 

#     inputs = {"user_question": user_input}

#     # Easy Questions:
#     # What are the top 3 most popular products by total quantity sold?
#     # How many customers are there in each continent?
#     # What payment methods are used and how often is each one used?

#     # Medium Questions:
#     # Which country generates the highest total revenue? Show all countries ranked by revenue?
#     # Who are the top 5 customers by total spending? Show their names and total amount spent?
#     # Which franchises have received the most customer reviews? List the top 5 franchise names with their review counts?

#     print("Agent starts! (Agent Started)\n")

#     for output in app.stream(inputs):
#         for key, value in output.items():
#             print(f"Node: {key}")
#             #pprint(value)
#             if str(key) in  ["generate_response", "generate_general_response"]:
#                 ai_message = value['messages'][-1].content
#                 print(f"\nAgent answers:\n{ai_message}")
    
#     print()