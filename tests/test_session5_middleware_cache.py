from httpx import AsyncClient

from tests.test_taskhub_api import _auth_header, _promote_to_admin, _register_user


async def test_session5_cache_flush_and_method_not_allowed_error_format(
    client: AsyncClient,
) -> None:
    """Session 5 test: verify 405 Method Not Allowed error schema and manual cache flush endpoint."""
    res_405 = await client.put("/api/v1/auth/login", json={})
    assert res_405.status_code == 405
    body_405 = res_405.json()
    assert body_405["error_code"] == "HTTP_405"
    assert body_405["request_id"] is not None
    assert "X-Process-Time-Ms" in res_405.headers
    assert res_405.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    reg = await _register_user(client, "s5_user@taskhub.io", "S5 User")
    token = str(reg["access_token"])
    user_id = int(reg["user"]["id"])  # type: ignore[index]

    ws = (
        await client.post(
            "/api/v1/workspaces",
            headers=_auth_header(token),
            json={"name": "S5 Cache WS"},
        )
    ).json()
    proj = (
        await client.post(
            f"/api/v1/workspaces/{ws['id']}/projects",
            headers=_auth_header(token),
            json={"name": "S5 Project"},
        )
    ).json()
    proj_id = proj["id"]

    await client.get(
        f"/api/v1/projects/{proj_id}/tasks",
        headers=_auth_header(token),
    )
    flush_res = await client.delete(
        f"/api/v1/projects/{proj_id}/tasks/cache",
        headers=_auth_header(token),
    )
    assert flush_res.status_code == 200
    assert "Invalidated" in flush_res.json()["message"]

    # Non-existent project cache-stats returns 404 for ADMIN
    await _promote_to_admin(user_id)
    missing_stats = await client.get(
        "/api/v1/projects/99999/tasks/cache-stats",
        headers=_auth_header(token),
    )
    assert missing_stats.status_code == 404
