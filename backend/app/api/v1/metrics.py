# backend/app/api/v1/metrics.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.models.financing import BusinessMetrics
from app.services.analytics_engine import AnalyticsEngine
from app.services.ai_agent import AIAgentService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()  # removed tags here to keep simple

def _row_to_dict(r: BusinessMetrics):
    return {
        "id": str(r.id),
        "user_id": str(r.user_id) if getattr(r, "user_id", None) is not None else None,
        "monthly_revenue": float(r.monthly_revenue) if r.monthly_revenue is not None else None,
        "monthly_expenses": float(r.monthly_expenses) if r.monthly_expenses is not None else None,
        "profit_margin": float(r.profit_margin) if r.profit_margin is not None else None,
        "cash_flow": float(r.cash_flow) if r.cash_flow is not None else None,
        "customer_count": int(r.customer_count) if r.customer_count is not None else None,
        "avg_order_value": float(r.avg_order_value) if r.avg_order_value is not None else None,
        "repeat_customer_rate": float(r.repeat_customer_rate) if r.repeat_customer_rate is not None else None,
        "inventory_turnover": float(r.inventory_turnover) if r.inventory_turnover is not None else None,
        "chargeback_rate": float(r.chargeback_rate) if r.chargeback_rate is not None else None,
        "refund_rate": float(r.refund_rate) if r.refund_rate is not None else None,
        "payment_failure_rate": float(r.payment_failure_rate) if r.payment_failure_rate is not None else None,
        "period_start": r.period_start.isoformat() if getattr(r, "period_start", None) else None,
        "period_end": r.period_end.isoformat() if getattr(r, "period_end", None) else None,
        "calculated_at": r.calculated_at.isoformat() if getattr(r, "calculated_at", None) else None,
    }

# use relative paths — router will be mounted under /api/v1/metrics
@router.get("/business_metrics", response_model=List[dict])
@router.get("/business-metrics", response_model=List[dict])
async def get_business_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 10
):
    try:
        q = await db.execute(
            select(BusinessMetrics)
            .where(BusinessMetrics.user_id == current_user.id)
            .order_by(BusinessMetrics.calculated_at.desc())
            .limit(limit)
        )
        rows = q.scalars().all()
        return [_row_to_dict(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/business_metrics/update")
@router.post("/business-metrics/update")
async def update_business_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger an update of business metrics for the current user.
    This recalculates all metrics based on the latest transaction data.
    """
    try:
        # Initialize services
        ai_service = AIAgentService()
        analytics = AnalyticsEngine(db, ai_service)
        
        # Update metrics for current user
        metrics = await analytics.update_business_metrics(str(current_user.id))
        
        return {
            "status": "success",
            "message": "Business metrics updated successfully",
            "metrics": _row_to_dict(metrics)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update metrics: {str(e)}")