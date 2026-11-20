from datetime import datetime
from typing import Any

from pydantic import ConfigDict, Field, field_validator, model_validator

from app.core.constants import (
    EMAIL_MAX_LENGTH,
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    USER_NAME_MAX_LENGTH,
    USER_NAME_MIN_LENGTH,
)
from app.models.enums import UserRole
from app.schemas.base import BaseSchema, reject_explicit_nulls


def validate_email_string(value: str) -> str:
    cleaned = value.strip().lower()
    if "@" not in cleaned or "." not in cleaned.split("@")[-1]:
        raise ValueError("Invalid email address format")
    return cleaned


class UserBase(BaseSchema):
    """Shared properties for User schemas."""

    email: str = Field(
        ...,
        max_length=EMAIL_MAX_LENGTH,
        description="Unique email address of the user",
        examples=["developer@taskhub.io"],
    )
    full_name: str = Field(
        ...,
        min_length=USER_NAME_MIN_LENGTH,
        max_length=USER_NAME_MAX_LENGTH,
        description="Full name of the user",
        examples=["Dinh Ngoc Quoc"],
    )
    role: UserRole = Field(default=UserRole.MEMBER, description="Global system role")
    is_active: bool = Field(default=True, description="Whether the user account is active")

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        return validate_email_string(value)


class UserCreate(UserBase):
    """Admin schema for creating a new user (password is mandatory)."""

    password: str = Field(
        ...,
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
        description="Plaintext password (6 to 72 characters)",
    )


class UserMeUpdate(BaseSchema):
    """Schema for a user updating their own profile (cannot change role or is_active)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: str | None = Field(default=None, max_length=EMAIL_MAX_LENGTH)
    full_name: str | None = Field(
        default=None,
        min_length=USER_NAME_MIN_LENGTH,
        max_length=USER_NAME_MAX_LENGTH,
    )

    @model_validator(mode="before")
    @classmethod
    def _reject_nulls(cls, data: Any) -> Any:
        return reject_explicit_nulls(data, ("email", "full_name"))

    @field_validator("email")
    @classmethod
    def _validate_optional_email(cls, value: str | None) -> str | None:
        return validate_email_string(value) if value is not None else None


class UserUpdate(BaseSchema):
    """Admin schema for updating an existing user profile including role/is_active."""

    email: str | None = Field(default=None, max_length=EMAIL_MAX_LENGTH)
    full_name: str | None = Field(
        default=None,
        min_length=USER_NAME_MIN_LENGTH,
        max_length=USER_NAME_MAX_LENGTH,
    )
    role: UserRole | None = None
    is_active: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def _reject_nulls(cls, data: Any) -> Any:
        return reject_explicit_nulls(
            data,
            ("email", "full_name", "role", "is_active"),
        )

    @field_validator("email")
    @classmethod
    def _validate_optional_email(cls, value: str | None) -> str | None:
        return validate_email_string(value) if value is not None else None


class UserResponse(UserBase):
    """Schema for returning a user in API responses."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: int
    created_at: datetime
