from pydantic import BaseModel, ConfigDict, Field


class LabelBase(BaseModel):
    """Shared properties for Label schemas."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Label name",
        examples=["bug", "backend", "urgent"],
    )
    color: str = Field(
        default="#3B82F6",
        max_length=20,
        description="Hex color code for the label",
        examples=["#EF4444"],
    )


class LabelCreate(LabelBase):
    """Schema for creating a label inside a project."""


class LabelUpdate(BaseModel):
    """Schema for updating a label."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    color: str | None = Field(default=None, max_length=20)


class LabelResponse(LabelBase):
    """Schema for returning a label in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
