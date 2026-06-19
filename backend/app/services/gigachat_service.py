import asyncio
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from app.config import get_settings
from app.services.base_ai_service import BaseAIService

settings = get_settings()

class GigaChatService(BaseAIService):
    def __init__(self):
        self.credentials = settings.GIGACHAT_CREDENTIALS

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
            def _call_gigachat():
                with GigaChat(credentials=self.credentials, verify_ssl_certs=False) as giga:
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
                    response = giga.chat(payload)
                    return response.choices[0].message.content
            
            return await asyncio.wait_for(asyncio.to_thread(_call_gigachat), timeout=60.0)
        except asyncio.TimeoutError:
            return "Ошибка: GigaChat не ответил за 60 секунд (Таймаут)."
        except Exception as e:
            return f"Ошибка при обращении к GigaChat: {str(e)}"
