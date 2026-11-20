from fastapi import APIRouter
from httpx import AsyncClient
from sqlalchemy import update

from app.main import app
from app.models.enums import UserRole
from app.models.user import User
from tests.conftest import TestSessionLocal


async def _register_user(
    client: AsyncClient,
    email: str,
    full_name: str = "Test User",
    password: str = "Secret123!",
) -> dict[str, object]:
    res = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": full_name, "password": password},
    )
    assert res.status_code == 201, res.text
    data: dict[str, object] = res.json()
    return data


async def _promote_to_admin(user_id: int) -> None:
    async with TestSessionLocal() as session:
        await session.execute(
            update(User).where(User.id == user_id).values(role=UserRole.ADMIN)
        )
        await session.commit()


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_register_rejects_role_field_and_defaults_to_member(
    client: AsyncClient,
) -> None:
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "attacker@taskhub.io",
            "full_name": "Attacker",
            "password": "Password123!",
            "role": "ADMIN",
        },
    )
    assert res.status_code == 422
    body = res.json()
    assert body["error_code"] == "VALIDATION_ERROR"

    valid = await _register_user(client, "member@taskhub.io")
    user_info = valid["user"]
    assert isinstance(user_info, dict)
    assert user_info["role"] == "MEMBER"


async def test_patch_me_cannot_change_role_or_is_active(client: AsyncClient) -> None:
    reg = await _register_user(client, "me@taskhub.io")
    token = str(reg["access_token"])

    res_role = await client.patch(
        "/api/v1/users/me",
        headers=_auth_header(token),
        json={"role": "ADMIN"},
    )
    assert res_role.status_code == 422

    res_active = await client.patch(
        "/api/v1/users/me",
        headers=_auth_header(token),
        json={"is_active": False},
    )
    assert res_active.status_code == 422

    res_null = await client.patch(
        "/api/v1/users/me",
        headers=_auth_header(token),
        json={"full_name": None},
    )
    assert res_null.status_code == 422

    res_ok = await client.patch(
        "/api/v1/users/me",
        headers=_auth_header(token),
        json={"full_name": "  Updated Name  "},
    )
    assert res_ok.status_code == 200
    assert res_ok.json()["full_name"] == "Updated Name"


async def test_refresh_token_rotation_and_password_change_revocation(
    client: AsyncClient,
) -> None:
    reg = await _register_user(client, "rotate@taskhub.io", password="OldPassword1!")
    old_access = str(reg["access_token"])
    old_refresh = str(reg["refresh_token"])

    refreshed = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert refreshed.status_code == 200
    new_tokens = refreshed.json()

    # Reusing the same refresh token must fail (atomic consumption)
    reuse = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert reuse.status_code == 401

    # Changing password invalidates previously issued tokens
    pw_res = await client.post(
        "/api/v1/users/me/change-password",
        headers=_auth_header(old_access),
        json={
            "current_password": "OldPassword1!",
            "new_password": "NewPassword2!",
        },
    )
    assert pw_res.status_code == 200

    refresh_after_pw = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": new_tokens["refresh_token"]},
    )
    assert refresh_after_pw.status_code == 401


async def test_unauthenticated_and_rbac_permissions(client: AsyncClient) -> None:
    # Unauthenticated calls must return 401
    unauth_ws = await client.post("/api/v1/workspaces", json={"name": "NoAuth WS"})
    assert unauth_ws.status_code == 401

    owner_reg = await _register_user(client, "owner@taskhub.io", "Owner User")
    viewer_reg = await _register_user(client, "viewer@taskhub.io", "Viewer User")
    owner_token = str(owner_reg["access_token"])
    viewer_token = str(viewer_reg["access_token"])
    owner_id = int(owner_reg["user"]["id"])  # type: ignore[index]
    viewer_id = int(viewer_reg["user"]["id"])  # type: ignore[index]

    # Regular member cannot access admin /users endpoint
    users_res = await client.get("/api/v1/users", headers=_auth_header(owner_token))
    assert users_res.status_code == 403

    # Create workspace -> owner is automatically OWNER member
    ws_res = await client.post(
        "/api/v1/workspaces",
        headers=_auth_header(owner_token),
        json={"name": "Sun* Workspace"},
    )
    assert ws_res.status_code == 201
    ws_id = ws_res.json()["id"]

    # Cannot downgrade primary workspace owner's role
    downgrade_owner = await client.patch(
        f"/api/v1/workspaces/{ws_id}/members/{owner_id}",
        headers=_auth_header(owner_token),
        json={"role": "VIEWER"},
    )
    assert downgrade_owner.status_code == 400

    # Add viewer member
    add_mem = await client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        headers=_auth_header(owner_token),
        json={"user_id": viewer_id, "role": "VIEWER"},
    )
    assert add_mem.status_code == 201

    # Owner creates project and task (assigned to viewer)
    proj_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/projects",
        headers=_auth_header(owner_token),
        json={"name": "FastAPI Backend", "description": "Core API"},
    )
    assert proj_res.status_code == 201
    proj_id = proj_res.json()["id"]

    task_res = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        headers=_auth_header(owner_token),
        json={
            "title": "Build RBAC tests",
            "priority": "HIGH",
            "assignee_id": viewer_id,
        },
    )
    assert task_res.status_code == 201
    task_id = task_res.json()["id"]

    # VIEWER can read tasks and post comments, but CANNOT update or delete task (403)
    viewer_list = await client.get(
        f"/api/v1/projects/{proj_id}/tasks",
        headers=_auth_header(viewer_token),
    )
    assert viewer_list.status_code == 200

    viewer_patch = await client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=_auth_header(viewer_token),
        json={"status": "DONE"},
    )
    assert viewer_patch.status_code == 403

    viewer_delete = await client.delete(
        f"/api/v1/tasks/{task_id}",
        headers=_auth_header(viewer_token),
    )
    assert viewer_delete.status_code == 403

    # Promote viewer to EDITOR -> can update task, then remove from workspace -> loses access (403)
    promote_res = await client.patch(
        f"/api/v1/workspaces/{ws_id}/members/{viewer_id}",
        headers=_auth_header(owner_token),
        json={"role": "EDITOR"},
    )
    assert promote_res.status_code == 200

    editor_patch = await client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=_auth_header(viewer_token),
        json={"status": "IN_PROGRESS"},
    )
    assert editor_patch.status_code == 200

    # PATCH with explicit null for title/status/priority must fail with 422
    null_patch = await client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=_auth_header(viewer_token),
        json={"title": None},
    )
    assert null_patch.status_code == 422

    # Remove member -> returns 204, and removed member gets 403 when trying to update old task
    rem_res = await client.delete(
        f"/api/v1/workspaces/{ws_id}/members/{viewer_id}",
        headers=_auth_header(owner_token),
    )
    assert rem_res.status_code == 204

    removed_patch = await client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=_auth_header(viewer_token),
        json={"status": "DONE"},
    )
    assert removed_patch.status_code == 403


async def test_error_format_middleware_headers_and_500_safety(
    client: AsyncClient,
) -> None:
    # 1. Unknown route returns standardized ErrorResponse with X-Request-ID & security headers
    res_404 = await client.get(
        "/api/v1/non-existent-endpoint",
        headers={"X-Request-ID": "valid-req-id-123"},
    )
    assert res_404.status_code == 404
    body_404 = res_404.json()
    assert body_404["error_code"] == "HTTP_404"
    assert body_404["request_id"] == "valid-req-id-123"
    assert res_404.headers["X-Request-ID"] == "valid-req-id-123"
    assert res_404.headers["X-Content-Type-Options"] == "nosniff"
    assert res_404.headers["X-Frame-Options"] == "DENY"

    # 2. Malformed X-Request-ID is sanitized
    res_bad_id = await client.get(
        "/api/v1/non-existent-endpoint",
        headers={"X-Request-ID": "bad id with spaces and $pecial chars!"},
    )
    assert res_bad_id.headers["X-Request-ID"] != "bad id with spaces and $pecial chars!"
    assert len(res_bad_id.headers["X-Request-ID"]) == 36

    # 3. Unhandled 500 error never leaks internal exception text and preserves headers
    boom_router = APIRouter()

    @boom_router.get("/api/v1/test-boom-500")
    async def _boom() -> None:
        raise RuntimeError("SECRET_DB_PASSWORD_LEAK_12345")

    app.include_router(boom_router)
    res_500 = await client.get(
        "/api/v1/test-boom-500",
        headers={"X-Request-ID": "trace-500-req"},
    )
    assert res_500.status_code == 500
    body_500 = res_500.json()
    assert body_500["detail"] == "Internal server error"
    assert body_500["error_code"] == "INTERNAL_SERVER_ERROR"
    assert "message" not in body_500
    assert "SECRET_DB_PASSWORD_LEAK_12345" not in res_500.text
    assert res_500.headers["X-Request-ID"] == "trace-500-req"
    assert res_500.headers["X-Content-Type-Options"] == "nosniff"


async def test_cache_invalidation_and_cache_endpoints_auth(
    client: AsyncClient,
) -> None:
    reg = await _register_user(client, "cache_admin@taskhub.io", "Cache Admin")
    token = str(reg["access_token"])
    user_id = int(reg["user"]["id"])  # type: ignore[index]

    ws = (
        await client.post(
            "/api/v1/workspaces",
            headers=_auth_header(token),
            json={"name": "Cache WS"},
        )
    ).json()
    proj = (
        await client.post(
            f"/api/v1/workspaces/{ws['id']}/projects",
            headers=_auth_header(token),
            json={"name": "Cache Project"},
        )
    ).json()
    proj_id = proj["id"]

    # DELETE .../tasks/cache without token -> 401
    unauth_flush = await client.delete(f"/api/v1/projects/{proj_id}/tasks/cache")
    assert unauth_flush.status_code == 401

    # First list populates cache (miss=1, hit=0)
    list_1 = await client.get(
        f"/api/v1/projects/{proj_id}/tasks",
        headers=_auth_header(token),
    )
    assert list_1.status_code == 200
    assert list_1.json()["total"] == 0

    # Second list hits cache (miss=1, hit=1)
    list_2 = await client.get(
        f"/api/v1/projects/{proj_id}/tasks",
        headers=_auth_header(token),
    )
    assert list_2.status_code == 200

    # Creating a task invalidates cache -> subsequent list immediately sees total=1
    created_task = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        headers=_auth_header(token),
        json={"title": "Cached Task 1", "assignee_id": user_id},
    )
    assert created_task.status_code == 201
    task_id = created_task.json()["id"]

    list_3 = await client.get(
        f"/api/v1/projects/{proj_id}/tasks",
        headers=_auth_header(token),
    )
    assert list_3.json()["total"] == 1

    # Attach label, then update label -> task list cache is invalidated and reflects updated label name
    lbl = (
        await client.post(
            f"/api/v1/projects/{proj_id}/labels",
            headers=_auth_header(token),
            json={"name": "v1-label", "color": "#112233"},
        )
    ).json()
    await client.post(
        f"/api/v1/tasks/{task_id}/labels/{lbl['id']}",
        headers=_auth_header(token),
    )
    await client.get(
        f"/api/v1/projects/{proj_id}/tasks",
        headers=_auth_header(token),
    )
    await client.patch(
        f"/api/v1/projects/{proj_id}/labels/{lbl['id']}",
        headers=_auth_header(token),
        json={"name": "v2-label"},
    )
    list_after_label_update = await client.get(
        f"/api/v1/projects/{proj_id}/tasks",
        headers=_auth_header(token),
    )
    assert (
        list_after_label_update.json()["items"][0]["labels"][0]["name"] == "v2-label"
    )

    # cache-stats requires ADMIN role (MEMBER gets 403)
    non_admin_stats = await client.get(
        f"/api/v1/projects/{proj_id}/tasks/cache-stats",
        headers=_auth_header(token),
    )
    assert non_admin_stats.status_code == 403

    await _promote_to_admin(user_id)
    admin_stats = await client.get(
        f"/api/v1/projects/{proj_id}/tasks/cache-stats",
        headers=_auth_header(token),
    )
    assert admin_stats.status_code == 200
    stats_body = admin_stats.json()
    assert stats_body["project_id"] == proj_id
    assert stats_body["hits"] >= 1
    assert stats_body["misses"] >= 1
