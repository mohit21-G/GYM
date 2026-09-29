import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from bson import ObjectId
from fastapi.encoders import ENCODERS_BY_TYPE
from .config import settings

# Automatically serialize MongoDB ObjectId as string
ENCODERS_BY_TYPE[ObjectId] = str
from .database import connect_to_mongo, close_mongo_connection, get_db
from .services.auth_service import AuthService
from .routers import (
    auth,
    users,
    chat,
    food_logs,
    activity_logs,
    weight_logs,
    hydration_logs,
    sleep_logs,
    dashboard,
    admin,
    health,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    db = get_db()
    
    # Ensure default admin user exists
    admin_email = settings.ADMIN_EMAIL.lower().strip()
    admin_user = await db.users.find_one({"email": admin_email})
    hashed = AuthService.hash_password(settings.ADMIN_PASSWORD)
    if not admin_user:
        await db.users.insert_one({
            "id": "admin-system-id",
            "email": admin_email,
            "passwordHash": hashed,
            "password_hash": hashed,
            "name": "System Administrator",
            "role": "ADMIN",
            "status": "ACTIVE",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        })
        print(f"[Admin] Seeded default admin user {admin_email}")
    else:
        # Ensure password hash is current
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"passwordHash": hashed, "password_hash": hashed, "role": "ADMIN", "status": "ACTIVE"}}
        )
    
    yield

    # Shutdown
    await close_mongo_connection()

app = FastAPI(
    title="Google Fitbit AI Chatbot API",
    description="FastAPI Backend for Health & Fitness Assistant with MongoDB (v1.0.4)",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Response Envelope Middleware: wraps /api/v1 responses in { success: true, statusCode: 200, data: ... }
class ResponseEnvelopeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path

        # Only wrap API JSON responses
        if path.startswith("/api/v1") and not path.startswith("/api/v1/health"):
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type and 200 <= response.status_code < 300:
                body = [section async for section in response.body_iterator]
                if body:
                    try:
                        raw_data = json.loads(body[0].decode("utf-8"))
                        # If already wrapped with statusCode, don't double wrap
                        if isinstance(raw_data, dict) and "success" in raw_data and "statusCode" in raw_data and "data" in raw_data:
                            wrapped = raw_data
                        else:
                            wrapped = {
                                "success": True,
                                "statusCode": response.status_code,
                                "data": raw_data,
                            }
                        encoded = json.dumps(wrapped).encode("utf-8")
                        response.headers["content-length"] = str(len(encoded))
                        return Response(
                            content=encoded,
                            status_code=response.status_code,
                            media_type="application/json",
                            headers=dict(response.headers),
                        )
                    except Exception:
                        pass
        return response

app.add_middleware(ResponseEnvelopeMiddleware)

# CORS setup - added outermost so preflight OPTIONS requests are handled immediately
cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://gym-zeta-five-47.vercel.app",
]
if settings.CORS_ORIGINS:
    for origin in settings.CORS_ORIGINS.split(","):
        origin = origin.strip()
        if origin and origin not in cors_origins:
            cors_origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"^https:\/\/.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Exception Handlers for frontend / test compatibility
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "statusCode": exc.status_code,
            "message": exc.detail,
            "error": exc.detail,
            "success": False,
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "statusCode": 500,
            "message": str(exc),
            "error": "Internal Server Error",
            "success": False,
        },
    )

# Include all routers under prefix /api/v1
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(food_logs.router, prefix="/api/v1")
app.include_router(activity_logs.router, prefix="/api/v1")
app.include_router(weight_logs.router, prefix="/api/v1")
app.include_router(hydration_logs.router, prefix="/api/v1")
app.include_router(sleep_logs.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "name": "Google Fitbit AI Chatbot API",
        "framework": "FastAPI",
        "status": "online",
        "documentation": "/docs",
    }
