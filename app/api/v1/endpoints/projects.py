from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.deps import PaginationParams, get_project_service
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.project import (
    ProjectCreate,
    ProjectDetailResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])

ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
PaginationDep = Annotated[PaginationParams, Depends()]


@router.get(
    "",
    response_model=PaginatedResponse[ProjectResponse],
    summary="List projects with pagination and filtering",
)
async def list_projects(
    service: ProjectServiceDep,
    pagination: PaginationDep,
    owner_id: Annotated[
        int | None,
        Query(ge=1, description="Filter projects by owner user ID"),
    ] = None,
    search: Annotated[
        str | None,
        Query(max_length=100, description="Search by project name or description"),
    ] = None,
) -> PaginatedResponse[ProjectResponse]:
    return await service.list_projects(
        page=pagination.page,
        size=pagination.size,
        owner_id=owner_id,
        search=search,
    )


@router.get(
    "/{project_id}",
    response_model=ProjectDetailResponse,
    summary="Get a project with its owner and tasks by ID",
)
async def get_project(
    service: ProjectServiceDep,
    project_id: Annotated[int, Path(ge=1, description="Project unique ID")],
) -> ProjectDetailResponse:
    return await service.get_project(project_id)


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
)
async def create_project(
    payload: ProjectCreate,
    service: ProjectServiceDep,
) -> ProjectResponse:
    return await service.create_project(payload)


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

