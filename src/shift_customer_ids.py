import os
import dotenv
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from load_data import DB_URL, get_engine

load_dotenv()

def main():
	
	engine = get_engine()

	print("CustomerID - 1,000,000 revision starts......")

	sql = """
	UPDATE sales_customers
	SET "customerID" = "customerID" - 1000000
	WHERE "customerID" >= 2000000;
	"""

	with engine.connect() as conn:

		conn.execute(text(sql))
		conn.commit()
		print("revison complieted.")

if __name__ == "__main__":
	main()

