import time
from datetime import datetime, timezone
from fastapi import APIRouter
from ..database import get_db
from ..config import settings

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
async def check_health():
    return {
        "status": "ok",
        "service": "Fitness Chatbot API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "engine": "FastAPI + Python 3.14 + MongoDB",
    }

@router.get("/database")
async def check_database():
    start = time.perf_counter()
    db = get_db()
    try:
        await db.command("ping")
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "status": "ok",
            "database": "mongodb",
            "connected": True,
            "latencyMs": latency_ms,
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "mongodb",
            "connected": False,
            "error": str(e),
        }

@router.get("/redis")
async def check_redis():
    return {
        "status": "ok",
        "type": "in-memory-fallback",
        "message": "In-memory caching active",
    }

@router.get("/ai")
async def check_ai():
    return {
        "status": "ok",
        "provider": "cloudflare",
        "model": settings.CLOUDFLARE_MODEL,
        "configured": bool(settings.CLOUDFLARE_API_KEY and settings.CLOUDFLARE_ACCOUNT_ID),
        "groqFallback": bool(settings.GROQ_API_KEY),
    }
