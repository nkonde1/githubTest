"""
Ollama LLaMA 3.2 Client for AI-powered finance insights and analytics.
Handles communication with Ollama service for generating context-aware responses.
"""

import asyncio
import json
import logging
import aiohttp
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import os
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "ollama_base_url": "http://localhost:11434",  # Or whatever your default Ollama URL is
    "model_name": "llama3.2",
    "max_retries": 3,  # Default model name
    "timeout": 60, # Default timeout in seconds
    "session_timeout": 3600,  # Default session timeout in seconds
    "max_sessions": 1000  # Maximum number of concurrent sessions
    # Add other default configuration items here if needed
}

@dataclass
class ChatMessage:
    """Represents a chat message with role and content."""
    role: str  # 'system', 'user', 'assistant'
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
        timeout: int = 120
    ):
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.max_retries = max_retries
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Load system prompts
        self.prompts_dir = Path(__file__).parent / "prompts"
        self.system_prompts = self._load_system_prompts()
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _load_system_prompts(self) -> Dict[str, str]:
        """Load system prompts from files."""
        prompts = {}
        try:
            # Load finance insights prompt
            finance_prompt_path = self.prompts_dir / "finance_insights_prompt.txt"
            if finance_prompt_path.exists():
                with open(finance_prompt_path, 'r', encoding='utf-8') as f:
                    prompts['finance_insights_prompt'] = f.read().strip()
            
            # Load analytics questions prompt
            analytics_prompt_path = self.prompts_dir / "analytics_questions_prompt.txt"
            if analytics_prompt_path.exists():
                with open(analytics_prompt_path, 'r', encoding='utf-8') as f:
                    prompts['analytics_questions_prompt'] = f.read().strip()
                    
        except Exception as e:
            logger.error(f"Error loading system prompts: {e}")
            
        return prompts
    
    async def health_check(self) -> bool:
        """Check if Ollama service is available."""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(timeout=self.timeout)
                
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    async def list_models(self) -> List[str]:
        """List available models in Ollama."""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(timeout=self.timeout)
                
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    return [model['name'] for model in data.get('models', [])]
                return []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    async def pull_model(self, model_name: Optional[str] = None) -> bool:
        """Pull/download a model if not available."""
        model = model_name or self.model_name
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(timeout=self.timeout)
                
            payload = {"name": model}
            async with self.session.post(
                f"{self.base_url}/api/pull",
                json=payload
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Error pulling model {model}: {e}")
            return False
    
    async def generate_response(
        self,
        messages: List[ChatMessage],
        context: Optional[FinanceContext] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> str:
        """
        Generate AI response using LLaMA 3.2 with financial context.
        
        Args:
            messages: List of chat messages
            context: Financial context data
            temperature: Response creativity (0.0-1.0)
            max_tokens: Maximum response length
            stream: Whether to stream response
            
        Returns:
            Generated response text
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(timeout=self.timeout)
            
            # Prepare system message with context
            system_message = self._build_system_message(context)
            
            # Format messages for Ollama
            formatted_messages = [{"role": "system", "content": system_message}]
            formatted_messages.extend([
                {"role": msg.role, "content": msg.content} 
                for msg in messages
            ])
            
            payload = {
                "model": self.model_name,
                "messages": formatted_messages,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                "stream": stream
            }
            
            for attempt in range(self.max_retries):
                try:
                    async with self.session.post(
                        f"{self.base_url}/api/chat",
                        json=payload
                    ) as response:
                        if response.status == 200:
                            if stream:
                                return await self._handle_streaming_response(response)
                            else:
                                data = await response.json()
                                return data.get('message', {}).get('content', '')
                        else:
                            error_text = await response.text()
                            logger.error(f"Ollama API error: {response.status} - {error_text}")
                            
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout on attempt {attempt + 1}")
                    if attempt == self.max_retries - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
                except Exception as e:
                    logger.error(f"Error on attempt {attempt + 1}: {e}")
                    if attempt == self.max_retries - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)
            
            return "I apologize, but I'm unable to process your request at the moment. Please try again later."
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I encountered an error while processing your request. Please contact support if this persists."
    
    async def _handle_streaming_response(self, response: aiohttp.ClientResponse) -> str:
        """Handle streaming response from Ollama."""
        content = ""
        async for line in response.content:
            try:
                line_str = line.decode('utf-8').strip()
                if line_str:
                    data = json.loads(line_str)
                    if 'message' in data and 'content' in data['message']:
                        content += data['message']['content']
                    if data.get('done', False):
                        break
            except json.JSONDecodeError:
                continue
        return content
    
    def _build_system_message(self, context: Optional[FinanceContext] = None) -> str:
        """Build system message with financial context."""
        base_prompt = self.system_prompts.get('finance_insights_prompt', """
You are an AI financial advisor and analytics expert specializing in SMB retail businesses.
You provide actionable insights, recommendations, and analysis based on financial data.
Always be specific, data-driven, and practical in your responses.
""")
        
        if not context:
            return base_prompt
        
        context_info = f"""
        
CURRENT FINANCIAL CONTEXT:
- Revenue Trends: {json.dumps(context.revenue_data, indent=2)}
- Expense Analysis: {json.dumps(context.expense_data, indent=2)}
- Cash Flow: {json.dumps(context.cash_flow, indent=2)}
- Key Trends: {json.dumps(context.trends, indent=2)}
- KPIs: {json.dumps(context.kpis, indent=2)}
- Business Profile: {json.dumps(context.user_profile, indent=2)}

IMPORTANT: Analyze ALL available data provided in the context. When the user asks about totals, revenues, or comprehensive metrics, use the COMPLETE dataset. Check for date_range information to understand the scope of data available. Do NOT limit analysis to recent periods unless explicitly requested.

Use this context to provide relevant, personalized financial insights and recommendations.
Focus on actionable advice that can improve business performance.
"""
        
        return base_prompt + context_info
    
    async def analyze_financial_data(
        self,
        context: FinanceContext,
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Perform AI-powered financial analysis.
        
        Args:
            context: Financial context data
            analysis_type: Type of analysis (comprehensive, cash_flow, profitability, etc.)
            
        Returns:
            Analysis results with insights and recommendations
        """
        try:
            # Create specific prompt for financial analysis
            analysis_prompt = f"""
Analyze the provided financial data and provide a {analysis_type} analysis.
Include:
1. Key findings and trends
2. Areas of concern or opportunity
3. Specific actionable recommendations
4. Risk assessment
5. Growth opportunities

Please structure your response as JSON with the following format:
{{
    "summary": "Brief overview",
    "key_findings": ["finding1", "finding2", ...],
    "recommendations": ["rec1", "rec2", ...],
    "risks": ["risk1", "risk2", ...],
    "opportunities": ["opp1", "opp2", ...],
    "confidence_score": 0.85
}}
"""
            
            messages = [ChatMessage(role="user", content=analysis_prompt)]
            response = await self.generate_response(messages, context, temperature=0.3)
            
            # Try to parse JSON response
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # Fallback to text response
                return {
                    "summary": response,
                    "key_findings": [],
                    "recommendations": [],
                    "risks": [],
                    "opportunities": [],
                    "confidence_score": 0.5
                }
                
        except Exception as e:
            logger.error(f"Error in financial analysis: {e}")
            return {
                "error": "Analysis failed",
                "summary": "Unable to complete analysis at this time",
                "key_findings": [],
                "recommendations": [],
                "risks": [],
                "opportunities": [],
                "confidence_score": 0.0
            }
    
    async def generate_insights(
        self,
        query: str,
        context: Optional[FinanceContext] = None,
        insight_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Generate specific financial insights based on user query.
        
        Args:
            query: User's question or request
            context: Financial context data
            insight_type: Type of insight (general, forecasting, optimization, etc.)
            
        Returns:
            Structured insights response
        """
        try:
            enhanced_query = f"""
Query: {query}
Insight Type: {insight_type}

Please provide a comprehensive response that includes:
1. Direct answer to the query
2. Supporting data analysis
3. Actionable recommendations
4. Related insights that might be valuable

Format your response as JSON:
{{
    "answer": "Direct answer to the query",
    "analysis": "Supporting analysis",
    "recommendations": ["rec1", "rec2", ...],
    "related_insights": ["insight1", "insight2", ...],
    "confidence": 0.85
}}
"""
            
            messages = [ChatMessage(role="user", content=enhanced_query)]
            response = await self.generate_response(messages, context, temperature=0.5)
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {
                    "answer": response,
                    "analysis": "",
                    "recommendations": [],
                    "related_insights": [],
                    "confidence": 0.5
                }
                
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return {
                "error": "Failed to generate insights",
                "answer": "I apologize, but I couldn't process your request at this time.",
                "analysis": "",
                "recommendations": [],
                "related_insights": [],
                "confidence": 0.0
            }