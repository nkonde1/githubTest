# backend/app/main.py
"""
Main FastAPI application entry point for the AI-embedded finance platform.
Handles CORS, middleware, and route registration.
"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from contextlib import asynccontextmanager
import time
import uuid # For generating request IDs

from app.core.config import settings
from app.core.logging import setup_logging, get_logger, log_api_request, log_api_response, log_security_event # Import granular loggers
from app.database import create_tables, SessionLocal, get_db
from app.core.auth import create_demo_user
from app.api.v1 import auth  # Import auth module
from app.api.v1.api import api_router  # Import the main v1 API router
from app.api.routes import payments, analytics, financing, insights, telco, mock_telco, billing
from app.redis_client import redis_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup logging FIRST
setup_logging()
# Get the root logger for main.py (or a specific 'app' logger)
logger = get_logger(__name__) 

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME}")
    await redis_client.init()
    await create_tables()  # This is now properly imported
    
    try:
        async with SessionLocal() as db:
            demo_user = await create_demo_user(db)
            if demo_user:
                logger.info(f"Demo user ready: {demo_user.email}")
    except Exception as e:
        logger.error(f"Demo user setup failed: {str(e)}")
    
    yield
    
    # Shutdown
    await redis_client.close()
    logger.info(f"Shutting down {settings.PROJECT_NAME}")

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Embedded Finance Platform API",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.allowed_hosts_list
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.BACKEND_CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "Authorization",
        "Content-Type",
        "X-Process-Time",
        # Add any other headers your frontend needs
    ]
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Middleware to add process time header and log API requests/responses.
    """
    request_id = str(uuid.uuid4()) # Generate a unique request ID
    
    log_api_request(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client_host=request.client.host if request.client else None
        # user_id will be added by `get_current_user` or subsequent logic if needed
    )
    
    start_time = time.time()
    try:
        response = await call_next(request)
    except HTTPException as e:
        # Catch FastAPI's HTTPExceptions to log them before they are handled by exception_handlers
        end_time = time.time()
        execution_time = end_time - start_time
        log_api_response(
            request_id=request_id,
            status_code=e.status_code,
            execution_time=execution_time,
            user_id=getattr(request.state, 'user_id', None) # Get user_id if set by auth dependency
        )
        # Re-raise the exception so FastAPI's exception handler can catch it
        raise
    except Exception as e:
        # Catch other unexpected exceptions
        end_time = time.time()
        execution_time = end_time - start_time
        logger.error(
            f"Unhandled exception in middleware for request {request_id}: {str(e)}", 
            exc_info=True, 
            extra={"request_id": request_id, "event": "middleware_exception"}
        )
        # Re-raise the exception so FastAPI's general exception handler can catch it
        raise
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    response.headers["X-Process-Time"] = str(execution_time)
    
    log_api_response(
        request_id=request_id,
        status_code=response.status_code,
        execution_time=execution_time,
        user_id=getattr(request.state, 'user_id', None) # Get user_id if set by auth dependency
    )
    
    return response

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global HTTP exception handler with consistent error format."""
    request_id = getattr(request.state, 'request_id', 'unknown') # Get request ID if available
    logger.error(
        f"HTTP Exception caught for request {request_id}: {exc.status_code} - {exc.detail}",
        exc_info=True,
        extra={"request_id": request_id, "status_code": exc.status_code, "detail": exc.detail, "event": "http_exception"}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unexpected errors."""
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.error(
        f"Unhandled exception for request {request_id}: {str(exc)}", 
        exc_info=True,
        extra={"request_id": request_id, "event": "unhandled_exception"}
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    logger.debug("Health check requested.") # Log health check as debug
    return {"status": "healthy", "service": "ai-finance-platform"}

# API Routes
# api_router already has prefix="/api/v1", include it without adding another prefix
app.include_router(api_router)
# mount resource routers under their resource paths
app.include_router(payments.router, prefix="/api/v1/payments")
app.include_router(analytics.router, prefix="/api/v1/analytics")
app.include_router(financing.router, prefix="/api/v1/financing")
app.include_router(insights.router, prefix="/api/v1/insights")
app.include_router(auth.router, prefix="/api/v1/auth")  # Mount the auth router with the /api/v1/auth prefix
app.include_router(telco.router, prefix="/api/v1/telco")
app.include_router(mock_telco.router, prefix="/api/v1/mock-telco")
app.include_router(billing.router, prefix="/api/v1/billing")

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Initialize Redis
        redis_connected = await redis_client.init()
        if not redis_connected:
            logger.warning("Running without Redis - using in-memory storage")
            
        # Create tables
        await create_tables()
        logger.info("Database tables ensured.")
        
        # Create demo user
        async with SessionLocal() as db:
            demo_user = await create_demo_user(db)
            if demo_user:
                logger.info(f"Demo user ready: {demo_user.email}")
            else:
                logger.info("No demo user created.")
        
        # Backfill credit scores
        async with SessionLocal() as db:
            try:
                from app.services.analytics_engine import AnalyticsEngine
                # Pass None for ai_service as it's not needed for backfill
                analytics = AnalyticsEngine(db, None)
                await analytics.backfill_credit_scores()
                logger.info("Credit score backfill check completed.")
            except Exception as e:
                logger.error(f"Startup backfill error: {str(e)}")
                
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        # Allow application to start even if Redis fails

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )