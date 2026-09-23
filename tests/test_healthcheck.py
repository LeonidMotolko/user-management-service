import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_healthcheck_returns_ok(client: AsyncClient):
    response = await client.get("/healthcheck")
    assert response.status_code == 200
    assert response.content == b""
