from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.api.deps import (
    PaginationParams,
    get_current_user,
    get_project_service,
    get_workspace_repository,
    get_workspace_service,
)
from app.core.permissions import (
    OWNER_ONLY_ROLES,
    READ_ROLES,
    WRITE_ROLES,
    ensure_workspace_role,
)
from app.models.user import User
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.common import PaginatedResponse
from app.schemas.error import (
    AUTH_ERROR_RESPONSES,
    RESOURCE_READ_RESPONSES,
    RESOURCE_WRITE_RESPONSES,
)
from app.schemas.project import ProjectCreate, ProjectResponse
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceDetailResponse,
    WorkspaceMemberAdd,
    WorkspaceMemberResponse,
    WorkspaceMemberRoleUpdate,
    WorkspaceResponse,
    WorkspaceUpdate,
)
from app.services.project_service import ProjectService
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

WorkspaceServiceDep = Annotated[WorkspaceService, Depends(get_workspace_service)]
WorkspaceRepoDep = Annotated[WorkspaceRepository, Depends(get_workspace_repository)]
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
PaginationDep = Annotated[PaginationParams, Depends()]


@router.get(
    "",
    response_model=PaginatedResponse[WorkspaceResponse],
    summary="List workspaces with pagination",
    responses=AUTH_ERROR_RESPONSES,
)
async def list_workspaces(
    _current_user: CurrentUserDep,
    service: WorkspaceServiceDep,
    pagination: PaginationDep,
    owner_id: Annotated[
        int | None,
        Query(ge=1, description="Filter by owner user ID"),
    ] = None,
) -> PaginatedResponse[WorkspaceResponse]:
    return await service.list_workspaces(
        page=pagination.page,
        limit=pagination.limit,
        owner_id=owner_id,
    )


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new workspace owned by the current authenticated user",
    responses=AUTH_ERROR_RESPONSES,
)
async def create_workspace(
    payload: WorkspaceCreate,
    current_user: CurrentUserDep,
    service: WorkspaceServiceDep,
) -> WorkspaceResponse:
    return await service.create_workspace(current_user.id, payload)


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceDetailResponse,
    summary="Get workspace details including owner and members (RBAC: OWNER/EDITOR/VIEWER)",
    responses=RESOURCE_READ_RESPONSES,
)
async def get_workspace(
    service: WorkspaceServiceDep,
    workspace_repo: WorkspaceRepoDep,
    current_user: CurrentUserDep,
    workspace_id: Annotated[int, Path(ge=1, description="Workspace ID")],
) -> WorkspaceDetailResponse:
    await ensure_workspace_role(
        workspace_repo,
        workspace_id,
        current_user,
        READ_ROLES,
    )
    return await service.get_workspace(workspace_id)


@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Update a workspace by ID (RBAC: OWNER only)",
    responses=RESOURCE_WRITE_RESPONSES,
)
async def update_workspace(
    payload: WorkspaceUpdate,
    service: WorkspaceServiceDep,
    workspace_repo: WorkspaceRepoDep,
    current_user: CurrentUserDep,
    workspace_id: Annotated[int, Path(ge=1, description="Workspace ID")],
) -> WorkspaceResponse:
    await ensure_workspace_role(
        workspace_repo,
        workspace_id,
        current_user,
        OWNER_ONLY_ROLES,
    )
    return await service.update_workspace(workspace_id, payload)


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a workspace by ID (RBAC: OWNER only)",
    responses=RESOURCE_READ_RESPONSES,
)
async def delete_workspace(
    service: WorkspaceServiceDep,
    workspace_repo: WorkspaceRepoDep,
    current_user: CurrentUserDep,
    workspace_id: Annotated[int, Path(ge=1, description="Workspace ID")],
) -> Response:
    await ensure_workspace_role(
        workspace_repo,
        workspace_id,
        current_user,
        OWNER_ONLY_ROLES,
    )
    await service.delete_workspace(workspace_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{workspace_id}/members",
    response_model=list[WorkspaceMemberResponse],
    summary="List all members and roles in a workspace (RBAC: OWNER/EDITOR/VIEWER)",
    responses=RESOURCE_READ_RESPONSES,
)
async def list_workspace_members(
    service: WorkspaceServiceDep,
    workspace_repo: WorkspaceRepoDep,
    current_user: CurrentUserDep,
    workspace_id: Annotated[int, Path(ge=1, description="Workspace ID")],
) -> list[WorkspaceMemberResponse]:
    await ensure_workspace_role(
        workspace_repo,
        workspace_id,
        current_user,
        READ_ROLES,
    )
    return await service.list_members(workspace_id)


@router.post(
    "/{workspace_id}/members",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite or update a member in a workspace (RBAC: OWNER only)",
    responses=RESOURCE_WRITE_RESPONSES,
)
async def add_workspace_member(
    payload: WorkspaceMemberAdd,
    service: WorkspaceServiceDep,
    workspace_repo: WorkspaceRepoDep,
    current_user: CurrentUserDep,
    workspace_id: Annotated[int, Path(ge=1, description="Workspace ID")],
) -> WorkspaceMemberResponse:
    await ensure_workspace_role(
        workspace_repo,
        workspace_id,
        current_user,
        OWNER_ONLY_ROLES,
    )
    return await service.add_member(workspace_id, payload)


@router.patch(
    "/{workspace_id}/members/{user_id}",
    response_model=WorkspaceMemberResponse,
    summary="Change a workspace member's role (RBAC: OWNER only)",
    responses=RESOURCE_WRITE_RESPONSES,
)
async def update_workspace_member_role(
    payload: WorkspaceMemberRoleUpdate,
    service: WorkspaceServiceDep,
    workspace_repo: WorkspaceRepoDep,
    current_user: CurrentUserDep,
    workspace_id: Annotated[int, Path(ge=1, description="Workspace ID")],
    user_id: Annotated[int, Path(ge=1, description="User ID to update role")],
) -> WorkspaceMemberResponse:
    await ensure_workspace_role(
        workspace_repo,
        workspace_id,
        current_user,
        OWNER_ONLY_ROLES,
    )
    return await service.update_member_role(workspace_id, user_id, payload)


@router.delete(
    "/{workspace_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member from a workspace (RBAC: OWNER only)",
    responses=RESOURCE_WRITE_RESPONSES,
)
async def remove_workspace_member(
    service: WorkspaceServiceDep,
    workspace_repo: WorkspaceRepoDep,
    current_user: CurrentUserDep,
    workspace_id: Annotated[int, Path(ge=1, description="Workspace ID")],
    user_id: Annotated[int, Path(ge=1, description="User ID to remove")],
) -> Response:
    await ensure_workspace_role(
        workspace_repo,
        workspace_id,
        current_user,
        OWNER_ONLY_ROLES,
    )
    await service.remove_member(workspace_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{workspace_id}/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project inside a workspace (RBAC: OWNER/EDITOR)",
    responses=RESOURCE_WRITE_RESPONSES,
)
async def create_workspace_project(
    payload: ProjectCreate,
    project_service: ProjectServiceDep,
    workspace_repo: WorkspaceRepoDep,
    current_user: CurrentUserDep,
    workspace_id: Annotated[int, Path(ge=1, description="Workspace ID")],
) -> ProjectResponse:
    await ensure_workspace_role(
        workspace_repo,
        workspace_id,
        current_user,
        WRITE_ROLES,
    )
    return await project_service.create_project(workspace_id, payload)
