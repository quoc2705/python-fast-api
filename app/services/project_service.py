from fastapi import HTTPException, status

from app.models.enums import ProjectStatus
from app.repositories.label_repository import LabelRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.common import PaginatedResponse
from app.schemas.label import LabelCreate, LabelResponse, LabelUpdate
from app.schemas.project import (
    ProjectCreate,
    ProjectDetailResponse,
    ProjectResponse,
    ProjectUpdate,
)


class ProjectService:
    """Business logic layer for managing projects and project labels."""

    def __init__(
        self,
        project_repo: ProjectRepository,
        workspace_repo: WorkspaceRepository,
        label_repo: LabelRepository,
    ) -> None:
        self._project_repo = project_repo
        self._workspace_repo = workspace_repo
        self._label_repo = label_repo

    async def list_projects(
        self,
        *,
        page: int = 1,
        limit: int = 10,
        workspace_id: int | None = None,
        status_filter: ProjectStatus | None = None,
        search: str | None = None,
    ) -> PaginatedResponse[ProjectResponse]:
        items, total, pages = await self._project_repo.list_projects(
            page=page,
            limit=limit,
            workspace_id=workspace_id,
            status=status_filter,
            search=search,
        )
        return PaginatedResponse[ProjectResponse](
            items=[ProjectResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            limit=limit,
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

    async def create_project(
        self,
        workspace_id: int,
        payload: ProjectCreate,
    ) -> ProjectResponse:
        workspace = await self._workspace_repo.get_by_id(workspace_id)
        if workspace is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace with id={workspace_id} not found",
            )
        data = payload.model_dump()
        data["workspace_id"] = workspace_id
        project = await self._project_repo.create(data)
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
        updated = await self._project_repo.update(
            project,
            payload.model_dump(exclude_unset=True),
        )
        return ProjectResponse.model_validate(updated)

    async def archive_project(self, project_id: int) -> ProjectResponse:
        project = await self._project_repo.get_by_id(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id={project_id} not found",
            )
        updated = await self._project_repo.update(
            project,
            {"status": ProjectStatus.ARCHIVED},
        )
        return ProjectResponse.model_validate(updated)

    async def delete_project(self, project_id: int) -> None:
        project = await self._project_repo.get_by_id(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id={project_id} not found",
            )
        await self._project_repo.delete(project)

    async def create_label(
        self,
        project_id: int,
        payload: LabelCreate,
    ) -> LabelResponse:
        project = await self._project_repo.get_by_id(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id={project_id} not found",
            )
        data = payload.model_dump()
        data["project_id"] = project_id
        label = await self._label_repo.create(data)
        return LabelResponse.model_validate(label)

    async def list_labels(self, project_id: int) -> list[LabelResponse]:
        items, _, _ = await self._label_repo.list_by_project(project_id)
        return [LabelResponse.model_validate(item) for item in items]

    async def update_label(
        self,
        label_id: int,
        payload: LabelUpdate,
    ) -> LabelResponse:
        label = await self._label_repo.get_by_id(label_id)
        if label is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Label with id={label_id} not found",
            )
        updated = await self._label_repo.update(
            label,
            payload.model_dump(exclude_unset=True),
        )
        return LabelResponse.model_validate(updated)

    async def delete_label(self, label_id: int) -> None:
        label = await self._label_repo.get_by_id(label_id)
        if label is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Label with id={label_id} not found",
            )
        await self._label_repo.delete(label)
