import pytest
from unittest.mock import patch, MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_chat_with_ai_unauthorized(unauth_client):
    response = await unauth_client.post(
        "/api/ai/chat",
        json={"message": "Привет!"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_chat_with_ai_success(client):
    mock_answer = "Привет! Я Локальная Модель."
    
    with patch("app.api.ai.get_ai_service") as mock_get_factory:
        mock_service_instance = MagicMock()
        mock_service_instance.generate_response = AsyncMock(return_value=mock_answer)
        mock_get_factory.return_value = mock_service_instance
        
        response = await client.post(
            "/api/ai/chat",
            json={"message": "Привет!"}
        )
        
    assert response.status_code == 200
    assert response.json()["response"] == mock_answer
    mock_service_instance.generate_response.assert_called_once_with(
        user_message="Привет!",
        system_prompt=None,
        temperature=0.7,
        max_tokens=1000,
        model="GigaChat"
    )
