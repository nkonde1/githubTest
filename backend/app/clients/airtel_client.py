import uuid
from datetime import datetime, timedelta
import random

class AirtelClient:
    """
    Mock client for Airtel Money API
    """
    
    async def request_otp(self, wallet_number: str) -> str:
        return "otp_sent"

    async def verify_otp(self, wallet_number: str, otp: str) -> bool:
        if otp == "654321" or otp.startswith("6"):
            return True
        return False

    async def fetch_statement(self, wallet_number: str, from_date: str, to_date: str):
        # Generate some random transactions (Different structure than MTN to test normalization)
        records = []
        start = datetime.fromisoformat(from_date)
        end = datetime.fromisoformat(to_date)
        
        days = (end - start).days
        count = min(days * 2, 20)
        
        for i in range(count):
            tx_date = start + timedelta(days=random.randint(0, days), hours=random.randint(0, 23))
            amount = random.randint(20, 3000)
            
            records.append({
                "txn_id": str(uuid.uuid4()),
                "txn_amount": amount,
                "txn_currency": "ZMW",
                "narrative": "Airtel Money Tx",
                "txn_status": "TS", # Transaction Success
                "txn_date": tx_date.strftime("%Y-%m-%d %H:%M:%S"),
                "txn_type": random.choice(["C2B", "B2B", "P2P"])
            })
            
        return records
