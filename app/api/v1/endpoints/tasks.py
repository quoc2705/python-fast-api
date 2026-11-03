from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.deps import PaginationParams, get_task_service
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.task import TaskCreate, TaskPriority, TaskResponse, TaskStatus, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])

TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
PaginationDep = Annotated[PaginationParams, Depends()]


@router.get(
    "",
    response_model=PaginatedResponse[TaskResponse],
    summary="List tasks with filtering and pagination",
)
async def list_tasks(
    service: TaskServiceDep,
    pagination: PaginationDep,
    status_filter: Annotated[
        TaskStatus | None,
        Query(alias="status", description="Filter tasks by status"),
    ] = None,
    priority_filter: Annotated[
        TaskPriority | None,
        Query(alias="priority", description="Filter tasks by priority"),
    ] = None,
    project_id: Annotated[
        int | None,
        Query(ge=1, description="Filter tasks by project ID"),
    ] = None,
    assignee_id: Annotated[
        int | None,
        Query(ge=1, description="Filter tasks by assignee user ID"),
    ] = None,
    search: Annotated[
        str | None,
        Query(max_length=100, description="Search keyword in title or description"),
    ] = None,
) -> PaginatedResponse[TaskResponse]:
    return await service.list_tasks(
        page=pagination.page,
        size=pagination.size,
        status_filter=status_filter,
        priority_filter=priority_filter,
        project_id=project_id,
        assignee_id=assignee_id,
        search=search,
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a task by ID",
)
async def get_task(
    service: TaskServiceDep,
    task_id: Annotated[int, Path(ge=1, description="Task unique ID")],
) -> TaskResponse:
    return await service.get_task(task_id)


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
async def create_task(
    payload: TaskCreate,
    service: TaskServiceDep,
) -> TaskResponse:
    return await service.create_task(payload)


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Replace a task by ID",
)
async def replace_task(
    payload: TaskCreate,
    service: TaskServiceDep,
    task_id: Annotated[int, Path(ge=1, description="Task unique ID")],
) -> TaskResponse:
    update_payload = TaskUpdate(
        title=payload.title,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        project_id=payload.project_id,
        assignee_id=payload.assignee_id,
    )
    return await service.update_task(task_id, update_payload)


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Partially update a task by ID",
)
async def update_task(
    payload: TaskUpdate,
    service: TaskServiceDep,
    task_id: Annotated[int, Path(ge=1, description="Task unique ID")],
) -> TaskResponse:
    return await service.update_task(task_id, payload)


@router.delete(
    "/{task_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a task by ID",
)
async def delete_task(
    service: TaskServiceDep,
    task_id: Annotated[int, Path(ge=1, description="Task unique ID")],
) -> MessageResponse:
    await service.delete_task(task_id)
    return MessageResponse(message=f"Task {task_id} deleted successfully")
