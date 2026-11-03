from fastapi import HTTPException, status

from app.models.enums import WorkspaceRole
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.common import PaginatedResponse
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceDetailResponse,
    WorkspaceMemberAdd,
    WorkspaceMemberResponse,
    WorkspaceResponse,
    WorkspaceUpdate,
)


class WorkspaceService:
    """Business logic layer for managing workspaces and workspace memberships."""

    def __init__(
        self,
        workspace_repo: WorkspaceRepository,
        user_repo: UserRepository,
    ) -> None:
        self._workspace_repo = workspace_repo
        self._user_repo = user_repo

    async def list_workspaces(
        self,
        *,
        page: int = 1,
        limit: int = 10,
        owner_id: int | None = None,
    ) -> PaginatedResponse[WorkspaceResponse]:
        items, total, pages = await self._workspace_repo.list_workspaces(
            page=page,
            limit=limit,
            owner_id=owner_id,
        )
        return PaginatedResponse[WorkspaceResponse](
            items=[WorkspaceResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            limit=limit,
            pages=pages,
        )

    async def get_workspace(self, workspace_id: int) -> WorkspaceDetailResponse:
        workspace = await self._workspace_repo.get_by_id_with_details(workspace_id)
        if workspace is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace with id={workspace_id} not found",
            )
        return WorkspaceDetailResponse.model_validate(workspace)

    async def create_workspace(self, payload: WorkspaceCreate) -> WorkspaceResponse:
        owner = await self._user_repo.get_by_id(payload.owner_id)
        if owner is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Owner User with id={payload.owner_id} not found",
            )
        workspace = await self._workspace_repo.create(payload.model_dump())
        await self._workspace_repo.add_or_update_member(
            workspace_id=workspace.id,
            user_id=payload.owner_id,
            role=WorkspaceRole.OWNER,
        )
        return WorkspaceResponse.model_validate(workspace)

    async def update_workspace(
        self,
        workspace_id: int,
        payload: WorkspaceUpdate,
    ) -> WorkspaceResponse:
        workspace = await self._workspace_repo.get_by_id(workspace_id)
        if workspace is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace with id={workspace_id} not found",
            )
        updated = await self._workspace_repo.update(
            workspace,
            payload.model_dump(exclude_unset=True),
        )
        return WorkspaceResponse.model_validate(updated)

    async def delete_workspace(self, workspace_id: int) -> None:
        workspace = await self._workspace_repo.get_by_id(workspace_id)
        if workspace is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace with id={workspace_id} not found",
            )
        await self._workspace_repo.delete(workspace)

    async def add_member(
        self,
        workspace_id: int,
        payload: WorkspaceMemberAdd,
    ) -> WorkspaceMemberResponse:
        workspace = await self._workspace_repo.get_by_id(workspace_id)
        if workspace is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace with id={workspace_id} not found",
            )
        user = await self._user_repo.get_by_id(payload.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id={payload.user_id} not found",
            )
        member = await self._workspace_repo.add_or_update_member(
            workspace_id=workspace_id,
            user_id=payload.user_id,
            role=payload.role,
        )
        return WorkspaceMemberResponse.model_validate(member)

    async def remove_member(self, workspace_id: int, user_id: int) -> None:
        member = await self._workspace_repo.get_member(workspace_id, user_id)
        if member is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Member user_id={user_id} not found in workspace {workspace_id}",
            )
        await self._workspace_repo.remove_member(member)
