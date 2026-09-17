import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers
from user_management_service.domain.entities.role import Role

pytestmark = pytest.mark.asyncio(loop_scope="session")


class TestUserMe:
    async def test_get_me_returns_own_data(self, client: AsyncClient, make_user, jwt_service):
        user, _ = await make_user(role=Role.USER)
        headers = auth_headers(jwt_service, user.id, user.role.value)

        response = await client.get("/api/v1/user/me", headers=headers)

        assert response.status_code == 200
        assert response.json()["id"] == str(user.id)

    async def test_get_me_without_token_returns_401(self, client: AsyncClient):
        response = await client.get("/api/v1/user/me")
        assert response.status_code == 401

    async def test_get_me_with_garbage_token_returns_401(self, client: AsyncClient):
        response = await client.get("/api/v1/user/me", headers={"Authorization": "Bearer not-a-real-token"})
        assert response.status_code == 401

    async def test_patch_me_updates_own_data(self, client: AsyncClient, make_user, jwt_service):
        user, _ = await make_user(role=Role.USER)
        headers = auth_headers(jwt_service, user.id, user.role.value)

        response = await client.patch("/api/v1/user/me", json={"name": "NewName"}, headers=headers)

        assert response.status_code == 200
        assert response.json()["name"] == "NewName"

    async def test_delete_me_removes_own_account(self, client: AsyncClient, make_user, jwt_service):
        user, _ = await make_user(role=Role.USER)
        headers = auth_headers(jwt_service, user.id, user.role.value)

        response = await client.delete("/api/v1/user/me", headers=headers)
        assert response.status_code == 204

        follow_up = await client.get("/api/v1/user/me", headers=headers)
        assert follow_up.status_code == 401


class TestUserByIdAccess:
    async def test_user_role_gets_403_on_other_user(self, client: AsyncClient, make_user, jwt_service):
        viewer, _ = await make_user(role=Role.USER)
        target, _ = await make_user(role=Role.USER)
        headers = auth_headers(jwt_service, viewer.id, viewer.role.value)

        response = await client.get(f"/api/v1/user/{target.id}", headers=headers)
        assert response.status_code == 403

    async def test_admin_can_view_any_user(self, client: AsyncClient, make_user, jwt_service):
        admin, _ = await make_user(role=Role.ADMIN)
        target, _ = await make_user(role=Role.USER)
        headers = auth_headers(jwt_service, admin.id, admin.role.value)

        response = await client.get(f"/api/v1/user/{target.id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["id"] == str(target.id)

    async def test_moderator_can_view_same_group_user(self, client: AsyncClient, make_user, make_group, jwt_service):
        group = await make_group()
        moderator, _ = await make_user(role=Role.MODERATOR, group_id=group.id)
        target, _ = await make_user(role=Role.USER, group_id=group.id)
        headers = auth_headers(jwt_service, moderator.id, moderator.role.value)

        response = await client.get(f"/api/v1/user/{target.id}", headers=headers)
        assert response.status_code == 200

    async def test_moderator_gets_403_on_other_group_user(
        self, client: AsyncClient, make_user, make_group, jwt_service
    ):
        group_a = await make_group(name="Group A")
        group_b = await make_group(name="Group B")
        moderator, _ = await make_user(role=Role.MODERATOR, group_id=group_a.id)
        target, _ = await make_user(role=Role.USER, group_id=group_b.id)
        headers = auth_headers(jwt_service, moderator.id, moderator.role.value)

        response = await client.get(f"/api/v1/user/{target.id}", headers=headers)
        assert response.status_code == 403

    async def test_moderator_without_group_gets_403(self, client: AsyncClient, make_user, jwt_service):
        moderator, _ = await make_user(role=Role.MODERATOR, group_id=None)
        target, _ = await make_user(role=Role.USER)
        headers = auth_headers(jwt_service, moderator.id, moderator.role.value)

        response = await client.get(f"/api/v1/user/{target.id}", headers=headers)
        assert response.status_code == 403

    async def test_get_nonexistent_user_returns_404_for_admin(self, client: AsyncClient, make_user, jwt_service):
        import uuid

        admin, _ = await make_user(role=Role.ADMIN)
        headers = auth_headers(jwt_service, admin.id, admin.role.value)

        response = await client.get(f"/api/v1/user/{uuid.uuid4()}", headers=headers)
        assert response.status_code == 404


class TestUserByIdUpdate:
    async def test_admin_can_patch_any_user(self, client: AsyncClient, make_user, jwt_service):
        admin, _ = await make_user(role=Role.ADMIN)
        target, _ = await make_user(role=Role.USER)
        headers = auth_headers(jwt_service, admin.id, admin.role.value)

        response = await client.patch(f"/api/v1/user/{target.id}", json={"name": "PatchedByAdmin"}, headers=headers)
        assert response.status_code == 200
        assert response.json()["name"] == "PatchedByAdmin"

    async def test_moderator_cannot_patch_same_group_user(
        self, client: AsyncClient, make_user, make_group, jwt_service
    ):
        group = await make_group()
        moderator, _ = await make_user(role=Role.MODERATOR, group_id=group.id)
        target, _ = await make_user(role=Role.USER, group_id=group.id)
        headers = auth_headers(jwt_service, moderator.id, moderator.role.value)

        response = await client.patch(f"/api/v1/user/{target.id}", json={"name": "ShouldFail"}, headers=headers)
        assert response.status_code == 403

    async def test_user_cannot_patch_other_user(self, client: AsyncClient, make_user, jwt_service):
        viewer, _ = await make_user(role=Role.USER)
        target, _ = await make_user(role=Role.USER)
        headers = auth_headers(jwt_service, viewer.id, viewer.role.value)

        response = await client.patch(f"/api/v1/user/{target.id}", json={"name": "ShouldFail"}, headers=headers)
        assert response.status_code == 403


class TestUsersList:
    async def test_admin_sees_all_users(self, client: AsyncClient, make_user, jwt_service):
        admin, _ = await make_user(role=Role.ADMIN)
        await make_user(role=Role.USER)
        await make_user(role=Role.USER)
        headers = auth_headers(jwt_service, admin.id, admin.role.value)

        response = await client.get("/api/v1/users?page=1&limit=50", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert body["total"] >= 3

    async def test_moderator_sees_only_own_group(self, client: AsyncClient, make_user, make_group, jwt_service):
        group_a = await make_group(name="Group A")
        group_b = await make_group(name="Group B")
        moderator, _ = await make_user(role=Role.MODERATOR, group_id=group_a.id)
        await make_user(role=Role.USER, group_id=group_a.id)
        await make_user(role=Role.USER, group_id=group_b.id)
        headers = auth_headers(jwt_service, moderator.id, moderator.role.value)

        response = await client.get("/api/v1/users?page=1&limit=50", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 2
        assert all(item["group"] is not None and item["group"]["id"] == group_a.id for item in body["items"])

    async def test_plain_user_gets_403_on_list(self, client: AsyncClient, make_user, jwt_service):
        user, _ = await make_user(role=Role.USER)
        headers = auth_headers(jwt_service, user.id, user.role.value)

        response = await client.get("/api/v1/users", headers=headers)
        assert response.status_code == 403

    async def test_pagination_limits_items_but_not_total(self, client: AsyncClient, make_user, jwt_service):
        admin, _ = await make_user(role=Role.ADMIN)
        for _ in range(5):
            await make_user(role=Role.USER)
        headers = auth_headers(jwt_service, admin.id, admin.role.value)

        response = await client.get("/api/v1/users?page=1&limit=2", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert len(body["items"]) == 2
        assert body["total"] >= 6
