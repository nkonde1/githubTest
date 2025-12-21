from sqlalchemy import create_engine, text

# Use sync driver (psycopg2 is default for postgresql://)
DATABASE_URL = "postgresql://postgres:agent2025@localhost:5432/financial_ai_db"

def add_column():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            with conn.begin():
                conn.execute(text("ALTER TABLE business_metrics ADD COLUMN credit_score INTEGER;"))
        print("Successfully added credit_score column.")
    except Exception as e:
        print(f"Error adding column: {e}")
        if "already exists" in str(e):
            print("Column already exists.")

if __name__ == "__main__":
    add_column()
