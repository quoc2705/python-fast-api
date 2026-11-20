from pydantic import ConfigDict, Field, field_validator

from app.core.constants import (
    EMAIL_MAX_LENGTH,
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    USER_NAME_MAX_LENGTH,
    USER_NAME_MIN_LENGTH,
)
from app.schemas.base import BaseSchema
from app.schemas.user import UserResponse, validate_email_string


class RegisterRequest(BaseSchema):
    """Schema for self-registering a new user account (role cannot be chosen by client)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: str = Field(
        ...,
        max_length=EMAIL_MAX_LENGTH,
        description="Unique email address",
        examples=["quoc@taskhub.io"],
    )
    full_name: str = Field(
        ...,
        min_length=USER_NAME_MIN_LENGTH,
        max_length=USER_NAME_MAX_LENGTH,
        description="Full name of the user",
        examples=["Dinh Ngoc Quoc"],
    )
    password: str = Field(
        ...,
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
        description="Account password (6 to 72 characters)",
        examples=["Password123!"],
    )

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        return validate_email_string(value)


class LoginRequest(BaseSchema):
    """Schema for user login returning JWT access and refresh tokens."""

    email: str = Field(..., examples=["quoc@taskhub.io"])
    password: str = Field(..., min_length=1, max_length=PASSWORD_MAX_LENGTH)

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        return validate_email_string(value)


class TokenResponse(BaseSchema):
    """JWT token pair response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseSchema):
    """Request payload to exchange a refresh token for a new token pair."""

    refresh_token: str = Field(..., min_length=10, description="Valid JWT refresh token")


class LogoutRequest(BaseSchema):
    """Request payload to revoke a refresh token upon logout."""

    refresh_token: str = Field(..., min_length=10, description="Refresh token to revoke")


class ChangePasswordRequest(BaseSchema):
    """Request payload for changing the current user's password."""

    current_password: str = Field(..., min_length=1, max_length=PASSWORD_MAX_LENGTH)
    new_password: str = Field(
        ...,
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
    )
