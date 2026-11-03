from fastapi import HTTPException, status

from app.repositories.task_repository import TaskRepository
from app.schemas.common import PaginatedResponse
from app.schemas.task import TaskCreate, TaskPriority, TaskResponse, TaskStatus, TaskUpdate


class TaskService:
    """Business logic layer for managing tasks."""

    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    def list_tasks(
        self,
        *,
        page: int = 1,
        size: int = 10,
        status_filter: TaskStatus | None = None,
        priority_filter: TaskPriority | None = None,
        search: str | None = None,
    ) -> PaginatedResponse[TaskResponse]:
        return self._repository.list_tasks(
            page=page,
            size=size,
            status=status_filter,
            priority=priority_filter,
            search=search,
        )

    def get_task(self, task_id: int) -> TaskResponse:
        task = self._repository.get_by_id(task_id)
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id={task_id} not found",
            )
        return task

    def create_task(self, payload: TaskCreate) -> TaskResponse:
        return self._repository.create(payload)

    def update_task(self, task_id: int, payload: TaskUpdate) -> TaskResponse:
        updated = self._repository.update(task_id, payload)
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id={task_id} not found",
            )
        return updated

    def delete_task(self, task_id: int) -> None:
        deleted = self._repository.delete(task_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id={task_id} not found",
            )
