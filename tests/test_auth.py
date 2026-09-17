import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


class TestSignup:
    async def test_signup_creates_user_with_user_role(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/signup",
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
        body = response.json()
        assert body["role"] == "USER"
        assert body["email"] == "alice@example.com"
        assert body["is_blocked"] is False
        assert "password" not in body
        assert "password_hash" not in body

    async def test_signup_duplicate_email_returns_409(self, client: AsyncClient):
        payload = {
            "name": "Bob",
            "surname": "Jones",
            "username": "bob_jones",
            "email": "bob@example.com",
            "password": "StrongPass123",
        }
        first = await client.post("/api/v1/auth/signup", json=payload)
        assert first.status_code == 201

        duplicate = await client.post(
            "/api/v1/auth/signup",
            json={**payload, "username": "bob_jones_2"},
        )
        assert duplicate.status_code == 409

    async def test_signup_ignores_client_supplied_role(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/signup",
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
        assert response.json()["role"] == "USER"

    async def test_signup_ignores_client_supplied_group_id(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/signup",
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
        assert response.json()["group"] is None


class TestLogin:
    async def test_login_with_valid_credentials_returns_tokens(self, client: AsyncClient, make_user):
        user, password = await make_user(password="LoginPass123")

        response = await client.post(
            "/api/v1/auth/login",
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
            "/api/v1/auth/login",
            json={"login": user.email, "password": password},
        )
        assert response.status_code == 200

    async def test_login_with_wrong_password_returns_401(self, client: AsyncClient, make_user):
        user, _ = await make_user(password="LoginPass123")

        response = await client.post(
            "/api/v1/auth/login",
            json={"login": user.username, "password": "WrongPassword"},
        )
        assert response.status_code == 401

    async def test_login_with_unknown_username_returns_401(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/login",
            json={"login": "no_such_user", "password": "whatever"},
        )
        assert response.status_code == 401


class TestRefreshToken:
    async def test_refresh_returns_new_token_pair(self, client: AsyncClient, make_user):
        user, password = await make_user(password="RefreshPass123")
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"login": user.username, "password": password},
        )
        refresh_token = login_response.json()["refresh_token"]

        response = await client.post("/api/v1/auth/refresh-token", json={"refresh_token": refresh_token})

        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert body["refresh_token"] != refresh_token  # ротация refresh-токена

    async def test_refresh_with_garbage_token_returns_401(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/refresh-token", json={"refresh_token": "not-a-real-token"})
        assert response.status_code == 401

    async def test_refresh_with_access_token_instead_of_refresh_returns_401(
        self, client: AsyncClient, make_user, jwt_service
    ):
        user, _ = await make_user()
        access_token = jwt_service.create_access_token(user.id, user.role.value)

        response = await client.post("/api/v1/auth/refresh-token", json={"refresh_token": access_token})
        assert response.status_code == 401

    async def test_old_refresh_token_cannot_be_reused_after_rotation(self, client: AsyncClient, make_user):
        user, password = await make_user(password="RefreshPass123")
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"login": user.username, "password": password},
        )
        refresh_token = login_response.json()["refresh_token"]

        first = await client.post("/api/v1/auth/refresh-token", json={"refresh_token": refresh_token})
        assert first.status_code == 200

        second = await client.post("/api/v1/auth/refresh-token", json={"refresh_token": refresh_token})
        assert second.status_code == 401
