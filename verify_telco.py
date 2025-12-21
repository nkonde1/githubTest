import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.main import app
from fastapi.testclient import TestClient
from app.database import SessionLocal
from app.models.user import User
from app.core.auth import create_access_token
from sqlalchemy import select
from unittest.mock import AsyncMock

# Mock Redis init to prevent connection attempts
from app.redis_client import redis_client
redis_client.init = AsyncMock(return_value=True)

# Create Test Client
client = TestClient(app)

async def get_demo_user_token():
    async with SessionLocal() as db:
        result = await db.execute(select(User).limit(1))
        user = result.scalars().first()
        if not user:
            print("No user found. Please run the app once to create demo user.")
            return None
        
        token = create_access_token(str(user.id))
        return token

def test_telco_flow():
    print("Starting Telco Flow Verification...")
    
    # 1. Get Auth Token
    # Since we can't easily run async code in this sync script with TestClient without some setup,
    # we'll try to get the token. 
    # Actually, TestClient is synchronous. But our DB access for token needs async.
    # Let's just mock the auth dependency or try to run a small async setup first.
    
    # Alternative: Just use the API if the server was running, but it's not.
    # We will use the TestClient which handles async endpoints by running them in a loop.
    # But we need a valid token.
    
    # Let's try to get a token via a hack or just bypass auth for the test if possible?
    # No, let's do it properly.
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    token = loop.run_until_complete(get_demo_user_token())
    
    if not token:
        print("Failed to get token.")
        return

    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Test Connect
    print("\n[1] Testing Connect (MTN)...")
    connect_payload = {
        "provider": "MTN",
        "wallet_number": "0961234567",
        "merchant_id": "TEST_MERCHANT"
    }
    response = client.post("/api/v1/telco/connect", json=connect_payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code != 200:
        print("Connect failed!")
        return
        
    connect_id = response.json()["connect_id"]
    
    # 3. Test Verify
    print("\n[2] Testing Verify...")
    verify_payload = {
        "connect_id": connect_id,
        "otp": "123456" # Mock OTP for MTN
    }
    response = client.post("/api/v1/telco/verify", json=verify_payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code != 200:
        print("Verify failed!")
        return
        
    # 4. Test Pull
    print("\n[3] Testing Pull...")
    pull_payload = {
        "provider": "MTN",
        "from_date": "2023-01-01",
        "to_date": "2023-01-31"
    }
    response = client.post("/api/v1/telco/pull", json=pull_payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code != 200:
        print("Pull failed!")
        return
        
    records = response.json().get("records_fetched", 0)
    print(f"Records fetched: {records}")
    
    if records > 0:
        print("\nSUCCESS: Full flow verified!")
    else:
        print("\nWARNING: No records fetched.")

if __name__ == "__main__":
    try:
        test_telco_flow()
    except Exception as e:
        print(f"An error occurred: {e}")
