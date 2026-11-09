from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import ProjectStatus
from app.schemas.label import LabelResponse
from app.schemas.task import TaskResponse


class ProjectBase(BaseModel):
    """Shared properties for Project schemas."""

    name: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Project name",
        examples=["TaskHub Core Backend"],
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Project description",
    )
    status: ProjectStatus = Field(
        default=ProjectStatus.ACTIVE,
        description="Project status (ACTIVE/ARCHIVED)",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise ValueError("Project name must contain at least 3 non-whitespace characters")
        return cleaned


class ProjectCreate(ProjectBase):
    """Schema for creating a new project inside a workspace."""


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project (or archiving it)."""

    name: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: ProjectStatus | None = None

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
    workspace_id: int
    created_at: datetime


class ProjectDetailResponse(ProjectResponse):
    """Schema for returning a project with its tasks and labels."""

    tasks: list[TaskResponse] = Field(default_factory=list)
    labels: list[LabelResponse] = Field(default_factory=list)
