# backend/app/api/v1/api.py

from fastapi import APIRouter
from . import auth
from . import metrics
from . import financing

api_router = APIRouter(prefix="/api/v1")

# include existing v1 routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
# mount metrics so final endpoint will be: /api/v1/metrics/business_metrics
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
# ALSO mount metrics at the v1 root to support legacy frontend path /api/v1/business-metrics
api_router.include_router(metrics.router, prefix="", tags=["metrics-legacy"])

api_router.include_router(financing.router, prefix="/financing", tags=["financing"])