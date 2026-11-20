from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query, Response, status

from app.api.deps import (
    PaginationParams,
    get_current_user,
    get_project_repository,
    get_project_service,
    get_task_service,
    get_workspace_repository,
    require_admin_user,
)
from app.core.permissions import (
    OWNER_ONLY_ROLES,
    READ_ROLES,
    WRITE_ROLES,
    ensure_project_role,
)
from app.models.enums import ProjectStatus, TaskPriority, TaskStatus
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.error import (
    AUTH_ERROR_RESPONSES,
    RESOURCE_READ_RESPONSES,
    RESOURCE_WRITE_RESPONSES,
    ProjectCacheStatsResponse,
)
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
ProjectRepoDep = Annotated[ProjectRepository, Depends(get_project_repository)]
WorkspaceRepoDep = Annotated[WorkspaceRepository, Depends(get_workspace_repository)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
AdminUserDep = Annotated[User, Depends(require_admin_user)]
PaginationDep = Annotated[PaginationParams, Depends()]


@router.get(
    "",
    response_model=PaginatedResponse[ProjectResponse],
    summary="List projects with pagination and filtering",
    responses=AUTH_ERROR_RESPONSES,
)
async def list_projects(
    _current_user: CurrentUserDep,
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
    summary="Get a project with its tasks and labels by ID (RBAC: OWNER/EDITOR/VIEWER)",
    responses=RESOURCE_READ_RESPONSES,
)
async def get_project(
    service: ProjectServiceDep,
    project_repo: ProjectRepoDep,
    workspace_repo: WorkspaceRepoDep,
    current_user: CurrentUserDep,
    project_id: Annotated[int, Path(ge=1, description="Project unique ID")],
) -> ProjectDetailResponse:
    await ensure_project_role(
        project_repo,
        workspace_repo,
        project_id,
        current_user,
        READ_ROLES,
    )
    return await service.get_project(project_id)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update a project by ID (RBAC: OWNER/EDITOR)",
    responses=RESOURCE_WRITE_RESPONSES,
)
async def update_project(
    payload: ProjectUpdate,
    service: ProjectServiceDep,
    project_repo: ProjectRepoDep,
    workspace_repo: WorkspaceRepoDep,
    current_user: CurrentUserDep,
    project_id: Annotated[int, Path(ge=1, description="Project unique ID")],
) -> ProjectResponse:
    await ensure_project_role(
        project_repo,
        workspace_repo,
        project_id,
        current_user,
        WRITE_ROLES,
    )
    return await service.update_project(project_id, payload)


@router.post(
    "/{project_id}/archive",
    response_model=ProjectResponse,
    summary="Archive a project by ID (RBAC: OWNER/EDITOR)",
    responses=RESOURCE_WRITE_RESPONSES,
)
async def archive_project(
    service: ProjectServiceDep,
    project_repo: ProjectRepoDep,
    workspace_repo: WorkspaceRepoDep,
    current_user: CurrentUserDep,
    project_id: Annotated[int, Path(ge=1, description="Project unique ID")],
) -> ProjectResponse:
    await ensure_project_role(
        project_repo,
        workspace_repo,
        project_id,
        current_user,
        WRITE_ROLES,
    )
    return await service.archive_project(project_id)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project by ID (RBAC: OWNER only)",
    responses=RESOURCE_READ_RESPONSES,
)
async def delete_project(
    service: ProjectServiceDep,
    project_repo: ProjectRepoDep,
    workspace_repo: WorkspaceRepoDep,
    current_user: CurrentUserDep,
    project_id: Annotated[int, Path(ge=1, description="Project unique ID")],
) -> Response:
    await ensure_project_role(
        project_repo,
        workspace_repo,
        project_id,
        current_user,
        OWNER_ONLY_ROLES,
    )
    await service.delete_project(project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{project_id}/tasks",
    response_model=PaginatedResponse[TaskResponse],
    summary="List tasks in a project (Filtered + Paginated + Cached in Redis, RBAC: OWNER/EDITOR/VIEWER)",
    responses=RESOURCE_READ_RESPONSES,
)
async def list_project_tasks(
    task_service: TaskServiceDep,
    project_repo: ProjectRepoDep,
    workspace_repo: WorkspaceRepoDep,
    current_user: CurrentUserDep,
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
    await ensure_project_role(
        project_repo,
        workspace_repo,
        project_id,
        current_user,
        READ_ROLES,
    )
    return await task_service.list_project_tasks(
        project_id=project_id,
        page=pagination.page,
        limit=pagination.limit,
        status_filter=status_filter,
        priority_filter=priority_filter,
        assignee_id=assignee_id,
        search=search,
    )


@router.get(
    "/{project_id}/tasks/cache-stats",
    response_model=ProjectCacheStatsResponse,
    summary="Inspect Redis / memory cache hit-rate and telemetry for a project (RBAC: ADMIN only)",
    responses=RESOURCE_READ_RESPONSES,
)
async def get_project_tasks_cache_stats(
    _admin: AdminUserDep,
    task_service: TaskServiceDep,
    project_id: Annotated[int, Path(ge=1, description="Project unique ID")],
) -> ProjectCacheStatsResponse:
    return await task_service.get_project_tasks_cache_stats(project_id)


@router.delete(
    "/{project_id}/tasks/cache",
    response_model=MessageResponse,
    summary="Manually invalidate cached task queries for a project (RBAC: OWNER/EDITOR)",
    responses=RESOURCE_READ_RESPONSES,
)
async def flush_project_tasks_cache(
    task_service: TaskServiceDep,
    project_repo: ProjectRepoDep,
    workspace_repo: WorkspaceRepoDep,
    current_user: CurrentUserDep,
    project_id: Annotated[int, Path(ge=1, description="Project unique ID")],
) -> MessageResponse:
    await ensure_project_role(
        project_repo,
        workspace_repo,
        project_id,
        current_user,
        WRITE_ROLES,
    )
    deleted = await task_service.flush_project_tasks_cache(project_id)
    return MessageResponse(
        message=f"Invalidated {deleted} cached entries for project {project_id}"
    )


@router.post(
    "/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task in a project (RBAC: OWNER/EDITOR)",
    responses=RESOURCE_WRITE_RESPONSES,
)
async def create_project_task(
    payload: TaskCreate,
    background_tasks: BackgroundTasks,
    task_service: TaskServiceDep,
    project_repo: ProjectRepoDep,
    workspace_repo: WorkspaceRepoDep,
    current_user: CurrentUserDep,
    project_id: Annotated[int, Path(ge=1, description="Project unique ID")],
) -> TaskResponse:
    await ensure_project_role(
        project_repo,
        workspace_repo,
        project_id,
        current_user,
        WRITE_ROLES,
    )
    return await task_service.create_task_in_project(
        project_id,
        payload,
        created_by=current_user.id,
        background_tasks=background_tasks,
    )


@router.get(
    "/{project_id}/labels",
    response_model=list[LabelResponse],
    summary="List labels defined for a project (RBAC: OWNER/EDITOR/VIEWER)",
    responses=RESOURCE_READ_RESPONSES,
)
async def list_project_labels(
    service: ProjectServiceDep,
    project_repo: ProjectRepoDep,
    workspace_repo: WorkspaceRepoDep,
    current_user: CurrentUserDep,
    project_id: Annotated[int, Path(ge=1, description="Project unique ID")],
) -> list[LabelResponse]:
    await ensure_project_role(
        project_repo,
        workspace_repo,
        project_id,
        current_user,
        READ_ROLES,
    )
    return await service.list_labels(project_id)


@router.post(
    "/{project_id}/labels",
    response_model=LabelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a label in a project (RBAC: OWNER/EDITOR)",
    responses=RESOURCE_WRITE_RESPONSES,
)
async def create_project_label(
    payload: LabelCreate,
    service: ProjectServiceDep,
    project_repo: ProjectRepoDep,
    workspace_repo: WorkspaceRepoDep,
    current_user: CurrentUserDep,
    project_id: Annotated[int, Path(ge=1, description="Project unique ID")],
) -> LabelResponse:
    await ensure_project_role(
        project_repo,
        workspace_repo,
        project_id,
        current_user,
        WRITE_ROLES,
    )
    return await service.create_label(project_id, payload)


@router.patch(
    "/{project_id}/labels/{label_id}",
    response_model=LabelResponse,
    summary="Update a label in a project and invalidate task cache (RBAC: OWNER/EDITOR)",
    responses=RESOURCE_WRITE_RESPONSES,
)
async def update_project_label(
    payload: LabelUpdate,
    service: ProjectServiceDep,
    project_repo: ProjectRepoDep,
    workspace_repo: WorkspaceRepoDep,
    current_user: CurrentUserDep,
    project_id: Annotated[int, Path(ge=1, description="Project unique ID")],
    label_id: Annotated[int, Path(ge=1, description="Label unique ID")],
) -> LabelResponse:
    await ensure_project_role(
        project_repo,
        workspace_repo,
        project_id,
        current_user,
        WRITE_ROLES,
    )
    return await service.update_label(project_id, label_id, payload)


@router.delete(
    "/{project_id}/labels/{label_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a label from a project and invalidate task cache (RBAC: OWNER/EDITOR)",
    responses=RESOURCE_READ_RESPONSES,
)
async def delete_project_label(
    service: ProjectServiceDep,
    project_repo: ProjectRepoDep,
    workspace_repo: WorkspaceRepoDep,
    current_user: CurrentUserDep,
    project_id: Annotated[int, Path(ge=1, description="Project unique ID")],
    label_id: Annotated[int, Path(ge=1, description="Label unique ID")],
) -> Response:
    await ensure_project_role(
        project_repo,
        workspace_repo,
        project_id,
        current_user,
        WRITE_ROLES,
    )
    await service.delete_label(project_id, label_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
