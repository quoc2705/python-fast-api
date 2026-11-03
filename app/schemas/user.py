from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserBase(BaseModel):
    """Shared properties for User schemas."""

    email: str = Field(
        ...,
        max_length=255,
        description="Unique email address of the user",
        examples=["developer@example.com"],
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Full name of the user",
        examples=["Nguyen Van A"],
    )
    is_active: bool = Field(default=True, description="Whether the user account is active")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if "@" not in cleaned or "." not in cleaned.split("@")[-1]:
            raise ValueError("Invalid email address format")
        return cleaned


class UserCreate(UserBase):
    """Schema for creating a new user."""


class UserUpdate(BaseModel):
    """Schema for updating an existing user."""

    email: str | None = Field(default=None, max_length=255)
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    is_active: bool | None = None

    @field_validator("email")
    @classmethod
    def validate_optional_email(cls, value: str | None) -> str | None:
        if value is not None:
            cleaned = value.strip().lower()
            if "@" not in cleaned or "." not in cleaned.split("@")[-1]:
                raise ValueError("Invalid email address format")
            return cleaned
        return value


class UserResponse(UserBase):
    """Schema for returning a user in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

