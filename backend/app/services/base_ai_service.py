from abc import ABC, abstractmethod

class BaseAIService(ABC):
    @abstractmethod
    async def generate_response(
        self,
        user_message: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        model: str = "default"
    ) -> str:
        pass
