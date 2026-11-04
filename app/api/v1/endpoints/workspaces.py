from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.deps import (
    PaginationParams,
    get_project_service,
    get_workspace_service,
)
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.project import ProjectCreate, ProjectResponse
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceDetailResponse,
    WorkspaceMemberAdd,
    WorkspaceMemberResponse,
    WorkspaceResponse,
    WorkspaceUpdate,
)
from app.services.project_service import ProjectService
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

WorkspaceServiceDep = Annotated[WorkspaceService, Depends(get_workspace_service)]
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
PaginationDep = Annotated[PaginationParams, Depends()]


@router.get(
    "",
    response_model=PaginatedResponse[WorkspaceResponse],
    summary="List workspaces with pagination",
)
async def list_workspaces(
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
    summary="Create a new workspace",
)
async def create_workspace(
    payload: WorkspaceCreate,
    service: WorkspaceServiceDep,
) -> WorkspaceResponse:
    return await service.create_workspace(payload)


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceDetailResponse,
    summary="Get workspace details including owner and members",
)
async def get_workspace(
    service: WorkspaceServiceDep,
    workspace_id: Annotated[int, Path(ge=1, description="Workspace ID")],
) -> WorkspaceDetailResponse:
    return await service.get_workspace(workspace_id)


@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Update a workspace by ID",
)
async def update_workspace(
    payload: WorkspaceUpdate,
    service: WorkspaceServiceDep,
    workspace_id: Annotated[int, Path(ge=1, description="Workspace ID")],
) -> WorkspaceResponse:
    return await service.update_workspace(workspace_id, payload)


@router.delete(
    "/{workspace_id}",
    response_model=MessageResponse,
    summary="Delete a workspace by ID",
)
async def delete_workspace(
    service: WorkspaceServiceDep,
    workspace_id: Annotated[int, Path(ge=1, description="Workspace ID")],
) -> MessageResponse:
    await service.delete_workspace(workspace_id)
    return MessageResponse(message=f"Workspace {workspace_id} deleted successfully")


@router.post(
    "/{workspace_id}/members",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite or update a member in a workspace",
)
async def add_workspace_member(
    payload: WorkspaceMemberAdd,
    service: WorkspaceServiceDep,
    workspace_id: Annotated[int, Path(ge=1, description="Workspace ID")],
) -> WorkspaceMemberResponse:
    return await service.add_member(workspace_id, payload)


@router.delete(
    "/{workspace_id}/members/{user_id}",
    response_model=MessageResponse,
    summary="Remove a member from a workspace",
)
async def remove_workspace_member(
    service: WorkspaceServiceDep,
    workspace_id: Annotated[int, Path(ge=1, description="Workspace ID")],
    user_id: Annotated[int, Path(ge=1, description="User ID to remove")],
) -> MessageResponse:
    await service.remove_member(workspace_id, user_id)
    return MessageResponse(
        message=f"User {user_id} removed from workspace {workspace_id}"
    )


@router.post(
    "/{workspace_id}/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project inside a workspace",
)
async def create_workspace_project(
    payload: ProjectCreate,
    project_service: ProjectServiceDep,
    workspace_id: Annotated[int, Path(ge=1, description="Workspace ID")],
) -> ProjectResponse:
    return await project_service.create_project(workspace_id, payload)

