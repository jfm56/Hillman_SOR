"""Bounded chat memory with summarization.

After every 5 turns, summarizes conversation into 1 paragraph.
At inference time, injects summary + last 3 turns only.
"""
from typing import List, Dict, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_memory import ChatMemory
from app.models.chat import ChatMessage
from app.core.config import settings


# Memory limits
MAX_HISTORY_TURNS = 10
SUMMARIZE_EVERY_N_TURNS = 5
INJECT_LAST_N_TURNS = 3
MAX_SUMMARY_TOKENS = 500


async def get_or_create_memory(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID,
    project_id: UUID = None,
) -> ChatMemory:
    """Get or create chat memory for a session."""
    result = await db.execute(
        select(ChatMemory).where(ChatMemory.session_id == session_id)
    )
    memory = result.scalar_one_or_none()
    
    if not memory:
        memory = ChatMemory(
            user_id=user_id,
            session_id=session_id,
            project_id=project_id,
            summary_memory=None,
            turn_count=0,
            last_summary_turn=0,
        )
        db.add(memory)
        await db.commit()
        await db.refresh(memory)
    
    return memory


async def should_summarize(memory: ChatMemory) -> bool:
    """Check if we should summarize the conversation."""
    turns_since_summary = memory.turn_count - memory.last_summary_turn
    return turns_since_summary >= SUMMARIZE_EVERY_N_TURNS


async def summarize_conversation(
    messages: List[Dict[str, str]],
    existing_summary: Optional[str] = None,
) -> str:
    """Summarize conversation into a single paragraph."""
    if not messages:
        return existing_summary or ""
    
    # Build conversation text
    conv_text = ""
    for msg in messages:
        role = "User" if msg["role"] == "user" else "Assistant"
        conv_text += f"{role}: {msg['content'][:200]}\n"
    
    # Include existing summary if any
    context = ""
    if existing_summary:
        context = f"Previous context: {existing_summary}\n\n"
    
    prompt = f"""{context}Summarize this conversation in ONE paragraph (max 100 words). Focus on key topics discussed and any decisions made:

{conv_text}

Summary:"""

    if settings.USE_LOCAL_LLM:
        from app.services.ai.local_llm import generate_completion
        summary = await generate_completion(
            prompt=prompt,
            system_prompt="You are a conversation summarizer. Be concise.",
            model=settings.LOCAL_FAST_MODEL,
            max_tokens=200,
        )
    else:
        summary = conv_text[:500]  # Fallback to truncation
    
    return summary.strip()


async def increment_turn_count(db: AsyncSession, memory: ChatMemory) -> None:
    """Increment turn count for memory."""
    await db.execute(
        update(ChatMemory)
        .where(ChatMemory.id == memory.id)
        .values(turn_count=memory.turn_count + 1)
    )
    await db.commit()


async def update_summary(
    db: AsyncSession,
    memory: ChatMemory,
    new_summary: str,
) -> None:
    """Update memory with new summary."""
    await db.execute(
        update(ChatMemory)
        .where(ChatMemory.id == memory.id)
        .values(
            summary_memory=new_summary,
            last_summary_turn=memory.turn_count,
        )
    )
    await db.commit()


async def get_bounded_context(
    db: AsyncSession,
    session_id: UUID,
    user_id: UUID,
    recent_messages: List[Dict[str, str]],
    project_id: UUID = None,
) -> Dict[str, any]:
    """Get bounded chat context: summary + last N turns.
    
    Returns dict with:
    - summary: Summarized history
    - messages: Last N messages to include
    - total_turns: Total conversation turns
    """
    memory = await get_or_create_memory(db, user_id, session_id, project_id)
    
    # Check if we need to summarize
    if await should_summarize(memory) and len(recent_messages) > INJECT_LAST_N_TURNS:
        # Get messages to summarize (all except last 3)
        messages_to_summarize = recent_messages[:-INJECT_LAST_N_TURNS]
        
        # Generate summary
        new_summary = await summarize_conversation(
            messages_to_summarize,
            memory.summary_memory,
        )
        
        # Update memory
        await update_summary(db, memory, new_summary)
        memory.summary_memory = new_summary
    
    # Increment turn count
    await increment_turn_count(db, memory)
    
    # Return bounded context
    return {
        "summary": memory.summary_memory,
        "messages": recent_messages[-INJECT_LAST_N_TURNS:] if len(recent_messages) > INJECT_LAST_N_TURNS else recent_messages,
        "total_turns": memory.turn_count,
    }
