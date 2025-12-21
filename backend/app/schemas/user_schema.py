"""
User-related Pydantic schemas for the AI-embedded finance platform.

This module defines all user-related data validation schemas including:
- User registration and authentication
- Profile management
- Business information
- GDPR-compliant data handling
- Security and role-based access control
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Annotated # Import Annotated
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, validator, root_validator
# No longer need to import constr, conint directly if using Annotated and Field
# from pydantic.types import constr, conint # REMOVE THIS LINE
import re


class UserRole(str, Enum):
    """User role enumeration for role-based access control."""
    ADMIN = "admin"
    BUSINESS_OWNER = "business_owner"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    READONLY = "readonly"


class BusinessType(str, Enum):
    """Business type classification for targeted features."""
    RETAIL = "retail"
    ECOMMERCE = "ecommerce"
    RESTAURANT = "restaurant"
    SERVICE = "service"
    MANUFACTURING = "manufacturing"
    OTHER = "other"


class SubscriptionTier(str, Enum):
    """Subscription tier for feature access control."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class UserPreferences(BaseModel):
    """User preferences for personalization and AI recommendations."""
    language: str = Field(default="en", description="User interface language")
    timezone: str = Field(default="UTC", description="User timezone")
    currency: str = Field(default="USD", description="Default currency")
    notifications_email: bool = Field(default=True, description="Email notifications enabled")
    notifications_push: bool = Field(default=True, description="Push notifications enabled")
    ai_insights_frequency: Annotated[str, Field(
        default="daily", 
        description="AI insights delivery frequency",
        regex="^(real_time|hourly|daily|weekly|monthly)$"
    )]
    dashboard_widgets: List[str] = Field(
        default_factory=lambda: ["revenue", "transactions", "cash_flow", "ai_insights"],
        description="Active dashboard widgets"
    )
    data_sharing_consent: bool = Field(default=False, description="GDPR data sharing consent")
    analytics_sharing: bool = Field(default=False, description="Anonymous analytics sharing")


class BusinessProfile(BaseModel):
    """Business profile information for context-aware AI insights."""
    # Corrected: Use Annotated[str, Field(strip_whitespace=True, min_length=1, max_length=200)]
    business_name: Annotated[str, Field(strip_whitespace=True, min_length=1, max_length=200)]
    business_type: BusinessType
    industry: Optional[str] = Field(None, max_length=100, description="Specific industry classification")
    # Corrected: Use Annotated[int, Field(ge=1, le=10000)]
    business_size: Annotated[int, Field(ge=1, le=10000, description="Number of employees")]
    annual_revenue: Optional[float] = Field(None, ge=0, description="Annual revenue in USD")
    business_address: Optional[str] = Field(None, max_length=500)
    business_phone: Optional[str] = Field(None, regex=r'^\+?[\d\s\-\(\)]{10,20}$')
    website_url: Optional[str] = Field(None, max_length=255)
    tax_id: Optional[str] = Field(None, max_length=50, description="Business tax identification")
    established_date: Optional[datetime] = Field(None, description="Business establishment date")
    
    @validator('website_url')
    def validate_website_url(cls, v):
        if v and not re.match(r'^https?://', v):
            return f"https://{v}"
        return v


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr = Field(description="User email address")
    # Corrected: Use Annotated[str, Field(strip_whitespace=True, min_length=1, max_length=50)]
    first_name: Annotated[str, Field(strip_whitespace=True, min_length=1, max_length=50)]
    # Corrected: Use Annotated[str, Field(strip_whitespace=True, min_length=1, max_length=50)]
    last_name: Annotated[str, Field(strip_whitespace=True, min_length=1, max_length=50)]
    phone: Optional[str] = Field(None, regex=r'^\+?[\d\s\-\(\)]{10,20}$')
    role: UserRole = Field(default=UserRole.BUSINESS_OWNER)
    is_active: bool = Field(default=True, description="User account status")
    preferences: UserPreferences = Field(default_factory=UserPreferences)


class UserCreate(UserBase):
    """Schema for user creation/registration."""
    # Corrected: Use Annotated[str, Field(min_length=8, max_length=128)]
    password: Annotated[str, Field(min_length=8, max_length=128, description="User password")]
    confirm_password: str = Field(description="Password confirmation")
    business_profile: BusinessProfile = Field(description="Business information")
    terms_accepted: bool = Field(description="Terms of service acceptance")
    privacy_accepted: bool = Field(description="Privacy policy acceptance")
    marketing_consent: bool = Field(default=False, description="Marketing communications consent")
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password meets security requirements."""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:,.<>?]', v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @root_validator(skip_on_set=True) # Use skip_on_set for root_validator in Pydantic v2
    def validate_passwords_match(cls, values):
        """Ensure password and confirmation match."""
        password = values.get('password')
        confirm_password = values.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise ValueError('Passwords do not match')
        return values
    
    @root_validator(skip_on_set=True) # Use skip_on_set for root_validator in Pydantic v2
    def validate_required_consents(cls, values):
        """Ensure required legal consents are provided."""
        if not values.get('terms_accepted'):
            raise ValueError('Terms of service must be accepted')
        if not values.get('privacy_accepted'):
            raise ValueError('Privacy policy must be accepted')
        return values


class UserUpdate(BaseModel):
    """Schema for user profile updates."""
    # Corrected: Use Optional[Annotated[str, Field(strip_whitespace=True, min_length=1, max_length=50)]]
    first_name: Optional[Annotated[str, Field(strip_whitespace=True, min_length=1, max_length=50)]] = None
    # Corrected: Use Optional[Annotated[str, Field(strip_whitespace=True, min_length=1, max_length=50)]]
    last_name: Optional[Annotated[str, Field(strip_whitespace=True, min_length=1, max_length=50)]] = None
    phone: Optional[str] = Field(None, regex=r'^\+?[\d\s\-\(\)]{10,20}$')
    preferences: Optional[UserPreferences] = None
    business_profile: Optional[BusinessProfile] = None


class UserPasswordChange(BaseModel):
    """Schema for password change operations."""
    current_password: str = Field(description="Current password")
    # Corrected: Use Annotated[str, Field(min_length=8, max_length=128)]
    new_password: Annotated[str, Field(min_length=8, max_length=128, description="New password")]
    confirm_new_password: str = Field(description="New password confirmation")
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """Validate new password meets security requirements."""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:,.<>?]', v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @root_validator(skip_on_set=True) # Use skip_on_set for root_validator in Pydantic v2
    def validate_passwords_match(cls, values):
        """Ensure new password and confirmation match."""
        new_password = values.get('new_password')
        confirm_new_password = values.get('confirm_new_password')
        if new_password and confirm_new_password and new_password != confirm_new_password:
            raise ValueError('New passwords do not match')
        return values


class UserInDB(UserBase):
    """Schema for user data in database responses."""
    id: int = Field(description="User unique identifier")
    created_at: datetime = Field(description="Account creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    login_count: int = Field(default=0, description="Total login count")
    subscription_tier: SubscriptionTier = Field(default=SubscriptionTier.FREE)
    business_profile: Optional[BusinessProfile] = None
    email_verified: bool = Field(default=False, description="Email verification status")
    phone_verified: bool = Field(default=False, description="Phone verification status")
    mfa_enabled: bool = Field(default=False, description="Multi-factor authentication status")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserPublic(BaseModel):
    """Public user schema for external API responses (GDPR-compliant)."""
    id: int
    first_name: str
    last_name: str
    role: UserRole
    business_name: Optional[str] = None
    business_type: Optional[BusinessType] = None
    subscription_tier: SubscriptionTier
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserList(BaseModel):
    """Schema for paginated user lists."""
    users: List[UserPublic]
    total: int = Field(description="Total number of users")
    page: int = Field(description="Current page number")
    per_page: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")


class UserAnalytics(BaseModel):
    """User analytics and activity metrics."""
    user_id: int
    total_logins: int
    last_activity: Optional[datetime]
    feature_usage: Dict[str, int] = Field(
        default_factory=dict,
        description="Feature usage statistics"
    )
    ai_interactions: int = Field(default=0, description="AI agent interaction count")
    insights_generated: int = Field(default=0, description="AI insights generated")
    dashboard_views: int = Field(default=0, description="Dashboard view count")
    data_exports: int = Field(default=0, description="Data export count")
    
    class Config:
        from_attributes = True


class GDPRDataRequest(BaseModel):
    """GDPR data request schema."""
    # Corrected: Use Annotated[str, Field(regex="^(export|delete|update)$")]
    request_type: Annotated[str, Field(regex="^(export|delete|update)$")]
    user_id: int
    requested_data: Optional[List[str]] = Field(
        default=None,
        description="Specific data categories requested"
    )
    reason: Optional[str] = Field(None, max_length=500)
    
    class Config:
        schema_extra = {
            "example": {
                "request_type": "export",
                "user_id": 123,
                "requested_data": ["profile", "transactions", "analytics"],
                "reason": "User data portability request"
            }
        }


class UserSession(BaseModel):
    """User session management schema."""
    session_id: str
    user_id: int
    ip_address: str
    user_agent: str
    created_at: datetime
    expires_at: datetime
    is_active: bool = True
    
    class Config:
        from_attributes = True


class SecurityEvent(BaseModel):
    """Security event logging schema."""
    user_id: int
    # Corrected: Use Annotated[str, Field(regex="^(login|logout|password_change|mfa_enable|suspicious_activity)$")]
    event_type: Annotated[str, Field(regex="^(login|logout|password_change|mfa_enable|suspicious_activity)$")]
    ip_address: str
    user_agent: str
    success: bool
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True


# API Response wrapper schemas
class UserResponse(BaseModel):
    """Standard user API response wrapper."""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[UserInDB] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "User retrieved successfully",
                "data": {
                    "id": 1,
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "role": "business_owner"
                }
            }
        }


class UserListResponse(BaseModel):
    """Standard user list API response wrapper."""
    success: bool = True
    message: str = "Users retrieved successfully"
    data: Optional[UserList] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Users retrieved successfully",
                "data": {
                    "users": [],
                    "total": 0,
                    "page": 1,
                    "per_page": 20,
                    "pages": 0
                }
            }
        }