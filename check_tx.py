
import asyncio
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.config import settings

async def check_transactions():
    database_url = settings.SQLALCHEMY_DATABASE_URI
    engine = create_async_engine(database_url)
    
    user_id = 'fbd5a828-afdd-442c-b916-dbc31bea4155'
    
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT count(*) FROM transactions WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        count = result.scalar()
        print(f"Transaction count for user {user_id}: {count}")
        
        if count == 0:
            print("Inserting test transaction...")
            import uuid
            from datetime import datetime
            
            tx_id = str(uuid.uuid4())
            await conn.execute(
                text("""
                    INSERT INTO transactions (id, user_id, amount, currency, status, transaction_type, description, created_at, updated_at)
                    VALUES (:id, :user_id, 100.00, 'USD', 'completed', 'payment', 'Test Transaction', :now, :now)
                """),
                {
                    "id": tx_id,
                    "user_id": user_id,
                    "now": datetime.utcnow()
                }
            )
            await conn.commit()
            print(f"Inserted test transaction {tx_id}")
        
        result = await conn.execute(
            text("SELECT count(*) FROM transactions WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        print(f"New count: {result.scalar()}")

if __name__ == "__main__":
    asyncio.run(check_transactions())
