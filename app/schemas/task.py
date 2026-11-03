from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import TaskPriority, TaskStatus
from app.schemas.comment import CommentResponse
from app.schemas.label import LabelResponse


class TaskBase(BaseModel):
    """Shared properties for TaskHub Task schemas."""

    title: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Short title of the task",
        examples=["Implement TaskHub SQLAlchemy 2.x Async Schema"],
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Detailed task description",
    )
    status: TaskStatus = Field(
        default=TaskStatus.TODO,
        description="Current workflow status (TODO/IN_PROGRESS/IN_REVIEW/DONE)",
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
    created_by: int | None = Field(
        default=None,
        ge=1,
        description="ID of the user who created the task",
    )

    @field_validator("title")
    @classmethod
    def validate_title_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise ValueError("Title must contain at least 3 non-whitespace characters")
        return cleaned


class TaskCreate(TaskBase):
    """Schema for creating a new task inside a project."""


class TaskUpdate(BaseModel):
    """Schema for partially updating an existing task."""

    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assignee_id: int | None = Field(default=None, ge=1)
    due_date: datetime | None = None

    @field_validator("title")
    @classmethod
    def validate_optional_title(cls, value: str | None) -> str | None:
        if value is not None:
            cleaned = value.strip()
            if len(cleaned) < 3:
                raise ValueError("Title must contain at least 3 non-whitespace characters")
            return cleaned
        return value


class TaskResponse(TaskBase):
    """Schema for returning a task in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    created_at: datetime
    labels: list[LabelResponse] = Field(default_factory=list)


class TaskDetailResponse(TaskResponse):
    """Schema for returning a task with its comments and labels."""

    comments: list[CommentResponse] = Field(default_factory=list)
