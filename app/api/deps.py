from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.repositories.comment_repository import CommentRepository
from app.repositories.label_repository import LabelRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.services.project_service import ProjectService
from app.services.task_service import TaskService
from app.services.user_service import UserService
from app.services.workspace_service import WorkspaceService

DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


@dataclass(frozen=True)
class PaginationParams:
    """Reusable pagination query parameters dependency (page + limit)."""

    page: int = Query(default=1, ge=1, description="Page number (1-indexed)")
    limit: int = Query(default=10, ge=1, le=100, description="Items per page (max 100)")


def get_user_repository(session: DBSessionDep) -> UserRepository:
    return UserRepository(session=session)


def get_workspace_repository(session: DBSessionDep) -> WorkspaceRepository:
    return WorkspaceRepository(session=session)


def get_project_repository(session: DBSessionDep) -> ProjectRepository:
    return ProjectRepository(session=session)


def get_task_repository(session: DBSessionDep) -> TaskRepository:
    return TaskRepository(session=session)


def get_label_repository(session: DBSessionDep) -> LabelRepository:
    return LabelRepository(session=session)


def get_comment_repository(session: DBSessionDep) -> CommentRepository:
    return CommentRepository(session=session)


def get_user_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(repository=user_repo)


def get_workspace_service(
    workspace_repo: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> WorkspaceService:
    return WorkspaceService(workspace_repo=workspace_repo, user_repo=user_repo)


def get_project_service(
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspace_repo: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    label_repo: Annotated[LabelRepository, Depends(get_label_repository)],
) -> ProjectService:
    return ProjectService(
        project_repo=project_repo,
        workspace_repo=workspace_repo,
        label_repo=label_repo,
    )


def get_task_service(
    task_repo: Annotated[TaskRepository, Depends(get_task_repository)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    label_repo: Annotated[LabelRepository, Depends(get_label_repository)],
    comment_repo: Annotated[CommentRepository, Depends(get_comment_repository)],
) -> TaskService:
    return TaskService(
        task_repo=task_repo,
        project_repo=project_repo,
        user_repo=user_repo,
        label_repo=label_repo,
        comment_repo=comment_repo,
    )
