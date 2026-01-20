from datetime import datetime, timedelta, timezone
def get_utc_now():
    return datetime.now(timezone.utc)
from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from fastapi.responses import JSONResponse
from jose import JWTError
from app.database import get_db
from app.models.user import User, UserSession
from app.schemas.auth import (
    TokenData, UserOut, LoginRequest, RegisterRequest, LoginResponse, 
    RefreshTokenRequest, LogoutRequest
)
from app.core.auth import (
    authenticate_user, verify_password, get_password_hash,
    create_access_token, create_refresh_token, verify_refresh_token,
    get_current_user, update_last_login
)
from app.core.config import settings
from app.core.logging import log_function_call, get_logger

logger = get_logger(__name__)

# Remove /api/v1 from prefix since it will be added by the main app router
router = APIRouter(tags=["auth"])

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=LoginResponse)
@log_function_call
async def register_user(
    user_data: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user. Automatically logs in the user after successful registration.
    """
    logger.info("Attempting user registration", extra={"email": user_data.email})

    existing_user = await db.execute(select(User).filter(User.email == user_data.email))
    if existing_user.scalars().first():
        logger.warning("Registration failed: Email already registered", extra={
            "email": user_data.email,
            "status": "email_exists"
        })
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

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
        terms_accepted_at=get_utc_now() if user_data.terms_accepted else None,
        privacy_policy_accepted_at=get_utc_now() if user_data.privacy_accepted else None,
        is_active=True,
    )

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        logger.info("User registered successfully", extra={
            "user_id": str(new_user.id),
            "email": new_user.email,
            "status": "success"
        })

    except Exception as e:
        await db.rollback()
        logger.error("User registration failed due to database error: " + str(e), extra={
            "email": user_data.email,
            "status": "db_error"
        }, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to server error.",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": str(new_user.id)}, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(data={"sub": str(new_user.id)}, expires_delta=refresh_token_expires)

    return LoginResponse(
        user=UserOut.model_validate(new_user),
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token,
    )

@router.post("/login", response_model=LoginResponse)
@log_function_call
async def login_user(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticates user with form data (x-www-form-urlencoded) and returns access/refresh tokens.
    """
    logger.info("Attempting form login", extra={"email": form_data.username})

    user = await db.execute(select(User).filter(User.email == form_data.username))
    user = user.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning("Failed form login attempt: Incorrect credentials", extra={"email": form_data.username})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        logger.warning("Form login attempt by inactive user", extra={"user_id": str(user.id)})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # --- FIXED SECTION START ---
    # We explicitly define the datetime objects here to resolve the 500 error 
    # caused by serialization issues in the production environment.
    now = get_utc_now()
    session_expiry = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    session = UserSession(
        user_id=user.id,
        session_token=refresh_token,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
        expires_at=session_expiry
    )
    # --- FIXED SECTION END ---

    await update_last_login(db, user)

    try:
        db.add(session)
        await db.commit()
        await db.refresh(user)

        logger.info("User logged in successfully (form)", extra={
            "user_id": str(user.id),
            "business_name": user.business_name
        })

        user_data_for_pydantic = user.__dict__.copy()
        if user_data_for_pydantic.get("notification_preferences") == {}:
            user_data_for_pydantic["notification_preferences"] = None
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
        logger.error("Login session creation failed (form): " + str(e), extra={
            "function": "login_user",
            "error_type": type(e).__name__,
            "success": False
        }, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/login-json", response_model=LoginResponse)
@log_function_call
async def login_json(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
    response: Response = None,
):
    """
    Authenticates user with JSON payload and returns access/refresh tokens.
    """
    logger.info("Attempting JSON login", extra={"email": login_data.email})

    user = await db.execute(select(User).filter(User.email == login_data.email))
    user = user.scalars().first()

    if not user or not verify_password(login_data.password, user.hashed_password):
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

    # --- FIXED SECTION START ---
    # We calculate the clean datetime object here to ensure the SQLAlchemy driver 
    # receives a valid object rather than an improperly serialized string.
    now = get_utc_now()
    session_expiry = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    session = UserSession(
        user_id=user.id,
        session_token=refresh_token,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
        expires_at=session_expiry  # Using the pre-calculated object
    )
    # --- FIXED SECTION END ---

    await update_last_login(db, user)

    try:
        db.add(session)
        await db.commit()
        await db.refresh(user)

        logger.info("User logged in successfully (JSON)", extra={
            "user_id": str(user.id),
            "business_name": user.business_name
        })

        user_data_for_pydantic = user.__dict__.copy()
        if user_data_for_pydantic.get("notification_preferences") == {}:
            user_data_for_pydantic["notification_preferences"] = None
        if user_data_for_pydantic.get("user_metadata") == {}:
            user_data_for_pydantic["user_metadata"] = None

        response_data = LoginResponse(
            user=UserOut.model_validate(user_data_for_pydantic),
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token,
        )
        
        if response is not None:
            response.headers["Authorization"] = f"Bearer {access_token}"
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=True,
                samesite="strict",
                max_age=7 * 24 * 60 * 60,  # 7 days
            )

        return response_data

    except Exception as e:
        await db.rollback()
        logger.error("Login session creation failed (JSON): " + str(e), extra={
            "function": "login_json",
            "error_type": type(e).__name__,
            "success": False
        }, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.get("/me", response_model=UserOut)
@log_function_call
async def read_current_user(current_user: User = Depends(get_current_user)):
    """
    Gets the current authenticated user's details.
    """
    logger.info("Fetching current user details", extra={"user_id": str(current_user.id)})
    return current_user

@router.post("/refresh", response_model=LoginResponse)
@log_function_call
async def refresh_access_token(
    refresh_token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    """
    token_prefix = refresh_token_data.refresh_token[:10]
    logger.info("Attempting token refresh", extra={"token_prefix": token_prefix})

    try:
        user_id_from_token = verify_refresh_token(refresh_token_data.refresh_token, db)
        user = await db.execute(select(User).filter(User.id == user_id_from_token))
        user = user.scalars().first()

        if not user or not user.is_active:
            logger.warning("Token refresh failed: Invalid refresh token or inactive user", extra={
                "user_id_from_token": user_id_from_token,
                "status": "invalid_refresh_token"
            })
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token or inactive user",
            )

        new_access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=new_access_token_expires
        )
        new_refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        new_refresh_token = create_refresh_token(
            data={"sub": str(user.id)}, expires_delta=new_refresh_token_expires
        )

        logger.info("Token refresh successful", extra={
            "user_id": str(user.id),
            "status": "success"
        })
        return LoginResponse(
            user=UserOut.model_validate(user),
            access_token=new_access_token,
            token_type="bearer",
            refresh_token=new_refresh_token,
        )
    except JWTError as e:
        logger.error("Token refresh failed due to JWT error: " + str(e), extra={
            "token_prefix": token_prefix,
            "status": "jwt_error"
        }, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    except Exception as e:
        logger.error("An unexpected error occurred during token refresh: " + str(e), extra={
            "status": "unexpected_error"
        }, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh",
        )

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
@log_function_call
async def logout(
    logout_data: LogoutRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Invalidates a refresh token and logs out the user.
    """
    token_prefix = logout_data.refresh_token[:10]
    logger.info("Logout request received", extra={"token_prefix": token_prefix})

    try:
        # Example: Invalidate session in your UserSession model
        # session = db.query(UserSession).filter(UserSession.session_token == logout_data.refresh_token).first()
        # if session:
        #    session.is_active = False
        #    db.commit()
        #    logger.info("User session deactivated", extra={"token_prefix": token_prefix, "status": "session_deactivated"})
        # else:
        #    logger.warning("Logout request for non-existent or already inactive session", extra={"token_prefix": token_prefix, "status": "session_not_found"})

        logger.info("Logout processed (local client tokens should be cleared)", extra={
            "token_prefix": token_prefix,
            "status": "success_local"
        })
        return
    except Exception as e:
        logger.error("Logout failed: " + str(e), extra={
            "token_prefix": token_prefix,
            "status": "failed"
        }, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process logout.",
        )

@router.post("/create-demo-user", response_model=LoginResponse)
@log_function_call
async def create_demo_user_endpoint(
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a demo user and logs them in, returning their details and tokens.
    """
    logger.info("Attempting to create/retrieve demo user")
    try:
        demo_user = create_demo_user(db)
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": str(demo_user.id)}, expires_delta=access_token_expires)
        refresh_token = create_refresh_token(data={"sub": str(demo_user.id)}, expires_delta=refresh_token_expires)
        update_last_login(db, demo_user)
        logger.info("Demo user created/logged in successfully", extra={
            "user_id": str(demo_user.id),
            "email": demo_user.email,
            "status": "success"
        })
        return LoginResponse(
            user=UserOut.model_validate(demo_user),
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token,
        )
    except Exception as e:
        logger.error("Failed to create/retrieve demo user: " + str(e), extra={
            "status": "failed"
        }, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create/retrieve demo user"
        )

@router.options("/login-json")
async def auth_options(request: Request):
    origin = request.headers.get("Origin")
    # Check if the incoming origin is in our allowed list
    allow_origin = origin if origin in [str(o).rstrip('/') for o in settings.BACKEND_CORS_ORIGINS] else str(settings.BACKEND_CORS_ORIGINS[0])
    
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": allow_origin,
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
        }
    )

@router.get("/debug-session")
async def debug_session(request: Request, current_user = Depends(get_current_user)):
    """Debug endpoint to check auth state"""
    return {
        "authenticated": True,
        "user": current_user,
        "headers": dict(request.headers),
        "cookies": request.cookies
    }