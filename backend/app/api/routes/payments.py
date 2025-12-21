# backend/app/api/routes/payments.py
"""
Payment processing and transaction management routes.
"""

from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
import csv
import io
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, and_, or_, select, func
from datetime import datetime, timedelta
from app.database import get_async_session
from app.services.data_sync import DataSyncService
from app.core.auth import get_current_user
from app.models.user import User
from app.models.transaction import Transaction, PaymentMethod
from app.schemas.payments import (
    TransactionResponse,
    PaymentMethodCreate,
    PaymentMethodResponse,
    TransactionFilter,
    PaginatedPayments,
    PaginatedTransactions
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/transactions", response_model=PaginatedTransactions)
async def get_transactions(
    page: int = 1,
    limit: int = 20,
    days: Optional[int] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    source: Optional[str] = None,
    type: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get user's transactions with filtering options."""
    
    # Calculate skip from page and limit
    skip = (page - 1) * limit
    
    # Build base query
    query = select(Transaction).filter(Transaction.user_id == current_user.id)
    
    # Apply filters
    if days:
        start_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(Transaction.created_at >= start_date)
    
    if status and status != 'all':
        query = query.filter(Transaction.status == status)
        
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Transaction.description.ilike(search_filter),
                Transaction.id.ilike(search_filter)
            )
        )
    
    # if source:
    #     query = query.filter(Transaction.source == source)
    
    if type:
        query = query.filter(Transaction.transaction_type == type)
    
    # Get total count for pagination
    count_query = select(func.count()).select_from(Transaction).filter(Transaction.user_id == current_user.id)
    if days:
        start_date = datetime.utcnow() - timedelta(days=days)
        count_query = count_query.filter(Transaction.created_at >= start_date)
    if status and status != 'all':
        count_query = count_query.filter(Transaction.status == status)
    if search:
        count_query = count_query.filter(
            or_(
                Transaction.description.ilike(search_filter),
                Transaction.id.ilike(search_filter)
            )
        )
    if type:
        count_query = count_query.filter(Transaction.transaction_type == type)
    
    result = await db.execute(count_query)
    total_count = result.scalar()
    
    # Order by most recent first and apply pagination
    query = query.order_by(desc(Transaction.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    # Calculate total pages
    total_pages = (total_count + limit - 1) // limit if limit > 0 else 0
    
    return {
        "items": [TransactionResponse.from_orm(t) for t in transactions],
        "total": total_count,
        "page": page,
        "page_size": limit,
        "total_pages": total_pages
    }


@router.get("/transactions/summary")
async def get_transaction_summary(
    days: Optional[int] = None,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get transaction summary statistics. If days is None or 0, returns all-time stats."""
    
    query = select(Transaction).filter(Transaction.user_id == current_user.id)
    
    if days and days > 0:
        start_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(Transaction.created_at >= start_date)
    
    # Calculate summary statistics
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    # Group totals by currency
    totals_by_currency = {}
    total_count = len(transactions)
    
    # Group by status
    by_status = {}
    successful_count = 0
    
    successful_statuses = ['completed', 'successful', 'succeeded']
    
    for transaction in transactions:
        # Currency totals (only for successful payment transactions)
        status = transaction.status.lower() if transaction.status else ""
        if status in successful_statuses and transaction.amount and transaction.transaction_type == 'payment':
            currency = transaction.currency or 'USD'
            if currency not in totals_by_currency:
                totals_by_currency[currency] = 0.0
            totals_by_currency[currency] += float(transaction.amount)

        # Status counts
        if status not in by_status:
            by_status[status] = {"count": 0, "amount": 0}
        by_status[status]["count"] += 1
        by_status[status]["amount"] += float(transaction.amount or 0)
        
        if status in successful_statuses:
            successful_count += 1
            
    success_rate = successful_count / total_count if total_count > 0 else 0
    
    return {
        "period_days": days,
        "totals_by_currency": totals_by_currency,
        "total_count": total_count,
        "success_rate": float(success_rate),
        "by_status": by_status
    }


@router.post("/payment-methods", response_model=PaymentMethodResponse)
async def create_payment_method(
    payment_method: PaymentMethodCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Add a new payment method configuration."""
    
    # Check if this is the first payment method (make it primary)
    count_query = select(func.count()).select_from(PaymentMethod).filter(
        PaymentMethod.user_id == current_user.id
    )
    result = await db.execute(count_query)
    existing_methods = result.scalar()
    
    method = PaymentMethod(
        user_id=current_user.id,
        provider=payment_method.provider,
        external_id=payment_method.external_id,
        account_id=payment_method.account_id,
        config=payment_method.config,
        is_primary=existing_methods == 0  # First method is primary
    )
    
    db.add(method)
    await db.commit()
    await db.refresh(method)
    
    logger.info(f"Payment method added: {payment_method.provider} for user {current_user.email}")
    
    return PaymentMethodResponse.from_orm(method)


@router.get("/payment-methods", response_model=List[PaymentMethodResponse])
async def get_payment_methods(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get user's configured payment methods."""
    
    query = select(PaymentMethod).filter(
        PaymentMethod.user_id == current_user.id
    )
    result = await db.execute(query)
    methods = result.scalars().all()
    
    return [PaymentMethodResponse.from_orm(m) for m in methods]


@router.post("/sync")
async def sync_payments(
    provider: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """Sync payments from specified provider"""
    try:
        # Create service instance
        service = DataSyncService(session)
        
        # Perform sync operation
        result = await service.sync_payment_data(str(current_user.id), provider)
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Payment sync failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync payments: {str(e)}"
        ) from e


@router.post("/transactions")
async def create_transaction(
    transaction_data: Dict[str, Any],
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new transaction manually."""
    try:
        # Extract fields from the request body
        amount = transaction_data.get('amount')
        currency = transaction_data.get('currency', 'USD')
        status_val = transaction_data.get('status', 'completed')
        transaction_type = transaction_data.get('transaction_type', 'payment')
        description = transaction_data.get('description')
        stripe_payment_id = transaction_data.get('stripe_payment_id')
        shopify_order_id = transaction_data.get('shopify_order_id')
        quickbooks_ref = transaction_data.get('quickbooks_ref')
        transaction_metadata = transaction_data.get('transaction_metadata')
        date_str = transaction_data.get('date')
        
        # Parse date if provided
        created_date = None
        if date_str:
            try:
                created_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                created_date = datetime.utcnow()
        else:
            created_date = datetime.utcnow()
        
        # Create new transaction object
        new_transaction = Transaction(
            user_id=current_user.id,
            amount=amount,
            currency=currency,
            status=status_val,
            transaction_type=transaction_type,
            description=description,
            stripe_payment_id=stripe_payment_id,
            shopify_order_id=shopify_order_id,
            quickbooks_ref=quickbooks_ref,
            transaction_metadata=transaction_metadata,
            created_at=created_date,
            updated_at=datetime.utcnow()
        )
        
        db.add(new_transaction)
        await db.commit()
        await db.refresh(new_transaction)
        
        logger.info(
            f"Transaction created manually",
            extra={"user_id": str(current_user.id), "transaction_id": str(new_transaction.id)}
        )
        
        # Return a simple dict
        return {
            "id": str(new_transaction.id),
            "amount": float(new_transaction.amount),
            "status": new_transaction.status,
            "description": new_transaction.description,
            "created_at": new_transaction.created_at.isoformat() if new_transaction.created_at else None
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


@router.post("/transactions/bulk")
async def bulk_upload_transactions(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Bulk upload transactions from a CSV file.
    Expected columns: date, amount, currency, description, status, type
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    try:
        content = await file.read()
        decoded_content = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(decoded_content))
        
        transactions_to_add = []
        errors = []
        row_index = 0
        
        for row in csv_reader:
            row_index += 1
            try:
                # Basic validation and parsing
                amount = float(row.get('amount', 0))
                currency = row.get('currency', 'USD')
                description = row.get('description', 'Bulk Import')
                status_val = row.get('status', 'completed')
                trans_type = row.get('type', 'payment')
                date_str = row.get('date')
                
                created_at = datetime.utcnow()
                if date_str:
                    try:
                        created_at = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    except:
                        pass # Keep default
                
                transaction = Transaction(
                    user_id=current_user.id,
                    amount=amount,
                    currency=currency,
                    description=description,
                    status=status_val,
                    transaction_type=trans_type,
                    created_at=created_at,
                    updated_at=datetime.utcnow(),
                    transaction_metadata={"source": "bulk_upload", "filename": file.filename}
                )
                transactions_to_add.append(transaction)
                
            except Exception as e:
                errors.append(f"Row {row_index}: {str(e)}")
        
        if transactions_to_add:
            db.add_all(transactions_to_add)
            await db.commit()
            
            # Trigger metrics update
            try:
                from app.services.analytics_engine import AnalyticsEngine
                from app.services.ai_agent import AIAgentService
                analytics = AnalyticsEngine(db, AIAgentService())
                await analytics.update_business_metrics(str(current_user.id))
            except Exception as e:
                logger.error(f"Failed to update metrics after bulk upload: {e}")

        return {
            "status": "success",
            "imported_count": len(transactions_to_add),
            "error_count": len(errors),
            "errors": errors[:10]  # Limit error details
        }

    except Exception as e:
        logger.error(f"Bulk upload failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
