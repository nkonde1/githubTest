"""
AI Agent Request Handlers for Finance Platform.
Handles different types of AI-powered requests and integrates with backend services.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json

from llama_service.llama_service import OllamaClient, ChatMessage, FinanceContext

logger = logging.getLogger(__name__)

@dataclass
class ChatSession:
    """Represents a user's chat session with the AI agent."""
    session_id: str
    user_id: str
    messages: List[ChatMessage]
    context: Optional[FinanceContext]
    created_at: datetime
    last_activity: datetime
    preferences: Dict[str, Any]

@dataclass
class InsightRequest:
    """Request for financial insights."""
    user_id: str
    query: str
    context_data: Dict[str, Any]
    insight_type: str
    priority: str = "normal"  # low, normal, high, urgent
    
@dataclass
class ReportRequest:
    """Request for financial report generation."""
    user_id: str
    report_type: str  # daily, weekly, monthly, quarterly, custom
    date_range: Tuple[datetime, datetime]
    metrics: List[str]
    format: str = "text"  # text, json, html

class AIAgentHandler:
    """
    Main handler for AI agent functionality.
    Manages chat sessions, insights generation, and report creation.
    """
    
    def __init__(
        self,
        ollama_client: OllamaClient,
        session_timeout: int = 3600,  # 1 hour
        max_sessions: int = 1000
    ):
        self.ollama_client = ollama_client
        self.session_timeout = session_timeout
        self.max_sessions = max_sessions
        
        # In-memory session storage (use Redis in production)
        self.active_sessions: Dict[str, ChatSession] = {}
        
        # Background task for session cleanup
        self._cleanup_task = None
        
    async def start(self):
        """Start the AI agent handler."""
        logger.info("Starting AI Agent Handler")
        
        # Start session cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_sessions())
        
        # Verify Ollama connection
        if not await self.ollama_client.health_check():
            logger.warning("Ollama service not available - some features may be limited")
        
    async def stop(self):
        """Stop the AI agent handler."""
        logger.info("Stopping AI Agent Handler")
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def _cleanup_sessions(self):
        """Background task to clean up expired sessions."""
        while True:
            try:
                current_time = datetime.utcnow()
                expired_sessions = []
                
                for session_id, session in self.active_sessions.items():
                    if (current_time - session.last_activity).total_seconds() > self.session_timeout:
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    del self.active_sessions[session_id]
                    logger.debug(f"Cleaned up expired session: {session_id}")
                
                # Sleep for 5 minutes before next cleanup
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def create_chat_session(
        self,
        session_id: str,
        user_id: str,
        initial_context: Optional[Dict[str, Any]] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> ChatSession:
        """Create a new chat session."""
        
        # Clean up old sessions if we're at max capacity
        if len(self.active_sessions) >= self.max_sessions:
            oldest_session = min(
                self.active_sessions.values(),
                key=lambda s: s.last_activity
            )
            del self.active_sessions[oldest_session.session_id]
        
        # Create finance context if data provided
        context = None
        if initial_context:
            context = FinanceContext(
                revenue_data=initial_context.get('revenue_data', {}),
                expense_data=initial_context.get('expense_data', {}),
                cash_flow=initial_context.get('cash_flow', {}),
                trends=initial_context.get('trends', {}),
                kpis=initial_context.get('kpis', {}),
                user_profile=initial_context.get('user_profile', {})
            )
        
        session = ChatSession(
            session_id=session_id,
            user_id=user_id,
            messages=[],
            context=context,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            preferences=preferences or {}
        )
        
        self.active_sessions[session_id] = session
        logger.info(f"Created chat session {session_id} for user {user_id}")
        
        return session
    
    async def get_chat_session(self, session_id: str) -> Optional[ChatSession]:
        """Get an existing chat session."""
        session = self.active_sessions.get(session_id)
        if session:
            session.last_activity = datetime.utcnow()
        return session
    
    async def update_session_context(
        self,
        session_id: str,
        context_data: Dict[str, Any]
    ) -> bool:
        """Update the financial context for a session."""
        session = await self.get_chat_session(session_id)
        if not session:
            return False
        
        session.context = FinanceContext(
            revenue_data=context_data.get('revenue_data', {}),
            expense_data=context_data.get('expense_data', {}),
            cash_flow=context_data.get('cash_flow', {}),
            trends=context_data.get('trends', {}),
            kpis=context_data.get('kpis', {}),
            user_profile=context_data.get('user_profile', {})
        )
        
        logger.debug(f"Updated context for session {session_id}")
        return True
    
    async def process_chat_message(
        self,
        session_id: str,
        message: str,
        message_type: str = "query"
    ) -> Dict[str, Any]:
        """
        Process a chat message and generate AI response.
        
        Args:
            session_id: Chat session ID
            message: User's message
            message_type: Type of message (query, command, feedback)
            
        Returns:
            Response dictionary with AI response and metadata
        """
        try:
            session = await self.get_chat_session(session_id)
            if not session:
                return {
                    "error": "Session not found",
                    "response": "Please start a new conversation.",
                    "session_expired": True
                }
            
            # Add user message to session
            user_message = ChatMessage(
                role="user",
                content=message,
                timestamp=datetime.utcnow()
            )
            session.messages.append(user_message)
            
            # Generate AI response
            response_text = await self.ollama_client.generate_response(
                messages=session.messages[-10:],  # Keep last 10 messages for context
                context=session.context,
                temperature=0.7
            )
            
            # Add AI response to session
            ai_message = ChatMessage(
                role="assistant",
                content=response_text,
                timestamp=datetime.utcnow()
            )
            session.messages.append(ai_message)
            
            # Determine response type and extract metadata
            response_metadata = await self._analyze_response_metadata(
                response_text, message_type
            )
            
            return {
                "response": response_text,
                "metadata": response_metadata,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message_count": len(session.messages)
            }
            
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            return {
                "error": "Processing failed",
                "response": "I apologize, but I encountered an error processing your message. Please try again.",
                "session_id": session_id
            }
    
    async def _analyze_response_metadata(
        self,
        response: str,
        message_type: str
    ) -> Dict[str, Any]:
        """Analyze response to extract metadata and classify response type."""
        metadata = {
            "response_type": "general",
            "confidence": 0.7,
            "contains_recommendations": False,
            "contains_data": False,
            "actionable_items": [],
            "follow_up_suggestions": []
        }
        
        # Simple keyword-based analysis (could be enhanced with ML)
        response_lower = response.lower()
        
        # Detect response type
        if any(word in response_lower for word in ["recommend", "suggest", "should", "consider"]):
            metadata["response_type"] = "recommendation"
            metadata["contains_recommendations"] = True
        
        if any(word in response_lower for word in ["$", "%", "increase", "decrease", "profit", "revenue"]):
            metadata["contains_data"] = True
        
        if any(word in response_lower for word in ["forecast", "predict", "trend", "projection"]):
            metadata["response_type"] = "forecast"
        
        # Extract actionable items (simplified)
        lines = response.split('\n')
        for line in lines:
            line_lower = line.lower().strip()
            if any(action in line_lower for action in ["action:", "todo:", "next step:", "implement"]):
                metadata["actionable_items"].append(line.strip())
        
        return metadata
    
    async def generate_financial_insights(
        self,
        request: InsightRequest
    ) -> Dict[str, Any]:
        """Generate financial insights based on request."""
        try:
            # Create finance context from request data
            context = FinanceContext(
                revenue_data=request.context_data.get('revenue_data', {}),
                expense_data=request.context_data.get('expense_data', {}),
                cash_flow=request.context_data.get('cash_flow', {}),
                trends=request.context_data.get('trends', {}),
                kpis=request.context_data.get('kpis', {}),
                user_profile=request.context_data.get('user_profile', {})
            )
            
            # Generate insights using Ollama
            insights = await self.ollama_client.generate_insights(
                query=request.query,
                context=context,
                insight_type=request.insight_type
            )
            
            return {
                "status": "success",
                "insights": insights,
                "request_id": f"insight_{datetime.utcnow().timestamp()}",
                "generated_at": datetime.utcnow().isoformat(),
                "user_id": request.user_id
            }
            
        except Exception as e:
            logger.error(f"Error generating financial insights: {e}")
            return {
                "status": "error",
                "error": str(e),
                "insights": {
                    "answer": "Unable to generate insights at this time.",
                    "analysis": "",
                    "recommendations": [],
                    "related_insights": [],
                    "confidence": 0.0
                }
            }
    
    async def generate_financial_report(
        self,
        request: ReportRequest
    ) -> Dict[str, Any]:
        """Generate automated financial reports."""
        try:
            # Create report generation prompt
            report_prompt = f"""
Generate a comprehensive {request.report_type} financial report for the period from {request.date_range[0].strftime('%Y-%m-%d')} to {request.date_range[1].strftime('%Y-%m-%d')}.

Include the following metrics: {', '.join(request.metrics)}

Structure the report with:
1. Executive Summary
2. Key Metrics Overview
3. Trend Analysis
4. Performance Highlights
5. Areas for Improvement
6. Recommendations
7. Outlook

Format: {request.format}
"""
            
            # Generate report using AI
            messages = [ChatMessage(role="user", content=report_prompt)]
            report_content = await self.ollama_client.generate_response(
                messages=messages,
                temperature=0.3  # Lower temperature for more consistent reports
            )
            
            return {
                "status": "success",
                "report": {
                    "content": report_content,
                    "type": request.report_type,
                    "period": f"{request.date_range[0].strftime('%Y-%m-%d')} to {request.date_range[1].strftime('%Y-%m-%d')}",
                    "metrics": request.metrics,
                    "format": request.format
                },
                "generated_at": datetime.utcnow().isoformat(),
                "user_id": request.user_id
            }
            
        except Exception as e:
            logger.error(f"Error generating financial report: {e}")
            return {
                "status": "error",
                "error": str(e),
                "report": None
            }
    
    async def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """Generate a summary of the conversation."""
        try:
            session = await self.get_chat_session(session_id)
            if not session or not session.messages:
                return {"error": "No conversation found"}
            
            # Create summary prompt
            conversation_text = "\n".join([
                f"{msg.role}: {msg.content}" for msg in session.messages[-20:]  # Last 20 messages
            ])
            
            summary_prompt = f"""
Summarize the following financial conversation:

{conversation_text}

Provide:
1. Main topics discussed
2. Key insights shared
3. Recommendations made
4. Action items identified
5. User's primary concerns

Keep the summary concise and focused on actionable information.
"""
            
            messages = [ChatMessage(role="user", content=summary_prompt)]
            summary = await self.ollama_client.generate_response(
                messages=messages,
                temperature=0.3
            )
            
            return {
                "status": "success",
                "summary": summary,
                "message_count": len(session.messages),
                "session_duration": (session.last_activity - session.created_at).total_seconds(),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating conversation summary: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about active sessions."""
        return {
            "active_sessions": len(self.active_sessions),
            "max_sessions": self.max_sessions,
            "session_timeout": self.session_timeout,
            "total_messages": sum(len(s.messages) for s in self.active_sessions.values()),
            "ollama_healthy": await self.ollama_client.health_check()
        }