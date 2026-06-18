"""Тесты health check эндпоинтов."""

import pytest


@pytest.mark.asyncio
async def test_root(client):
    """GET / — quick health check."""
    response = await client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
