"""Authentication routes (register, login, refresh, etc.)."""

import structlog
from fastapi import APIRouter, HTTPException, status

from src.app.auth.dependencies import CurrentUserId
from src.app.auth.models import InviteCodeModel, UserModel
from src.app.auth.utils import create_access_token
from src.app.clients.supabase import get_supabase_client
from src.app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    UserProfileResponse,
    ValidateInviteRequest,
    ValidateInviteResponse,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/validate-invite", response_model=ValidateInviteResponse)
async def validate_invite(request: ValidateInviteRequest) -> ValidateInviteResponse:
    """Validate an invite code before registration.

    This endpoint is called before showing the signup form.

    Args:
        request: Request with invite code

    Returns:
        Validation result with domain and role info

    """
    try:
        invite = await InviteCodeModel.validate_invite(request.code)

        if not invite:
            logger.warning("Invalid invite code", code=request.code)
            return ValidateInviteResponse(
                valid=False,
                message="Invalid or expired invite code",
            )

        return ValidateInviteResponse(
            valid=True,
            message="Invite code is valid",
            domain_id=invite.get("domain_id"),
            role=invite.get("role"),
        )

    except Exception as e:
        logger.error("Invite validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate invite code",
        )


@router.post(
    "/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED
)
async def register(request: RegisterRequest) -> AuthResponse:
    """Register a new user with an invite code.

    Frontend flow:
    1. User enters invite code
    2. Call /auth/validate-invite
    3. If valid, show signup form
    4. User fills email, password
    5. Call /auth/register with code, email, password
    6. Returns JWT token

    Args:
        request: Registration request with email, password, invite code

    Returns:
        Authentication response with JWT token

    Raises:
        HTTPException: If registration fails

    """
    try:
        # Validate invite code first
        invite = await InviteCodeModel.validate_invite(request.invite_code)
        if not invite:
            logger.warning(
                "Registration failed: invalid invite", code=request.invite_code
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired invite code",
            )

        supabase = get_supabase_client()

        # Try to create user in Supabase Auth
        try:
            auth_response = supabase.auth.sign_up(
                {
                    "email": request.email,
                    "password": request.password,
                }
            )

            user_id = auth_response.user.id
            logger.info(
                "User registered with Supabase Auth",
                user_id=user_id,
                email=request.email,
            )

        except Exception as auth_error:
            logger.error("Supabase auth signup failed", error=str(auth_error))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account",
            )

        # Create user record in database
        await UserModel.create_user(user_id, request.email, request.invite_code)

        # Mark invite as used
        await InviteCodeModel.use_invite(request.invite_code, user_id)

        # Create JWT token
        access_token = create_access_token(user_id)

        logger.info(
            "User registered successfully", user_id=user_id, email=request.email
        )

        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user_id,
            email=request.email,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Registration failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest) -> AuthResponse:
    """Login with email and password.

    Frontend flow:
    1. User submits email and password
    2. Call /auth/login
    3. Returns JWT token
    4. Store token in localStorage/sessionStorage
    5. Use token in Authorization header for subsequent requests

    Args:
        request: Login request with email and password

    Returns:
        Authentication response with JWT token

    Raises:
        HTTPException: If login fails

    """
    try:
        supabase = get_supabase_client()

        # Authenticate with Supabase
        try:
            auth_response = supabase.auth.sign_in_with_password(
                {
                    "email": request.email,
                    "password": request.password,
                }
            )

            user_id = auth_response.user.id
            access_token = (
                auth_response.session.access_token if auth_response.session else None
            )

            if not access_token:
                logger.warning("Login succeeded but no token returned")
                # Generate token as fallback
                access_token = create_access_token(user_id)

            logger.info("User logged in", user_id=user_id, email=request.email)

            return AuthResponse(
                access_token=access_token,
                token_type="bearer",
                user_id=user_id,
                email=request.email,
            )

        except Exception as auth_error:
            logger.warning("Login failed", error=str(auth_error), email=request.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(request: RefreshTokenRequest) -> AuthResponse:
    """Refresh access token using refresh token.

    Frontend usage:
    1. When access token expires (401 response)
    2. Call /auth/refresh with the refresh token
    3. Store new access token
    4. Retry original request

    Args:
        request: Request with refresh token

    Returns:
        New authentication response with fresh access token

    Raises:
        HTTPException: If refresh fails

    """
    try:
        supabase = get_supabase_client()

        # Refresh session with Supabase
        try:
            new_session = supabase.auth.refresh_session(
                request.refresh_token,
            )

            user_id = new_session.user.id if new_session.user else None
            if not user_id:
                raise ValueError("No user in refreshed session")

            access_token = new_session.access_token
            logger.info("Token refreshed", user_id=user_id)

            return AuthResponse(
                access_token=access_token,
                token_type="bearer",
                user_id=user_id,
                email=new_session.user.email if new_session.user else "",
            )

        except Exception as refresh_error:
            logger.warning("Token refresh failed", error=str(refresh_error))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to refresh token. Please login again.",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token",
        )


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(user_id: CurrentUserId) -> UserProfileResponse:
    """Get current user profile.

    Requires valid JWT token in Authorization header.

    Args:
        user_id: Current user ID (from dependency)

    Returns:
        User profile

    Raises:
        HTTPException: If user not found

    """
    try:
        user = await UserModel.get_user_by_id(user_id)

        if not user:
            logger.warning("User not found", user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found",
            )

        return UserProfileResponse(
            id=user["id"],
            email=user["email"],
            role=user.get("role", "contributor"),
            domain_id=user.get("domain_id"),
            created_at=user.get("created_at", ""),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get user profile", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile",
        )


@router.post("/logout")
async def logout(user_id: CurrentUserId) -> dict[str, str]:
    """Logout user (client-side operation).

    Frontend should:
    1. Call this endpoint
    2. Clear JWT token from localStorage/sessionStorage
    3. Redirect to welcome page

    Args:
        user_id: Current user ID (from dependency)

    Returns:
        Success message

    """
    try:
        supabase = get_supabase_client()
        supabase.auth.sign_out()

        logger.info("User logged out", user_id=user_id)

        return {"message": "Successfully logged out"}

    except Exception as e:
        logger.warning("Logout failed", user_id=user_id, error=str(e))
        # Don't fail, client will clear token anyway
        return {"message": "Logged out"}
