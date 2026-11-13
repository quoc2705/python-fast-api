from app.core.exceptions import BadRequestException, NotFoundException
from app.models.enums import WorkspaceRole
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.common import PaginatedResponse
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceDetailResponse,
    WorkspaceMemberAdd,
    WorkspaceMemberResponse,
    WorkspaceMemberRoleUpdate,
    WorkspaceResponse,
    WorkspaceUpdate,
)


class WorkspaceService:
    """Business logic layer for managing workspaces and workspace RBAC memberships."""

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
            raise NotFoundException(f"Workspace with id={workspace_id} not found")
        return WorkspaceDetailResponse.model_validate(workspace)

    async def create_workspace(self, payload: WorkspaceCreate) -> WorkspaceResponse:
        owner = await self._user_repo.get_by_id(payload.owner_id)
        if owner is None:
            raise NotFoundException(f"Owner User with id={payload.owner_id} not found")
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
            raise NotFoundException(f"Workspace with id={workspace_id} not found")
        updated = await self._workspace_repo.update(
            workspace,
            payload.model_dump(exclude_unset=True),
        )
        return WorkspaceResponse.model_validate(updated)

    async def delete_workspace(self, workspace_id: int) -> None:
        workspace = await self._workspace_repo.get_by_id(workspace_id)
        if workspace is None:
            raise NotFoundException(f"Workspace with id={workspace_id} not found")
        await self._workspace_repo.delete(workspace)

    async def list_members(self, workspace_id: int) -> list[WorkspaceMemberResponse]:
        workspace = await self._workspace_repo.get_by_id(workspace_id)
        if workspace is None:
            raise NotFoundException(f"Workspace with id={workspace_id} not found")
        members = await self._workspace_repo.list_members(workspace_id)
        return [WorkspaceMemberResponse.model_validate(m) for m in members]

    async def add_member(
        self,
        workspace_id: int,
        payload: WorkspaceMemberAdd,
    ) -> WorkspaceMemberResponse:
        workspace = await self._workspace_repo.get_by_id(workspace_id)
        if workspace is None:
            raise NotFoundException(f"Workspace with id={workspace_id} not found")
        user = await self._user_repo.get_by_id(payload.user_id)
        if user is None:
            raise NotFoundException(f"User with id={payload.user_id} not found")
        member = await self._workspace_repo.add_or_update_member(
            workspace_id=workspace_id,
            user_id=payload.user_id,
            role=payload.role,
        )
        return WorkspaceMemberResponse.model_validate(member)

    async def update_member_role(
        self,
        workspace_id: int,
        user_id: int,
        payload: WorkspaceMemberRoleUpdate,
    ) -> WorkspaceMemberResponse:
        member = await self._workspace_repo.get_member(workspace_id, user_id)
        if member is None:
            raise NotFoundException(
                f"Member user_id={user_id} not found in workspace {workspace_id}"
            )
        updated = await self._workspace_repo.add_or_update_member(
            workspace_id=workspace_id,
            user_id=user_id,
            role=payload.role,
        )
        return WorkspaceMemberResponse.model_validate(updated)

    async def remove_member(self, workspace_id: int, user_id: int) -> None:
        workspace = await self._workspace_repo.get_by_id(workspace_id)
        if workspace is not None and workspace.owner_id == user_id:
            raise BadRequestException("Cannot remove the primary owner of the workspace")
        member = await self._workspace_repo.get_member(workspace_id, user_id)
        if member is None:
            raise NotFoundException(
                f"Member user_id={user_id} not found in workspace {workspace_id}"
            )
        await self._workspace_repo.remove_member(member)
