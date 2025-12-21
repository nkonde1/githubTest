"""
Telco connection database models
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.database import Base

class TelcoConnection(Base):
    """Stores connection details for a user's telco account"""
    __tablename__ = "telco_connections"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Connection details
    provider = Column(String(20), nullable=False)  # MTN, Airtel
    wallet_number = Column(String(20), nullable=False)
    merchant_id = Column(String(50), nullable=True) # Optional, if B2B
    
    # Auth/Verification
    status = Column(String(20), default="pending") # pending, verified, failed
    access_token = Column(String, nullable=True) # Mock token for now
    verified_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="telco_connections")
