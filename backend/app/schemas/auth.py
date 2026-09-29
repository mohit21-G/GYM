from typing import Optional, Any
from pydantic import BaseModel, EmailStr, Field

class RegisterDto(BaseModel):
    name: str = Field(..., max_length=100)
    email: EmailStr
    username: Optional[str] = None
    password: str = Field(..., min_length=6)
    timezone: Optional[str] = "Asia/Kolkata"
    preferredLanguage: Optional[str] = "en"
    age: Optional[int] = None
    gender: Optional[str] = "MALE"
    heightCm: Optional[float] = None
    currentWeightKg: Optional[float] = None
    targetWeightKg: Optional[float] = None
    activityLevel: Optional[str] = "MODERATE"

class LoginDto(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenDto(BaseModel):
    refreshToken: str

class UserProfileDto(BaseModel):
    id: Optional[str] = None
    userId: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = "MALE"
    heightCm: Optional[float] = None
    currentWeightKg: Optional[float] = None
    targetWeightKg: Optional[float] = None
    dailyCalorieTarget: Optional[int] = 2000
    dailyWaterMlTarget: Optional[int] = 2500
    dailySleepMinutesTarget: Optional[int] = 480
    activityLevel: Optional[str] = "MODERATE"

class UserResponseDto(BaseModel):
    id: str
    name: str
    email: str
    username: Optional[str] = None
    role: str = "CUSTOMER"
    status: str = "ACTIVE"
    timezone: str = "Asia/Kolkata"
    preferredLanguage: str = "en"
    profile: Optional[UserProfileDto] = None

class AuthResponseDto(BaseModel):
    user: UserResponseDto
    accessToken: str
    refreshToken: str
