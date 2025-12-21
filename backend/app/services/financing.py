"""
Financing and lending service
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.financing import LoanApplication, FinancingOffer
from app.models.transaction import Transaction
from app.services.analytics_engine import AnalyticsEngine
import asyncio

logger = logging.getLogger(__name__)

class FinancingService:
    """Service for processing financing applications and generating offers"""
    
    def __init__(self):
        self.analytics_engine = AnalyticsEngine()
    
    async def process_application(self, db: Session, application_id: str):
        """Process a financing application and generate offers"""
        try:
            application = db.query(LoanApplication).filter(
                LoanApplication.id == application_id
            ).first()
            
            if not application:
                logger.error(f"Application {application_id} not found")
                return
            
            # Update status
            application.status = "processing"
            db.commit()
            
            # Calculate credit score and risk assessment
            risk_score = await self._calculate_risk_score(db, application)
            
            # Generate loan offers based on risk
            offers = self._generate_loan_offers(application, risk_score)
            
            # Save offers to database
            for offer_data in offers:
                offer = FinancingOffer(
                    user_id=application.user_id,
                    application_id=application.id,
                    **offer_data
                )
                db.add(offer)
            
            # Update application status
            application.status = "completed"
            application.risk_score = risk_score
            db.commit()
            
            logger.info(f"Processed application {application_id}, generated {len(offers)} offers")
            
        except Exception as e:
            logger.error(f"Error processing application {application_id}: {str(e)}")
            # Update application status to failed
            application = db.query(LoanApplication).filter(
                LoanApplication.id == application_id
            ).first()
            if application:
                application.status = "failed"
                db.commit()
    
    async def _calculate_risk_score(self, db: Session, application: LoanApplication) -> float:
        """Calculate risk score based on financial data"""
        try:
            # Get user's financial metrics
            metrics = self.analytics_engine.calculate_revenue_metrics(
                db, application.user_id, 90
            )
            
            # Base score calculation
            score = 500  # Start with neutral score
            
            # Revenue consistency (30% weight)
            if metrics['total_revenue'] > 0:
                revenue_score = min(metrics['total_revenue'] / 10000 * 100, 200)
                score += revenue_score * 0.3
            
            # Growth rate (25% weight)
            if metrics['growth_rate'] > 0:
                growth_score = min(metrics['growth_rate'] * 5, 150)
                score += growth_score * 0.25
            
            # Transaction volume (20% weight)
            if metrics['transaction_count'] > 0:
                volume_score = min(metrics['transaction_count'] / 100 * 100, 100)
                score += volume_score * 0.2
            
            # Business age (15% weight)
            age_score = min(application.time_in_business * 10, 100)
            score += age_score * 0.15
            
            # Application amount vs revenue ratio (10% weight)
            if metrics['total_revenue'] > 0:
                ratio = application.amount_requested / (metrics['total_revenue'] * 12)
                if ratio < 0.1:
                    score += 50 * 0.1
                elif ratio < 0.3:
                    score += 25 * 0.1
            
            # Normalize to 300-850 range (like FICO)
            normalized_score = max(300, min(850, score))
            
            return round(normalized_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {str(e)}")
            return 500.0  # Return neutral score on error
    
    def _generate_loan_offers(self, application: LoanApplication, risk_score: float) -> List[Dict[str, Any]]:
        """Generate loan offers based on risk score"""
        offers = []
        
        # Define offer tiers based on risk score
        if risk_score >= 700:  # Excellent credit
            offers.extend([
                {
                    'offer_type': 'term_loan',
                    'amount': min(application.amount_requested, 250000),
                    'interest_rate': 6.5,
                    'term_months': 36,
                    'monthly_payment': self._calculate_payment(min(application.amount_requested, 250000), 6.5, 36),
                    'approval_probability': 95
                },
                {
                    'offer_type': 'line_of_credit',
                    'amount': min(application.amount_requested * 1.5, 100000),
                    'interest_rate': 8.0,
                    'term_months': 12,
                    'monthly_payment': 0,  # Interest only
                    'approval_probability': 90
                }
            ])
        elif risk_score >= 600:  # Good credit
            offers.extend([
                {
                    'offer_type': 'term_loan',
                    'amount': min(application.amount_requested, 150000),
                    'interest_rate': 9.5,
                    'term_months': 24,
                    'monthly_payment': self._calculate_payment(min(application.amount_requested, 150000), 9.5, 24),
                    'approval_probability': 80
                },
                {
                    'offer_type': 'merchant_advance',
                    'amount': min(application.amount_requested, 75000),
                    'interest_rate': 12.0,
                    'term_months': 18,
                    'monthly_payment': self._calculate_payment(min(application.amount_requested, 75000), 12.0, 18),
                    'approval_probability': 85
                }
            ])
        elif risk_score >= 500:  # Fair credit
            offers.append({
                'offer_type': 'merchant_advance',
                'amount': min(application.amount_requested, 50000),
                'interest_rate': 18.0,
                'term_months': 12,
                'monthly_payment': self._calculate_payment(min(application.amount_requested, 50000), 18.0, 12),
                'approval_probability': 65
            })
        
        return offers
    
    def _calculate_payment(self, principal: float, annual_rate: float, months: int) -> float:
        """Calculate monthly payment for loan"""
        if annual_rate == 0:
            return principal / months
        
        monthly_rate = annual_rate / 100 / 12
        payment = principal * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
        return round(payment, 2)
