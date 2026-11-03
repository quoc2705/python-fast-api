from datetime import datetime, timezone
from math import ceil

from app.schemas.common import PaginatedResponse
from app.schemas.task import TaskCreate, TaskPriority, TaskResponse, TaskStatus, TaskUpdate


class TaskRepository:
    """In-memory repository for Task resource (Session 1 skeleton before DB integration)."""

    def __init__(self) -> None:
        self._storage: dict[int, TaskResponse] = {}
        self._counter: int = 0

    def seed_initial_data(self) -> None:
        """Seed sample tasks on startup if empty."""
        if self._storage:
            return
        self.create(
            TaskCreate(
                title="Setup FastAPI Layered Architecture",
                description="Initialize routers, services, repositories, and Pydantic v2 schemas",
                status=TaskStatus.DONE,
                priority=TaskPriority.HIGH,
            )
        )
        self.create(
            TaskCreate(
                title="Implement CRUD Endpoints for Tasks",
                description="Support GET, POST, PUT, PATCH, DELETE with dependency injection",
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.MEDIUM,
            )
        )

    def create(self, payload: TaskCreate) -> TaskResponse:
        self._counter += 1
        now = datetime.now(timezone.utc)
        task = TaskResponse(
            id=self._counter,
            title=payload.title,
            description=payload.description,
            status=payload.status,
            priority=payload.priority,
            created_at=now,
            updated_at=now,
        )
        self._storage[task.id] = task
        return task

    def get_by_id(self, task_id: int) -> TaskResponse | None:
        return self._storage.get(task_id)

    def list_tasks(
        self,
        *,
        page: int = 1,
        size: int = 10,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        search: str | None = None,
    ) -> PaginatedResponse[TaskResponse]:
        items = list(self._storage.values())
        if status is not None:
            items = [item for item in items if item.status == status]
        if priority is not None:
            items = [item for item in items if item.priority == priority]
        if search:
            keyword = search.lower().strip()
            items = [
                item
                for item in items
                if keyword in item.title.lower()
                or (item.description and keyword in item.description.lower())
            ]

        total = len(items)
        pages = ceil(total / size) if total > 0 else 0
        start = (page - 1) * size
        end = start + size
        return PaginatedResponse[TaskResponse](
            items=items[start:end],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    def update(self, task_id: int, payload: TaskUpdate) -> TaskResponse | None:
        existing = self._storage.get(task_id)
        if existing is None:
            return None
        update_data = payload.model_dump(exclude_unset=True)
        updated = existing.model_copy(
            update={
                **update_data,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        self._storage[task_id] = updated
        return updated

    def delete(self, task_id: int) -> bool:
        return self._storage.pop(task_id, None) is not None


task_repository_singleton = TaskRepository()
