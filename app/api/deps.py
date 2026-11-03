from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query

from app.repositories.task_repository import TaskRepository, task_repository_singleton
from app.services.task_service import TaskService


@dataclass(frozen=True)
class PaginationParams:
    """Reusable pagination query parameters dependency."""

    page: int = Query(default=1, ge=1, description="Page number (1-indexed)")
    size: int = Query(default=10, ge=1, le=100, description="Items per page (max 100)")


def get_task_repository() -> TaskRepository:
    """Dependency provider for TaskRepository."""
    return task_repository_singleton


def get_task_service(
    repository: Annotated[TaskRepository, Depends(get_task_repository)],
) -> TaskService:
    """Dependency provider for TaskService."""
    return TaskService(repository=repository)
