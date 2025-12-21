import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres:agent2025@localhost:5432/financial_ai_db"

async def add_column():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE business_metrics ADD COLUMN credit_score INTEGER;"))
            print("Successfully added credit_score column.")
        except Exception as e:
            print(f"Error adding column: {e}")
            # It might fail if column already exists, which is fine.
            if "already exists" in str(e):
                print("Column already exists.")

if __name__ == "__main__":
    asyncio.run(add_column())
