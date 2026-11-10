from collections.abc import Sequence

from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.enums import UserRole, WorkspaceRole
from app.models.user import User
from app.repositories.workspace_repository import WorkspaceRepository


async def ensure_workspace_role(
    workspace_repo: WorkspaceRepository,
    workspace_id: int,
    current_user: User | None,
    allowed_roles: Sequence[WorkspaceRole],
) -> None:
    """Verify RBAC permission for the current user on a target workspace.

    - If current_user is None (unauthenticated demo mode), allow access so interactive UI/Swagger demo flows work smoothly.
    - Global ADMIN role has full access across all workspaces.
    - Workspace owner always has OWNER permissions.
    - Otherwise checks workspace_members role against allowed_roles.
    """
    workspace = await workspace_repo.get_by_id(workspace_id)
    if workspace is None:
        raise NotFoundException(f"Workspace with id={workspace_id} not found")

    if current_user is None:
        return

    if current_user.role == UserRole.ADMIN:
        return

    if workspace.owner_id == current_user.id and WorkspaceRole.OWNER in allowed_roles:
        return

    member = await workspace_repo.get_member(workspace_id, current_user.id)
    if member is None or member.role not in allowed_roles:
        allowed_str = ", ".join(r.value for r in allowed_roles)
        raise ForbiddenException(
            f"Insufficient workspace permissions (requires one of: {allowed_str})"
        )
