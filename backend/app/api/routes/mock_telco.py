from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

router = APIRouter()

class MockStatementRequest(BaseModel):
    wallet_number: str
    from_date: str
    to_date: str

@router.post("/mtn/statement")
async def mock_mtn_statement(request: MockStatementRequest):
    """
    Direct endpoint to test MTN mock data generation
    """
    from app.clients.mtn_client import MTNClient
    client = MTNClient()
    data = await client.fetch_statement(request.wallet_number, request.from_date, request.to_date)
    return {"data": data}

@router.post("/airtel/statement")
async def mock_airtel_statement(request: MockStatementRequest):
    """
    Direct endpoint to test Airtel mock data generation
    """
    from app.clients.airtel_client import AirtelClient
    client = AirtelClient()
    data = await client.fetch_statement(request.wallet_number, request.from_date, request.to_date)
    return {"data": data}
