from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query, status

from app.api.deps import PaginationParams, get_task_service
from app.core.notifications import notification_outbox
from app.models.enums import TaskPriority, TaskStatus
from app.schemas.comment import CommentCreate, CommentResponse
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.task import TaskDetailResponse, TaskResponse, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])

TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
PaginationDep = Annotated[PaginationParams, Depends()]


@router.get(
    "",
    response_model=PaginatedResponse[TaskResponse],
    summary="List tasks across projects with filtering and pagination (page + limit)",
)
async def list_tasks(
    service: TaskServiceDep,
    pagination: PaginationDep,
    project_id: Annotated[
        int | None,
        Query(ge=1, description="Filter tasks by project ID"),
    ] = None,
    status_filter: Annotated[
        TaskStatus | None,
        Query(alias="status", description="Filter tasks by status"),
    ] = None,
    priority_filter: Annotated[
        TaskPriority | None,
        Query(alias="priority", description="Filter tasks by priority"),
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
    return await service.list_project_tasks(
        project_id=project_id,
        page=pagination.page,
        limit=pagination.limit,
        status_filter=status_filter,
        priority_filter=priority_filter,
        assignee_id=assignee_id,
        search=search,
    )


@router.get(
    "/notifications/outbox",
    summary="Inspect background email notifications sent upon task assignment",
)
async def list_sent_notifications() -> list[dict[str, Any]]:
    return list(reversed(notification_outbox[-50:]))


@router.get(
    "/{task_id}",
    response_model=TaskDetailResponse,
    summary="Get a task by ID including labels and comments",
)
async def get_task(
    service: TaskServiceDep,
    task_id: Annotated[int, Path(ge=1, description="Task unique ID")],
) -> TaskDetailResponse:
    return await service.get_task(task_id)


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Partially update a task (invalidates Redis cache & triggers email notification if assignee changes)",
)
async def update_task(
    payload: TaskUpdate,
    background_tasks: BackgroundTasks,
    service: TaskServiceDep,
    task_id: Annotated[int, Path(ge=1, description="Task unique ID")],
) -> TaskResponse:
    return await service.update_task(
        task_id,
        payload,
        background_tasks=background_tasks,
    )


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


@router.post(
    "/{task_id}/labels/{label_id}",
    response_model=TaskDetailResponse,
    summary="Attach a project label to a task",
)
async def attach_label_to_task(
    service: TaskServiceDep,
    task_id: Annotated[int, Path(ge=1, description="Task unique ID")],
    label_id: Annotated[int, Path(ge=1, description="Label unique ID")],
) -> TaskDetailResponse:
    return await service.attach_label(task_id, label_id)


@router.delete(
    "/{task_id}/labels/{label_id}",
    response_model=MessageResponse,
    summary="Detach a label from a task",
)
async def detach_label_from_task(
    service: TaskServiceDep,
    task_id: Annotated[int, Path(ge=1, description="Task unique ID")],
    label_id: Annotated[int, Path(ge=1, description="Label unique ID")],
) -> MessageResponse:
    await service.detach_label(task_id, label_id)
    return MessageResponse(
        message=f"Label {label_id} detached from task {task_id} successfully"
    )


@router.post(
    "/{task_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a comment on a task",
)
async def add_comment_to_task(
    payload: CommentCreate,
    service: TaskServiceDep,
    task_id: Annotated[int, Path(ge=1, description="Task unique ID")],
) -> CommentResponse:
    return await service.add_comment(task_id, payload)


@router.delete(
    "/{task_id}/comments/{comment_id}",
    response_model=MessageResponse,
    summary="Delete a comment from a task",
)
async def delete_comment_from_task(
    service: TaskServiceDep,
    task_id: Annotated[int, Path(ge=1, description="Task unique ID")],
    comment_id: Annotated[int, Path(ge=1, description="Comment unique ID")],
) -> MessageResponse:
    await service.delete_comment(task_id, comment_id)
    return MessageResponse(message=f"Comment {comment_id} deleted successfully")
