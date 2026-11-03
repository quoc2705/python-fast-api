from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.task import TaskResponse
from app.schemas.user import UserResponse


class ProjectBase(BaseModel):
    """Shared properties for Project schemas."""

    name: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Project name",
        examples=["FastAPI Training Platform"],
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Project description",
    )
    owner_id: int = Field(..., ge=1, description="ID of the user who owns the project")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise ValueError("Project name must contain at least 3 non-whitespace characters")
        return cleaned


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project."""

    name: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    owner_id: int | None = Field(default=None, ge=1)

    @field_validator("name")
    @classmethod
    def validate_optional_name(cls, value: str | None) -> str | None:
        if value is not None:
            cleaned = value.strip()
            if len(cleaned) < 3:
                raise ValueError(
                    "Project name must contain at least 3 non-whitespace characters"
                )
            return cleaned
        return value


class ProjectResponse(ProjectBase):
    """Schema for returning a project in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ProjectDetailResponse(ProjectResponse):
    """Schema for returning a project along with its owner and tasks."""

    owner: UserResponse | None = None
    tasks: list[TaskResponse] = Field(default_factory=list)

