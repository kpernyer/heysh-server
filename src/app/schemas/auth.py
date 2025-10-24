"""Authentication request/response schemas."""

from pydantic import BaseModel, EmailStr, Field


class ValidateInviteRequest(BaseModel):
    """Request to validate an invite code."""

    code: str = Field(..., description="Invite code")


class ValidateInviteResponse(BaseModel):
    """Response from invite validation."""

    valid: bool = Field(..., description="Whether invite is valid")
    message: str | None = Field(None, description="Validation message")
    domain_id: str | None = Field(None, description="Domain if code is valid")
    role: str | None = Field(None, description="Role that will be assigned")


class RegisterRequest(BaseModel):
    """Request to register a new user."""

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password")
    invite_code: str = Field(..., description="Invite code")


class LoginRequest(BaseModel):
    """Request to login."""

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


class AuthResponse(BaseModel):
    """Authentication response with token."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str | None = Field(None, description="Refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    user_id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")


class RefreshTokenRequest(BaseModel):
    """Request to refresh access token."""

    refresh_token: str = Field(..., description="Refresh token")


class UserProfileResponse(BaseModel):
    """User profile response."""

    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    role: str = Field(..., description="User role")
    domain_id: str | None = Field(None, description="Domain ID if member of domain")
    created_at: str = Field(..., description="Creation timestamp")
