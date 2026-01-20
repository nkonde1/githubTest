from fastapi import APIRouter
from . import auth, metrics, financing, payments, analytics, insights, telco, billing

api_router = APIRouter()

# Register all routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
# Corrected the prefix to "/metrics"
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(financing.router, prefix="/financing", tags=["financing"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(telco.router, prefix="/telco", tags=["telco"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])