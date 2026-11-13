from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_auth_service
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.common import MessageResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account and issue JWT access + refresh tokens",
    responses={
        409: {"description": "Email is already registered"},
    },
)
async def register(
    payload: RegisterRequest,
    service: AuthServiceDep,
) -> TokenResponse:
    return await service.register(payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user credentials and return JWT access + refresh tokens",
    responses={
        401: {"description": "Invalid email or password"},
        403: {"description": "User account is deactivated"},
    },
)
async def login(
    payload: LoginRequest,
    service: AuthServiceDep,
) -> TokenResponse:
    return await service.login(payload)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate refresh token and issue a new JWT access + refresh token pair",
    responses={
        401: {"description": "Invalid, expired, or revoked refresh token"},
    },
)
async def refresh_token(
    payload: RefreshTokenRequest,
    service: AuthServiceDep,
) -> TokenResponse:
    return await service.refresh(payload.refresh_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Revoke a refresh token to log out the user",
    responses={
        401: {"description": "Invalid refresh token"},
    },
)
async def logout(
    payload: LogoutRequest,
    service: AuthServiceDep,
) -> MessageResponse:
    await service.logout(payload.refresh_token)
    return MessageResponse(message="Logged out and refresh token revoked successfully")

