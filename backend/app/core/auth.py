# backend/app/core/auth.py
"""
Core authentication and security functions for JWT token management,
password hashing, and user authentication.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.database import get_db
from app.models.user import User
from app.schemas.auth import TokenData # Ensure this schema is defined for token data
from app.core.config import settings

# --- Configuration ---
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

# Calculate REFRESH_TOKEN_EXPIRE_MINUTES from days for timedelta
REFRESH_TOKEN_EXPIRE_MINUTES = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login-json") # Update tokenUrl if needed

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Password Hashing Functions ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

# --- JWT Token Functions ---
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with an 'access' type claim."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire, "type": "access"}) # Add token type
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token with a 'refresh' type claim."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire, "type": "refresh"}) # Add token type
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verifies a generic JWT token and returns its payload.
    This function is internal and used by specific token verification functions.
    Raises HTTPException if the token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise credentials_exception from e

def verify_access_token(token: str, db: Session) -> str:
    """
    Verifies an access token, checks its type, and returns the user ID (sub).
    Raises HTTPException if the token is invalid, expired, not an access token,
    or if the associated user is not found/active.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid access token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = verify_jwt_token(token) # Reuse generic verification
        
        # Ensure it's an access token
        token_type = payload.get("type")
        if token_type != "access":
            raise credentials_exception 

        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Optional: Check if the user associated with the token exists and is active
        # This adds an extra layer of security and ensures the token is tied to a valid user.
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise credentials_exception

        return user_id
    except HTTPException: # Re-raise HTTPExceptions from verify_jwt_token or our checks
        raise
    except Exception as e:
        # Catch any other unexpected errors during token verification
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during access token verification.",
        ) from e


async def verify_refresh_token(token: str, db: AsyncSession) -> Dict[str, Any]:
    """
    Verifies a refresh token, checks its type, and returns the payload dictionary.
    Raises HTTPException if the token is invalid, expired, not a refresh token,
    or if the associated user is not found/active.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = verify_jwt_token(token) # Reuse generic verification
        
        # Ensure it's a refresh token
        token_type = payload.get("type")
        if token_type != "refresh":
            raise credentials_exception # Not a refresh token

        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Optional: Check if the user associated with the token exists and is active
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise credentials_exception

        return payload  # Return the full payload dictionary
    except HTTPException: # Re-raise HTTPExceptions from verify_jwt_token or our checks
        raise
    except Exception as e:
        # Catch any other unexpected errors during token verification
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during refresh token verification.",
        ) from e


# --- User Authentication and Retrieval ---
async def authenticate_user(db: AsyncSession, email: str, password: str):
    """Authenticate a user with email and password."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT access token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
        
    try:
        payload = verify_jwt_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception from e
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user

async def create_demo_user(db: AsyncSession):
    """Create or verify demo user exists"""
    # Check if demo user already exists
    result = await db.execute(
        select(User).where(User.email == "demo@financeai.com")
    )
    demo_user = result.scalar_one_or_none()
    
    if demo_user:
        return demo_user

    # Create demo user with correct field names
    hashed_password = get_password_hash("demo123")
    demo_user = User(
        email="demo@financeai.com",
        first_name="Demo",
        last_name="User",
        business_name="Demo Company",
        hashed_password=hashed_password,
        is_active=True,
        business_type="other",
        phone_number="",
        gdpr_consent=True,
        terms_accepted_at=datetime.utcnow(),
        privacy_policy_accepted_at=datetime.utcnow(),
        is_verified=True,
        subscription_tier="free"
    )
    db.add(demo_user)
    await db.commit()
    await db.refresh(demo_user)
    return demo_user

async def update_last_login(db: AsyncSession, user: User):
    """Update the user's last login timestamp."""
    user.last_login_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    return user