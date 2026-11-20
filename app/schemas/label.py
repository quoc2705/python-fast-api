from typing import Any

from pydantic import ConfigDict, Field, model_validator

from app.core.constants import (
    LABEL_COLOR_MAX_LENGTH,
    LABEL_NAME_MAX_LENGTH,
    LABEL_NAME_MIN_LENGTH,
)
from app.schemas.base import BaseSchema, reject_explicit_nulls


class LabelBase(BaseSchema):
    """Shared properties for Label schemas."""

    name: str = Field(
        ...,
        min_length=LABEL_NAME_MIN_LENGTH,
        max_length=LABEL_NAME_MAX_LENGTH,
        description="Label name",
        examples=["bug", "backend", "urgent"],
    )
    color: str = Field(
        default="#3B82F6",
        min_length=3,
        max_length=LABEL_COLOR_MAX_LENGTH,
        description="Hex color code for the label",
        examples=["#EF4444"],
    )


class LabelCreate(LabelBase):
    """Schema for creating a label inside a project."""


class LabelUpdate(BaseSchema):
    """Schema for updating a label."""

    name: str | None = Field(
        default=None,
        min_length=LABEL_NAME_MIN_LENGTH,
        max_length=LABEL_NAME_MAX_LENGTH,
    )
    color: str | None = Field(
        default=None,
        min_length=3,
        max_length=LABEL_COLOR_MAX_LENGTH,
    )

    @model_validator(mode="before")
    @classmethod
    def _reject_nulls(cls, data: Any) -> Any:
        return reject_explicit_nulls(data, ("name", "color"))


class LabelResponse(LabelBase):
    """Schema for returning a label in API responses."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: int
    project_id: int
