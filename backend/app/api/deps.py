"""
FastAPI dependency injection utilities.
Handles authentication, database sessions, and common dependencies.
"""

from typing import Optional, AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.database import get_async_session
from app.models.user import User
from app.redis_client import get_redis, RedisClient
from app.core.logging import get_logger

logger = get_logger(__name__)
http_bearer_security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer_security),
    db: AsyncSession = Depends(get_async_session),
    redis_client = Depends(get_redis)
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # First try Redis for cached session
        try:
            session = await redis_client.get_user_session(credentials.credentials)
            if session:
                return User(**session)
        except Exception as redis_error:
            logger.warning("Redis unavailable, falling back to JWT: %s", redis_error)

        # Fallback to JWT validation
        token = credentials.credentials.strip()
        if not token or len(token.split('.')) != 3:
            logger.error(f"Invalid JWT token format: {token[:20]}...")
            raise credentials_exception

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            logger.warning(f"User not found for ID: {user_id}")
            raise credentials_exception

        # Cache user session
        user_data = user.to_dict()
        await redis_client.set_user_session(
            credentials.credentials,
            user_data,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

        return user

    except JWTError as e:
        logger.error(f"JWT validation error: {e}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Authentication error: {e}", exc_info=True)
        raise credentials_exception


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer_security),
    db: AsyncSession = Depends(get_async_session),
    redis_client: RedisClient = Depends(get_redis)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db, redis_client)
    except HTTPException:
        return None

# ... (The rest of the file remains the same) ...
