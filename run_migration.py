"""
Script to add missing subscription columns to the users table.
Run this script to fix the 'column users.subscription_start_date does not exist' error.
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "")

async def run_migration():
    # Parse the database URL to get connection parameters
    # Convert from SQLAlchemy format to asyncpg format
    db_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    print(f"Connecting to database...")
    
    try:
        conn = await asyncpg.connect(db_url)
        print("Connected successfully!")
        
        # List of ALTER TABLE statements
        migrations = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_start_date TIMESTAMP WITH TIME ZONE;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_end_date TIMESTAMP WITH TIME ZONE;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS billing_due_date TIMESTAMP WITH TIME ZONE;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_payment_date TIMESTAMP WITH TIME ZONE;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_payment_amount DOUBLE PRECISION;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS payment_provider VARCHAR(50);"
        ]
        
        for sql in migrations:
            print(f"Running: {sql[:60]}...")
            await conn.execute(sql)
            print("  Done!")
        
        await conn.close()
        print("\n✅ Migration completed successfully!")
        print("Please restart your backend server.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_migration())
