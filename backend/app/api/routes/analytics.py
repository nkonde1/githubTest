# backend/app/api/routes/analytics.py
"""
Analytics and reporting routes.
"""

from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.core.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
def get_analytics_data(
    timeframe: str = Query("30d"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Lightweight analytics endpoint returning the keys the frontend expects.
    This is a safe fallback implementation that reads from Transaction.
    """
    try:
        days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
        days = days_map.get(timeframe, 30)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Time-series points (one per day)
        points: List[Dict] = []
        for i in range(days):
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            q = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
                Transaction.user_id == current_user.id,
                Transaction.created_at >= day_start,
                Transaction.created_at < day_end,
                or_(Transaction.status.ilike("completed"), Transaction.status.ilike("ts")),
            )
            day_revenue = float(q.scalar() or 0)
            q_tx = db.query(func.count(Transaction.id)).filter(
                Transaction.user_id == current_user.id,
                Transaction.created_at >= day_start,
                Transaction.created_at < day_end,
            )
            day_tx = int(q_tx.scalar() or 0)
            points.append({"date": day_start.strftime("%Y-%m-%d"), "revenue": round(day_revenue, 2), "transactions": day_tx})

        total_revenue = sum(p["revenue"] for p in points)
        total_transactions = sum(p["transactions"] for p in points)
        average_order_value = (total_revenue / total_transactions) if total_transactions > 0 else 0.0

        # Simple growth: compare last half vs first half of selected window
        half = max(1, days // 2)
        first_half = sum(p["revenue"] for p in points[:half])
        second_half = sum(p["revenue"] for p in points[half:])
        growth_rate = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0.0

        # Risk proxies
        recent_failed = db.query(func.count(Transaction.id)).filter(
            Transaction.user_id == current_user.id,
            Transaction.status == "failed",
            Transaction.created_at >= start_date,
        ).scalar() or 0
        risk_score = min(100, int((recent_failed / max(1, total_transactions)) * 100)) if total_transactions > 0 else 0
        risk_level = "low" if risk_score < 30 else ("medium" if risk_score < 70 else "high")

        return {
            "timeframe": timeframe,
            "totalRevenue": round(total_revenue, 2),
            "totalTransactions": int(total_transactions),
            "averageOrderValue": round(average_order_value, 2),
            "growthRate": round(growth_rate, 2),
            "chartData": points,
            "riskScore": risk_score,
            "riskLevel": risk_level,
            "lastUpdated": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.exception("Error generating analytics data")
        raise HTTPException(status_code=500, detail="Error generating analytics data")


@router.get("/dashboard")
def get_dashboard(
    period: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dashboard summary for the given period (days).
    Returns keys expected by the frontend analytics slice.
    """
    try:
        start_date = datetime.utcnow() - timedelta(days=period)

        total_revenue = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            Transaction.user_id == current_user.id,
            or_(Transaction.status.ilike("completed"), Transaction.status.ilike("ts")),
            Transaction.created_at >= start_date,
        ).scalar() or 0

        total_transactions = db.query(func.count(Transaction.id)).filter(
            Transaction.user_id == current_user.id,
            Transaction.created_at >= start_date,
        ).scalar() or 0

        avg_order_value = (float(total_revenue) / total_transactions) if total_transactions else 0.0

        # customer growth using distinct customer_email if available, otherwise fallback
        try:
            this_period_customers = db.query(func.count(func.distinct(Transaction.customer_email))).filter(
                Transaction.user_id == current_user.id,
                Transaction.created_at >= start_date,
            ).scalar() or 0
        except Exception:
            this_period_customers = 0

        prev_start = start_date - timedelta(days=period)
        try:
            prev_period_customers = db.query(func.count(func.distinct(Transaction.customer_email))).filter(
                Transaction.user_id == current_user.id,
                Transaction.created_at >= prev_start,
                Transaction.created_at < start_date,
            ).scalar() or 0
        except Exception:
            prev_period_customers = 0

        customer_growth = ((this_period_customers - prev_period_customers) / prev_period_customers) if prev_period_customers > 0 else None

        completed_count = db.query(func.count(Transaction.id)).filter(
            Transaction.user_id == current_user.id,
            or_(Transaction.status.ilike("completed"), Transaction.status.ilike("ts")),
            Transaction.created_at >= start_date,
        ).scalar() or 0
        conversion_rate = (completed_count / total_transactions) if total_transactions > 0 else 0.0

        # MRR proxy (transaction_type == 'recurring' if present)
        try:
            mrr = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
                Transaction.user_id == current_user.id,
                Transaction.created_at >= start_date,
                Transaction.transaction_type == "recurring",
            ).scalar() or 0
        except Exception:
            mrr = 0

        payload = {
            "totalRevenue": float(total_revenue),
            "totalTransactions": int(total_transactions),
            "averageOrderValue": float(avg_order_value),
            "customerGrowth": float(customer_growth) if customer_growth is not None else None,
            "conversionRate": float(conversion_rate),
            "monthlyRecurring": float(mrr),
            "periodDays": int(period),
        }

        logger.info("Dashboard summary served", extra={"user_id": str(current_user.id), "period": period})
        return payload

    except Exception as e:
        logger.exception("Failed to build dashboard summary")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate dashboard summary")