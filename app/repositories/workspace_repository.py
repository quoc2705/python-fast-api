from sqlalchemy import ColumnElement, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import WorkspaceRole
from app.models.workspace import Workspace, WorkspaceMember
from app.repositories.base import BaseRepository


class WorkspaceRepository(BaseRepository[Workspace]):
    """Asynchronous repository for Workspace and WorkspaceMember models."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Workspace, session)

    async def get_by_id_with_details(self, workspace_id: int) -> Workspace | None:
        stmt = (
            select(Workspace)
            .where(Workspace.id == workspace_id)
            .options(
                selectinload(Workspace.owner),
                selectinload(Workspace.members).selectinload(WorkspaceMember.user),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_workspaces(
        self,
        *,
        page: int = 1,
        limit: int = 10,
        owner_id: int | None = None,
    ) -> tuple[list[Workspace], int, int]:
        filters: list[ColumnElement[bool]] = []
        if owner_id is not None:
            filters.append(Workspace.owner_id == owner_id)
        return await self.get_multi_paginated(page=page, limit=limit, filters=filters)

    async def get_member(
        self,
        workspace_id: int,
        user_id: int,
    ) -> WorkspaceMember | None:
        stmt = (
            select(WorkspaceMember)
            .where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
            .options(selectinload(WorkspaceMember.user))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_or_update_member(
        self,
        workspace_id: int,
        user_id: int,
        role: WorkspaceRole,
    ) -> WorkspaceMember:
        member = await self.get_member(workspace_id, user_id)
        if member is None:
            member = WorkspaceMember(
                workspace_id=workspace_id,
                user_id=user_id,
                role=role,
            )
            self.session.add(member)
        else:
            member.role = role
            self.session.add(member)
        await self.session.commit()
        refreshed = await self.get_member(workspace_id, user_id)
        assert refreshed is not None
        return refreshed

    async def remove_member(self, member: WorkspaceMember) -> None:
        await self.session.delete(member)
        await self.session.commit()
