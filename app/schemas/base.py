from typing import Any

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Shared Pydantic v2 base schema with automatic whitespace stripping."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        populate_by_name=True,
    )


def reject_explicit_nulls(data: Any, non_nullable_fields: tuple[str, ...]) -> Any:
    """Reject PATCH payloads that explicitly pass null for non-nullable DB columns."""
    if isinstance(data, dict):
        for field_name in non_nullable_fields:
            if field_name in data and data[field_name] is None:
                raise ValueError(f"Field '{field_name}' cannot be null")
    return data
