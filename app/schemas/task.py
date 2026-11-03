from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskStatus(str, Enum):
    """Supported statuses for a task."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(str, Enum):
    """Supported priority levels for a task."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskBase(BaseModel):
    """Shared properties for Task schemas."""

    title: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Short title of the task",
        examples=["Implement FastAPI Layered Architecture"],
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Detailed task description",
        examples=["Build routers, services, repositories, and Pydantic v2 schemas"],
    )
    status: TaskStatus = Field(
        default=TaskStatus.TODO,
        description="Current status of the task",
    )
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM,
        description="Task priority level",
    )

    @field_validator("title")
    @classmethod
    def validate_title_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise ValueError("Title must contain at least 3 non-whitespace characters")
        return cleaned


class TaskCreate(TaskBase):
    """Schema for creating a new task."""


class TaskUpdate(BaseModel):
    """Schema for updating an existing task (partial or full)."""

    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None

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

    id: int = Field(..., description="Unique identifier of the task")
    created_at: datetime = Field(..., description="UTC timestamp when task was created")
    updated_at: datetime = Field(..., description="UTC timestamp when task was last updated")
