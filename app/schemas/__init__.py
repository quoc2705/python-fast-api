"""TaskHub Pydantic v2 Schemas package."""
from app.models.enums import (
    ProjectStatus,
    TaskPriority,
    TaskStatus,
    UserRole,
    WorkspaceRole,
)
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.comment import CommentCreate, CommentResponse
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.error import COMMON_ERROR_RESPONSES, ErrorResponse
from app.schemas.label import LabelCreate, LabelResponse, LabelUpdate
from app.schemas.project import (
    ProjectCreate,
    ProjectDetailResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.schemas.task import (
    TaskCreate,
    TaskDetailResponse,
    TaskResponse,
    TaskUpdate,
)
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceDetailResponse,
    WorkspaceMemberAdd,
    WorkspaceMemberResponse,
    WorkspaceMemberRoleUpdate,
    WorkspaceResponse,
    WorkspaceUpdate,
)

__all__ = [
    "COMMON_ERROR_RESPONSES",
    "ChangePasswordRequest",
    "CommentCreate",
    "CommentResponse",
    "ErrorResponse",
    "LabelCreate",
    "LabelResponse",
    "LabelUpdate",
    "LoginRequest",
    "LogoutRequest",
    "MessageResponse",
    "PaginatedResponse",
    "ProjectCreate",
    "ProjectDetailResponse",
    "ProjectResponse",
    "ProjectStatus",
    "ProjectUpdate",
    "RefreshTokenRequest",
    "RegisterRequest",
    "TaskCreate",
    "TaskDetailResponse",
    "TaskPriority",
    "TaskResponse",
    "TaskStatus",
    "TaskUpdate",
    "TokenResponse",
    "UserCreate",
    "UserResponse",
    "UserRole",
    "UserUpdate",
    "WorkspaceCreate",
    "WorkspaceDetailResponse",
    "WorkspaceMemberAdd",
    "WorkspaceMemberResponse",
    "WorkspaceMemberRoleUpdate",
    "WorkspaceResponse",
    "WorkspaceRole",
    "WorkspaceUpdate",
]
