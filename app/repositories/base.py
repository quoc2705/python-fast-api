from collections.abc import Sequence
from math import ceil
from typing import Any, Generic, TypeVar

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic asynchronous repository implementing CRUD and pagination for SQLAlchemy 2.x."""

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, record_id: int) -> ModelType | None:
        """Fetch a single record by its primary key ID."""
        stmt = select(self.model).where(getattr(self.model, "id") == record_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi_paginated(
        self,
        *,
        page: int = 1,
        limit: int = 10,
        filters: Sequence[ColumnElement[bool]] | None = None,
        order_by: Any = None,
    ) -> tuple[list[ModelType], int, int]:
        """Fetch paginated records using (page, limit) and return (items, total, pages)."""
        stmt = select(self.model)
        count_stmt = select(func.count()).select_from(self.model)

        if filters:
            for condition in filters:
                stmt = stmt.where(condition)
                count_stmt = count_stmt.where(condition)

        if order_by is not None:
            stmt = stmt.order_by(order_by)
        elif hasattr(self.model, "id"):
            stmt = stmt.order_by(getattr(self.model, "id").desc())

        total_result = await self.session.execute(count_stmt)
        total = int(total_result.scalar_one() or 0)
        pages = ceil(total / limit) if total > 0 else 0

        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total, pages

    async def create(self, obj_in: dict[str, Any]) -> ModelType:
        """Create and persist a new model instance."""
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: ModelType, obj_in: dict[str, Any]) -> ModelType:
        """Update an existing model instance with partial or full dictionary data."""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, db_obj: ModelType) -> None:
        """Delete an existing model instance."""
        await self.session.delete(db_obj)
        await self.session.commit()
