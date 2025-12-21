# backend/app/api/routes/__init__.py
"""
API routes package
Contains all route handlers for different endpoints
"""

from app.api.v1.auth import router as auth_router
from . import payments, analytics, financing, insights

# Re-export routers for backwards compatibility
auth = auth_router