from enum import StrEnum


class UserRole(StrEnum):
    """Global user role in TaskHub."""

    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class WorkspaceRole(StrEnum):
    """Role of a user inside a specific workspace."""

    OWNER = "OWNER"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"


class ProjectStatus(StrEnum):
    """Lifecycle status of a project."""

    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class TaskStatus(StrEnum):
    """Workflow status of a task."""

    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    DONE = "DONE"


class TaskPriority(StrEnum):
    """Priority level of a task."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"
