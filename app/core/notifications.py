from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger

logger = get_logger("app.notifications")

# In-memory notification log for inspection / testing via API & logs
notification_outbox: list[dict[str, Any]] = []


def send_task_assigned_email_notification(
    *,
    assignee_email: str,
    assignee_name: str,
    task_id: int,
    task_title: str,
    project_id: int,
) -> None:
    """Background task simulating sending an email notification when a task is assigned."""
    record = {
        "to": assignee_email,
        "recipient_name": assignee_name,
        "subject": f"[TaskHub] You have been assigned to Task #{task_id}: {task_title}",
        "body": (
            f"Hi {assignee_name},\n\n"
            f"You have been assigned to task '{task_title}' (ID #{task_id}) "
            f"in Project #{project_id}.\n\n"
            "Best regards,\nTaskHub Notification Service"
        ),
        "task_id": task_id,
        "project_id": project_id,
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }
    notification_outbox.append(record)
    logger.info(
        "Background email notification sent to %s for Task #%s (%s)",
        assignee_email,
        task_id,
        task_title,
    )

