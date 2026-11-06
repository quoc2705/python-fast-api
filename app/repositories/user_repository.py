from sqlalchemy import ColumnElement, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Asynchronous repository for User model."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower().strip())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_users(
        self,
        *,
        page: int = 1,
        limit: int = 10,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[User], int, int]:
        filters: list[ColumnElement[bool]] = []
        if is_active is not None:
            filters.append(User.is_active == is_active)
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    User.email.ilike(pattern),
                    User.full_name.ilike(pattern),
                )
            )
        return await self.get_multi_paginated(page=page, limit=limit, filters=filters)
