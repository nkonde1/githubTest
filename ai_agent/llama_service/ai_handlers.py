"""
AI Agent Request Handlers for Finance Platform.
Handles different types of AI-powered requests and integrates with backend services.
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import aiohttp

from llama_service.llama_service import OllamaClient, ChatMessage, FinanceContext

logger = logging.getLogger(__name__)

# Use environment variable for backend URL, with a fallback for local dev
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://backend:8000/api/v1")

@dataclass
class ChatSession:
    session_id: str
    user_id: str
    messages: List[ChatMessage]
    context: Optional[FinanceContext]
    created_at: datetime
    last_activity: datetime
    preferences: Dict[str, Any]

class AIAgentHandler:
    def __init__(
        self,
        ollama_client: OllamaClient,
        session_timeout: int = 3600,
        max_sessions: int = 1000
    ):
        self.ollama_client = ollama_client
        self.session_timeout = session_timeout
        self.max_sessions = max_sessions
        self.active_sessions: Dict[str, ChatSession] = {}
        self._cleanup_task = None

    async def start(self):
        logger.info("Starting AI Agent Handler")
        self._cleanup_task = asyncio.create_task(self._cleanup_sessions())

    async def stop(self):
        logger.info("Stopping AI Agent Handler")
        if self._cleanup_task:
            self._cleanup_task.cancel()

    async def _cleanup_sessions(self):
        while True:
            await asyncio.sleep(300)
            # Session cleanup logic

    def get_chat_session(self, session_id: str) -> Optional[ChatSession]:
        return self.active_sessions.get(session_id)

    async def get_or_create_session(self, session_id: str, user_id: str) -> ChatSession:
        session = self.get_chat_session(session_id)
        if session:
            session.last_activity = datetime.utcnow()
            return session
        
        session = ChatSession(
            session_id=session_id, user_id=user_id, messages=[], context=None,
            created_at=datetime.utcnow(), last_activity=datetime.utcnow(), preferences={}
        )
        self.active_sessions[session_id] = session
        logger.info(f"Created chat session {session_id} for user {user_id}")
        return session

    async def fetch_and_inject_context(self, session: ChatSession):
        if not session.user_id:
            return
        
        try:
            # Corrected the endpoint to /business-metrics
            api_url = f"{BACKEND_API_URL}/metrics/business-metrics?user_id={session.user_id}"
            logger.info(f"Fetching context from {api_url}")
            async with aiohttp.ClientSession() as http_session:
                async with http_session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Assuming the data is a list of metrics, take the first one
                        metrics = data[0] if data else {}
                        session.context = FinanceContext(
                            revenue_data={"total": metrics.get("monthly_revenue", 0)},
                            expense_data={"total": metrics.get("monthly_expenses", 0)},
                            cash_flow={"avg_transaction": metrics.get("avg_order_value", 0)},
                            trends={"profit_margin": metrics.get("profit_margin", 0)},
                            kpis={
                                "credit_score": metrics.get("credit_score", "N/A"),
                                "customer_count": metrics.get("customer_count", 0)
                            },
                            user_profile={"business_name": "Your Business"} # Placeholder
                        )
                        logger.info(f"Successfully injected context for user {session.user_id}.")
                    else:
                        logger.error(f"Failed to fetch metrics for user {session.user_id}, status: {response.status}")
        except Exception as e:
            logger.error(f"Context fetch error for user {session.user_id}: {e}", exc_info=True)


    async def process_chat_message(self, session_id: str, message: str, user_id_for_creation: Optional[str] = None):
        session = self.get_chat_session(session_id)
        if not session:
            if not user_id_for_creation:
                raise ValueError("User ID is required to create a new session.")
            session = await self.get_or_create_session(session_id, user_id_for_creation)
        
        if not session.context:
            await self.fetch_and_inject_context(session)

        user_message = ChatMessage(role="user", content=message, timestamp=datetime.utcnow())
        session.messages.append(user_message)

        response_text = await self.ollama_client.generate_response(
            messages=session.messages[-10:], context=session.context
        )

        ai_message = ChatMessage(role="assistant", content=response_text, timestamp=datetime.utcnow())
        session.messages.append(ai_message)

        return {
            "response": response_text,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "has_context": session.context is not None
        }
