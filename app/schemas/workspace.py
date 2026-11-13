from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import WorkspaceRole
from app.schemas.user import UserResponse


class WorkspaceBase(BaseModel):
    """Shared properties for Workspace schemas."""

    name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Workspace name",
        examples=["Engineering Workspace"],
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("Workspace name must be at least 2 characters")
        return cleaned


class WorkspaceCreate(WorkspaceBase):
    """Schema for creating a new workspace."""

    owner_id: int = Field(..., ge=1, description="User ID of the workspace owner")


class WorkspaceUpdate(BaseModel):
    """Schema for updating a workspace."""

    name: str | None = Field(default=None, min_length=2, max_length=200)


class WorkspaceMemberAdd(BaseModel):
    """Schema for adding/updating a member in a workspace."""

    user_id: int = Field(..., ge=1, description="User ID to invite to the workspace")
    role: WorkspaceRole = Field(
        default=WorkspaceRole.VIEWER,
        description="Workspace member role (OWNER/EDITOR/VIEWER)",
    )


class WorkspaceMemberRoleUpdate(BaseModel):
    """Schema for updating an existing workspace member's role."""

    role: WorkspaceRole = Field(
        ...,
        description="New workspace role (OWNER/EDITOR/VIEWER)",
    )


class WorkspaceMemberResponse(BaseModel):
    """Schema for returning workspace membership details."""

    model_config = ConfigDict(from_attributes=True)

    workspace_id: int
    user_id: int
    role: WorkspaceRole
    user: UserResponse | None = None


class WorkspaceResponse(WorkspaceBase):
    """Schema for returning a workspace in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    created_at: datetime


class WorkspaceDetailResponse(WorkspaceResponse):
    """Schema for returning a workspace with owner and members."""

    owner: UserResponse | None = None
    members: list[WorkspaceMemberResponse] = Field(default_factory=list)
