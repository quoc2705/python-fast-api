import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.core.config import Settings
from tests.test_taskhub_api import _auth_header, _promote_to_admin, _register_user


def test_session6_settings_fail_fast_validation() -> None:
    """Session 6 test: verify pydantic-settings rejects short SECRET_KEY and wildcard CORS."""
    with pytest.raises(ValidationError):
        Settings(SECRET_KEY="too-short")

    with pytest.raises(ValidationError):
        Settings(
            SECRET_KEY="a" * 36,
            CORS_ORIGINS=["*"],
        )


async def test_session6_background_notification_outbox(client: AsyncClient) -> None:
    """Session 6 test: verify assigning a task triggers background email notification in outbox."""
    reg = await _register_user(client, "s6_notify@taskhub.io", "S6 Assignee")
    token = str(reg["access_token"])
    user_id = int(reg["user"]["id"])  # type: ignore[index]

    ws = (
        await client.post(
            "/api/v1/workspaces",
            headers=_auth_header(token),
            json={"name": "S6 Notification WS"},
        )
    ).json()
    proj = (
        await client.post(
            f"/api/v1/workspaces/{ws['id']}/projects",
            headers=_auth_header(token),
            json={"name": "S6 Notification Project"},
        )
    ).json()

    task_res = await client.post(
        f"/api/v1/projects/{proj['id']}/tasks",
        headers=_auth_header(token),
        json={
            "title": "Notify Assignee via BackgroundTasks",
            "assignee_id": user_id,
        },
    )
    assert task_res.status_code == 201

    # Non-admin cannot read notification outbox (403)
    forbidden_outbox = await client.get(
        "/api/v1/tasks/notifications/outbox",
        headers=_auth_header(token),
    )
    assert forbidden_outbox.status_code == 403

    await _promote_to_admin(user_id)
    outbox_res = await client.get(
        "/api/v1/tasks/notifications/outbox",
        headers=_auth_header(token),
    )
    assert outbox_res.status_code == 200
    items = outbox_res.json()
    assert len(items) == 1
    assert items[0]["to"] == "s6_notify@taskhub.io"
