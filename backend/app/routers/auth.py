import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends
from ..database import get_db
from ..schemas.auth import RegisterDto, LoginDto, RefreshTokenDto
from ..services.auth_service import hash_password, verify_password, create_access_token, create_refresh_token, decode_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Customer Auth"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(dto: RegisterDto):
    db = get_db()
    email_clean = dto.email.lower().strip()
    
    existing = await db.users.find_one({"email": email_clean})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    user_id = str(uuid.uuid4())
    pw_hash = hash_password(dto.password)
    now = datetime.now(timezone.utc)

    profile = {
        "id": str(uuid.uuid4()),
        "userId": user_id,
        "age": dto.age,
        "gender": dto.gender or "MALE",
        "heightCm": dto.heightCm,
        "currentWeightKg": dto.currentWeightKg or 70.0,
        "targetWeightKg": dto.targetWeightKg,
        "dailyCalorieTarget": 2000,
        "dailyWaterMlTarget": 2500,
        "dailySleepMinutesTarget": 480,
        "activityLevel": dto.activityLevel or "MODERATE",
        "createdAt": now,
        "updatedAt": now,
    }

    user_doc = {
        "id": user_id,
        "name": dto.name,
        "email": email_clean,
        "username": dto.username.lower().strip() if dto.username else None,
        "passwordHash": pw_hash,
        "role": "CUSTOMER",
        "status": "ACTIVE",
        "timezone": dto.timezone or "Asia/Kolkata",
        "preferredLanguage": dto.preferredLanguage or "en",
        "profile": profile,
        "createdAt": now,
        "updatedAt": now,
    }

    await db.users.insert_one(user_doc)

    token_payload = {"sub": user_id, "email": email_clean, "role": "CUSTOMER"}
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)

    user_doc.pop("passwordHash", None)
    user_doc.pop("_id", None)

    return {
        "user": user_doc,
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "tokens": {
            "accessToken": access_token,
            "refreshToken": refresh_token,
        },
    }

@router.post("/login")
async def login(dto: LoginDto):
    db = get_db()
    email_clean = dto.email.lower().strip()

    user = await db.users.find_one({"email": email_clean})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    pw_hash = user.get("passwordHash") or user.get("password_hash")
    if not pw_hash or not verify_password(dto.password, pw_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user_id = user.get("id") or str(user.get("_id"))
    token_payload = {"sub": user_id, "email": user["email"], "role": user.get("role", "CUSTOMER")}
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)

    user.pop("passwordHash", None)
    user.pop("password_hash", None)
    user.pop("_id", None)

    return {
        "user": user,
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "tokens": {
            "accessToken": access_token,
            "refreshToken": refresh_token,
        },
    }

@router.post("/refresh")
async def refresh_token_endpoint(dto: RefreshTokenDto):
    payload = decode_token(dto.refreshToken)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = payload["sub"]
    token_payload = {"sub": user_id, "email": payload.get("email"), "role": payload.get("role", "CUSTOMER")}
    access_token = create_access_token(token_payload)
    new_refresh = create_refresh_token(token_payload)

    return {
        "accessToken": access_token,
        "refreshToken": new_refresh,
        "tokens": {
            "accessToken": access_token,
            "refreshToken": new_refresh,
        },
    }

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    user = current_user.copy()
    user.pop("passwordHash", None)
    user.pop("password_hash", None)
    user.pop("_id", None)
    return user

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    return {"message": "Successfully logged out"}
