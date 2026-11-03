from enum import Enum


class UserRole(str, Enum):
    """Global user role in TaskHub."""

    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class WorkspaceRole(str, Enum):
    """Role of a user inside a specific workspace."""

    OWNER = "OWNER"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"


class ProjectStatus(str, Enum):
    """Lifecycle status of a project."""

    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class TaskStatus(str, Enum):
    """Workflow status of a task."""

    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    DONE = "DONE"


class TaskPriority(str, Enum):
    """Priority level of a task."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

