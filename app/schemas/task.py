from datetime import datetime
from typing import Any

from pydantic import ConfigDict, Field, model_validator

from app.core.constants import (
    DESCRIPTION_MAX_LENGTH,
    TITLE_MAX_LENGTH,
    TITLE_MIN_LENGTH,
)
from app.models.enums import TaskPriority, TaskStatus
from app.schemas.base import BaseSchema, reject_explicit_nulls
from app.schemas.comment import CommentResponse
from app.schemas.label import LabelResponse


class TaskCreate(BaseSchema):
    """Schema for creating a new task inside a project (status defaults to TODO, created_by from auth user)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(
        ...,
        min_length=TITLE_MIN_LENGTH,
        max_length=TITLE_MAX_LENGTH,
        description="Short title of the task",
        examples=["Implement TaskHub SQLAlchemy 2.x Async Schema"],
    )
    description: str | None = Field(
        default=None,
        max_length=DESCRIPTION_MAX_LENGTH,
        description="Detailed task description",
    )
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM,
        description="Priority level (LOW/MEDIUM/HIGH/URGENT)",
    )
    assignee_id: int | None = Field(
        default=None,
        ge=1,
        description="Optional ID of the user assigned to this task",
    )
    due_date: datetime | None = Field(
        default=None,
        description="Optional due date for completing the task",
    )


class TaskUpdate(BaseSchema):
    """Schema for partially updating an existing task (non-nullable fields cannot be null)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str | None = Field(
        default=None,
        min_length=TITLE_MIN_LENGTH,
        max_length=TITLE_MAX_LENGTH,
    )
    description: str | None = Field(
        default=None,
        max_length=DESCRIPTION_MAX_LENGTH,
    )
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assignee_id: int | None = Field(default=None, ge=1)
    due_date: datetime | None = None

    @model_validator(mode="before")
    @classmethod
    def _reject_null_on_required_columns(cls, data: Any) -> Any:
        return reject_explicit_nulls(data, ("title", "status", "priority"))


class TaskResponse(BaseSchema):
    """Schema for returning a task in API responses."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: int
    project_id: int
    title: str
    description: str | None = None
    status: TaskStatus
    priority: TaskPriority
    assignee_id: int | None = None
    due_date: datetime | None = None
    created_by: int | None = None
    created_at: datetime
    labels: list[LabelResponse] = Field(default_factory=list)


class TaskDetailResponse(TaskResponse):
    """Schema for returning a task with its comments and labels."""

    comments: list[CommentResponse] = Field(default_factory=list)
