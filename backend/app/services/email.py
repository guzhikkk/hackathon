import httpx
from app.config import get_settings

settings = get_settings()

async def send_email_async(to_email: str, subject: str, body: str, is_html: bool = False):
    resend_key = settings.RESEND_API_KEY
    if not resend_key:
        return

    payload = {
        "from": "Test <onboarding@resend.dev>",
        "to": [to_email],
        "subject": subject,
    }
    
    if is_html:
        payload["html"] = body
    else:
        payload["text"] = body

    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {resend_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=10.0
            )
    except Exception:
        pass
