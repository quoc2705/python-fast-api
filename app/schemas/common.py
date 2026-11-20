from math import ceil
from typing import Generic, TypeVar

from pydantic import ConfigDict, Field

from app.schemas.base import BaseSchema

T = TypeVar("T")


class MessageResponse(BaseSchema):
    """Standard message response schema."""

    message: str = Field(..., description="Human-readable response message")


class PaginatedResponse(BaseSchema, Generic[T]):
    """Generic paginated response wrapper using Pydantic v2 (page + limit)."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    items: list[T] = Field(default_factory=list, description="Items on current page")
    total: int = Field(..., ge=0, description="Total number of matching items")
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    limit: int = Field(..., ge=1, description="Maximum items per page")
    pages: int = Field(..., ge=0, description="Total number of pages")

    @classmethod
    def create(
        cls,
        *,
        items: list[T],
        total: int,
        page: int,
        limit: int,
    ) -> "PaginatedResponse[T]":
        pages = ceil(total / limit) if total > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=pages,
        )
