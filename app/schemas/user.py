from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import UserRole


class UserBase(BaseModel):
    """Shared properties for User schemas."""

    email: str = Field(
        ...,
        max_length=255,
        description="Unique email address of the user",
        examples=["developer@taskhub.io"],
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Full name of the user",
        examples=["Dinh Ngoc Quoc"],
    )
    role: UserRole = Field(default=UserRole.MEMBER, description="Global system role")
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

    password: str = Field(
        default="Password123!",
        min_length=6,
        max_length=128,
        description="Plaintext password to be hashed before storage",
    )


class UserUpdate(BaseModel):
    """Schema for updating an existing user profile."""

    email: str | None = Field(default=None, max_length=255)
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    role: UserRole | None = None
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
