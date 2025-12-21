import uuid
from datetime import datetime, timedelta
import random

class MTNClient:
    """
    Mock client for MTN Mobile Money API
    """
    
    async def request_otp(self, wallet_number: str) -> str:
        """
        Simulate requesting an OTP. In a real scenario, this would trigger an SMS.
        For dev/mock, we just return a success indicator.
        """
        # Simulate network delay?
        return "otp_sent"

    async def verify_otp(self, wallet_number: str, otp: str) -> bool:
        """
        Verify the OTP.
        For mock: accept '123456' or any 6 digit number starting with '1'.
        """
        if otp == "123456" or otp.startswith("1"):
            return True
        return False

    async def fetch_statement(self, wallet_number: str, from_date: str, to_date: str):
        """
        Return mock statement data.
        """
        # Generate some random transactions
        records = []
        start = datetime.fromisoformat(from_date)
        end = datetime.fromisoformat(to_date)
        
        # Ensure we don't generate too many
        days = (end - start).days
        count = min(days * 2, 20) # Approx 2 per day, max 20
        
        for i in range(count):
            tx_date = start + timedelta(days=random.randint(0, days), hours=random.randint(0, 23))
            amount = random.randint(50, 5000)
            is_credit = random.choice([True, False])
            
            records.append({
                "externalId": str(uuid.uuid4()),
                "amount": str(amount),
                "currency": "ZMW",
                "payerMessage": "Payment Received" if is_credit else "Payment Sent",
                "payeeNote": "Services",
                "status": "SUCCESSFUL",
                "date": tx_date.isoformat(),
                "type": "DEPOSIT" if is_credit else "PAYMENT"
            })
            
        return records
