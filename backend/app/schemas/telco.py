"""
Pydantic schemas for Telco API
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.payments import TransactionResponse

class TelcoConnectRequest(BaseModel):
    provider: str = Field(..., description="Telco provider (MTN or Airtel)")
    wallet_number: str = Field(..., description="Mobile wallet number")
    merchant_id: Optional[str] = Field(None, description="Merchant ID if applicable")

class TelcoConnectResponse(BaseModel):
    connect_id: str
    status: str
    message: str

class TelcoVerifyRequest(BaseModel):
    connect_id: str
    otp: str

class TelcoVerifyResponse(BaseModel):
    connect_id: str
    status: str
    message: str
    verified_at: datetime

class TelcoPullRequest(BaseModel):
    provider: str
    from_date: Optional[str] = None # ISO format
    to_date: Optional[str] = None   # ISO format
    # We might infer wallet/connection from user context or pass connect_id explicitly.
    # For simplicity, let's assume we look up the active connection for the provider.

class TelcoPullResponse(BaseModel):
    records_fetched: int
    transactions: List[TransactionResponse]
    message: str
