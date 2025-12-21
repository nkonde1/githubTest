# embedded-finance-platform/backend/app/__init__.py

"""
Backend Application Initialization Module

This module initializes the FastAPI application, bringing together all
the core components, API routes, and middleware. It sets up logging,
configures CORS, and includes routers for various functionalities.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.routes import auth, payments, analytics, financing, insights
from app.database import get_db
from backend.app.redis_client import redis_client
from app.celery_worker import celery_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown events.

    On startup, it initializes the database and Redis client.
    On shutdown, it performs any necessary cleanup.
    """
    setup_logging()
    print("Application startup: Initializing database and Redis...")
    await get_db
    await redis_client
    yield
    print("Application shutdown: Performing cleanup...")
    # Add any cleanup code here, e.g., closing database connections, Redis connections
    # For SQLAlchemy, connection pool is typically managed, but explicit close might be needed for some drivers.
    # For Redis, `close()` might be called if `init_redis` created a client that needs explicit closing.


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    version="0.1.0",
    description="AI-embedded finance and analytics platform for SMB retailers and fintech SaaS.",
    lifespan=lifespan,
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix=settings.API_V1_STR, tags=["Authentication"])
app.include_router(payments.router, prefix=settings.API_V1_STR, tags=["Payments"])
app.include_router(analytics.router, prefix=settings.API_V1_STR, tags=["Analytics"])
app.include_router(financing.router, prefix=settings.API_V1_STR, tags=["Financing"])
app.include_router(insights.router, prefix=settings.API_V1_STR, tags=["Insights"])


@app.get("/")
async def root():
    """
    Root endpoint for the API.
    """
    return {"message": f"{settings.PROJECT_NAME} API is running!"}