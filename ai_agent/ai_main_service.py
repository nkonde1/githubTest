"""
Main entry point for AI Agent service.
Provides FastAPI endpoints for LLaMA 3.2 powered financial insights.
"""

import asyncio
import logging
import os
import signal
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime
from llama_service.ai_handlers import ChatSession, InsightRequest, ReportRequest, AIAgentHandler
from llama_service.llama_service import (
    OllamaClient,
    ChatMessage,
    FinanceContext,
    DEFAULT_CONFIG
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
ollama_client: Optional[OllamaClient] = None
ai_handler: Optional[AIAgentHandler] = None

# Pydantic models for API
class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Chat session ID")
    message: str = Field(..., description="User message")
    message_type: str = Field(default="query", description="Message type")

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str
    metadata: Dict[str, Any]
    message_count: int

class SessionCreateRequest(BaseModel):
    session_id: str = Field(..., description="Unique session ID")
    user_id: str = Field(..., description="User ID")
    initial_context: Optional[Dict[str, Any]] = Field(None, description="Initial financial context")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")

class InsightGenerationRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    query: str = Field(..., description="Insight query")
    context_data: Dict[str, Any] = Field(..., description="Financial context data")
    insight_type: str = Field(default="general", description="Type of insight")
    priority: str = Field(default="normal", description="Request priority")

class ReportGenerationRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    report_type: str = Field(..., description="Report type")
    start_date: datetime = Field(..., description="Report start date")
    end_date: datetime = Field(..., description="Report end date")
    metrics: List[str] = Field(..., description="Metrics to include")
    format: str = Field(default="text", description="Report format")

class ContextUpdateRequest(BaseModel):
    session_id: str = Field(..., description="Session ID")
    context_data: Dict[str, Any] = Field(..., description="Updated context data")

# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global ollama_client, ai_handler
    
    # Startup
    logger.info("Starting AI Agent service...")
    
    # Initialize Ollama client
    ollama_client = OllamaClient(
        base_url=os.getenv("OLLAMA_BASE_URL", DEFAULT_CONFIG["ollama_base_url"]),
        model_name=os.getenv("OLLAMA_MODEL", DEFAULT_CONFIG["model_name"]),
        max_retries=int(os.getenv("OLLAMA_MAX_RETRIES", DEFAULT_CONFIG["max_retries"])),
        timeout=int(os.getenv("OLLAMA_TIMEOUT", DEFAULT_CONFIG["timeout"]))
    )
    
    # Initialize AI handler
    ai_handler = AIAgentHandler(
        ollama_client=ollama_client,
        session_timeout=int(os.getenv("SESSION_TIMEOUT", DEFAULT_CONFIG["session_timeout"])),
        max_sessions=int(os.getenv("MAX_SESSIONS", DEFAULT_CONFIG["max_sessions"]))
    )
    
    # Start services
    await ai_handler.start()
    
    logger.info("AI Agent service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Agent service...")
    
    if ai_handler:
        await ai_handler.stop()
    
    if ollama_client:
        if hasattr(ollama_client, 'session') and ollama_client.session:
            await ollama_client.session.close()
    
    logger.info("AI Agent service shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="AI Financial Agent",
    description="LLaMA 3.2 powered financial insights and analytics for SMB retailers",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency injection
async def get_ai_handler() -> AIAgentHandler:
    """Get AI handler instance."""
    if ai_handler is None:
        raise HTTPException(status_code=503, detail="AI Agent service not available")
    return ai_handler

async def get_ollama_client() -> OllamaClient:
    """Get Ollama client instance."""
    if ollama_client is None:
        raise HTTPException(status_code=503, detail="Ollama client not available")
    return ollama_client

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        client = await get_ollama_client()
        ollama_healthy = await client.health_check()
        
        handler = await get_ai_handler()
        stats = await handler.get_session_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "ollama_healthy": ollama_healthy,
            "session_stats": stats
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.post("/sessions", response_model=Dict[str, Any])
async def create_session(
    request: SessionCreateRequest,
    handler: AIAgentHandler = Depends(get_ai_handler)
):
    """Create a new chat session."""
    try:
        session = await handler.create_chat_session(
            session_id=request.session_id,
            user_id=request.user_id,
            initial_context=request.initial_context,
            preferences=request.preferences
        )
        
        return {
            "status": "success",
            "session_id": session.session_id,
            "user_id": session.user_id,
            "created_at": session.created_at.isoformat(),
            "message": "Session created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    handler: AIAgentHandler = Depends(get_ai_handler)
):
    """Process chat message and get AI response."""
    try:
        response = await handler.process_chat_message(
            session_id=request.session_id,
            message=request.message,
            message_type=request.message_type
        )
        
        if "error" in response:
            raise HTTPException(status_code=400, detail=response["error"])
        
        return ChatResponse(**response)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/insights", response_model=Dict[str, Any])
async def generate_insights(
    request: InsightGenerationRequest,
    handler: AIAgentHandler = Depends(get_ai_handler)
):
    """Generate financial insights."""
    try:
        insight_request = InsightRequest(
            user_id=request.user_id,
            query=request.query,
            context_data=request.context_data,
            insight_type=request.insight_type,
            priority=request.priority
        )
        
        result = await handler.generate_financial_insights(insight_request)
        return result
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reports", response_model=Dict[str, Any])
async def generate_report(
    request: ReportGenerationRequest,
    handler: AIAgentHandler = Depends(get_ai_handler)
):
    """Generate financial report."""
    try:
        report_request = ReportRequest(
            user_id=request.user_id,
            report_type=request.report_type,
            date_range=(request.start_date, request.end_date),
            metrics=request.metrics,
            format=request.format
        )
        
        result = await handler.generate_financial_report(report_request)
        return result
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/sessions/{session_id}/context")
async def update_session_context(
    session_id: str,
    request: ContextUpdateRequest,
    handler: AIAgentHandler = Depends(get_ai_handler)
):
    """Update session context."""
    try:
        success = await handler.update_session_context(
            session_id=session_id,
            context_data=request.context_data
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"status": "success", "message": "Context updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/{session_id}/summary")
async def get_conversation_summary(
    session_id: str,
    handler: AIAgentHandler = Depends(get_ai_handler)
):
    """Get conversation summary."""
    try:
        result = await handler.get_conversation_summary(session_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def list_models(client: OllamaClient = Depends(get_ollama_client)):
    """List available Ollama models."""
    try:
        models = await client.list_models()
        return {"models": models}
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/{model_name}/pull")
async def pull_model(
    model_name: str,
    background_tasks: BackgroundTasks,
    client: OllamaClient = Depends(get_ollama_client)
):
    """Pull/download a model."""
    try:
        # Run model pull in background
        background_tasks.add_task(client.pull_model, model_name)
        return {"status": "started", "message": f"Pulling model {model_name}"}
    except Exception as e:
        logger.error(f"Error pulling model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats(handler: AIAgentHandler = Depends(get_ai_handler)):
    """Get service statistics."""
    try:
        stats = await handler.get_session_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

def main():
    """Main entry point."""
    host = os.getenv("AI_AGENT_HOST", "0.0.0.0")
    port = int(os.getenv("AI_AGENT_PORT", "8080"))
    workers = int(os.getenv("AI_AGENT_WORKERS", "1"))
    debug = os.getenv("AI_AGENT_DEBUG", "false").lower() == "true"
    
    if workers > 1:
        # Use gunicorn for multiple workers
        import gunicorn.app.base
        
        class StandaloneApplication(gunicorn.app.base.BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()
            
            def load_config(self):
                for key, value in self.options.items():
                    self.cfg.set(key.lower(), value)
            
            def load(self):
                return self.application
        
        options = {
            'bind': f'{host}:{port}',
            'workers': workers,
            'worker_class': 'uvicorn.workers.UvicornWorker',
            'timeout': 120,
            'keepalive': 60,
            'max_requests': 1000,
            'max_requests_jitter': 100
        }
        
        StandaloneApplication(app, options).run()
    else:
        # Use uvicorn for single worker
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info" if not debug else "debug",
            reload=debug
        )

if __name__ == "__main__":
    main()