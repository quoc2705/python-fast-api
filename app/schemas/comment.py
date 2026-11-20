from datetime import datetime

from pydantic import ConfigDict, Field

from app.core.constants import COMMENT_MAX_LENGTH, COMMENT_MIN_LENGTH
from app.schemas.base import BaseSchema
from app.schemas.user import UserResponse


class CommentCreate(BaseSchema):
    """Schema for adding a comment on a task (author_id is set from current_user)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    content: str = Field(
        ...,
        min_length=COMMENT_MIN_LENGTH,
        max_length=COMMENT_MAX_LENGTH,
        description="Comment text content",
        examples=["Looks great, ready for code review!"],
    )


class CommentResponse(BaseSchema):
    """Schema for returning a comment in API responses."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: int
    task_id: int
    author_id: int
    content: str
    created_at: datetime
    author: UserResponse | None = None
