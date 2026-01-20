import logging
from datetime import datetime, timedelta
from typing import Any, Dict
from uuid import UUID

from sqlalchemy import and_, func, select, String, cast
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.financing import BusinessMetrics
from app.models.transaction import Transaction
from app.services.ai_agent import AIAgentService


class AnalyticsEngine:
    def __init__(self, db: AsyncSession, ai_service: AIAgentService):
        self.db = db
        self.ai_agent = ai_service
        self.logger = logging.getLogger(__name__)

    async def update_business_metrics(self, user_id: str) -> BusinessMetrics:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        transaction_metrics = await self._calculate_transaction_metrics(
            user_id, start_date, end_date
        )

        # ... existing logic ...
        metrics = await self._save_metrics(user_id, transaction_metrics)
        return metrics

    async def _calculate_transaction_metrics(
        self, user_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        # DEFINITIVE FIX: Use the user ID as a string, as required by the database schema.
        query = (
            select(Transaction.status, func.count(Transaction.id).label("count"))
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.created_at >= start_date,
                    Transaction.created_at <= end_date,
                )
            )
            .group_by(Transaction.status)
        )

        result = await self.db.execute(query)
        transaction_counts = result.all()

        counts_dict = {status: count for status, count in transaction_counts}
        total_transactions = sum(counts_dict.values())

        successful_transactions = (
            counts_dict.get("completed", 0)
            + counts_dict.get("successful", 0)
            + counts_dict.get("succeeded", 0)
        )
        success_rate = (
            (successful_transactions / total_transactions * 100)
            if total_transactions > 0
            else 0
        )

        # ... rest of the function
        return {
            "total_transactions": total_transactions,
            "success_rate": success_rate,
            # ... other metrics
        }

    async def _save_metrics(
        self, user_id: str, metrics_data: Dict[str, Any]
    ) -> BusinessMetrics:
        # This is a placeholder for the actual implementation.
        # In a real application, this would save the calculated metrics to the BusinessMetrics table.
        self.logger.info(f"Saving metrics for user {user_id}: {metrics_data}")
        # For now, return a dummy BusinessMetrics object.
        return BusinessMetrics(user_id=user_id, monthly_revenue=12345.67)
