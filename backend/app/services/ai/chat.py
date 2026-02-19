import time
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
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

You have access to project context when provided. Use it to give more relevant responses.
All conversations are private and processed locally - no data is sent to external services."""


async def generate_chat_response(
    messages: List[dict],
    context: Optional[dict] = None,
    project_id: Optional[UUID] = None,
    report_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    db: Optional[AsyncSession] = None,
) -> dict:
    """Generate a chat response using local LLM or OpenAI. Logs interaction for learning."""
    start_time = time.time()
    
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
    
    # Use local LLM if configured
    input_tokens = 0
    output_tokens = 0
    
    if settings.USE_LOCAL_LLM:
        from app.services.ai.local_llm import generate_chat_completion
        
        content = await generate_chat_completion(chat_messages)
        model_used = f"local:{settings.LOCAL_MODEL}"
    else:
        # Fallback to OpenAI
        from app.services.ai.openai_client import get_openai_client
        client = get_openai_client()
        
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=chat_messages,
            max_tokens=1000,
            temperature=0.7,
        )
        
        content = response.choices[0].message.content
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        model_used = settings.OPENAI_MODEL
    
    # Calculate latency
    latency_ms = int((time.time() - start_time) * 1000)
    
    # Log interaction for learning (if db session provided)
    if db is not None:
        from app.services.ai.ai_learning import log_ai_interaction
        
        # Get last user message as prompt
        user_message = messages[-1]["content"] if messages else ""
        
        await log_ai_interaction(
            db=db,
            user_id=user_id,
            interaction_type="chat",
            model_name=model_used,
            prompt=user_message[:2000],
            response=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            project_id=project_id,
            report_id=report_id,
            status="success",
        )
    
    return {
        "content": content,
        "tokens_used": input_tokens + output_tokens,
        "model": model_used,
    }
