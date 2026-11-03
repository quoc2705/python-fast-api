from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserResponse


class CommentCreate(BaseModel):
    """Schema for adding a comment on a task."""

    author_id: int = Field(..., ge=1, description="User ID of the comment author")
    content: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Comment text content",
        examples=["Looks great, ready for code review!"],
    )


class CommentResponse(BaseModel):
    """Schema for returning a comment in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    author_id: int
    content: str
    created_at: datetime
    author: UserResponse | None = None

