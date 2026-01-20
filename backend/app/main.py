# backend/app/main.py
"""
Main FastAPI application entry point for the AI-embedded finance platform.
Handles CORS, middleware, and route registration.
"""

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="AI-Powered Finance Platform",
    description="Embedded Finance Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ADDED: Logging middleware to debug request paths
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request path: {request.url.path}")
    response = await call_next(request)
    return response

# Set up CORS
origins = [
    "https://easyflowfinance.com",
    "http://easyflowfinance.com",
    "https://easyflow-58299932-e99e8.web.app",
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# FIX: Add the /api/v1 prefix!
app.include_router(api_router, prefix="/api/v1")