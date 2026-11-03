from fastapi import HTTPException, status

from app.models.enums import TaskPriority, TaskStatus
from app.repositories.comment_repository import CommentRepository
from app.repositories.label_repository import LabelRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.schemas.comment import CommentCreate, CommentResponse
from app.schemas.common import PaginatedResponse
from app.schemas.task import (
    TaskCreate,
    TaskDetailResponse,
    TaskResponse,
    TaskUpdate,
)


class TaskService:
    """Business logic layer for managing tasks, task labels, and task comments."""

    def __init__(
        self,
        task_repo: TaskRepository,
        project_repo: ProjectRepository,
        user_repo: UserRepository,
        label_repo: LabelRepository,
        comment_repo: CommentRepository,
    ) -> None:
        self._task_repo = task_repo
        self._project_repo = project_repo
        self._user_repo = user_repo
        self._label_repo = label_repo
        self._comment_repo = comment_repo

    async def _validate_users(
        self,
        assignee_id: int | None,
        created_by: int | None = None,
    ) -> None:
        if assignee_id is not None:
            assignee = await self._user_repo.get_by_id(assignee_id)
            if assignee is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Assignee User with id={assignee_id} not found",
                )
        if created_by is not None:
            creator = await self._user_repo.get_by_id(created_by)
            if creator is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Creator User with id={created_by} not found",
                )

    async def list_project_tasks(
        self,
        project_id: int | None = None,
        *,
        page: int = 1,
        limit: int = 10,
        status_filter: TaskStatus | None = None,
        priority_filter: TaskPriority | None = None,
        assignee_id: int | None = None,
        search: str | None = None,
    ) -> PaginatedResponse[TaskResponse]:
        if project_id is not None:
            project = await self._project_repo.get_by_id(project_id)
            if project is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Project with id={project_id} not found",
                )
        items, total, pages = await self._task_repo.list_tasks(
            page=page,
            limit=limit,
            project_id=project_id,
            status=status_filter,
            priority=priority_filter,
            assignee_id=assignee_id,
            search=search,
        )
        return PaginatedResponse[TaskResponse](
            items=[TaskResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            limit=limit,
            pages=pages,
        )

    async def get_task(self, task_id: int) -> TaskDetailResponse:
        task = await self._task_repo.get_by_id_with_details(task_id)
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id={task_id} not found",
            )
        return TaskDetailResponse.model_validate(task)

    async def create_task_in_project(
        self,
        project_id: int,
        payload: TaskCreate,
    ) -> TaskResponse:
        project = await self._project_repo.get_by_id(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id={project_id} not found",
            )
        await self._validate_users(payload.assignee_id, payload.created_by)
        data = payload.model_dump()
        data["project_id"] = project_id
        task = await self._task_repo.create(data)
        return TaskResponse.model_validate(task)

    async def update_task(self, task_id: int, payload: TaskUpdate) -> TaskResponse:
        task = await self._task_repo.get_by_id(task_id)
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id={task_id} not found",
            )
        update_data = payload.model_dump(exclude_unset=True)
        await self._validate_users(update_data.get("assignee_id"))
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

    async def attach_label(self, task_id: int, label_id: int) -> TaskDetailResponse:
        task = await self._task_repo.get_by_id(task_id)
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id={task_id} not found",
            )
        label = await self._label_repo.get_by_id(label_id)
        if label is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Label with id={label_id} not found",
            )
        if label.project_id != task.project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Label does not belong to the same project as the task",
            )
        await self._task_repo.attach_label(task_id, label_id)
        refreshed = await self._task_repo.get_by_id_with_details(task_id)
        assert refreshed is not None
        return TaskDetailResponse.model_validate(refreshed)

    async def detach_label(self, task_id: int, label_id: int) -> None:
        deleted = await self._task_repo.detach_label(task_id, label_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Label {label_id} is not attached to task {task_id}",
            )

    async def add_comment(
        self,
        task_id: int,
        payload: CommentCreate,
    ) -> CommentResponse:
        task = await self._task_repo.get_by_id(task_id)
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id={task_id} not found",
            )
        author = await self._user_repo.get_by_id(payload.author_id)
        if author is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Author User with id={payload.author_id} not found",
            )
        comment = await self._comment_repo.create(
            {
                "task_id": task_id,
                "author_id": payload.author_id,
                "content": payload.content,
            }
        )
        return CommentResponse.model_validate(comment)

    async def delete_comment(self, task_id: int, comment_id: int) -> None:
        comment = await self._comment_repo.get_by_id(comment_id)
        if comment is None or comment.task_id != task_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comment with id={comment_id} not found on task {task_id}",
            )
        await self._comment_repo.delete(comment)
