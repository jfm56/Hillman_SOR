"""Local LLM management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.core.security import get_current_active_user, require_role
from app.core.config import settings
from app.db.session import get_db
from app.services.ai.local_llm import (
    check_ollama_connection,
    pull_model,
    generate_completion,
)

router = APIRouter()


class ModelPullRequest(BaseModel):
    model_name: str


class CompletionRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = None
    temperature: float = 0.7


@router.get("/status")
async def get_llm_status(
    current_user: User = Depends(get_current_active_user),
):
    """Get local LLM status and available models."""
    status = await check_ollama_connection()
    return {
        "use_local_llm": settings.USE_LOCAL_LLM,
        "ollama_host": settings.OLLAMA_HOST,
        "configured_model": settings.LOCAL_MODEL,
        "embedding_model": settings.LOCAL_EMBEDDING_MODEL,
        **status,
    }


@router.post("/pull")
async def pull_llm_model(
    request: ModelPullRequest,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
):
    """Pull a model from Ollama registry (admin only)."""
    success = await pull_model(request.model_name)
    if success:
        return {"message": f"Model {request.model_name} pulled successfully"}
    raise HTTPException(status_code=500, detail="Failed to pull model")


@router.post("/test")
async def test_completion(
    request: CompletionRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Test local LLM with a simple completion."""
    if not settings.USE_LOCAL_LLM:
        raise HTTPException(status_code=400, detail="Local LLM not enabled")
    
    try:
        response = await generate_completion(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
        )
        return {
            "response": response,
            "model": settings.LOCAL_MODEL,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def list_required_models(
    current_user: User = Depends(get_current_active_user),
):
    """List required models for all features."""
    return {
        "required_models": [
            {
                "name": settings.LOCAL_MODEL,
                "purpose": "Chat and text generation",
                "pull_command": f"docker exec sor_ollama ollama pull {settings.LOCAL_MODEL}",
            },
            {
                "name": settings.LOCAL_EMBEDDING_MODEL,
                "purpose": "Embeddings for style learning and RAG",
                "pull_command": f"docker exec sor_ollama ollama pull {settings.LOCAL_EMBEDDING_MODEL}",
            },
        ],
        "note": "Run the pull commands to download models before using AI features",
    }


@router.get("/learning-stats")
async def get_learning_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get statistics about AI learning from logged interactions."""
    from app.services.ai.ai_learning import get_learning_stats
    
    stats = await get_learning_stats(db)
    return {
        "learning_enabled": True,
        "storage": "PostgreSQL (ai_interaction_logs table)",
        **stats,
    }
