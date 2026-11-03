from fastapi import HTTPException, status

from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.project import (
    ProjectCreate,
    ProjectDetailResponse,
    ProjectResponse,
    ProjectUpdate,
)


class ProjectService:
    """Business logic layer for managing projects and their owner relationships."""

    def __init__(
        self,
        project_repo: ProjectRepository,
        user_repo: UserRepository,
    ) -> None:
        self._project_repo = project_repo
        self._user_repo = user_repo

    async def list_projects(
        self,
        *,
        page: int = 1,
        size: int = 10,
        owner_id: int | None = None,
        search: str | None = None,
    ) -> PaginatedResponse[ProjectResponse]:
        items, total, pages = await self._project_repo.list_projects(
            page=page,
            size=size,
            owner_id=owner_id,
            search=search,
        )
        return PaginatedResponse[ProjectResponse](
            items=[ProjectResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def get_project(self, project_id: int) -> ProjectDetailResponse:
        project = await self._project_repo.get_by_id_with_details(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id={project_id} not found",
            )
        return ProjectDetailResponse.model_validate(project)

    async def create_project(self, payload: ProjectCreate) -> ProjectResponse:
        owner = await self._user_repo.get_by_id(payload.owner_id)
        if owner is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Owner User with id={payload.owner_id} not found",
            )
        project = await self._project_repo.create(payload.model_dump())
        return ProjectResponse.model_validate(project)

    async def update_project(
        self,
        project_id: int,
        payload: ProjectUpdate,
    ) -> ProjectResponse:
        project = await self._project_repo.get_by_id(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id={project_id} not found",
            )
        update_data = payload.model_dump(exclude_unset=True)
        if "owner_id" in update_data and update_data["owner_id"] is not None:
            owner = await self._user_repo.get_by_id(update_data["owner_id"])
            if owner is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Owner User with id={update_data['owner_id']} not found",
                )
        updated = await self._project_repo.update(project, update_data)
        return ProjectResponse.model_validate(updated)

    async def delete_project(self, project_id: int) -> None:
        project = await self._project_repo.get_by_id(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id={project_id} not found",
            )
        await self._project_repo.delete(project)

