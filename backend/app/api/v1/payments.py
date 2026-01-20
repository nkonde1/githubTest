# backend/app/api/v1/payments.py

from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from sqlalchemy import select, and_, func, or_, String, cast
from app.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.core.auth import get_current_user
import logging
from datetime import datetime, timedelta
from app.schemas import payments as schemas

logger = logging.getLogger(__name__)
router = APIRouter()

def _build_filters(current_user_id: str, status: str, search: str):
    """Builds a list of SQLAlchemy filter conditions for transactions."""
    # DEFINITIVE FIX: Use the user ID as a string, as required by the database schema.
    filters = [Transaction.user_id == current_user_id]

    if status and status != "all":
        filters.append(Transaction.status == status)

    if search:
        search_term = f"%{search}%"
        filters.append(
            or_(
                Transaction.description.ilike(search_term),
                cast(Transaction.id, String).ilike(search_term)
            )
        )

    return filters

@router.get("/transactions")
async def get_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: str = Query('all'),
    search: str = Query(''),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetches a paginated list of transactions for the current user."""
    try:
        status_val = status.lower().strip() if status else "all"
        search_val = search.lower().strip()

        # Pass the user ID as a string, which is what the database expects.
        base_filters = _build_filters(str(current_user.id), status_val, search_val)

        count_query = select(func.count(Transaction.id)).filter(*base_filters)
        total_count_result = await db.execute(count_query)
        total_count = total_count_result.scalar_one_or_none() or 0

        transactions_query = (
            select(Transaction)
            .filter(*base_filters)
            .order_by(Transaction.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        transactions_result = await db.execute(transactions_query)
        transactions = transactions_result.scalars().all()

        transactions_list = [
            {
                "id": str(t.id),
                "amount": float(t.amount) if t.amount is not None else 0,
                "status": t.status,
                "type": t.transaction_type,
                "date": t.created_at.isoformat() if t.created_at else None,
                "description": t.description or "No description",
            }
            for t in transactions
        ]

        return {
            "transactions": transactions_list,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit if limit > 0 else 0,
        }

    except Exception as e:
        logger.error(f"Error fetching transactions: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching transactions."
        )

@router.get("/transactions/summary")
async def get_payment_summary(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get payment summary for the specified number of days."""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)

        # DEFINITIVE FIX: Use the user ID as a string, as required by the database schema.
        base_query = (
            select(Transaction)
            .filter(Transaction.user_id == str(current_user.id))
            .filter(Transaction.created_at >= start_date)
        )

        result = await db.execute(base_query)
        transactions = result.scalars().all()

        total_transactions = len(transactions)
        
        successful_statuses = ["completed", "succeeded", "successful"]
        completed_transactions = [t for t in transactions if t.status in successful_statuses]
        failed_transactions = [t for t in transactions if t.status == 'failed']
        
        completed_count = len(completed_transactions)
        failed_count = len(failed_transactions)
        
        total_revenue = sum(t.amount for t in completed_transactions)

        total_finished_transactions = completed_count + failed_count
        success_rate = (completed_count / total_finished_transactions) if total_finished_transactions > 0 else 0
        
        return {
            "total_transactions": total_transactions,
            "total_revenue": float(total_revenue),
            "completed_transactions": completed_count,
            "failed_transactions": failed_count,
            "success_rate": success_rate,
            "period_days": days,
        }
        
    except Exception as e:
        logger.error(f"Error retrieving payment summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving payment summary"
        )
