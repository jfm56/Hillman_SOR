"""Prompt size control for memory-safe LLM calls.

Ensures prompts never exceed MAX_TOKENS limit.
Truncates low-relevance content when necessary.
"""
from typing import List, Dict, Any

# Hard limits
MAX_PROMPT_TOKENS = 6000
MAX_CHUNK_TOKENS = 800
MAX_CHUNKS = 8


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return len(text) // 4


def truncate_to_token_limit(text: str, max_tokens: int) -> str:
    """Truncate text to fit within token limit."""
    estimated = estimate_tokens(text)
    if estimated <= max_tokens:
        return text
    
    # Truncate to approximate char limit
    max_chars = max_tokens * 4
    return text[:max_chars] + "..."


def build_bounded_prompt(
    system_prompt: str,
    user_message: str,
    context_chunks: List[Dict[str, Any]] = None,
    chat_summary: str = None,
    recent_messages: List[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Build a prompt that fits within token limits.
    
    Priority order (highest to lowest):
    1. System prompt (truncate if needed)
    2. User message (truncate if needed)
    3. Recent messages (last 3)
    4. Context chunks (top 8 by relevance)
    5. Chat summary
    
    Returns dict with:
    - messages: List of message dicts
    - total_tokens: Estimated token count
    - truncated: Whether any content was truncated
    """
    messages = []
    total_tokens = 0
    truncated = False
    
    # 1. System prompt (reserve 500 tokens)
    system_tokens = estimate_tokens(system_prompt)
    if system_tokens > 500:
        system_prompt = truncate_to_token_limit(system_prompt, 500)
        truncated = True
        system_tokens = 500
    
    messages.append({"role": "system", "content": system_prompt})
    total_tokens += system_tokens
    
    # 2. Reserve space for user message (up to 1000 tokens)
    user_tokens = min(estimate_tokens(user_message), 1000)
    remaining_tokens = MAX_PROMPT_TOKENS - total_tokens - user_tokens
    
    # 3. Add chat summary if available (up to 300 tokens)
    if chat_summary and remaining_tokens > 300:
        summary_text = truncate_to_token_limit(chat_summary, 300)
        messages.append({
            "role": "system",
            "content": f"Previous conversation summary: {summary_text}"
        })
        total_tokens += estimate_tokens(summary_text)
        remaining_tokens -= estimate_tokens(summary_text)
    
    # 4. Add context chunks (up to MAX_CHUNKS, sorted by relevance)
    if context_chunks and remaining_tokens > 500:
        context_text = "Relevant context:\n"
        chunks_added = 0
        
        for chunk in context_chunks[:MAX_CHUNKS]:
            chunk_text = chunk.get("chunk_text", "")
            chunk_tokens = estimate_tokens(chunk_text)
            
            if total_tokens + chunk_tokens > MAX_PROMPT_TOKENS - user_tokens - 100:
                truncated = True
                break
            
            context_text += f"\n---\n{chunk_text}\n"
            chunks_added += 1
            total_tokens += chunk_tokens
        
        if chunks_added > 0:
            messages.append({"role": "system", "content": context_text})
    
    # 5. Add recent messages (last 3)
    if recent_messages:
        for msg in recent_messages[-3:]:
            msg_tokens = estimate_tokens(msg["content"])
            if total_tokens + msg_tokens > MAX_PROMPT_TOKENS - user_tokens:
                truncated = True
                break
            messages.append(msg)
            total_tokens += msg_tokens
    
    # 6. Add user message
    if estimate_tokens(user_message) > 1000:
        user_message = truncate_to_token_limit(user_message, 1000)
        truncated = True
    
    messages.append({"role": "user", "content": user_message})
    total_tokens += estimate_tokens(user_message)
    
    return {
        "messages": messages,
        "total_tokens": total_tokens,
        "truncated": truncated,
    }


def validate_prompt_size(messages: List[Dict[str, str]]) -> bool:
    """Validate that prompt is within limits."""
    total_tokens = sum(estimate_tokens(m.get("content", "")) for m in messages)
    return total_tokens <= MAX_PROMPT_TOKENS
