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


async def get_user_workspace_role(
    workspace_repo: WorkspaceRepository,
    workspace_id: int,
    current_user: User,
) -> WorkspaceRole:
    """Resolve the current user's effective role in a workspace, or raise 404/403."""
    workspace = await workspace_repo.get_by_id(workspace_id)
    if workspace is None:
        raise NotFoundException(f"Workspace with id={workspace_id} not found")

    if current_user.role == UserRole.ADMIN or workspace.owner_id == current_user.id:
        return WorkspaceRole.OWNER

    member = await workspace_repo.get_member(workspace_id, current_user.id)
    if member is None:
        raise ForbiddenException("You are not a member of this workspace")
    return member.role


async def ensure_workspace_role(
    workspace_repo: WorkspaceRepository,
    workspace_id: int,
    current_user: User,
    allowed_roles: Sequence[WorkspaceRole],
) -> WorkspaceRole:
    """Verify RBAC permission for the authenticated user on a target workspace."""
    role = await get_user_workspace_role(workspace_repo, workspace_id, current_user)
    if current_user.role == UserRole.ADMIN:
        return role
    if role not in allowed_roles:
        allowed_str = ", ".join(r.value for r in allowed_roles)
        raise ForbiddenException(
            f"Insufficient workspace permissions (requires one of: {allowed_str})"
        )
    return role


async def ensure_project_role(
    project_repo: ProjectRepository,
    workspace_repo: WorkspaceRepository,
    project_id: int,
    current_user: User,
    allowed_roles: Sequence[WorkspaceRole],
) -> WorkspaceRole:
    """Verify RBAC permission on the workspace owning the given project."""
    project = await project_repo.get_by_id(project_id)
    if project is None:
        raise NotFoundException(f"Project with id={project_id} not found")

    return await ensure_workspace_role(
        workspace_repo,
        project.workspace_id,
        current_user,
        allowed_roles,
    )


async def ensure_task_read_permission(
    task_repo: TaskRepository,
    project_repo: ProjectRepository,
    workspace_repo: WorkspaceRepository,
    task_id: int,
    current_user: User,
) -> None:
    """Verify the user is an active workspace member (OWNER/EDITOR/VIEWER) or ADMIN to read/comment on a task."""
    task = await task_repo.get_by_id(task_id)
    if task is None:
        raise NotFoundException(f"Task with id={task_id} not found")

    await ensure_project_role(
        project_repo,
        workspace_repo,
        task.project_id,
        current_user,
        READ_ROLES,
    )


async def ensure_task_update_permission(
    task_repo: TaskRepository,
    project_repo: ProjectRepository,
    workspace_repo: WorkspaceRepository,
    task_id: int,
    current_user: User,
) -> None:
    """Verify permission to update a task: user MUST be an active member of the workspace with OWNER or EDITOR role (VIEWER cannot update)."""
    task = await task_repo.get_by_id(task_id)
    if task is None:
        raise NotFoundException(f"Task with id={task_id} not found")

    await ensure_project_role(
        project_repo,
        workspace_repo,
        task.project_id,
        current_user,
        WRITE_ROLES,
    )


async def ensure_task_delete_permission(
    task_repo: TaskRepository,
    project_repo: ProjectRepository,
    workspace_repo: WorkspaceRepository,
    task_id: int,
    current_user: User,
) -> None:
    """Verify permission to delete a task: must still be a workspace member AND (workspace OWNER, ADMIN, or EDITOR who created the task)."""
    task = await task_repo.get_by_id(task_id)
    if task is None:
        raise NotFoundException(f"Task with id={task_id} not found")

    role = await ensure_project_role(
        project_repo,
        workspace_repo,
        task.project_id,
        current_user,
        WRITE_ROLES,
    )
    if (
        current_user.role != UserRole.ADMIN
        and role != WorkspaceRole.OWNER
        and task.created_by != current_user.id
    ):
        raise ForbiddenException(
            "Only the workspace OWNER, ADMIN, or the task creator (with EDITOR role) can delete a task"
        )


async def ensure_comment_delete_permission(
    comment_repo: CommentRepository,
    task_repo: TaskRepository,
    project_repo: ProjectRepository,
    workspace_repo: WorkspaceRepository,
    task_id: int,
    comment_id: int,
    current_user: User,
) -> None:
    """Verify that a comment is deleted only by its author (who is still a workspace member), workspace OWNER, or ADMIN."""
    comment = await comment_repo.get_by_id(comment_id)
    if comment is None or comment.task_id != task_id:
        raise NotFoundException(
            f"Comment with id={comment_id} not found on task {task_id}"
        )

    task = await task_repo.get_by_id(task_id)
    if task is None:
        raise NotFoundException(f"Task with id={task_id} not found")

    role = await ensure_project_role(
        project_repo,
        workspace_repo,
        task.project_id,
        current_user,
        READ_ROLES,
    )
    if (
        current_user.role != UserRole.ADMIN
        and role != WorkspaceRole.OWNER
        and comment.author_id != current_user.id
    ):
        raise ForbiddenException(
            "Only the comment author, workspace OWNER, or ADMIN can delete this comment"
        )
