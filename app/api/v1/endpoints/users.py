from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.deps import PaginationParams, get_user_service
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])

UserServiceDep = Annotated[UserService, Depends(get_user_service)]
PaginationDep = Annotated[PaginationParams, Depends()]


@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    summary="List users with pagination and filtering",
)
async def list_users(
    service: UserServiceDep,
    pagination: PaginationDep,
    is_active: Annotated[
        bool | None,
        Query(description="Filter by active status"),
    ] = None,
    search: Annotated[
        str | None,
        Query(max_length=100, description="Search by email or full name"),
    ] = None,
) -> PaginatedResponse[UserResponse]:
    return await service.list_users(
        page=pagination.page,
        size=pagination.size,
        is_active=is_active,
        search=search,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get a user by ID",
)
async def get_user(
    service: UserServiceDep,
    user_id: Annotated[int, Path(ge=1, description="User unique ID")],
) -> UserResponse:
    return await service.get_user(user_id)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
)
async def create_user(
    payload: UserCreate,
    service: UserServiceDep,
) -> UserResponse:
    return await service.create_user(payload)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update a user by ID",
)
async def update_user(
    payload: UserUpdate,
    service: UserServiceDep,
    user_id: Annotated[int, Path(ge=1, description="User unique ID")],
) -> UserResponse:
    return await service.update_user(user_id, payload)


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="Delete a user by ID",
)
async def delete_user(
    service: UserServiceDep,
    user_id: Annotated[int, Path(ge=1, description="User unique ID")],
) -> MessageResponse:
    await service.delete_user(user_id)
    return MessageResponse(message=f"User {user_id} deleted successfully")

