from openai import AsyncOpenAI
from app.core.config import settings
from typing import Optional

_client: Optional[AsyncOpenAI] = None


def get_openai_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


async def check_openai_connection() -> str:
    """Check if OpenAI API is accessible."""
    if not settings.OPENAI_API_KEY:
        return "not_configured"
    
    try:
        client = get_openai_client()
        await client.models.list()
        return "healthy"
    except Exception as e:
        return f"error: {str(e)}"
