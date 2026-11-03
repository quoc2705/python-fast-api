from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.deps import PaginationParams, get_project_service, get_task_service
from app.models.enums import ProjectStatus, TaskPriority, TaskStatus
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.label import LabelCreate, LabelResponse, LabelUpdate
from app.schemas.project import (
    ProjectDetailResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.schemas.task import TaskCreate, TaskResponse
from app.services.project_service import ProjectService
from app.services.task_service import TaskService

router = APIRouter(prefix="/projects", tags=["Projects"])

ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
PaginationDep = Annotated[PaginationParams, Depends()]


@router.get(
    "",
    response_model=PaginatedResponse[ProjectResponse],
    summary="List projects with pagination and filtering",
)
async def list_projects(
    service: ProjectServiceDep,
    pagination: PaginationDep,
    workspace_id: Annotated[
        int | None,
        Query(ge=1, description="Filter projects by workspace ID"),
    ] = None,
    status_filter: Annotated[
        ProjectStatus | None,
        Query(alias="status", description="Filter projects by status (ACTIVE/ARCHIVED)"),
    ] = None,
    search: Annotated[
        str | None,
        Query(max_length=100, description="Search by project name or description"),
    ] = None,
) -> PaginatedResponse[ProjectResponse]:
    return await service.list_projects(
        page=pagination.page,
        limit=pagination.limit,
        workspace_id=workspace_id,
        status_filter=status_filter,
        search=search,
    )


@router.get(
    "/{project_id}",
    response_model=ProjectDetailResponse,
    summary="Get a project with its tasks and labels by ID",
)
async def get_project(
    service: ProjectServiceDep,
    project_id: Annotated[int, Path(ge=1, description="Project unique ID")],
) -> ProjectDetailResponse:
    return await service.get_project(project_id)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update a project by ID",
)
async def update_project(
    payload: ProjectUpdate,
    service: ProjectServiceDep,
    project_id: Annotated[int, Path(ge=1, description="Project unique ID")],
) -> ProjectResponse:
    return await service.update_project(project_id, payload)


@router.post(
    "/{project_id}/archive",
    response_model=ProjectResponse,
    summary="Archive a project by ID",
)
async def archive_project(
    service: ProjectServiceDep,
    project_id: Annotated[int, Path(ge=1, description="Project unique ID")],
) -> ProjectResponse:
    return await service.archive_project(project_id)


@router.delete(
    "/{project_id}",
    response_model=MessageResponse,
    summary="Delete a project by ID",
)
async def delete_project(
    service: ProjectServiceDep,
    project_id: Annotated[int, Path(ge=1, description="Project unique ID")],
) -> MessageResponse:
    await service.delete_project(project_id)
    return MessageResponse(message=f"Project {project_id} deleted successfully")


@router.get(
    "/{project_id}/tasks",
    response_model=PaginatedResponse[TaskResponse],
    summary="List tasks in a project with filtering and pagination (page + limit)",
)
async def list_project_tasks(
    task_service: TaskServiceDep,
    pagination: PaginationDep,
    project_id: Annotated[int, Path(ge=1, description="Project unique ID")],
    status_filter: Annotated[
        TaskStatus | None,
        Query(alias="status", description="Filter by task status"),
    ] = None,
    priority_filter: Annotated[
        TaskPriority | None,
        Query(alias="priority", description="Filter by task priority"),
    ] = None,
    assignee_id: Annotated[
        int | None,
        Query(ge=1, description="Filter by assignee user ID"),
    ] = None,
    search: Annotated[
        str | None,
        Query(max_length=100, description="Search keyword in title or description"),
    ] = None,
) -> PaginatedResponse[TaskResponse]:
    return await task_service.list_project_tasks(
        project_id=project_id,
        page=pagination.page,
        limit=pagination.limit,
        status_filter=status_filter,
        priority_filter=priority_filter,
        assignee_id=assignee_id,
        search=search,
    )


@router.post(
    "/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task inside a project",
)
async def create_project_task(
    payload: TaskCreate,
    task_service: TaskServiceDep,
    project_id: Annotated[int, Path(ge=1, description="Project unique ID")],
) -> TaskResponse:
    return await task_service.create_task_in_project(project_id, payload)


@router.get(
    "/{project_id}/labels",
    response_model=list[LabelResponse],
    summary="List labels defined for a project",
)
async def list_project_labels(
    service: ProjectServiceDep,
    project_id: Annotated[int, Path(ge=1, description="Project unique ID")],
) -> list[LabelResponse]:
    return await service.list_labels(project_id)


@router.post(
    "/{project_id}/labels",
    response_model=LabelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a label in a project",
)
async def create_project_label(
    payload: LabelCreate,
    service: ProjectServiceDep,
    project_id: Annotated[int, Path(ge=1, description="Project unique ID")],
) -> LabelResponse:
    return await service.create_label(project_id, payload)


@router.patch(
    "/{project_id}/labels/{label_id}",
    response_model=LabelResponse,
    summary="Update a label in a project",
)
async def update_project_label(
    payload: LabelUpdate,
    service: ProjectServiceDep,
    project_id: Annotated[int, Path(ge=1, description="Project unique ID")],
    label_id: Annotated[int, Path(ge=1, description="Label unique ID")],
) -> LabelResponse:
    _ = project_id
    return await service.update_label(label_id, payload)


@router.delete(
    "/{project_id}/labels/{label_id}",
    response_model=MessageResponse,
    summary="Delete a label from a project",
)
async def delete_project_label(
    service: ProjectServiceDep,
    project_id: Annotated[int, Path(ge=1, description="Project unique ID")],
    label_id: Annotated[int, Path(ge=1, description="Label unique ID")],
) -> MessageResponse:
    _ = project_id
    await service.delete_label(label_id)
    return MessageResponse(message=f"Label {label_id} deleted successfully")
