from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.deps import (
    PaginationParams,
    get_auth_service,
    get_current_user,
    get_user_service,
)
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])

UserServiceDep = Annotated[UserService, Depends(get_user_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
PaginationDep = Annotated[PaginationParams, Depends()]


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get profile of the currently authenticated user",
    responses={401: {"description": "Missing or invalid Bearer token"}},
)
async def get_my_profile(current_user: CurrentUserDep) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update profile of the currently authenticated user",
    responses={401: {"description": "Missing or invalid Bearer token"}},
)
async def update_my_profile(
    payload: UserUpdate,
    current_user: CurrentUserDep,
    service: UserServiceDep,
) -> UserResponse:
    return await service.update_user(current_user.id, payload)


@router.post(
    "/me/change-password",
    response_model=MessageResponse,
    summary="Change password of the currently authenticated user",
    responses={
        400: {"description": "Current password is incorrect"},
        401: {"description": "Missing or invalid Bearer token"},
    },
)
async def change_my_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUserDep,
    auth_service: AuthServiceDep,
) -> MessageResponse:
    await auth_service.change_password(current_user, payload)
    return MessageResponse(message="Password updated successfully")


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
        limit=pagination.limit,
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
