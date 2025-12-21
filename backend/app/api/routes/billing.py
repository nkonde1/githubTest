from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.api.deps import get_current_user
from app.services.payment_gateway import ZambiaPaymentGateway

router = APIRouter()
gateway = ZambiaPaymentGateway()

class SubscriptionRequest(BaseModel):
    plan_id: str # "6_months" or "12_months"
    phone_number: str
    provider: str # "mtn" or "airtel"

class SubscriptionResponse(BaseModel):
    status: str
    message: str
    transaction_id: Optional[str] = None

@router.post("/subscribe", response_model=SubscriptionResponse)
async def subscribe(
    request: SubscriptionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Initiate a subscription payment.
    """
    if request.plan_id not in gateway.FEES:
        raise HTTPException(status_code=400, detail="Invalid plan ID")
    
    amount = gateway.get_fee(request.plan_id)
    reference = f"SUB-{current_user.id}-{datetime.utcnow().timestamp()}"
    
    try:
        # Initiate payment
        result = await gateway.initiate_payment(
            request.phone_number, 
            request.provider, 
            amount, 
            reference
        )
        
        transaction_id = result.get("transaction_id")
        status = result.get("status")
        
        # Create Transaction record
        new_transaction = Transaction(
            id=transaction_id,
            user_id=current_user.id,
            amount=-amount, # Negative amount for subscription outflow
            currency="ZMW",
            status=status,
            transaction_type="subscription",
            description=f"Subscription {request.plan_id}",
            transaction_metadata={
                "provider": request.provider,
                "plan_id": request.plan_id,
                "phone_number": request.phone_number,
                "provider_ref": result.get("provider_ref")
            }
        )
        db.add(new_transaction)
        await db.commit()
        
        return {
            "status": status,
            "message": result.get("message"),
            "transaction_id": transaction_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check-status/{transaction_id}")
async def check_payment_status(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check the status of a payment transaction.
    """
    # Find transaction
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == current_user.id))
    transaction = result.scalars().first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    if transaction.status == "successful":
        return {"status": "successful", "message": "Payment already completed"}
        
    # Check status with gateway
    provider = transaction.transaction_metadata.get("provider")
    gateway_result = await gateway.check_status(transaction_id, provider=provider)
    new_status = gateway_result.get("status")
    
    if new_status and new_status != transaction.status:
        transaction.status = new_status
        transaction.updated_at = datetime.utcnow()
        
        if new_status == "successful":
            # Update user subscription
            plan_id = transaction.transaction_metadata.get("plan_id")
            
            # Use naive UTC for consistency with DB schema (processed_at is naive DateTime)
            now = datetime.utcnow()
            duration_months = 6 if plan_id == "6_months" else 12
            
            # For subscription dates, we can use aware if the column supports it, 
            # but let's stick to what works for the User model.
            # User model has DateTime(timezone=True) for subscription fields.
            # So we might need aware for those, but naive for processed_at.
            
            now_aware = datetime.now(timezone.utc)
            
            start_date = now_aware
            if current_user.subscription_end_date and current_user.subscription_end_date > now_aware:
                start_date = current_user.subscription_end_date
                
            end_date = start_date + timedelta(days=30 * duration_months)
            
            current_user.subscription_tier = plan_id
            current_user.subscription_status = "active"
            current_user.subscription_start_date = start_date
            current_user.subscription_end_date = end_date
            current_user.billing_due_date = end_date
            current_user.last_payment_date = now_aware
            current_user.last_payment_amount = float(transaction.amount)
            current_user.payment_provider = transaction.transaction_metadata.get("provider")
            
            # processed_at is naive in Transaction model
            transaction.processed_at = now
            
        await db.commit()
        
    return {
        "status": transaction.status,
        "message": "Payment successful" if transaction.status == "successful" else "Payment pending"
    }

@router.get("/status")
async def get_subscription_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get current subscription status.
    """
    return {
        "tier": current_user.subscription_tier,
        "status": current_user.subscription_status,
        "end_date": current_user.subscription_end_date,
        "due_date": current_user.billing_due_date,
        "last_payment": {
            "date": current_user.last_payment_date,
            "amount": current_user.last_payment_amount,
            "provider": current_user.payment_provider
        }
    }
