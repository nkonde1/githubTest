"""
Main entry point for AI Agent service.
Provides FastAPI endpoints for LLaMA 3.2 powered financial insights.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime

from llama_service.ai_handlers import AIAgentHandler
from llama_service.llama_service import OllamaClient, DEFAULT_CONFIG

# --- Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
ai_handler: Optional[AIAgentHandler] = None

# --- Pydantic Models ---
class SessionRequest(BaseModel):
    session_id: str
    user_id: str

class ChatRequest(BaseModel):
    session_id: str
    message: str
    user_id: Optional[str] = None  # User ID is now optional

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str
    has_context: bool

# --- App Lifecycle ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global ai_handler
    logger.info("Starting AI Agent service...")
    async with OllamaClient(
        base_url=os.getenv("OLLAMA_BASE_URL", DEFAULT_CONFIG["ollama_base_url"]),
        model_name=os.getenv("OLLAMA_MODEL", DEFAULT_CONFIG["model_name"])
    ) as client:
        ai_handler = AIAgentHandler(ollama_client=client)
        await ai_handler.start()
        yield
    logger.info("Shutting down AI Agent service...")
    if ai_handler: await ai_handler.stop()

# --- FastAPI App ---
app = FastAPI(title="AI Financial Agent", version="1.4.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, 
    allow_methods=["*"], allow_headers=["*"]
)

async def get_ai_handler() -> AIAgentHandler:
    if ai_handler is None or not ai_handler.ollama_client.is_connected():
        raise HTTPException(status_code=503, detail="AI service is unavailable.")
    return ai_handler

# --- API Endpoints ---
@app.post("/sessions", status_code=201)
async def create_session(req: SessionRequest, handler: AIAgentHandler = Depends(get_ai_handler)):
    await handler.get_or_create_session(session_id=req.session_id, user_id=req.user_id)
    return {"status": "success", "session_id": req.session_id}

@app.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str, handler: AIAgentHandler = Depends(get_ai_handler)):
    session = handler.get_chat_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"history": [{"role": msg.role, "content": msg.content} for msg in session.messages]}

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, handler: AIAgentHandler = Depends(get_ai_handler)):
    try:
        response_data = await handler.process_chat_message(
            session_id=req.session_id,
            message=req.message,
            user_id_for_creation=req.user_id # Pass optional user_id
        )
        return ChatResponse(**response_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in /chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred.")

if __name__ == "__main__":
    uvicorn.run(app, host=os.getenv("AI_AGENT_HOST", "0.0.0.0"), port=int(os.getenv("PORT", "8080")))
