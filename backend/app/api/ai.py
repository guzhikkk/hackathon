from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.ai_factory import get_ai_service
from app.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    system_prompt: str | None = None
    temperature: float = 0.7
    max_tokens: int = 1000
    model: str = "GigaChat"

class ChatResponse(BaseModel):
    response: str

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    service = get_ai_service()
    answer = await service.generate_response(
        user_message=request.message,
        system_prompt=request.system_prompt,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        model=request.model
    )
    return ChatResponse(response=answer)
