# backend/app/services/ai_agent.py
"""
Service to interact with the custom AI Agent container.
"""

import asyncio
import aiohttp
import json
import os
from typing import Dict, Any, Optional

from ..core.logging import get_logger

logger = get_logger(__name__)

class AIAgentService:
    """Service to communicate with the ai_agent container."""

    def __init__(self):
        # The URL for our custom AI agent service, configured in docker-compose.yml
        self.agent_base_url = os.getenv("AI_AGENT_URL", "http://localhost:8080")
        if not self.agent_base_url:
            raise ValueError("AI_AGENT_URL environment variable is not set.")

    async def _make_request(self, method: str, endpoint: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a generic request to the AI Agent service."""
        url = f"{self.agent_base_url}{endpoint}"
        logger.info(f"Making {method.upper()} request to AI Agent at: {url}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"AI Agent service returned an error: {response.status} - {error_text}")
                        raise Exception(f"AI Agent error: {error_text}")
        except asyncio.TimeoutError:
            logger.error(f"Request to AI Agent at {url} timed out.")
            raise Exception("AI Agent service timed out.")
        except Exception as e:
            logger.error(f"Error communicating with AI Agent at {url}: {e}")
            raise

    async def generate_business_insights(self, metrics_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate business insights from metrics data by calling the AI agent."""
        request_payload = {
            "user_id": "backend_service_user",  # Or pass a real user ID
            "query": "Generate business insights based on the following data.",
            "context_data": metrics_context,
            "insight_type": "business_overview",
            "priority": "normal"
        }
        return await self._make_request("post", "/insights", payload=request_payload)

    async def generate_financing_recommendations(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate financing recommendations by calling the AI agent."""
        # This endpoint doesn't exist yet on the ai_agent, so we'll simulate a call
        # In a real scenario, you would add a /financing-recommendations endpoint to the ai_agent
        logger.info("Simulating financing recommendations call to AI Agent.")
        # For now, just return a default structure or an empty dict
        return {"recommendations": [], "message": "Financing recommendations are under development."}

    async def chat_with_agent(self, user_message: str, session_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle conversational chat with the AI agent by passing backend context."""
        chat_payload = {
            "session_id": session_id,
            "message": user_message,
            "message_type": "query",
            # ADD THIS: Pass the backend metrics into the payload
            "context_data": context 
        }
        
        # Ensure your AI Agent container endpoint handles "context_data"
        return await self._make_request("post", "/chat", payload=chat_payload)

    async def get_health(self) -> Dict[str, Any]:
        """Check the health of the AI Agent service."""
        return await self._make_request("get", "/health")
