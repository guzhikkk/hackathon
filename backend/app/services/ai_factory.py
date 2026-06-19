from app.config import get_settings
from app.services.base_ai_service import BaseAIService
from app.services.gigachat_service import GigaChatService
from app.services.local_ai_service import LocalAIService

settings = get_settings()

def get_ai_service() -> BaseAIService:
    provider = settings.AI_PROVIDER.lower()
    
    if provider == "local":
        return LocalAIService()
    elif provider == "gigachat":
        return GigaChatService()
    else:
        return GigaChatService()
