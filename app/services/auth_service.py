from datetime import UTC, datetime

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    UnauthorizedException,
)
from app.core.security import (
    consume_token_atomically,
    create_access_token,
    create_refresh_token,
    decode_jwt_token,
    get_user_password_changed_at,
    hash_password_async,
    increment_user_token_version,
    revoke_token,
    verify_password_async,
)
from app.models.enums import UserRole
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
    """Business logic layer for authentication, JWT issuance, and atomic token revocation."""

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
        hashed_pw = await hash_password_async(payload.password)
        user = await self._user_repo.create(
            {
                "email": payload.email,
                "full_name": payload.full_name,
                "hashed_password": hashed_pw,
                "role": UserRole.MEMBER,
                "is_active": True,
            }
        )
        return self._issue_tokens(user)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        user = await self._user_repo.get_by_email(payload.email)
        if user is None or not await verify_password_async(
            payload.password,
            user.hashed_password,
        ):
            raise UnauthorizedException("Incorrect email or password")
        if not user.is_active:
            raise ForbiddenException("User account is deactivated")
        return self._issue_tokens(user)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        claims = decode_jwt_token(refresh_token, expected_type="refresh")
        jti = str(claims.get("jti", ""))
        exp = int(claims.get("exp", 0))
        iat = int(claims.get("iat", 0))
        if not jti:
            raise UnauthorizedException("Malformed refresh token (missing jti)")

        try:
            user_id = int(claims["sub"])
        except (KeyError, ValueError, TypeError) as exc:
            raise UnauthorizedException("Invalid token subject") from exc

        pw_changed_at = await get_user_password_changed_at(user_id)
        if pw_changed_at is not None and iat < pw_changed_at:
            raise UnauthorizedException(
                "Refresh token invalidated due to password change"
            )

        consumed = await consume_token_atomically(jti, exp)
        if not consumed:
            raise UnauthorizedException("Refresh token has already been used or revoked")

        user = await self._user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise UnauthorizedException("User account not found or inactive")

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
        current_token_jti: str | None = None,
        current_token_exp: int | None = None,
    ) -> UserResponse:
        if not await verify_password_async(
            payload.current_password,
            user.hashed_password,
        ):
            raise BadRequestException("Current password is incorrect")
        new_hashed = await hash_password_async(payload.new_password)
        updated = await self._user_repo.update(
            user,
            {"hashed_password": new_hashed},
        )
        await increment_user_token_version(user.id)
        if current_token_jti:
            exp_ts = current_token_exp or (
                int(datetime.now(UTC).timestamp()) + 1800
            )
            await revoke_token(current_token_jti, exp_ts)
        return UserResponse.model_validate(updated)

    async def get_active_user_by_id(self, user_id: int) -> User:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise UnauthorizedException("Authenticated user no longer exists")
        if not user.is_active:
            raise ForbiddenException("User account is inactive")
        return user
