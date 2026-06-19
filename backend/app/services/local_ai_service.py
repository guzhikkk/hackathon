from openai import AsyncOpenAI
from app.config import get_settings
from app.services.base_ai_service import BaseAIService

settings = get_settings()

class LocalAIService(BaseAIService):
    def __init__(self):
        self.base_url = settings.LOCAL_AI_BASE_URL
        self.api_key = settings.LOCAL_AI_API_KEY
        
        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

    async def generate_response(
        self,
        user_message: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        model: str = "default"
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": user_message})

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка локальной нейросети: {str(e)}"
