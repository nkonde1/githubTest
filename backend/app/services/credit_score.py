from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.financing import BusinessMetrics
from app.models.transaction import Transaction
from datetime import datetime, timedelta

class CreditScoreService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_score(self, user_id: str, metrics: BusinessMetrics = None) -> dict:
        """
        Calculate a credit score (0-1000) based on business metrics and transaction history.
        If metrics is provided, uses that instead of fetching from DB.
        """
        # 1. Use provided metrics or fetch latest
        if not metrics:
            stmt = select(BusinessMetrics).where(
                BusinessMetrics.user_id == user_id
            ).order_by(BusinessMetrics.calculated_at.desc()).limit(1)
            
            result = await self.db.execute(stmt)
            metrics = result.scalars().first()
        
        # 2. Fetch transaction stats (last 90 days)
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        stmt_tx = select(
            func.count(Transaction.id).label("tx_count"),
            func.sum(Transaction.amount).label("tx_volume"),
            func.count(Transaction.id).filter(Transaction.status == 'failed').label("failed_tx")
        ).where(
            Transaction.user_id == user_id,
            Transaction.created_at >= ninety_days_ago
        )
        
        tx_result = await self.db.execute(stmt_tx)
        tx_stats = tx_result.one()
        
        # Default values if no data
        monthly_revenue = float(metrics.monthly_revenue) if metrics and metrics.monthly_revenue else 0
        cash_flow = float(metrics.cash_flow) if metrics and metrics.cash_flow else 0
        profit_margin = float(metrics.profit_margin) if metrics and metrics.profit_margin else 0
        
        tx_count = tx_stats.tx_count or 0
        tx_volume = float(tx_stats.tx_volume or 0)
        failed_tx = tx_stats.failed_tx or 0
        
        # --- SCORING LOGIC ---
        score = 300 # Base score
        
        # Revenue Impact (up to 200 points)
        if monthly_revenue > 50000: score += 200
        elif monthly_revenue > 10000: score += 100
        elif monthly_revenue > 1000: score += 50
        
        # Cash Flow Impact (up to 150 points)
        if cash_flow > 10000: score += 150
        elif cash_flow > 0: score += 75
        
        # Profit Margin Impact (up to 100 points)
        if profit_margin > 0.2: score += 100
        elif profit_margin > 0.05: score += 50
        
        # Transaction Volume Stability (up to 150 points)
        if tx_count > 100: score += 150
        elif tx_count > 20: score += 75
        
        # Negative Factors
        failure_rate = (failed_tx / tx_count) if tx_count > 0 else 0
        if failure_rate > 0.1: score -= 100
        elif failure_rate > 0.05: score -= 50
        
        # Cap score
        score = max(300, min(850, score))
        
        rating = "Poor"
        if score >= 750: rating = "Excellent"
        elif score >= 700: rating = "Good"
        elif score >= 650: rating = "Fair"
        
        return {
            "score": score,
            "rating": rating,
            "factors": {
                "revenue": monthly_revenue,
                "cash_flow": cash_flow,
                "transaction_volume_90d": tx_volume,
                "transaction_count_90d": tx_count
            }
        }
