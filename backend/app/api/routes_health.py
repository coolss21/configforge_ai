from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "mode": settings.GENERATION_MODE,
        "offline_mode": settings.DEMO_OFFLINE_MODE or not settings.OPENROUTER_API_KEY
    }
