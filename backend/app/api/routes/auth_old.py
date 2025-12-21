from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
import structlog

from app.database import get_db
from app.models.user import User, UserSession
from app.schemas.auth import (
    TokenData, UserOut, LoginRequest, RegisterRequest, LoginResponse, RefreshTokenRequest, LogoutRequest
)
from app.core.auth import (
    authenticate_user,
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, verify_refresh_token, get_current_user, update_last_login
)
from app.core.config import settings
from app.core.logging import log_function_call, get_logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = get_logger(__name__)

router = APIRouter()

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=LoginResponse)
@log_function_call
async def register_user(
    user_data: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new SMB user with business information. Automatically logs in the user.
    """
    logger.info("Attempting user registration", extra={"email": user_data.email})

    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        logger.warning("Registration attempt with existing email", extra={"email": user_data.email})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        business_name=user_data.business_name,
        business_type=user_data.business_type,
        phone_number=user_data.phone_number,
        gdpr_consent=user_data.gdpr_consent,
        terms_accepted_at=datetime.utcnow() if user_data.terms_accepted else None,
        privacy_policy_accepted_at=datetime.utcnow() if user_data.privacy_accepted else None
    )

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        logger.info("New user registered",
                     extra={"user_id": str(new_user.id),
                            "business_name": new_user.business_name})

        # Generate tokens for immediate login after registration
        access_token = create_access_token(data={"sub": str(new_user.id)})
        refresh_token = create_refresh_token(data={"sub": str(new_user.id)})

        # Create session record for the new user
        session = UserSession(
            user_id=new_user.id,
            session_token=refresh_token,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", ""),
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        db.add(session)
        await db.commit()

        return LoginResponse(
            user=UserOut.model_validate(new_user),
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token,
        )

    except Exception as e:
        await db.rollback()
        logger.error("User registration failed", extra={"error_message": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=LoginResponse)
@log_function_call
async def login_user(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticates user and returns access/refresh tokens. Uses OAuth2PasswordRequestForm (form-data).
    """
    logger.info("Attempting form login", extra={"username": form_data.username})
    
    # Use async query
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning("Failed form login attempt", extra={"email": form_data.username})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning("Form login attempt by inactive user", extra={"user_id": str(user.id)})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )

    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Create session record
    session = UserSession(
        user_id=user.id,
        session_token=refresh_token,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    # Update last login
    await update_last_login(db, user)

    try:
        db.add(session)
        await db.commit()
        await db.refresh(user)

        logger.info("User logged in successfully (form)",
                     extra={"user_id": str(user.id),
                            "business_name": user.business_name})

        return LoginResponse(
            user=UserOut.model_validate(user),
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token,
        )

    except Exception as e:
        await db.rollback()
        logger.error("Login session creation failed (form)", extra={"error_message": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/login-json", response_model=LoginResponse)
@log_function_call
async def login_json(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticates user with JSON payload and returns access/refresh tokens.
    """
    logger.info("Attempting JSON login", extra={"email": login_data.email})
    
    user = await authenticate_user(db, login_data.email, login_data.password)

    if not user:
        logger.warning("Failed JSON login attempt: Incorrect credentials", extra={"email": login_data.email})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        logger.warning("JSON login attempt by inactive user", extra={"user_id": str(user.id)})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    session = UserSession(
        user_id=user.id,
        session_token=refresh_token,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    update_last_login(db, user)

    try:
        db.add(session)
        await db.commit()
        await db.refresh(user)

        logger.info("User logged in successfully (JSON)",
                     extra={"user_id": str(user.id),
                            "business_name": user.business_name})

        # Handle JSON fields explicitly
        user_data_for_pydantic = user.__dict__.copy()

        # Handle 'notification_preferences'
        if user_data_for_pydantic.get("notification_preferences") == {}:
            user_data_for_pydantic["notification_preferences"] = None
        
        # Handle 'user_metadata'
        if user_data_for_pydantic.get("user_metadata") == {}:
            user_data_for_pydantic["user_metadata"] = None

        return LoginResponse(
            user=UserOut.model_validate(user_data_for_pydantic),
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token,
        )

    except Exception as e:
        await db.rollback()
        logger.error("Login session creation failed (JSON)", extra={"error_message": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/refresh", response_model=LoginResponse)
@log_function_call
async def refresh_token_endpoint(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    """
    logger.info("Attempting token refresh", extra={"token_prefix": token_data.refresh_token[:10] + "..."})
    try:
        payload = await verify_refresh_token(token_data.refresh_token, db)
        user_id = payload.get("sub")

        if not user_id:
            logger.warning("Token refresh failed: Invalid refresh token payload", extra={"payload": payload})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload"
            )

        # Verify session exists and is active
        result = await db.execute(select(UserSession).where(
            UserSession.session_token == token_data.refresh_token,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ))
        session = result.scalar_one_or_none()

        if not session:
            logger.warning("Token refresh failed: Session expired or invalid", extra={"user_id": user_id})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or invalid"
            )

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            logger.warning("Token refresh failed: User not found or inactive", extra={"user_id": user_id})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Create new access token
        new_access_token = create_access_token(data={"sub": str(user_id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user_id)})

        # Update session activity
        session.last_activity_at = datetime.utcnow()
        await db.commit()
        await db.refresh(user)

        logger.info("Token refreshed successfully", extra={"user_id": str(user.id)})

        return LoginResponse(
            user=UserOut.model_validate(user),
            access_token=new_access_token,
            token_type="bearer",
            refresh_token=new_refresh_token,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("An unexpected error occurred during token refresh", extra={"error_message": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh",
        )

@router.post("/logout")
@log_function_call
async def logout_user(
    logout_data: LogoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout user and invalidate session based on refresh token.
    """
    logger.info("Logout request received", extra={"user_id": str(current_user.id), "token_prefix": logout_data.refresh_token[:10]})
    try:
        # Deactivate specific session matching the refresh token and user ID
        session = db.query(UserSession).filter(
            UserSession.session_token == logout_data.refresh_token,
            UserSession.user_id == current_user.id,
            UserSession.is_active == True
        ).first()

        if session:
            session.is_active = False
            db.commit()
            logger.info("User session deactivated", extra={"user_id": str(current_user.id), "session_id": str(session.id)})
            return {"message": "Successfully logged out"}
        else:
            logger.warning("Logout attempt for non-existent or inactive session", extra={"user_id": str(current_user.id)})
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or already inactive"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Logout failed", extra={"error_message": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get("/me", response_model=UserOut)
@log_function_call
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    """
    logger.info("Fetching current user info", extra={"user_id": str(current_user.id)})
    return current_user

@router.post("/logout-all")
@log_function_call
async def logout_all_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout from all devices/sessions for the current user.
    """
    logger.info("Attempting to logout all sessions", extra={"user_id": str(current_user.id)})
    try:
        # Deactivate all active user sessions
        updated_count = db.query(UserSession).filter(
            UserSession.user_id == current_user.id,
            UserSession.is_active == True
        ).update({"is_active": False}, synchronize_session=False)

        db.commit()

        logger.info("All sessions logged out", extra={"user_id": str(current_user.id), "deactivated_sessions_count": updated_count})

        return {"message": f"Logged out from {updated_count} devices."}

    except Exception as e:
        db.rollback()
        logger.error("Logout all failed", extra={"error_message": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout all failed"
        )

@router.post("/create-demo-user", response_model=LoginResponse)
@log_function_call
async def create_demo_user_endpoint(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Create or get demo user for testing.
    """
    logger.info("Attempting to create/retrieve demo user")
    # Check if demo user already exists
    demo_user = db.query(User).filter(User.email == "demo@financeai.com").first()
    if demo_user:
        logger.info("Demo user already exists, logging in existing user", extra={"email": demo_user.email})
        # If demo user exists, just log them in and return tokens
        access_token = create_access_token(data={"sub": str(demo_user.id)})
        refresh_token = create_refresh_token(data={"sub": str(demo_user.id)})

        # Update last login
        update_last_login(db, demo_user)

        # Create session record for the existing demo user
        session = UserSession(
            user_id=demo_user.id,
            session_token=refresh_token,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", ""),
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        db.add(session)
        db.commit()

        logger.info("Demo user logged in successfully", extra={"user_id": str(demo_user.id), "email": demo_user.email})
        return LoginResponse(
            user=UserOut.model_validate(demo_user),
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token,
        )

    # Create demo user if not exists
    hashed_password = get_password_hash("demo123")
    new_demo_user = User(
        email="demo@financeai.com",
        first_name="Demo",
        last_name="User",
        business_name="Demo Company",
        business_type="retail",
        hashed_password=hashed_password,
        is_active=True,
        is_verified=True,
        subscription_tier="basic"
    )

    try:
        db.add(new_demo_user)
        db.commit()
        db.refresh(new_demo_user)

        logger.info("New demo user created successfully", extra={"user_id": str(new_demo_user.id), "email": new_demo_user.email})

        # Generate tokens for the new demo user
        access_token = create_access_token(data={"sub": str(new_demo_user.id)})
        refresh_token = create_refresh_token(data={"sub": str(new_demo_user.id)})

        # Create session record for the new demo user
        session = UserSession(
            user_id=new_demo_user.id,
            session_token=refresh_token,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", ""),
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        db.add(session)
        db.commit()
        db.refresh(new_demo_user)

        return LoginResponse(
            user=UserOut.model_validate(new_demo_user),
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token,
        )

    except Exception as e:
        db.rollback()
        logger.error("Demo user creation failed unexpectedly", extra={"error_message": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create demo user"
        )

@router.options("/login-json")
async def auth_options():
    """Handle preflight requests for login"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
        }
    )