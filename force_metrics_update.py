import asyncio
import os
import sys

# Add backend directory to python path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.database import async_session_maker
from app.services.analytics_engine import AnalyticsEngine
from app.services.ai_agent import AIAgentService

async def force_update():
    user_id = "fbd5a828-afdd-442c-b916-dbc31bea4155"
    print(f"Forcing metrics update for user: {user_id}")
    
    async with async_session_maker() as session:
        ai_service = AIAgentService()
        analytics = AnalyticsEngine(session, ai_service)
        
        try:
            metrics = await analytics.update_business_metrics(user_id)
            print("Successfully updated metrics!")
            print(f"New Monthly Revenue (USD): {metrics.monthly_revenue}")
            print(f"New Cash Flow (USD): {metrics.cash_flow}")
        except Exception as e:
            print(f"Error updating metrics: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(force_update())
