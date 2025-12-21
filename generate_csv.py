import csv
import random
from datetime import datetime, timedelta

# Set a fixed start date relative to "now" (assuming Dec 2025 based on conversation)
# or just use a recent past date.
start_date = datetime(2025, 11, 10) 

rows = []
# Weighted statuses and types
statuses = ['completed'] * 42 + ['failed'] * 5 + ['pending'] * 3
types = ['payment'] * 45 + ['refund'] * 5

# Shuffle them to randomize order
random.shuffle(statuses)
random.shuffle(types)

descriptions = [
    "Office Supplies", "Software Subscription", "Client Payment", "Consulting Fee",
    "Hardware Purchase", "Server Hosting", "Marketing Campaign", "Travel Expenses",
    "Utility Bill", "Maintenance Service"
]

for i in range(50):
    # Random date within last 30 days
    date = start_date + timedelta(days=random.randint(0, 30), hours=random.randint(9, 17), minutes=random.randint(0, 59))
    
    # Random amount
    amount = round(random.uniform(25.0, 850.0), 2)
    
    # If refund, make amount negative (optional, but good for realism)
    # The backend might handle absolute values, but let's keep it positive for upload 
    # as the 'type' field dictates the logic usually. 
    # However, for a 'payment' system, refunds might be negative. 
    # Let's keep amounts positive and rely on 'type'.
    
    row = {
        'date': date.isoformat() + 'Z',
        'amount': amount,
        'currency': 'USD',
        'description': f"{random.choice(descriptions)} - #{1000 + i}",
        'status': statuses[i],
        'type': types[i]
    }
    rows.append(row)

# Sort by date
rows.sort(key=lambda x: x['date'])

output_path = r'c:\Users\nkond\Embeded_Finance_Platform\sample_transactions.csv'

with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['date', 'amount', 'currency', 'description', 'status', 'type'])
    writer.writeheader()
    writer.writerows(rows)

print(f"Successfully generated {len(rows)} transactions to {output_path}")
