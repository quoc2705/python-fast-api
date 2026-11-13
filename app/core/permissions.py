from collections.abc import Sequence

from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.enums import UserRole, WorkspaceRole
from app.models.user import User
from app.repositories.comment_repository import CommentRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.workspace_repository import WorkspaceRepository

READ_ROLES: tuple[WorkspaceRole, ...] = (
    WorkspaceRole.OWNER,
    WorkspaceRole.EDITOR,
    WorkspaceRole.VIEWER,
)
WRITE_ROLES: tuple[WorkspaceRole, ...] = (
    WorkspaceRole.OWNER,
    WorkspaceRole.EDITOR,
)
OWNER_ONLY_ROLES: tuple[WorkspaceRole, ...] = (WorkspaceRole.OWNER,)


async def ensure_workspace_role(
    workspace_repo: WorkspaceRepository,
    workspace_id: int,
    current_user: User | None,
    allowed_roles: Sequence[WorkspaceRole],
) -> None:
    """Verify RBAC permission for the current user on a target workspace."""
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


async def ensure_project_role(
    project_repo: ProjectRepository,
    workspace_repo: WorkspaceRepository,
    project_id: int,
    current_user: User | None,
    allowed_roles: Sequence[WorkspaceRole],
) -> None:
    """Verify RBAC permission on the workspace owning the given project."""
    project = await project_repo.get_by_id(project_id)
    if project is None:
        raise NotFoundException(f"Project with id={project_id} not found")

    await ensure_workspace_role(
        workspace_repo,
        project.workspace_id,
        current_user,
        allowed_roles,
    )


async def ensure_task_ownership_or_role(
    task_repo: TaskRepository,
    project_repo: ProjectRepository,
    workspace_repo: WorkspaceRepository,
    task_id: int,
    current_user: User | None,
    allowed_roles: Sequence[WorkspaceRole],
) -> None:
    """Verify task resource ownership (creator/assignee) or workspace RBAC role."""
    task = await task_repo.get_by_id(task_id)
    if task is None:
        raise NotFoundException(f"Task with id={task_id} not found")

    if current_user is None or current_user.role == UserRole.ADMIN:
        return

    if task.created_by == current_user.id or task.assignee_id == current_user.id:
        return

    await ensure_project_role(
        project_repo,
        workspace_repo,
        task.project_id,
        current_user,
        allowed_roles,
    )


async def ensure_comment_ownership_or_role(
    comment_repo: CommentRepository,
    task_repo: TaskRepository,
    project_repo: ProjectRepository,
    workspace_repo: WorkspaceRepository,
    task_id: int,
    comment_id: int,
    current_user: User | None,
) -> None:
    """Verify that a comment is deleted only by its author, workspace OWNER, or ADMIN."""
    comment = await comment_repo.get_by_id(comment_id)
    if comment is None or comment.task_id != task_id:
        raise NotFoundException(
            f"Comment with id={comment_id} not found on task {task_id}"
        )

    if current_user is None or current_user.role == UserRole.ADMIN:
        return

    if comment.author_id == current_user.id:
        return

    task = await task_repo.get_by_id(task_id)
    if task is None:
        raise NotFoundException(f"Task with id={task_id} not found")

    await ensure_project_role(
        project_repo,
        workspace_repo,
        task.project_id,
        current_user,
        OWNER_ONLY_ROLES,
    )
