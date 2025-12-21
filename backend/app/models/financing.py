# backend/app/models/financing.py
"""
Financing and lending-related database models
"""

from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base


class FinancingOffer(Base):
    """AI-generated financing offers for businesses"""
    __tablename__ = "financing_offers"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Offer details
    offer_type = Column(String(50), nullable=False)  # working_capital, equipment, line_of_credit
    amount = Column(Numeric(12, 2), nullable=False)
    interest_rate = Column(Numeric(5, 4), nullable=False)  # Annual percentage rate
    term_months = Column(Integer, nullable=False)
    
    # Approval details
    status = Column(String(20), default="pending")  # pending, approved, rejected, accepted, completed
    approval_probability = Column(Numeric(3, 2), nullable=True)  # AI-calculated probability
    
    # Requirements and conditions
    requirements = Column(JSON, default={})
    conditions = Column(JSON, default={})
    
    # Partner information
    lender_name = Column(String(100), nullable=False)
    lender_logo_url = Column(String(255), nullable=True)
    partner_id = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship('User', back_populates="financing_offers")
    applications = relationship("LoanApplication", back_populates="offer")


class LoanApplication(Base):
    """Loan applications from users"""
    __tablename__ = "loan_applications"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    offer_id = Column(String, ForeignKey("financing_offers.id"), nullable=True)
    
    # Application details
    requested_amount = Column(Numeric(12, 2), nullable=False)
    purpose = Column(Text, nullable=False)
    business_revenue = Column(Numeric(12, 2), nullable=True)
    time_in_business = Column(Integer, nullable=True)  # months
    
    # Application data
    application_data = Column(JSON, default={})
    documents = Column(JSON, default={})  # Document URLs and metadata
    
    # Status tracking
    status = Column(String(20), default="submitted")  # submitted, under_review, approved, rejected
    reviewed_at = Column(DateTime, nullable=True)
    decision_reason = Column(Text, nullable=True)
    
    # AI scoring
    credit_score = Column(Integer, nullable=True)
    risk_assessment = Column(JSON, default={})
    ai_recommendation = Column(String(20), nullable=True)  # approve, reject, manual_review
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="loan_applications")
    offer = relationship("FinancingOffer", back_populates="applications")


class BusinessMetrics(Base):
    """Business performance metrics for financing decisions"""
    __tablename__ = "business_metrics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Financial metrics
    monthly_revenue = Column(Numeric(12, 2), nullable=True)
    monthly_expenses = Column(Numeric(12, 2), nullable=True)
    profit_margin = Column(Numeric(5, 4), nullable=True)
    cash_flow = Column(Numeric(12, 2), nullable=True)
    credit_score = Column(Integer, nullable=True)  # New field for persisting credit score
    
    # Business metrics
    customer_count = Column(Integer, nullable=True)
    avg_order_value = Column(Numeric(8, 2), nullable=True)
    repeat_customer_rate = Column(Numeric(3, 2), nullable=True)
    inventory_turnover = Column(Numeric(4, 2), nullable=True)
    
    # Risk indicators (stored as percentages, 0-100)
    chargeback_rate = Column(Numeric(5, 2), nullable=True)  # Changed from (3,2) to (5,2) to support up to 999.99%
    refund_rate = Column(Numeric(5, 2), nullable=True)  # Changed from (3,2) to (5,2) to support up to 999.99%
    payment_failure_rate = Column(Numeric(5, 2), nullable=True)  # Changed from (3,2) to (5,2) to support up to 999.99%
    
    # Data period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates="business_metrics")
