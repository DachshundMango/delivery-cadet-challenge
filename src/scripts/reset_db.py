# src/reset_db.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def reset_database():
    load_dotenv()
    
    # .env 설정 가져오기
    DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@localhost:5432/{os.getenv('DB_NAME')}"
    engine = create_engine(DB_URL)

    print(f"🧹 데이터베이스 '{os.getenv('DB_NAME')}' 초기화 시작...")

    try:
        with engine.connect() as conn:
            # 🔥 CASCADE 옵션으로 강제 삭제 (이게 핵심입니다!)
            tables = ["sales_transactions", "sales_customers", "sales_franchises", "sales_suppliers"]
            for table in tables:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
                print(f"   ✅ Table dropped: {table}")
            conn.commit()
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")

if __name__ == "__main__":
    reset_database()