import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


def _bearer(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


class TestSignup:
    async def test_signup_creates_user_and_returns_success_message(self, client: AsyncClient):
        response = await client.post(
            "/auth/signup",
            json={
                "name": "Alice",
                "surname": "Smith",
                "username": "alice_smith",
                "email": "alice@example.com",
                "password": "StrongPass123",
                "phone_number": "+79990000000",
            },
        )

        assert response.status_code == 201
        assert "access_token" not in response.json()
        assert response.json()["detail"] == "User registered successfully"

        login = await client.post(
            "/auth/login",
            json={"login": "alice_smith", "password": "StrongPass123"},
        )
        assert login.status_code == 200

        me = await client.get("/user/me", headers=_bearer(login.json()["access_token"]))
        assert me.status_code == 200
        me_body = me.json()
        assert me_body["role"] == "USER"
        assert me_body["email"] == "alice@example.com"
        assert me_body["is_blocked"] is False
        assert "password" not in me_body
        assert "password_hash" not in me_body

    async def test_signup_duplicate_email_returns_409(self, client: AsyncClient):
        payload = {
            "name": "Bob",
            "surname": "Jones",
            "username": "bob_jones",
            "email": "bob@example.com",
            "password": "StrongPass123",
        }
        first = await client.post("/auth/signup", json=payload)
        assert first.status_code == 201

        duplicate = await client.post(
            "/auth/signup",
            json={**payload, "username": "bob_jones_2"},
        )
        assert duplicate.status_code == 409

    async def test_signup_ignores_client_supplied_role(self, client: AsyncClient):
        response = await client.post(
            "/auth/signup",
            json={
                "name": "Eve",
                "surname": "Hacker",
                "username": "eve_hacker",
                "email": "eve@example.com",
                "password": "StrongPass123",
                "role": "ADMIN",
            },
        )
        assert response.status_code == 201

        login = await client.post(
            "/auth/login",
            json={"login": "eve_hacker", "password": "StrongPass123"},
        )
        me = await client.get("/user/me", headers=_bearer(login.json()["access_token"]))
        assert me.status_code == 200
        assert me.json()["role"] == "USER"

    async def test_signup_ignores_client_supplied_group_id(self, client: AsyncClient):
        response = await client.post(
            "/auth/signup",
            json={
                "name": "Frank",
                "surname": "NoGroup",
                "username": "frank_nogroup",
                "email": "frank@example.com",
                "password": "StrongPass123",
                "group_id": 999,
            },
        )
        assert response.status_code == 201

        login = await client.post(
            "/auth/login",
            json={"login": "frank_nogroup", "password": "StrongPass123"},
        )
        me = await client.get("/user/me", headers=_bearer(login.json()["access_token"]))
        assert me.status_code == 200
        assert me.json()["group"] is None


class TestLogin:
    async def test_login_with_valid_credentials_returns_tokens(self, client: AsyncClient, make_user):
        user, password = await make_user(password="LoginPass123")

        response = await client.post(
            "/auth/login",
            json={"login": user.username, "password": password},
        )

        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "Bearer"

    async def test_login_with_email_as_login_works(self, client: AsyncClient, make_user):
        user, password = await make_user(password="LoginPass123")

        response = await client.post(
            "/auth/login",
            json={"login": user.email, "password": password},
        )
        assert response.status_code == 200

    async def test_login_with_phone_number_as_login_works(self, client: AsyncClient, make_user):
        user, password = await make_user(password="LoginPass123", phone_number="+79991112233")

        response = await client.post(
            "/auth/login",
            json={"login": user.phone_number, "password": password},
        )
        assert response.status_code == 200

    async def test_login_with_wrong_password_returns_401(self, client: AsyncClient, make_user):
        user, _ = await make_user(password="LoginPass123")

        response = await client.post(
            "/auth/login",
            json={"login": user.username, "password": "WrongPassword"},
        )
        assert response.status_code == 401

    async def test_login_with_unknown_username_returns_401(self, client: AsyncClient):
        response = await client.post(
            "/auth/login",
            json={"login": "no_such_user", "password": "whatever"},
        )
        assert response.status_code == 401


class TestRefreshToken:
    async def test_refresh_returns_new_token_pair(self, client: AsyncClient, make_user):
        user, password = await make_user(password="RefreshPass123")
        login_response = await client.post(
            "/auth/login",
            json={"login": user.username, "password": password},
        )
        access_token = login_response.json()["access_token"]
        refresh_token = login_response.json()["refresh_token"]

        response = await client.post(
            "/auth/refresh-token",
            json={"refresh_token": refresh_token},
            headers=_bearer(access_token),
        )

        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert body["refresh_token"] != refresh_token  # ротация refresh-токена

    async def test_refresh_without_access_token_returns_401(self, client: AsyncClient, make_user):
        user, password = await make_user(password="RefreshPass123")
        login_response = await client.post(
            "/auth/login",
            json={"login": user.username, "password": password},
        )
        refresh_token = login_response.json()["refresh_token"]

        response = await client.post("/auth/refresh-token", json={"refresh_token": refresh_token})
        assert response.status_code == 401

    async def test_refresh_with_garbage_token_returns_401(self, client: AsyncClient, make_user, jwt_service):
        user, _ = await make_user()
        access_token = jwt_service.create_access_token(user.id, user.role.value)

        response = await client.post(
            "/auth/refresh-token",
            json={"refresh_token": "not-a-real-token"},
            headers=_bearer(access_token),
        )
        assert response.status_code == 401

    async def test_refresh_with_access_token_instead_of_refresh_returns_401(
        self, client: AsyncClient, make_user, jwt_service
    ):
        user, _ = await make_user()
        access_token = jwt_service.create_access_token(user.id, user.role.value)

        response = await client.post(
            "/auth/refresh-token",
            json={"refresh_token": access_token},
            headers=_bearer(access_token),
        )
        assert response.status_code == 401

    async def test_old_refresh_token_cannot_be_reused_after_rotation(self, client: AsyncClient, make_user):
        user, password = await make_user(password="RefreshPass123")
        login_response = await client.post(
            "/auth/login",
            json={"login": user.username, "password": password},
        )
        access_token = login_response.json()["access_token"]
        refresh_token = login_response.json()["refresh_token"]
        headers = _bearer(access_token)

        first = await client.post(
            "/auth/refresh-token",
            json={"refresh_token": refresh_token},
            headers=headers,
        )
        assert first.status_code == 200

        second = await client.post(
            "/auth/refresh-token",
            json={"refresh_token": refresh_token},
            headers=headers,
        )
        assert second.status_code == 401


class TestResetPassword:
    async def test_reset_password_returns_202_when_user_exists(self, client: AsyncClient, make_user, message_publisher):
        user, _ = await make_user(email="reset.me@example.com")

        response = await client.post("/auth/reset-password", json={"email": user.email})

        assert response.status_code == 202
        message_publisher.publish_reset_password.assert_awaited_once()

    async def test_reset_password_returns_202_when_email_unknown(self, client: AsyncClient, message_publisher):
        response = await client.post("/auth/reset-password", json={"email": "nobody@example.com"})

        assert response.status_code == 202
        message_publisher.publish_reset_password.assert_not_awaited()
