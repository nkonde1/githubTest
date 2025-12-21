# backend/app/api/v1/payments.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from app.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.core.auth import get_current_user
import logging
from datetime import datetime, timedelta
from app.schemas import payments as schemas

logger = logging.getLogger(__name__)
router = APIRouter()


# helper to build filters consistently
def _build_filters(current_user_id, status: str, search: str):
    filters = [Transaction.user_id == current_user_id]
    if status and status != "all":
        filters.append(Transaction.status == status)
    if search:
        filters.append(
            or_(
                Transaction.id.ilike(f"%{search}%"),
                Transaction.customer_name.ilike(f"%{search}%")
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
    """
    Get paginated transactions for the authenticated user.
    
    Query Parameters:
    - page: Page number (default: 1)
    - limit: Items per page (default: 10, max: 100)
    - status: Filter by status (all, completed, pending, failed, cancelled)
    - search: Search by transaction ID or customer name
    """
    try:
        # Build base query with consistent filters
        base_filters = _build_filters(current_user.id, status, search)
        query = select(Transaction).filter(*base_filters)
        
        # Get total count for pagination using same filters
        count_query = select(func.count(Transaction.id)).filter(*base_filters)
        
        # Get total revenue (apply same user/status/search filters; omit search if not desired)
        revenue_filters = [Transaction.user_id == current_user.id, Transaction.status == 'completed']
        if search:
            revenue_filters.append(
                or_(
                    Transaction.id.ilike(f"%{search}%"),
                    Transaction.customer_name.ilike(f"%{search}%")
                )
            )
        revenue_query = select(func.sum(Transaction.amount)).filter(*revenue_filters)
        
        # Get success rate (use same filters as count_query + status completed)
        success_filters = [Transaction.user_id == current_user.id]
        if search:
            success_filters.append(
                or_(
                    Transaction.id.ilike(f"%{search}%"),
                    Transaction.customer_name.ilike(f"%{search}%")
                )
            )
        success_filters.append(Transaction.status == 'completed')
        success_query = select(func.count(Transaction.id)).filter(*success_filters)
        
        # Apply pagination
        offset = (page - 1) * limit
        query = query.order_by(Transaction.created_at.desc()).offset(offset).limit(limit)
        
        # Execute all queries
        result = await db.execute(query)
        transactions = result.scalars().all()
        
        count_result = await db.execute(count_query)
        total_count = count_result.scalar() or 0
        
        revenue_result = await db.execute(revenue_query)
        total_revenue = revenue_result.scalar() or 0
        
        success_result = await db.execute(success_query)
        success_count = success_result.scalar() or 0
        success_rate = (success_count / total_count) if total_count > 0 else 0
        
        # Format response
        transactions_list = [
            {
                "id": t.id,
                "amount": float(t.amount) if t.amount else 0,
                "status": t.status,
                "payment_method": t.payment_method,
                "customer_name": t.customer_name,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "description": t.description,
            }
            for t in transactions
        ]
        
        logger.info(
            f"Transactions retrieved successfully",
            extra={"user_id": str(current_user.id), "count": len(transactions_list)}
        )
        
        return {
            "transactions": transactions_list,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit,
            "total_revenue": float(total_revenue),
            "success_rate": success_rate,
        }
        
    except Exception as e:
        logger.error(
            f"Error retrieving transactions: {str(e)}",
            extra={"user_id": str(current_user.id)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving transactions"
        )


@router.get("/summary")
async def get_payment_summary(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get payment summary for the specified number of days.
    """
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total transactions
        total_query = select(func.count(Transaction.id)).filter(
            Transaction.user_id == current_user.id,
            Transaction.created_at >= start_date
        )
        total_result = await db.execute(total_query)
        total_transactions = total_result.scalar() or 0
        
        # Total revenue
        revenue_query = select(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.status == 'completed',
            Transaction.created_at >= start_date
        )
        revenue_result = await db.execute(revenue_query)
        total_revenue = revenue_result.scalar() or 0
        
        # Completed transactions
        completed_query = select(func.count(Transaction.id)).filter(
            Transaction.user_id == current_user.id,
            Transaction.status == 'completed',
            Transaction.created_at >= start_date
        )
        completed_result = await db.execute(completed_query)
        completed_count = completed_result.scalar() or 0
        
        # Failed transactions
        failed_query = select(func.count(Transaction.id)).filter(
            Transaction.user_id == current_user.id,
            Transaction.status == 'failed',
            Transaction.created_at >= start_date
        )
        failed_result = await db.execute(failed_query)
        failed_count = failed_result.scalar() or 0
        
        success_rate = (completed_count / total_transactions) if total_transactions > 0 else 0
        
        logger.info(
            f"Payment summary retrieved",
            extra={"user_id": str(current_user.id), "days": days}
        )
        
        return {
            "total_transactions": total_transactions,
            "total_revenue": float(total_revenue),
            "completed_transactions": completed_count,
            "failed_transactions": failed_count,
            "success_rate": success_rate,
            "period_days": days,
        }
        
    except Exception as e:
        logger.error(
            f"Error retrieving payment summary: {str(e)}",
            extra={"user_id": str(current_user.id)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving payment summary"
        )


@router.post("/transactions", response_model=dict)
async def create_transaction(
    transaction_in: schemas.TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new transaction manually.
    """
    try:
        # Create new transaction object
        new_transaction = Transaction(
            user_id=current_user.id,
            amount=transaction_in.amount,
            currency=transaction_in.currency,
            status=transaction_in.status,
            transaction_type=transaction_in.transaction_type,
            description=transaction_in.description,
            stripe_payment_id=transaction_in.stripe_payment_id,
            shopify_order_id=transaction_in.shopify_order_id,
            quickbooks_ref=transaction_in.quickbooks_ref,
            transaction_metadata=transaction_in.transaction_metadata,
            created_at=transaction_in.date or datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(new_transaction)
        await db.commit()
        await db.refresh(new_transaction)
        
        logger.info(
            f"Transaction created manually",
            extra={"user_id": str(current_user.id), "transaction_id": str(new_transaction.id)}
        )
        
        # Trigger business metrics update
        try:
            from app.services.analytics_engine import AnalyticsEngine
            from app.services.ai_agent import AIAgentService
            
            # Initialize services
            ai_service = AIAgentService()
            analytics = AnalyticsEngine(db, ai_service)
            
            # Update metrics
            await analytics.update_business_metrics(str(current_user.id))
            logger.info(f"Business metrics updated for user {current_user.id}")
            
        except Exception as e:
            # Log error but don't fail the request
            logger.error(f"Failed to update business metrics: {str(e)}")
        
        # Return a simple dict or map to a response schema
        return {
            "id": str(new_transaction.id),
            "amount": float(new_transaction.amount),
            "status": new_transaction.status,
            "description": new_transaction.description,
            "created_at": new_transaction.created_at.isoformat()
        }
        
    except Exception as e:
        logger.error(
            f"Error creating transaction: {str(e)}",
            extra={"user_id": str(current_user.id)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating transaction: {str(e)}"
        )