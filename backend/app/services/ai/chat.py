from typing import List, Optional
from uuid import UUID
from app.services.ai.openai_client import get_openai_client
from app.core.config import settings


SYSTEM_PROMPT = """You are an AI assistant for Hillmann Consulting, helping with Site Observation Reports (SOR).

You can help with:
- Rewriting text in formal SOR language
- Clarifying observations
- Suggesting improvements to report sections
- Answering questions about construction terminology
- Making text less speculative and more evidence-based

Guidelines:
- Use formal, professional language appropriate for engineering reports
- Reference specific evidence when making claims
- Avoid speculation - recommend stating only what was directly observed
- Use Hillmann's standard terminology and phrasing
- Be helpful but concise

You have access to project context when provided. Use it to give more relevant responses."""


async def generate_chat_response(
    messages: List[dict],
    context: Optional[dict] = None,
    project_id: Optional[UUID] = None,
    report_id: Optional[UUID] = None,
) -> dict:
    """Generate a chat response."""
    client = get_openai_client()
    
    # Build system message with context
    system_content = SYSTEM_PROMPT
    
    if context:
        if context.get("section_type"):
            system_content += f"\n\nCurrent section: {context['section_type'].replace('_', ' ').title()}"
        if context.get("report_number"):
            system_content += f"\nReport #: {context['report_number']}"
    
    # Prepare messages
    chat_messages = [{"role": "system", "content": system_content}]
    
    # Add conversation history (limit to last 10 messages to stay within context)
    for msg in messages[-10:]:
        chat_messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=chat_messages,
        max_tokens=1000,
        temperature=0.7,
    )
    
    return {
        "content": response.choices[0].message.content,
        "tokens_used": response.usage.total_tokens,
        "model": settings.OPENAI_MODEL,
    }
