from fastapi import APIRouter

from app.api.v1.endpoints import auth, projects, sites, buildings, upload, reports, ai, chat, audit, style_learning, local_llm

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(sites.router, prefix="/sites", tags=["Sites"])
api_router.include_router(buildings.router, prefix="/buildings", tags=["Buildings"])
api_router.include_router(upload.router, prefix="/upload", tags=["File Upload"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Pipeline"])
api_router.include_router(chat.router, prefix="/chat", tags=["AI Chat"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit"])
api_router.include_router(style_learning.router, prefix="/style", tags=["Style Learning"])
api_router.include_router(local_llm.router, prefix="/llm", tags=["Local LLM"])
