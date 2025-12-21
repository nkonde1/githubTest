# backend/app/schemas/auth.py
"""
Authentication schemas for request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Any
from datetime import datetime
import uuid # Needed for UUID type hint if you use it directly

class TokenData(BaseModel):
    """Token data for JWT payload"""
    email: Optional[str] = None
    # Add other payload claims like user_id if they exist in your token
    user_id: Optional[uuid.UUID] = None # Assuming user_id is also stored in token

class Token(BaseModel):
    """Simple token response for OAuth2 compatibility"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

# --- User Schemas (Pure User Data) ---
class UserOut(BaseModel):
    """Schema for returning full user details (e.g., from /me endpoint)"""
    id: uuid.UUID # Use UUID type directly, Pydantic with from_attributes handles serialization to str
    email: EmailStr
    first_name: str
    last_name: str
    business_name: str
    business_type: Optional[str] = None
    industry: Optional[str] = None # Added
    phone_number: Optional[str] = None
    
    # Address
    address_line1: Optional[str] = None # Added
    address_line2: Optional[str] = None # Added
    city: Optional[str] = None # Added
    state: Optional[str] = None # Added
    zip_code: Optional[str] = None # Added
    country: Optional[str] = None # Added
    
    # Account Status
    is_active: bool
    is_verified: bool
    is_premium: bool # Added
    
    # Subscription & Billing
    subscription_tier: str
    subscription_status: Optional[str] = None # Added
    
    # Integration Settings
    stripe_account_id: Optional[str] = None # Added
    shopify_store_url: Optional[str] = None # Added
    quickbooks_company_id: Optional[str] = None # Added
    
    # Preferences
    timezone: Optional[str] = None # Added
    currency: Optional[str] = None # Added
    notification_preferences: Optional[dict] = None # Added (JSON column)
    
    # AI Settings
    ai_insights_enabled: Optional[bool] = None # Added
    ai_recommendations_enabled: Optional[bool] = None # Added
    
    # Compliance
    gdpr_consent: Optional[bool] = None # Added
    terms_accepted_at: Optional[datetime] = None # Added
    privacy_policy_accepted_at: Optional[datetime] = None # Added
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None # Added
    last_login_at: Optional[datetime] = None

    # Metadata
    user_metadata: Optional[dict] = None # Added (JSON column)

    class Config:
        from_attributes = True # Pydantic v2+
        # If you're on Pydantic v1, use: orm_mode = True

        # Custom JSON encoder for UUID if Pydantic doesn't convert automatically
        json_encoders = {
            uuid.UUID: str,
            datetime: lambda v: v.isoformat() if v else None # Ensures datetime is isoformatted
        }

# --- Auth Specific Schemas ---

class LoginRequest(BaseModel):
    """Login request payload"""
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    business_name: str
    business_type: Optional[str] = None
    phone_number: Optional[str] = None
    gdpr_consent: Optional[bool] = False
    terms_accepted: Optional[bool] = False
    privacy_accepted: Optional[bool] = False

class LoginResponse(BaseModel):
    """Response for successful login/registration, including user details and tokens"""
    user: UserOut # Embed the UserOut schema for user details
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None

    class Config:
        from_attributes = True # Allow ORM mode for LoginResponse if it directly takes ORM models

class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str

class LogoutRequest(BaseModel):
    """Logout request"""
    refresh_token: str