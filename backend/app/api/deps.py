"""
FastAPI dependency injection utilities.
Handles authentication, database sessions, and common dependencies.
"""

from typing import Generator, Optional, AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.config import settings
from app.database import get_db, get_async_session
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
        # First try Redis for cached session; if Redis is unavailable, fall back silently
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
            
        # Get user from database using async SQLAlchemy
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            logger.warning(f"User not found for ID: {user_id}")
            raise credentials_exception
            
        # Cache user session using to_dict method
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


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (redundant check for clarity)."""
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user with admin privileges."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer_security),
    db: AsyncSession = Depends(get_async_session),
    redis_client: RedisClient = Depends(get_redis)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.
    Useful for endpoints that work with or without auth.
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db, redis_client)
    except HTTPException:
        return None


class RateLimiter:
    """Rate limiting dependency factory."""
    
    def __init__(self, requests: int, window: int):
        self.requests = requests
        self.window = window
    
    async def __call__(
        self,
        request,
        redis_client: RedisClient = Depends(get_redis),
        current_user: Optional[User] = Depends(get_optional_user)
    ):
        """Apply rate limiting based on user ID or IP address."""
        # Use user ID if authenticated, otherwise use IP
        identifier = (
            f"user:{current_user.id}" if current_user 
            else f"ip:{request.client.host}"
        )
        
        allowed, remaining = await redis_client.rate_limit_check(
            identifier, self.requests, self.window
        )
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(self.window)}
            )
        
        return {"remaining_requests": remaining}


# Common rate limiters
rate_limit_strict = RateLimiter(requests=10, window=60)  # 10 requests per minute
rate_limit_moderate = RateLimiter(requests=100, window=60)  # 100 requests per minute
rate_limit_generous = RateLimiter(requests=1000, window=60)  # 1000 requests per minute


async def check_api_key(
    api_key: str,
    db: AsyncSession = Depends(get_async_session)
) -> User:
    """
    Validate API key authentication.
    Alternative to JWT for service-to-service communication.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # Hash the API key and look up user
    result = await db.execute(
        select(User).where(User.api_key_hash == api_key)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return user


def require_permissions(*required_permissions: str):
    """
    Dependency factory for permission-based access control.
    Usage: @app.get("/admin", dependencies=[Depends(require_permissions("admin:read"))])
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user)
    ):
        user_permissions = set(current_user.permissions or [])
        required_perms = set(required_permissions)
        
        if not required_perms.issubset(user_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_user
    
    return permission_checker


async def validate_tenant_access(
    tenant_id: str,
    current_user: User = Depends(get_current_user)
) -> str:
    """
    Validate that current user has access to specified tenant.
    Useful for multi-tenant applications.
    """
    if current_user.tenant_id != tenant_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to tenant"
        )
    
    return tenant_id


class PaginationParams:
    """Pagination parameters dependency."""
    
    def __init__(
        self,
        skip: int = 0,
        limit: int = 100,
        max_limit: int = 1000
    ):
        if skip < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Skip must be >= 0"
            )
        
        if limit <= 0 or limit > max_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Limit must be between 1 and {max_limit}"
            )
        
        self.skip = skip
        self.limit = limit


def get_pagination_params(
    skip: int = 0,
    limit: int = 100
) -> PaginationParams:
    """Get pagination parameters with validation."""
    return PaginationParams(skip=skip, limit=limit)


async def get_async_db() -> AsyncGenerator:
    """
    Async DB session dependency - yields an AsyncSession and ensures proper cleanup.
    """
    from app.db.session import async_session
    
    async with async_session() as session:
        yield session