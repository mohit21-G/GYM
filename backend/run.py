import uvicorn
from app.config import settings

if __name__ == "__main__":
    print(f"Starting FastAPI server on {settings.API_HOST}:{settings.API_PORT} (reload={settings.API_RELOAD})")
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,
        log_level="info",
    )
