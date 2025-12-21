"""
AI Agent Module for Embedded Finance Platform.
Provides LLaMA 3.2-powered financial insights and analytics for SMB retailers.
"""

from .llama_service import OllamaClient, ChatMessage, FinanceContext
from .ai_handlers import (
    AIAgentHandler,
    ChatSession,
    InsightRequest,
    ReportRequest
)

__version__ = "1.0.0"
__author__ = "Finance Platform Team"

# Export main classes
__all__ = [
    "OllamaClient",
    "ChatMessage", 
    "FinanceContext",
    "AIAgentHandler",
    "ChatSession",
    "InsightRequest",
    "ReportRequest"
]

# Default configuration
DEFAULT_CONFIG = {
    "ollama_base_url": "http://localhost:11434",
    "model_name": "llama3.2",
    "session_timeout": 3600,  # 1 hour
    "max_sessions": 1000,
    "max_retries": 3,
    "timeout": 120
}