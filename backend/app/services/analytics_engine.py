# backend/app/services/analytics_engine.py
"""
Analytics engine for generating business insights and metrics
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.transaction import Transaction, TransactionInsight
from ..models.financing import BusinessMetrics
from ..models.user import User
from ..core.logging import get_logger
from .ai_agent import AIAgentService

logger = get_logger(__name__)


class AnalyticsEngine:
    """Core analytics engine for business intelligence"""
    
    def __init__(self, db: AsyncSession, ai_service: AIAgentService):
        self.db = db
        self.ai_service = ai_service
    
    async def generate_dashboard_metrics(self, user_id: str) -> Dict[str, Any]:
        """Generate comprehensive dashboard metrics for a user"""
        try:
            # Get time periods
            now = datetime.utcnow()
            last_30_days = now - timedelta(days=30)
            last_7_days = now - timedelta(days=7)
            
            # Revenue metrics
            revenue_metrics = await self._calculate_revenue_metrics(user_id, last_30_days, now)
            
            # Transaction metrics
            transaction_metrics = await self._calculate_transaction_metrics(user_id, last_30_days, now)
            
            # Growth metrics
            growth_metrics = await self._calculate_growth_metrics(user_id)
            
            # Risk metrics
            risk_metrics = await self._calculate_risk_metrics(user_id, last_30_days, now)
            
            # Financing data
            financing_data = await self._get_financing_data(user_id)
            
            # AI insights
            ai_insights = await self._generate_ai_insights(user_id, {
                "revenue": revenue_metrics,
                "transactions": transaction_metrics,
                "growth": growth_metrics,
                "risk": risk_metrics,
                "financing": financing_data
            })
            
            return {
                "revenue": revenue_metrics,
                "transactions": transaction_metrics,
                "growth": growth_metrics,
                "risk": risk_metrics,
                "financing": financing_data,
                "ai_insights": ai_insights,
                "generated_at": now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating dashboard metrics for user {user_id}: {str(e)}")
            raise
    
    async def _calculate_revenue_metrics(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate revenue-related metrics, normalized to USD"""
        
        # Exchange rates to USD (approximate)
        rates_to_usd = {
            'USD': 1.0,
            'EUR': 1.05,
            'ZMW': 0.037,
            'GBP': 1.25,
            'CAD': 0.74
        }

        # Current period revenue - Group by currency
        query = select(
            Transaction.currency,
            func.sum(Transaction.amount)
        ).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.status.in_(["completed", "successful", "succeeded"]),
                Transaction.transaction_type == "payment",
                Transaction.created_at >= start_date,
                Transaction.created_at <= end_date
            )
        ).group_by(Transaction.currency)
        
        result = await self.db.execute(query)
        current_totals = result.all()
        
        current_revenue_usd = 0.0
        for currency, amount in current_totals:
            rate = rates_to_usd.get(currency, 1.0)
            current_revenue_usd += float(amount or 0) * rate
            
        # Previous period for comparison
        prev_start = start_date - (end_date - start_date)
        query = select(
            Transaction.currency,
            func.sum(Transaction.amount)
        ).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.status.in_(["completed", "successful", "succeeded"]),
                Transaction.transaction_type == "payment",
                Transaction.created_at >= prev_start,
                Transaction.created_at < start_date
            )
        ).group_by(Transaction.currency)
        
        result = await self.db.execute(query)
        prev_totals = result.all()
        
        prev_revenue_usd = 0.0
        for currency, amount in prev_totals:
            rate = rates_to_usd.get(currency, 1.0)
            prev_revenue_usd += float(amount or 0) * rate
        
        # Calculate growth
        revenue_growth = 0
        if prev_revenue_usd > 0:
            revenue_growth = ((current_revenue_usd - prev_revenue_usd) / prev_revenue_usd) * 100
        
        # Average transaction value (in USD)
        # We need total count for this since we can't easily avg mixed currencies
        count_query = select(func.count(Transaction.id)).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.status.in_(["completed", "successful", "succeeded"]),
                Transaction.transaction_type == "payment",
                Transaction.created_at >= start_date,
                Transaction.created_at <= end_date
            )
        )
        count_result = await self.db.execute(count_query)
        tx_count = count_result.scalar() or 0
        
        avg_transaction_usd = (current_revenue_usd / tx_count) if tx_count > 0 else 0.0
        
        return {
            "total_revenue": float(current_revenue_usd),
            "previous_revenue": float(prev_revenue_usd),
            "revenue_growth_percent": float(revenue_growth),
            "average_transaction_value": float(avg_transaction_usd),
            "period_days": (end_date - start_date).days
        }
    
    async def _calculate_risk_metrics(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate risk-related metrics"""
        
        # Get total transactions
        query = select(func.count(Transaction.id)).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.created_at >= start_date,
                Transaction.created_at <= end_date
            )
        )
        result = await self.db.execute(query)
        total_transactions = result.scalar() or 0
        
        # Get failed transactions
        query = select(func.count(Transaction.id)).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.status == "failed",
                Transaction.created_at >= start_date,
                Transaction.created_at <= end_date
            )
        )
        result = await self.db.execute(query)
        failed_transactions = result.scalar() or 0
        
        # Get refunded transactions
        query = select(func.count(Transaction.id)).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.transaction_type == "refund",
                Transaction.created_at >= start_date,
                Transaction.created_at <= end_date
            )
        )
        result = await self.db.execute(query)
        refunded_transactions = result.scalar() or 0
        
        # Calculate rates
        failure_rate = (failed_transactions / total_transactions * 100) if total_transactions > 0 else 0
        refund_rate = (refunded_transactions / total_transactions * 100) if total_transactions > 0 else 0
        
        # Calculate risk score (0-100, lower is better)
        risk_score = min(100, (failure_rate * 2) + (refund_rate * 3))
        
        risk_level = "low"
        if risk_score > 20:
            risk_level = "medium"
        if risk_score > 40:
            risk_level = "high"
        
        return {
            "failure_rate": failure_rate,
            "refund_rate": refund_rate,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "total_transactions_analyzed": total_transactions
        }
    
    async def _calculate_growth_metrics(self, user_id: str) -> Dict[str, Any]:
        """Calculate growth and trend metrics"""
        
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        
        # FIXED: Use text() for date_trunc to ensure proper grouping
        query = select(
            func.date_trunc(text("'month'"), Transaction.created_at).label('month'),
            func.sum(Transaction.amount).label('revenue')
        ).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.status.in_(["completed", "successful", "succeeded"]),
                Transaction.transaction_type == "payment",
                Transaction.created_at >= six_months_ago
            )
        ).group_by(
            func.date_trunc(text("'month'"), Transaction.created_at)
        )
        
        result = await self.db.execute(query)
        monthly_revenue = result.all()
        
        # FIXED: Handle both datetime and string results from date_trunc
        monthly_data = []
        for month, revenue in monthly_revenue:
            # month could be datetime or string depending on database
            if isinstance(month, datetime):
                month_str = month.strftime("%Y-%m")
            else:
                # If it's a string, extract YYYY-MM format
                month_str = str(month)[:7] if month else "unknown"
            
            monthly_data.append({
                "month": month_str,
                "revenue": float(revenue) if revenue else 0.0
            })
        
        # Calculate growth trend
        growth_trend = "stable"
        if len(monthly_data) >= 2:
            recent_avg = sum(d["revenue"] for d in monthly_data[-2:]) / 2 if monthly_data[-2:] else 0
            older_avg = sum(d["revenue"] for d in monthly_data[:-2]) / max(1, len(monthly_data) - 2) if monthly_data[:-2] else 0
            
            if recent_avg > older_avg * 1.1 and older_avg > 0:
                growth_trend = "growing"
            elif recent_avg < older_avg * 0.9 and older_avg > 0:
                growth_trend = "declining"
        
        return {
            "monthly_revenue": monthly_data,
            "growth_trend": growth_trend,
            "total_months": len(monthly_data)
        }
    
    async def _calculate_transaction_metrics(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate transaction-related metrics"""
        
        # Get transaction counts by status
        query = select(
            Transaction.status,
            func.count(Transaction.id).label('count')
        ).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.created_at >= start_date,
                Transaction.created_at <= end_date
            )
        ).group_by(Transaction.status)
        
        result = await self.db.execute(query)
        transaction_counts = result.all()
        
        counts_dict = {status: count for status, count in transaction_counts}
        total_transactions = sum(counts_dict.values())
        
        # Calculate success rate
        successful_transactions = counts_dict.get("completed", 0) + counts_dict.get("successful", 0) + counts_dict.get("succeeded", 0)
        success_rate = (successful_transactions / total_transactions * 100) if total_transactions > 0 else 0
        
        # Get daily transaction trends
        query = select(
            func.date(Transaction.created_at).label('date'),
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('amount')
        ).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.status.in_(["completed", "successful", "succeeded"]),
                Transaction.created_at >= start_date,
                Transaction.created_at <= end_date
            )
        ).group_by(func.date(Transaction.created_at))
        
        result = await self.db.execute(query)
        daily_trends = result.all()
        
        trends = [
            {
                "date": trend.date.isoformat() if hasattr(trend.date, 'isoformat') else str(trend.date),
                "transaction_count": trend.count,
                "revenue": float(trend.amount) if trend.amount else 0.0
            }
            for trend in daily_trends
        ]
        
        return {
            "total_transactions": total_transactions,
            "successful_transactions": successful_transactions,
            "failed_transactions": counts_dict.get("failed", 0),
            "pending_transactions": counts_dict.get("pending", 0),
            "success_rate": success_rate,
            "daily_trends": trends
        }
    
    async def _generate_ai_insights(self, user_id: str, metrics_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate AI-powered insights from metrics data"""
        
        try:
            # Prepare context for AI
            context = f"""
            Business Metrics Analysis:
            - Total Revenue (30 days): ${metrics_data['revenue']['total_revenue']:.2f}
            - Revenue Growth: {metrics_data['revenue']['revenue_growth_percent']:.1f}%
            - Transaction Success Rate: {metrics_data['transactions']['success_rate']:.1f}%
            - Risk Level: {metrics_data['risk']['risk_level']}
            - Growth Trend: {metrics_data['growth']['growth_trend']}
            
            Financing Context:
            - Active Offers: {len(metrics_data.get('financing', {}).get('active_offers', []))}
            - Recent Applications: {len(metrics_data.get('financing', {}).get('applications', []))}
            """
            
            # Generate insights using AI
            insights_response = await self.ai_service.generate_business_insights(context)
            
            return [
                {
                    "type": "revenue_analysis",
                    "title": "Revenue Performance",
                    "description": insights_response.get("revenue_analysis", ""),
                    "priority": "high" if metrics_data['revenue']['revenue_growth_percent'] < 0 else "medium"
                },
                {
                    "type": "risk_assessment",
                    "title": "Risk Analysis",
                    "description": insights_response.get("risk_analysis", ""),
                    "priority": "high" if metrics_data['risk']['risk_level'] == "high" else "low"
                },
                {
                    "type": "growth_opportunity",
                    "title": "Growth Opportunities",
                    "description": insights_response.get("growth_opportunities", ""),
                    "priority": "medium"
                }
            ]
            
        except Exception as e:
            logger.error(f"Error generating AI insights: {str(e)}")
            return []

    async def _get_financing_data(self, user_id: str) -> Dict[str, Any]:
        """Fetch financing offers and loan applications for the user"""
        try:
            from ..models.financing import FinancingOffer, LoanApplication
            
            # Fetch active/recent offers
            offers_query = select(FinancingOffer).where(
                FinancingOffer.user_id == user_id,
                FinancingOffer.expires_at >= datetime.utcnow()
            )
            offers_result = await self.db.execute(offers_query)
            offers = offers_result.scalars().all()
            
            # Fetch loan applications
            apps_query = select(LoanApplication).where(
                LoanApplication.user_id == user_id
            ).order_by(LoanApplication.created_at.desc())
            apps_result = await self.db.execute(apps_query)
            applications = apps_result.scalars().all()
            
            return {
                "active_offers": [
                    {
                        "provider": o.lender_name,
                        "amount": float(o.amount),
                        "interest_rate": float(o.interest_rate),
                        "term_months": o.term_months,
                        "type": o.offer_type
                    } for o in offers
                ],
                "applications": [
                    {
                        "status": a.status,
                        "amount": float(a.requested_amount),
                        "date": a.created_at.isoformat() if a.created_at else None,
                        "type": "loan_application"
                    } for a in applications
                ],
                "total_offers": len(offers),
                "total_applications": len(applications)
            }
        except Exception as e:
            logger.error(f"Error fetching financing data: {str(e)}")
            return {"active_offers": [], "applications": [], "error": str(e)}

    async def update_business_metrics(self, user_id: str) -> BusinessMetrics:
        """Update business metrics for a user"""
        
        try:
            # Calculate metrics for the last 30 days
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            # Calculate various metrics
            revenue_data = await self._calculate_revenue_metrics(user_id, start_date, end_date)
            risk_data = await self._calculate_risk_metrics(user_id, start_date, end_date)
            transaction_data = await self._calculate_transaction_metrics(user_id, start_date, end_date)
            
            # Calculate total cash flow (sum of all successful transactions, including negative subscriptions)
            cash_flow_query = select(
                Transaction.currency,
                func.sum(Transaction.amount)
            ).filter(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.status.in_(["completed", "successful", "succeeded"]),
                    Transaction.created_at >= start_date,
                    Transaction.created_at <= end_date
                )
            ).group_by(Transaction.currency)
            
            cf_result = await self.db.execute(cash_flow_query)
            cf_totals = cf_result.all()
            
            rates_to_usd = {
                'USD': 1.0,
                'EUR': 1.05,
                'ZMW': 0.037,
                'GBP': 1.25,
                'CAD': 0.74
            }
            
            total_cash_flow_usd = 0.0
            for currency, amount in cf_totals:
                rate = rates_to_usd.get(currency, 1.0)
                total_cash_flow_usd += float(amount or 0) * rate

            # Get rates from risk metrics (already calculated as percentages)
            refund_rate = Decimal(str(risk_data.get('refund_rate', 0)))
            payment_failure_rate = Decimal(str(risk_data.get('failure_rate', 0)))
            
            # Calculate chargeback rate (if you have chargeback data)
            chargeback_rate = Decimal('0')  # Placeholder - implement if you track chargebacks
            
            # Create new business metrics record
            metrics = BusinessMetrics(
                id=None,  # Let database generate UUID
                user_id=user_id,
                monthly_revenue=Decimal(str(revenue_data['total_revenue'])),
                monthly_expenses=Decimal('0'),  # To be calculated
                profit_margin=Decimal('0.20'),
                cash_flow=Decimal(str(total_cash_flow_usd)),
                customer_count=0,  # To be calculated
                avg_order_value=Decimal(str(revenue_data['average_transaction_value'])),
                repeat_customer_rate=Decimal('0'),
                inventory_turnover=Decimal('0'),
                chargeback_rate=chargeback_rate,
                refund_rate=refund_rate,
                payment_failure_rate=payment_failure_rate,
                period_start=start_date,
                period_end=end_date,
                calculated_at=datetime.utcnow()
            )
            
            # Calculate credit score using the new metrics
            # We need to temporarily add metrics to session or pass data manually
            # For simplicity, we'll pass the metrics object (even if not flushed yet, attributes are accessible)
            from .credit_score import CreditScoreService
            credit_service = CreditScoreService(self.db)
            
            # We need to ensure the metrics object has the data needed by CreditScoreService
            # CreditScoreService reads .monthly_revenue, .cash_flow, .profit_margin
            # These are already set on the 'metrics' object above.
            
            score_result = await credit_service.calculate_score(user_id, metrics)
            metrics.credit_score = score_result.get("score", 300)
            
            self.db.add(metrics)
            await self.db.commit()
            await self.db.refresh(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error updating business metrics for user {user_id}: {str(e)}")
            await self.db.rollback()
            raise
    async def backfill_credit_scores(self):
        """Backfill credit scores for metrics that have them as null"""
        try:
            # Find metrics with null credit score
            query = select(BusinessMetrics).where(BusinessMetrics.credit_score == None)
            result = await self.db.execute(query)
            metrics_list = result.scalars().all()
            
            if not metrics_list:
                return
                
            from .credit_score import CreditScoreService
            credit_service = CreditScoreService(self.db)
            
            count = 0
            for metrics in metrics_list:
                # Calculate score
                score_result = await credit_service.calculate_score(str(metrics.user_id), metrics)
                metrics.credit_score = score_result.get("score", 300)
                count += 1
            
            if count > 0:
                await self.db.commit()
                logger.info(f"Backfilled credit scores for {count} records")
                
        except Exception as e:
            logger.error(f"Error backfilling credit scores: {str(e)}")
            raise