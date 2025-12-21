import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.analytics_engine import AnalyticsEngine
from app.services.ai_agent import AIAgentService
from app.core.config import settings
import asyncio

async def generate_metrics():
    # Setup async database connection
    engine = create_async_engine(
        settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://'),
        echo=True
    )
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as db:
        try:
            # Initialize services
            ai_service = AIAgentService()
            analytics = AnalyticsEngine(db, ai_service)
            
            # Generate metrics for user
            user_id = "40348185-dac8-4dca-be0c-5748e27fd6a3"
            metrics = await analytics.update_business_metrics(user_id)
            print(f"Generated metrics: {metrics}")
        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            await db.close()
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(generate_metrics())