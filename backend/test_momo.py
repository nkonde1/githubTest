import asyncio
import sys
import os
import uuid

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.payment_gateway import ZambiaPaymentGateway

async def test_gateway():
    gateway = ZambiaPaymentGateway()
    
    print("1. Testing MTN Token Generation...")
    try:
        token = await gateway._get_momo_token()
        print(f"MTN Token received: {token[:10]}...")
    except Exception as e:
        print(f"MTN Token generation failed: {e}")

    print("\n2. Testing MTN Payment Initiation...")
    try:
        result = await gateway.initiate_payment(
            phone_number="46733123453", # Test number for sandbox
            provider="mtn",
            amount=100.0,
            reference="TEST-REF-001"
        )
        print(f"MTN Payment Result: {result}")
        
        transaction_id = result.get("transaction_id")
        if transaction_id:
            print(f"\n3. Checking MTN Status for {transaction_id}...")
            status = await gateway.check_status(transaction_id, provider="mtn")
            print(f"MTN Status Result: {status}")
            
    except Exception as e:
        print(f"MTN Payment initiation failed: {e}")

    # Test Airtel Token
    print("\n4. Testing Airtel Token...")
    try:
        # This might return mock-airtel-token if credentials are placeholders
        airtel_token = await gateway._get_airtel_token()
        print(f"Airtel Token: {airtel_token[:10]}...")
    except Exception as e:
        print(f"Airtel Token generation failed: {e}")

    # Test Airtel Payment
    print("\n5. Testing Airtel Payment Initiation...")
    try:
        airtel_payment = await gateway.initiate_payment("0977000000", "airtel", 100.0, "TestRef")
        print(f"Airtel Payment Result: {airtel_payment}")

        if airtel_payment.get("transaction_id"):
            print("\n6. Testing Airtel Status Check...")
            # Pass provider explicitly for Airtel
            status = await gateway.check_status(airtel_payment["transaction_id"], provider="airtel")
            print(f"Airtel Status: {status}")
    except Exception as e:
        print(f"Airtel Payment initiation failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_gateway())
