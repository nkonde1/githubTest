# backend/app/models/user.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, UUID, Text, ForeignKey, Float, func
from sqlalchemy.dialects.postgresql import JSON, ARRAY
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

class User(Base):
    """User model for SMB retailers"""
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
        
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Business Information
    business_name = Column(String(255), nullable=False)
    business_type = Column(String(100))  # retail, restaurant, service, etc.
    industry = Column(String(100))
    
    # Personal Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone_number = Column(String(20))
    
    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    country = Column(String(50), default="US")
    
    # Account Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    
    # Subscription & Billing
    subscription_tier = Column(String(50), default="free_trial")  # free_trial, 6_months, 12_months
    subscription_status = Column(String(50), default="active") # active, overdue, cancelled
    subscription_start_date = Column(DateTime(timezone=True))
    subscription_end_date = Column(DateTime(timezone=True))
    billing_due_date = Column(DateTime(timezone=True))
    last_payment_date = Column(DateTime(timezone=True))
    last_payment_amount = Column(Float)
    payment_provider = Column(String(50)) # mtn, airtel
    
    # Integration Settings
    stripe_account_id = Column(String(255))
    shopify_store_url = Column(String(255))
    quickbooks_company_id = Column(String(255))
    
    # Preferences
    timezone = Column(String(50), default="UTC")
    currency = Column(String(3), default="USD")
    notification_preferences = Column(JSON, default={})
    
    # AI Settings
    ai_insights_enabled = Column(Boolean, default=True)
    ai_recommendations_enabled = Column(Boolean, default=True)
    
    # Compliance
    gdpr_consent = Column(Boolean, default=False)
    terms_accepted_at = Column(DateTime(timezone=True))
    privacy_policy_accepted_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))
    
    # Metadata
    user_metadata = Column(JSON, default={})  # For storing additional custom fields
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    payment_methods = relationship("PaymentMethod", back_populates="user")
    financing_offers = relationship("FinancingOffer", back_populates="user")
    loan_applications = relationship("LoanApplication", back_populates="user")
    business_metrics = relationship("BusinessMetrics", back_populates="user")
    
    # New fields
    is_superuser = Column(Boolean(), default=False)
    is_admin = Column(Boolean(), default=False)
    permissions = Column(ARRAY(String), nullable=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    api_key_hash = Column(String, nullable=True)

    # Shopify integration fields
    shopify_access_token = Column(String(255), nullable=True)
    shopify_shop_domain = Column(String(255), nullable=True)
    shopify_integration_active = Column(Boolean, default=False)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, business={self.business_name})>"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self):
        """Convert user to dictionary for serialization"""
        return {
            "id": str(self.id),
            "email": self.email,
            "business_name": self.business_name,
            "business_type": self.business_type,
            "full_name": self.full_name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "subscription_tier": self.subscription_tier,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "is_superuser": self.is_superuser,
            "is_admin": self.is_admin,
            "permissions": self.permissions,
            "tenant_id": str(self.tenant_id) if self.tenant_id else None
        }

class UserSession(Base):
    """User session tracking for security and analytics"""
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False)
    
    # Session Details
    ip_address = Column(String(45))  # IPv6 support
    user_agent = Column(Text)
    device_fingerprint = Column(String(255))
    
    # Location (optional, for security alerts)
    country = Column(String(50))
    region = Column(String(100))
    city = Column(String(100))
    
    # Session Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"