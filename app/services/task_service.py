from fastapi import HTTPException, status

from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.task import TaskCreate, TaskPriority, TaskResponse, TaskStatus, TaskUpdate


class TaskService:
    """Business logic layer for managing tasks with async SQLAlchemy repositories."""

    def __init__(
        self,
        task_repo: TaskRepository,
        project_repo: ProjectRepository,
        user_repo: UserRepository,
    ) -> None:
        self._task_repo = task_repo
        self._project_repo = project_repo
        self._user_repo = user_repo

    async def _validate_relations(
        self,
        project_id: int | None,
        assignee_id: int | None,
    ) -> None:
        if project_id is not None:
            project = await self._project_repo.get_by_id(project_id)
            if project is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Project with id={project_id} not found",
                )
        if assignee_id is not None:
            assignee = await self._user_repo.get_by_id(assignee_id)
            if assignee is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Assignee User with id={assignee_id} not found",
                )

    async def list_tasks(
        self,
        *,
        page: int = 1,
        size: int = 10,
        status_filter: TaskStatus | None = None,
        priority_filter: TaskPriority | None = None,
        project_id: int | None = None,
        assignee_id: int | None = None,
        search: str | None = None,
    ) -> PaginatedResponse[TaskResponse]:
        items, total, pages = await self._task_repo.list_tasks(
            page=page,
            size=size,
            status=status_filter,
            priority=priority_filter,
            project_id=project_id,
            assignee_id=assignee_id,
            search=search,
        )
        return PaginatedResponse[TaskResponse](
            items=[TaskResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def get_task(self, task_id: int) -> TaskResponse:
        task = await self._task_repo.get_by_id(task_id)
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id={task_id} not found",
            )
        return TaskResponse.model_validate(task)

    async def create_task(self, payload: TaskCreate) -> TaskResponse:
        await self._validate_relations(payload.project_id, payload.assignee_id)
        task = await self._task_repo.create(payload.model_dump())
        return TaskResponse.model_validate(task)

    async def update_task(self, task_id: int, payload: TaskUpdate) -> TaskResponse:
        task = await self._task_repo.get_by_id(task_id)
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id={task_id} not found",
            )
        update_data = payload.model_dump(exclude_unset=True)
        await self._validate_relations(
            update_data.get("project_id"),
            update_data.get("assignee_id"),
        )
        updated = await self._task_repo.update(task, update_data)
        return TaskResponse.model_validate(updated)

    async def delete_task(self, task_id: int) -> None:
        task = await self._task_repo.get_by_id(task_id)
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id={task_id} not found",
            )
        await self._task_repo.delete(task)
