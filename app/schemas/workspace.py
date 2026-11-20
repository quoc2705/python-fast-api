from datetime import datetime
from typing import Any

from pydantic import ConfigDict, Field, model_validator

from app.core.constants import WORKSPACE_NAME_MAX_LENGTH, WORKSPACE_NAME_MIN_LENGTH
from app.models.enums import WorkspaceRole
from app.schemas.base import BaseSchema, reject_explicit_nulls
from app.schemas.user import UserResponse


class WorkspaceBase(BaseSchema):
    """Shared properties for Workspace schemas."""

    name: str = Field(
        ...,
        min_length=WORKSPACE_NAME_MIN_LENGTH,
        max_length=WORKSPACE_NAME_MAX_LENGTH,
        description="Workspace name",
        examples=["Engineering Workspace"],
    )


class WorkspaceCreate(WorkspaceBase):
    """Schema for creating a new workspace (owner is set from current authenticated user)."""


class WorkspaceUpdate(BaseSchema):
    """Schema for updating a workspace."""

    name: str | None = Field(
        default=None,
        min_length=WORKSPACE_NAME_MIN_LENGTH,
        max_length=WORKSPACE_NAME_MAX_LENGTH,
    )

    @model_validator(mode="before")
    @classmethod
    def _reject_nulls(cls, data: Any) -> Any:
        return reject_explicit_nulls(data, ("name",))


class WorkspaceMemberAdd(BaseSchema):
    """Schema for adding/updating a member in a workspace."""

    user_id: int = Field(..., ge=1, description="User ID to invite to the workspace")
    role: WorkspaceRole = Field(
        default=WorkspaceRole.VIEWER,
        description="Workspace member role (OWNER/EDITOR/VIEWER)",
    )


class WorkspaceMemberRoleUpdate(BaseSchema):
    """Schema for updating an existing workspace member's role."""

    role: WorkspaceRole = Field(
        ...,
        description="New workspace role (OWNER/EDITOR/VIEWER)",
    )


class WorkspaceMemberResponse(BaseSchema):
    """Schema for returning workspace membership details."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    workspace_id: int
    user_id: int
    role: WorkspaceRole
    user: UserResponse | None = None


class WorkspaceResponse(WorkspaceBase):
    """Schema for returning a workspace in API responses."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: int
    owner_id: int
    created_at: datetime


class WorkspaceDetailResponse(WorkspaceResponse):
    """Schema for returning a workspace with owner and members."""

    owner: UserResponse | None = None
    members: list[WorkspaceMemberResponse] = Field(default_factory=list)
