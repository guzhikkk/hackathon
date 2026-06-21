import asyncio
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from app.config import get_settings
from app.services.base_ai_service import BaseAIService

settings = get_settings()

class GigaChatService(BaseAIService):
    _client: GigaChat | None = None

    def __init__(self):
        self.credentials = settings.GIGACHAT_CREDENTIALS

    @classmethod
    def get_client(cls, credentials: str) -> GigaChat:
        if cls._client is None:
            cls._client = GigaChat(credentials=credentials, verify_ssl_certs=False)
        return cls._client

    async def generate_response(
        self,
        user_message: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        model: str = "GigaChat"
    ) -> str:
        if not self.credentials:
            return "Ошибка: Токен GigaChat не настроен в конфигурации."
            
        try:
            client = self.get_client(self.credentials)
            
            messages_payload = []
            if system_prompt:
                messages_payload.append(Messages(role=MessagesRole.SYSTEM, content=system_prompt))
            
            messages_payload.append(Messages(role=MessagesRole.USER, content=user_message))

            payload = Chat(
                messages=messages_payload,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model
            )
            
            response = await asyncio.wait_for(client.achat(payload), timeout=60.0)
            return response.choices[0].message.content
            
        except asyncio.TimeoutError:
            return "Ошибка: GigaChat не ответил за 60 секунд (Таймаут)."
        except Exception as e:
            return f"Ошибка при обращении к GigaChat: {str(e)}"
