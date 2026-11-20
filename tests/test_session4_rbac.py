from httpx import AsyncClient

from tests.test_taskhub_api import _auth_header, _register_user


async def test_session4_workspace_member_roles_and_ownership(
    client: AsyncClient,
) -> None:
    """Session 4 RBAC test: verify OWNER, EDITOR, and VIEWER permissions and member listing."""
    owner_reg = await _register_user(client, "s4_owner@taskhub.io", "S4 Owner")
    editor_reg = await _register_user(client, "s4_editor@taskhub.io", "S4 Editor")
    owner_token = str(owner_reg["access_token"])
    editor_token = str(editor_reg["access_token"])
    editor_id = int(editor_reg["user"]["id"])  # type: ignore[index]

    ws = (
        await client.post(
            "/api/v1/workspaces",
            headers=_auth_header(owner_token),
            json={"name": "Session 4 RBAC Workspace"},
        )
    ).json()
    ws_id = ws["id"]

    # Invite editor as VIEWER initially
    await client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        headers=_auth_header(owner_token),
        json={"user_id": editor_id, "role": "VIEWER"},
    )

    members_res = await client.get(
        f"/api/v1/workspaces/{ws_id}/members",
        headers=_auth_header(editor_token),
    )
    assert members_res.status_code == 200
    assert len(members_res.json()) == 2

    # VIEWER cannot create project in workspace (403)
    forbidden_proj = await client.post(
        f"/api/v1/workspaces/{ws_id}/projects",
        headers=_auth_header(editor_token),
        json={"name": "Unauthorized Project"},
    )
    assert forbidden_proj.status_code == 403

    # Upgrade to EDITOR -> can create project, but cannot delete workspace (OWNER only)
    await client.patch(
        f"/api/v1/workspaces/{ws_id}/members/{editor_id}",
        headers=_auth_header(owner_token),
        json={"role": "EDITOR"},
    )
    ok_proj = await client.post(
        f"/api/v1/workspaces/{ws_id}/projects",
        headers=_auth_header(editor_token),
        json={"name": "Authorized Editor Project"},
    )
    assert ok_proj.status_code == 201

    forbidden_del_ws = await client.delete(
        f"/api/v1/workspaces/{ws_id}",
        headers=_auth_header(editor_token),
    )
    assert forbidden_del_ws.status_code == 403
