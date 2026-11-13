from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_jwt_token, is_token_revoked
from app.db.session import get_db_session
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.comment_repository import CommentRepository
from app.repositories.label_repository import LabelRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.services.auth_service import AuthService
from app.services.project_service import ProjectService
from app.services.task_service import TaskService
from app.services.user_service import UserService
from app.services.workspace_service import WorkspaceService

DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]

bearer_scheme = HTTPBearer(
    scheme_name="BearerAuth",
    description="Enter JWT Access Token obtained from /api/v1/auth/login or /api/v1/auth/register",
    auto_error=False,
)


@dataclass(frozen=True)
class PaginationParams:
    """Reusable pagination query parameters dependency (page + limit)."""

    page: int = Query(default=1, ge=1, description="Page number (1-indexed)")
    limit: int = Query(default=10, ge=1, le=100, description="Items per page (max 100)")


def get_user_repository(session: DBSessionDep) -> UserRepository:
    return UserRepository(session=session)


def get_workspace_repository(session: DBSessionDep) -> WorkspaceRepository:
    return WorkspaceRepository(session=session)


def get_project_repository(session: DBSessionDep) -> ProjectRepository:
    return ProjectRepository(session=session)


def get_task_repository(session: DBSessionDep) -> TaskRepository:
    return TaskRepository(session=session)


def get_label_repository(session: DBSessionDep) -> LabelRepository:
    return LabelRepository(session=session)


def get_comment_repository(session: DBSessionDep) -> CommentRepository:
    return CommentRepository(session=session)


def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthService:
    return AuthService(user_repo=user_repo)


def get_user_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(repository=user_repo)


def get_workspace_service(
    workspace_repo: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> WorkspaceService:
    return WorkspaceService(workspace_repo=workspace_repo, user_repo=user_repo)


def get_project_service(
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspace_repo: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    label_repo: Annotated[LabelRepository, Depends(get_label_repository)],
) -> ProjectService:
    return ProjectService(
        project_repo=project_repo,
        workspace_repo=workspace_repo,
        label_repo=label_repo,
    )


def get_task_service(
    task_repo: Annotated[TaskRepository, Depends(get_task_repository)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    label_repo: Annotated[LabelRepository, Depends(get_label_repository)],
    comment_repo: Annotated[CommentRepository, Depends(get_comment_repository)],
) -> TaskService:
    return TaskService(
        task_repo=task_repo,
        project_repo=project_repo,
        user_repo=user_repo,
        label_repo=label_repo,
        comment_repo=comment_repo,
    )


async def get_optional_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User | None:
    """Resolve the authenticated User if a Bearer token is supplied, else None."""
    if credentials is None or not credentials.credentials:
        return None
    claims = decode_jwt_token(credentials.credentials, expected_type="access")
    jti = str(claims.get("jti", ""))
    if jti and await is_token_revoked(jti):
        raise UnauthorizedException("Access token has been revoked")
    user_id = int(claims["sub"])
    return await auth_service.get_active_user_by_id(user_id)


async def get_current_user(
    user: Annotated[User | None, Depends(get_optional_current_user)],
) -> User:
    """Require a valid JWT Bearer access token and return the current active User."""
    if user is None:
        raise UnauthorizedException("Authentication required (missing Bearer token)")
    return user


async def require_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require global ADMIN role."""
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenException("Admin privileges required")
    return current_user
