from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.services.project_service import ProjectService
from app.services.task_service import TaskService
from app.services.user_service import UserService

DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


@dataclass(frozen=True)
class PaginationParams:
    """Reusable pagination query parameters dependency."""

    page: int = Query(default=1, ge=1, description="Page number (1-indexed)")
    size: int = Query(default=10, ge=1, le=100, description="Items per page (max 100)")


def get_user_repository(session: DBSessionDep) -> UserRepository:
    return UserRepository(session=session)


def get_project_repository(session: DBSessionDep) -> ProjectRepository:
    return ProjectRepository(session=session)


def get_task_repository(session: DBSessionDep) -> TaskRepository:
    return TaskRepository(session=session)


def get_user_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(repository=user_repo)


def get_project_service(
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> ProjectService:
    return ProjectService(project_repo=project_repo, user_repo=user_repo)


def get_task_service(
    task_repo: Annotated[TaskRepository, Depends(get_task_repository)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> TaskService:
    return TaskService(
        task_repo=task_repo,
        project_repo=project_repo,
        user_repo=user_repo,
    )
