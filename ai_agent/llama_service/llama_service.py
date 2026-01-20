"""
Ollama LLaMA 3.2 Client for AI-powered finance insights and analytics.
Handles communication with Ollama service for generating context-aware responses.
"""

import asyncio
import json
import logging
import aiohttp
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import os
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "ollama_base_url": "http://localhost:11434",
    "model_name": "llama3.2",
    "max_retries": 3,
    "startup_retries": 5,
    "startup_delay": 3,
    "timeout": 60,
    "session_timeout": 3600,
    "max_sessions": 1000
}

@dataclass
class ChatMessage:
    """Represents a chat message with role and content."""
    role: str
    content: str
    timestamp: Optional[datetime] = None

@dataclass
class FinanceContext:
    """Financial context data for AI agent."""
    revenue_data: Dict[str, Any]
    expense_data: Dict[str, Any]
    cash_flow: Dict[str, Any]
    trends: Dict[str, Any]
    kpis: Dict[str, Any]
    user_profile: Dict[str, Any]

class OllamaClient:
    """
    Async client for interacting with Ollama LLaMA 3.2 model.
    Provides finance-specific AI capabilities for SMB retailers.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "llama3.2",
        max_retries: int = 3,
        timeout: int = 120,
        startup_retries: int = 5,
        startup_delay: int = 3
    ):
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.max_retries = max_retries
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
        self.startup_retries = startup_retries
        self.startup_delay = startup_delay
        self._is_connected = False
        
        self.prompts_dir = Path(__file__).parent / "prompts"
        self.system_prompts = self._load_system_prompts()
        
    async def __aenter__(self):
        """Async context manager entry, now more resilient."""
        for attempt in range(self.startup_retries):
            try:
                self.session = aiohttp.ClientSession(timeout=self.timeout)
                if await self.health_check():
                    logger.info("Ollama connection successful.")
                    self._is_connected = True
                    return self
                else:
                    logger.warning(f"Ollama health check failed on attempt {attempt + 1}.")
                    await self.session.close() # Close the unsuccessful session
            except Exception as e:
                logger.warning(f"Ollama connection attempt {attempt + 1} failed with exception: {e}")
                if self.session and not self.session.closed:
                    await self.session.close()
            
            if attempt < self.startup_retries - 1:
                await asyncio.sleep(self.startup_delay)
        
        logger.error("Ollama connection failed after multiple retries. The service will start in a degraded state.")
        self.session = None # Ensure session is None if connection failed
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _load_system_prompts(self) -> Dict[str, str]:
        """Load system prompts from files."""
        prompts = {}
        try:
            finance_prompt_path = self.prompts_dir / "finance_insights_prompt.txt"
            if finance_prompt_path.exists():
                with open(finance_prompt_path, 'r', encoding='utf-8') as f:
                    prompts['finance_insights_prompt'] = f.read().strip()
            
            analytics_prompt_path = self.prompts_dir / "analytics_questions_prompt.txt"
            if analytics_prompt_path.exists():
                with open(analytics_prompt_path, 'r', encoding='utf-8') as f:
                    prompts['analytics_questions_prompt'] = f.read().strip()
                    
        except Exception as e:
            logger.error(f"Error loading system prompts: {e}")
            
        return prompts
    
    async def health_check(self) -> bool:
        """Check if Ollama service is available."""
        if not self.session or self.session.closed:
             return False
        try:
            async with self.session.get(f"{self.base_url}/api/tags", timeout=5) as response:
                return response.status == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False

    def is_connected(self) -> bool:
        """Returns the connection status."""
        return self._is_connected

    async def generate_response(
        self,
        messages: List[ChatMessage],
        context: Optional[FinanceContext] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> str:
        if not self.is_connected() or not self.session:
            logger.error("Cannot generate response: Ollama client is not connected.")
            return "I'm sorry, but I'm currently unable to connect to my core AI service. Please try again later."
        
        try:
            system_message = self._build_system_message(context)
            
            # Convert ChatMessage objects to dictionaries for the API call, excluding timestamp
            dict_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

            formatted_messages = [{"role": "system", "content": system_message}] + dict_messages
            
            payload = {
                "model": self.model_name,
                "messages": formatted_messages,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                "stream": stream
            }
            
            async with self.session.post(f"{self.base_url}/api/chat", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('message', {}).get('content', '')
                else:
                    error_text = await response.text()
                    logger.error(f"Ollama API error: {response.status} - {error_text}")
                    return "I encountered an API error. Please check the service logs."
        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            return "An unexpected error occurred while generating a response."

    def _build_system_message(self, context: Optional[FinanceContext] = None) -> str:
        """Builds the system prompt based on whether financial context is available."""
        
        base_prompt = self.system_prompts.get('finance_insights_prompt', "You are a helpful assistant.")

        if not context:
            return (
                f"{base_prompt} "
                "You do not have financial data. Inform the user you are waiting for data."
            )

        stats = {
            "business": context.user_profile.get("business_name", "the business"),
            "total_revenue_zmw": context.revenue_data.get("total"),
            "transaction_count": context.expense_data.get("total"),
            "avg_sale_zmw": context.cash_flow.get("avg_transaction"),
            "credit_score": context.kpis.get("credit_score", "N/A")
        }

        valid_stats = {k: v for k, v in stats.items() if v is not None}
        
        context_prompt = (
            "Use ONLY the following real-time data to answer questions. Do not invent values.\n"
            f"DATABASE_VALUES: {json.dumps(valid_stats)}"
        )

        rules = self.system_prompts.get('analytics_questions_prompt', "Be accurate.")

        return f"""{base_prompt}\n{context_prompt}\n\n{rules}\n"""
