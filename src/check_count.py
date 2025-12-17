# src/check_count.py
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@localhost:5432/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)

def check_data():
    table = "sales_transactions" # 확인하고 싶은 테이블
    try:
        with engine.connect() as conn:
            # 개수 세기
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"\n📊 현재 '{table}' 테이블의 데이터 개수: {count}개")
            
            if count > 0:
                print("✅ 데이터가 있습니다! 에이전트 문제입니다.")
                # 샘플 데이터 1개 찍어보기
                sample = conn.execute(text(f"SELECT * FROM {table} LIMIT 1")).fetchall()
                print(f"🔎 샘플 데이터: {sample}")
            else:
                print("❌ 데이터가 0개입니다. load_data.py가 실패했었나 봅니다.")
                
    except Exception as e:
        print(f"⚠️ 에러 발생: {e}")

if __name__ == "__main__":
    check_data()