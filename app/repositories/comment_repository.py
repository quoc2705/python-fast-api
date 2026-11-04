from sqlalchemy import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.repositories.base import BaseRepository


class CommentRepository(BaseRepository[Comment]):
    """Asynchronous repository for Comment model."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Comment, session)

    async def list_by_task(
        self,
        task_id: int,
        *,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[Comment], int, int]:
        filters: list[ColumnElement[bool]] = [Comment.task_id == task_id]
        return await self.get_multi_paginated(page=page, limit=limit, filters=filters)

