"""Authentication utilities."""

import os
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from fastapi import HTTPException, status
from jose import JWTError, jwt

logger = structlog.get_logger()


def verify_supabase_jwt(token: str) -> dict[str, Any]:
    """Verify and decode Supabase JWT token.

    Args:
        token: JWT token from Authorization header

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired

    """
    try:
        # Get Supabase JWT secret for verification
        supabase_jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
        if not supabase_jwt_secret:
            logger.warning("SUPABASE_JWT_SECRET not configured, using test mode")
            # In production, this should fail. For dev, we allow it.
            return {"sub": "test-user", "email": "test@example.com"}

        # Decode JWT
        payload = jwt.decode(
            token,
            supabase_jwt_secret,
            algorithms=["HS256"],
        )

        user_id: str | None = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
            )

        return payload

    except JWTError as e:
        logger.warning("JWT verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def create_access_token(user_id: str, expires_delta: timedelta | None = None) -> str:
    """Create JWT access token (for development/testing).

    In production, use Supabase to create tokens.

    Args:
        user_id: User UUID
        expires_delta: Token expiration time

    Returns:
        JWT token string

    """
    if expires_delta is None:
        expires_delta = timedelta(hours=1)

    expire = datetime.now(UTC) + expires_delta
    to_encode = {"sub": user_id, "exp": expire}

    secret = os.getenv("SUPABASE_JWT_SECRET", "dev-secret-key")
    encoded_jwt = jwt.encode(to_encode, secret, algorithm="HS256")

    return encoded_jwt


def extract_token_from_header(authorization: str | None) -> str:
    """Extract JWT token from Authorization header.

    Args:
        authorization: Authorization header value

    Returns:
        Token string

    Raises:
        HTTPException: If header format is invalid

    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid authentication scheme")
        return token
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
