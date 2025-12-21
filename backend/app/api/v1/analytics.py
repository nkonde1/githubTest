from fastapi import APIRouter, Query
from typing import Optional, List
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/analytics")
async def analytics(timeframe: Optional[str] = Query("30d")):
    """
    Lightweight analytics compatibility endpoint.
    Replace with real implementation later.
    """
    # Basic sample chart data generator (adjust as needed)
    now = datetime.utcnow()
    points = []
    days = 30
    if timeframe.endswith("d"):
        days = int(timeframe[:-1])
    for i in range(days):
        dt = now - timedelta(days=days - i - 1)
        points.append({
            "date": dt.strftime("%Y-%m-%d"),
            "revenue": round(100 + i * 5 + (i % 3) * 10, 2),
            "transactions": 5 + (i % 7),
            "customers": 2 + (i % 5)
        })

    response = {
        "totalRevenue": sum(p["revenue"] for p in points),
        "growthRate": 12.5,
        "totalTransactions": sum(p["transactions"] for p in points),
        "averageOrderValue": (sum(p["revenue"] for p in points) / max(1, sum(p["transactions"] for p in points))),
        "riskScore": 25,
        "riskLevel": "Low",
        "chartData": points,
        "marketingRoi": [
            {"channel": "Search", "spend": 2000, "revenue": 12000, "roi": 500},
            {"channel": "Social", "spend": 1000, "revenue": 3500, "roi": 250}
        ]
    }
    return response