from app.core.exceptions import ConflictException, NotFoundException
from app.core.security import hash_password
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserCreate, UserResponse, UserUpdate


class UserService:
    """Business logic layer for managing TaskHub users."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def list_users(
        self,
        *,
        page: int = 1,
        limit: int = 10,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> PaginatedResponse[UserResponse]:
        items, total, pages = await self._repository.list_users(
            page=page,
            limit=limit,
            is_active=is_active,
            search=search,
        )
        return PaginatedResponse[UserResponse](
            items=[UserResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            limit=limit,
            pages=pages,
        )

    async def get_user(self, user_id: int) -> UserResponse:
        user = await self._repository.get_by_id(user_id)
        if user is None:
            raise NotFoundException(f"User with id={user_id} not found")
        return UserResponse.model_validate(user)

    async def create_user(self, payload: UserCreate) -> UserResponse:
        existing = await self._repository.get_by_email(payload.email)
        if existing is not None:
            raise ConflictException(
                f"User with email '{payload.email}' already exists"
            )
        data = payload.model_dump(exclude={"password"})
        data["hashed_password"] = hash_password(payload.password)
        user = await self._repository.create(data)
        return UserResponse.model_validate(user)

    async def update_user(self, user_id: int, payload: UserUpdate) -> UserResponse:
        user = await self._repository.get_by_id(user_id)
        if user is None:
            raise NotFoundException(f"User with id={user_id} not found")
        update_data = payload.model_dump(exclude_unset=True)
        if "email" in update_data and update_data["email"] != user.email:
            conflict = await self._repository.get_by_email(update_data["email"])
            if conflict is not None:
                raise ConflictException(
                    f"User with email '{update_data['email']}' already exists"
                )
        updated = await self._repository.update(user, update_data)
        return UserResponse.model_validate(updated)

    async def delete_user(self, user_id: int) -> None:
        user = await self._repository.get_by_id(user_id)
        if user is None:
            raise NotFoundException(f"User with id={user_id} not found")
        await self._repository.delete(user)
