from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_jwt_token,
    hash_password,
    is_token_revoked,
    revoke_token,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse


class AuthService:
    """Business logic layer for authentication, JWT issuance, and token revocation."""

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    def _issue_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token(user.id, role=user.role.value)
        refresh_token = create_refresh_token(user.id, role=user.role.value)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

    async def register(self, payload: RegisterRequest) -> TokenResponse:
        existing = await self._user_repo.get_by_email(payload.email)
        if existing is not None:
            raise ConflictException(
                f"User with email '{payload.email}' already exists"
            )
        user = await self._user_repo.create(
            {
                "email": payload.email,
                "full_name": payload.full_name,
                "hashed_password": hash_password(payload.password),
                "role": payload.role,
                "is_active": True,
            }
        )
        return self._issue_tokens(user)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        user = await self._user_repo.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise UnauthorizedException("Incorrect email or password")
        if not user.is_active:
            raise ForbiddenException("User account is deactivated")
        return self._issue_tokens(user)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        claims = decode_jwt_token(refresh_token, expected_type="refresh")
        jti = str(claims.get("jti", ""))
        exp = int(claims.get("exp", 0))
        if jti and await is_token_revoked(jti):
            raise UnauthorizedException("Refresh token has been revoked")

        user_id = int(claims["sub"])
        user = await self._user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise UnauthorizedException("User account not found or inactive")

        if jti:
            await revoke_token(jti, exp)
        return self._issue_tokens(user)

    async def logout(self, refresh_token: str) -> None:
        claims = decode_jwt_token(refresh_token, expected_type="refresh")
        jti = str(claims.get("jti", ""))
        exp = int(claims.get("exp", 0))
        if jti:
            await revoke_token(jti, exp)

    async def change_password(
        self,
        user: User,
        payload: ChangePasswordRequest,
    ) -> UserResponse:
        if not verify_password(payload.current_password, user.hashed_password):
            raise BadRequestException("Current password is incorrect")
        updated = await self._user_repo.update(
            user,
            {"hashed_password": hash_password(payload.new_password)},
        )
        return UserResponse.model_validate(updated)

    async def get_active_user_by_id(self, user_id: int) -> User:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundException(f"User with id={user_id} not found")
        if not user.is_active:
            raise ForbiddenException("User account is inactive")
        return user

