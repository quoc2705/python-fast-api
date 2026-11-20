from datetime import datetime
from typing import Any

from pydantic import ConfigDict, Field, model_validator

from app.core.constants import (
    DESCRIPTION_MAX_LENGTH,
    PROJECT_NAME_MAX_LENGTH,
    PROJECT_NAME_MIN_LENGTH,
)
from app.models.enums import ProjectStatus
from app.schemas.base import BaseSchema, reject_explicit_nulls
from app.schemas.label import LabelResponse
from app.schemas.task import TaskResponse


class ProjectCreate(BaseSchema):
    """Schema for creating a new project inside a workspace (status defaults to ACTIVE)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(
        ...,
        min_length=PROJECT_NAME_MIN_LENGTH,
        max_length=PROJECT_NAME_MAX_LENGTH,
        description="Project name",
        examples=["TaskHub Core Backend"],
    )
    description: str | None = Field(
        default=None,
        max_length=DESCRIPTION_MAX_LENGTH,
        description="Project description",
    )


class ProjectUpdate(BaseSchema):
    """Schema for updating an existing project (or archiving it)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str | None = Field(
        default=None,
        min_length=PROJECT_NAME_MIN_LENGTH,
        max_length=PROJECT_NAME_MAX_LENGTH,
    )
    description: str | None = Field(
        default=None,
        max_length=DESCRIPTION_MAX_LENGTH,
    )
    status: ProjectStatus | None = None

    @model_validator(mode="before")
    @classmethod
    def _reject_nulls(cls, data: Any) -> Any:
        return reject_explicit_nulls(data, ("name", "status"))


class ProjectResponse(BaseSchema):
    """Schema for returning a project in API responses."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: int
    workspace_id: int
    name: str
    description: str | None = None
    status: ProjectStatus
    created_at: datetime


class ProjectDetailResponse(ProjectResponse):
    """Schema for returning a project with its tasks and labels."""

    tasks: list[TaskResponse] = Field(default_factory=list)
    labels: list[LabelResponse] = Field(default_factory=list)
