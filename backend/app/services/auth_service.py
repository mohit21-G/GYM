import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..config import settings
from ..database import get_db

security = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )
    token = credentials.credentials
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )
    
    user_id = payload["sub"]
    db = get_db()
    user = await db.users.find_one({"$or": [{"id": user_id}, {"user_id": user_id}]})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user

async def get_current_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    role = current_user.get("role", "CUSTOMER")
    if role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Admin role required",
        )
    return current_user

class AuthService:
    hash_password = staticmethod(hash_password)
    verify_password = staticmethod(verify_password)
    create_access_token = staticmethod(create_access_token)
    create_refresh_token = staticmethod(create_refresh_token)
    decode_token = staticmethod(decode_token)

    @classmethod
    async def login_user(cls, email: str, password: str) -> Dict[str, Any]:
        db = get_db()
        email_clean = email.lower().strip()
        user = await db.users.find_one({"email": email_clean})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        pw_hash = user.get("passwordHash") or user.get("password_hash")
        if not pw_hash or not verify_password(password, pw_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        user_id = user.get("id") or str(user.get("_id"))
        role = user.get("role", "CUSTOMER")
        token_payload = {"sub": user_id, "email": user["email"], "role": role}
        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token(token_payload)

        user_clean = user.copy()
        user_clean.pop("passwordHash", None)
        user_clean.pop("password_hash", None)
        user_clean.pop("_id", None)

        return {
            "user": user_clean,
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "tokens": {
                "accessToken": access_token,
                "refreshToken": refresh_token,
            }
        }

    @classmethod
    async def refresh_access_token(cls, refresh_token: str) -> Dict[str, Any]:
        payload = decode_token(refresh_token)
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
            }
        }
