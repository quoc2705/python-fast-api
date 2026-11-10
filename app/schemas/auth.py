from pydantic import BaseModel, Field, field_validator

from app.models.enums import UserRole
from app.schemas.user import UserResponse


class RegisterRequest(BaseModel):
    """Schema for registering a new user account."""

    email: str = Field(
        ...,
        max_length=255,
        description="Unique email address",
        examples=["quoc@taskhub.io"],
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Full name of the user",
        examples=["Dinh Ngoc Quoc"],
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="Account password (min 6 characters)",
        examples=["Password123!"],
    )
    role: UserRole = Field(
        default=UserRole.MEMBER,
        description="System role (ADMIN or MEMBER)",
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if "@" not in cleaned or "." not in cleaned.split("@")[-1]:
            raise ValueError("Invalid email address format")
        return cleaned


class LoginRequest(BaseModel):
    """Schema for user login returning JWT access and refresh tokens."""

    email: str = Field(..., examples=["quoc@taskhub.io"])
    password: str = Field(..., examples=["Password123!"])


class TokenResponse(BaseModel):
    """JWT token pair response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Request payload to exchange a refresh token for a new token pair."""

    refresh_token: str = Field(..., description="Valid JWT refresh token")


class LogoutRequest(BaseModel):
    """Request payload to revoke a refresh token upon logout."""

    refresh_token: str = Field(..., description="Refresh token to revoke")


class ChangePasswordRequest(BaseModel):
    """Request payload for changing the current user's password."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=128)
