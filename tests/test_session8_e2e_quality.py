from httpx import AsyncClient

from tests.test_taskhub_api import _auth_header, _register_user


async def test_session8_full_taskhub_lifecycle_e2e(client: AsyncClient) -> None:
    """Session 8 E2E test: complete user -> workspace -> project -> label -> task -> comment -> archive flow."""
    reg = await _register_user(client, "s8_lead@taskhub.io", "S8 Tech Lead")
    token = str(reg["access_token"])
    user_id = int(reg["user"]["id"])  # type: ignore[index]

    health = await client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    ws = (
        await client.post(
            "/api/v1/workspaces",
            headers=_auth_header(token),
            json={"name": "S8 Production Workspace"},
        )
    ).json()
    proj = (
        await client.post(
            f"/api/v1/workspaces/{ws['id']}/projects",
            headers=_auth_header(token),
            json={"name": "S8 Release 1.0", "description": "Final E2E verification"},
        )
    ).json()
    proj_id = proj["id"]

    label = (
        await client.post(
            f"/api/v1/projects/{proj_id}/labels",
            headers=_auth_header(token),
            json={"name": "release-ready", "color": "#10B981"},
        )
    ).json()

    task = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            headers=_auth_header(token),
            json={
                "title": "Complete Session 8 Review & Optimization",
                "priority": "URGENT",
                "assignee_id": user_id,
            },
        )
    ).json()
    task_id = task["id"]

    # Attach label & add comment
    attach_res = await client.post(
        f"/api/v1/tasks/{task_id}/labels/{label['id']}",
        headers=_auth_header(token),
    )
    assert attach_res.status_code == 200
    assert len(attach_res.json()["labels"]) == 1

    comment_res = await client.post(
        f"/api/v1/tasks/{task_id}/comments",
        headers=_auth_header(token),
        json={"content": "All Ruff, Mypy, and Pytest checks passing 100%!"},
    )
    assert comment_res.status_code == 201
    comment_id = comment_res.json()["id"]

    detail_res = await client.get(
        f"/api/v1/tasks/{task_id}",
        headers=_auth_header(token),
    )
    assert detail_res.status_code == 200
    assert len(detail_res.json()["comments"]) == 1

    # Delete comment -> 204, detach label -> 204, archive project -> 200, delete task -> 204
    del_comment = await client.delete(
        f"/api/v1/tasks/{task_id}/comments/{comment_id}",
        headers=_auth_header(token),
    )
    assert del_comment.status_code == 204

    detach_res = await client.delete(
        f"/api/v1/tasks/{task_id}/labels/{label['id']}",
        headers=_auth_header(token),
    )
    assert detach_res.status_code == 204

    archive_res = await client.post(
        f"/api/v1/projects/{proj_id}/archive",
        headers=_auth_header(token),
    )
    assert archive_res.status_code == 200
    assert archive_res.json()["status"] == "ARCHIVED"

    del_task = await client.delete(
        f"/api/v1/tasks/{task_id}",
        headers=_auth_header(token),
    )
    assert del_task.status_code == 204
