from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class MessageResponse(BaseModel):
    """Standard message response schema."""

    message: str = Field(..., description="Human-readable response message")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper using Pydantic v2 (page + limit)."""

    model_config = ConfigDict(from_attributes=True)

    items: list[T] = Field(default_factory=list, description="Items on current page")
    total: int = Field(..., ge=0, description="Total number of matching items")
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    limit: int = Field(..., ge=1, description="Maximum items per page")
    pages: int = Field(..., ge=0, description="Total number of pages")
