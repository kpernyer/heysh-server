"""Authentication dependencies for FastAPI."""

from typing import Annotated, Any

import structlog
from fastapi import Depends, Header, HTTPException, status

from src.app.auth.utils import extract_token_from_header, verify_supabase_jwt

logger = structlog.get_logger()


async def get_current_user(
    authorization: str | None = Header(None),
) -> dict[str, Any]:
    """Dependency to get current authenticated user from JWT token.

    Usage:
        @app.get("/api/protected")
        async def protected_endpoint(user = Depends(get_current_user)):
            return {"user_id": user["sub"]}

    Args:
        authorization: Authorization header value

    Returns:
        Decoded JWT payload with user information

    Raises:
        HTTPException: If token is missing or invalid

    """
    token = extract_token_from_header(authorization)
    payload = verify_supabase_jwt(token)

    logger.debug("User authenticated", user_id=payload.get("sub"))

    return payload


async def get_current_user_id(
    user: dict[str, Any] = Depends(get_current_user),
) -> str:
    """Dependency to get just the current user ID.

    Args:
        user: Current user from get_current_user

    Returns:
        User ID (sub claim)

    """
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID",
        )
    return user_id


async def get_current_user_email(
    user: dict[str, Any] = Depends(get_current_user),
) -> str:
    """Dependency to get current user email.

    Args:
        user: Current user from get_current_user

    Returns:
        User email

    """
    email = user.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing email",
        )
    return email


# Type alias for cleaner annotations
CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]
CurrentUserEmail = Annotated[str, Depends(get_current_user_email)]
