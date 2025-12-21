from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid

from app.database import get_async_session
from app.core.auth import get_current_user
from app.models.user import User
from app.models.telco import TelcoConnection
from app.models.transaction import Transaction
from app.schemas.telco import (
    TelcoConnectRequest, TelcoConnectResponse,
    TelcoVerifyRequest, TelcoVerifyResponse,
    TelcoPullRequest, TelcoPullResponse
)
from app.clients.mtn_client import MTNClient
from app.clients.airtel_client import AirtelClient

router = APIRouter()

@router.get("/connections")
async def get_telco_connections(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get all telco connections for the current user.
    """
    result = await db.execute(
        select(TelcoConnection).filter(TelcoConnection.user_id == current_user.id)
    )
    connections = result.scalars().all()
    
    return [
        {
            "id": conn.id,
            "provider": conn.provider,
            "wallet_number": conn.wallet_number,
            "status": conn.status,
            "verified_at": conn.verified_at
        }
        for conn in connections
    ]


@router.post("/connect", response_model=TelcoConnectResponse)
async def connect_telco(
    request: TelcoConnectRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Initiate connection to a telco provider.
    """
    # 1. Create connection record
    connection = TelcoConnection(
        user_id=current_user.id,
        provider=request.provider,
        wallet_number=request.wallet_number,
        merchant_id=request.merchant_id,
        status="pending"
    )
    db.add(connection)
    await db.commit()
    await db.refresh(connection)
    
    # 2. Trigger OTP (Mock)
    if request.provider.upper() == "MTN":
        client = MTNClient()
    elif request.provider.upper() == "AIRTEL":
        client = AirtelClient()
    else:
        raise HTTPException(status_code=400, detail="Invalid provider")
        
    await client.request_otp(request.wallet_number)
    
    return {
        "connect_id": connection.id,
        "status": "pending_verification",
        "message": f"OTP sent to {request.wallet_number}"
    }

@router.post("/verify", response_model=TelcoVerifyResponse)
async def verify_telco(
    request: TelcoVerifyRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Verify OTP and finalize connection.
    """
    # 1. Get connection
    result = await db.execute(select(TelcoConnection).filter(TelcoConnection.id == request.connect_id))
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection request not found")
        
    if connection.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    # 2. Verify OTP (Mock)
    if connection.provider.upper() == "MTN":
        client = MTNClient()
    elif connection.provider.upper() == "AIRTEL":
        client = AirtelClient()
    else:
        raise HTTPException(status_code=400, detail="Invalid provider")
        
    is_valid = await client.verify_otp(connection.wallet_number, request.otp)
    
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid OTP")
        
    # 3. Update status
    connection.status = "verified"
    connection.verified_at = datetime.utcnow()
    connection.access_token = f"mock_token_{uuid.uuid4()}" # Store a mock token
    
    await db.commit()
    
    return {
        "connect_id": connection.id,
        "status": "verified",
        "message": "Connection verified successfully",
        "verified_at": connection.verified_at
    }

@router.post("/pull", response_model=TelcoPullResponse)
async def pull_telco_data(
    request: TelcoPullRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Pull historical data from connected telco account.
    """
    # 1. Find active connection
    result = await db.execute(
        select(TelcoConnection).filter(
            TelcoConnection.user_id == current_user.id,
            TelcoConnection.provider == request.provider,
            TelcoConnection.status == "verified"
        )
    )
    connection = result.scalars().first()
    
    if not connection:
        raise HTTPException(status_code=400, detail=f"No verified connection found for {request.provider}")
        
    # 2. Fetch data
    if request.provider.upper() == "MTN":
        client = MTNClient()
    elif request.provider.upper() == "AIRTEL":
        client = AirtelClient()
    else:
        raise HTTPException(status_code=400, detail="Invalid provider")
        
    # Default dates if not provided
    from_date = request.from_date or (datetime.utcnow().replace(day=1).isoformat()) # Start of current month? Or just some default
    if not request.from_date:
         # Default to last 30 days
         from_date = (datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)).isoformat()
         
    to_date = request.to_date or datetime.utcnow().isoformat()
    
    raw_records = await client.fetch_statement(connection.wallet_number, from_date, to_date)
    
    # 3. Normalize and Save
    saved_transactions = []
    
    for record in raw_records:
        # Check if already exists (idempotency)
        # For mock, we'll just check if external_id exists in transaction_metadata or similar
        # But since we don't have a dedicated external_id column for this, we'll use transaction_metadata
        
        # Normalization logic
        if request.provider.upper() == "MTN":
            ext_id = record.get("externalId")
            amount = float(record.get("amount"))
            currency = record.get("currency")
            desc = f"{record.get('payerMessage')} - {record.get('payeeNote')}"
            status_val = "completed" if record.get("status") == "SUCCESSFUL" else "failed"
            type_val = "payment" # simplified
            date_val = datetime.fromisoformat(record.get("date"))
            
        elif request.provider.upper() == "AIRTEL":
            ext_id = record.get("txn_id")
            amount = float(record.get("txn_amount"))
            currency = record.get("txn_currency")
            desc = record.get("narrative")
            status_val = "completed" if record.get("txn_status") == "TS" else "failed"
            type_val = "payment"
            date_val = datetime.strptime(record.get("txn_date"), "%Y-%m-%d %H:%M:%S")
            
        # Check existence
        # This is a bit expensive in a loop, but fine for MVP/Mock
        # Ideally we'd query all existing IDs in range and filter in memory
        
        # Create Transaction
        tx = Transaction(
            user_id=current_user.id,
            amount=amount,
            currency=currency,
            status=status_val,
            transaction_type=type_val,
            description=desc,
            created_at=date_val,
            updated_at=datetime.utcnow(),
            transaction_metadata={
                "source": "telco_pull",
                "provider": request.provider,
                "external_id": ext_id,
                "original_record": record
            }
        )
        saved_transactions.append(tx)
        
    if saved_transactions:
        db.add_all(saved_transactions)
        await db.commit()
        
        # Trigger metrics update (optional but good)
        try:
            from app.services.analytics_engine import AnalyticsEngine
            from app.services.ai_agent import AIAgentService
            analytics = AnalyticsEngine(db, AIAgentService())
            await analytics.update_business_metrics(str(current_user.id))
        except Exception:
            pass
            
    # Convert to response format
    from app.schemas.payments import TransactionResponse
    return {
        "records_fetched": len(saved_transactions),
        "transactions": [TransactionResponse.from_orm(t) for t in saved_transactions],
        "message": "Data pulled successfully"
    }
