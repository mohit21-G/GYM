import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from ..database import get_db
from ..services.auth_service import get_current_user

router = APIRouter(prefix="/users", tags=["User Profile"])

class UpdateProfileDto(BaseModel):
    name: Optional[str] = None
    timezone: Optional[str] = None
    preferredLanguage: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    heightCm: Optional[float] = None
    currentWeightKg: Optional[float] = None
    targetWeightKg: Optional[float] = None
    dailyCalorieTarget: Optional[int] = None
    dailyWaterMlTarget: Optional[int] = None
    dailySleepMinutesTarget: Optional[int] = None
    activityLevel: Optional[str] = None

@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("id") or str(current_user.get("_id"))
    db = get_db()
    user = await db.users.find_one({"id": user_id}) or current_user

    # Format user response, excluding password hash
    profile = user.get("profile") or {}
    return {
        "id": user.get("id"),
        "name": user.get("name"),
        "email": user.get("email"),
        "username": user.get("username"),
        "role": user.get("role", "CUSTOMER"),
        "timezone": user.get("timezone", "Asia/Kolkata"),
        "preferredLanguage": user.get("preferredLanguage", "en"),
        "profile": {
            "age": profile.get("age"),
            "gender": profile.get("gender", "MALE"),
            "heightCm": profile.get("heightCm"),
            "currentWeightKg": profile.get("currentWeightKg", 70.0),
            "targetWeightKg": profile.get("targetWeightKg"),
            "dailyCalorieTarget": profile.get("dailyCalorieTarget", 2000),
            "dailyWaterMlTarget": profile.get("dailyWaterMlTarget", 2500),
            "dailySleepMinutesTarget": profile.get("dailySleepMinutesTarget", 480),
            "activityLevel": profile.get("activityLevel", "MODERATE"),
        },
    }

@router.patch("/profile")
async def update_profile(
    dto: UpdateProfileDto,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user.get("id") or str(current_user.get("_id"))
    db = get_db()
    now = datetime.now(timezone.utc)

    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    existing_profile = user.get("profile") or {}

    update_fields: Dict[str, Any] = {"updatedAt": now}
    profile_updates: Dict[str, Any] = {"updatedAt": now}

    if dto.name is not None:
        update_fields["name"] = dto.name.strip()
    if dto.timezone is not None:
        update_fields["timezone"] = dto.timezone
    if dto.preferredLanguage is not None:
        update_fields["preferredLanguage"] = dto.preferredLanguage

    # Profile subdocument fields
    if dto.age is not None:
        profile_updates["age"] = dto.age
    if dto.gender is not None:
        profile_updates["gender"] = dto.gender
    if dto.heightCm is not None:
        profile_updates["heightCm"] = dto.heightCm
    if dto.currentWeightKg is not None:
        profile_updates["currentWeightKg"] = dto.currentWeightKg
    if dto.targetWeightKg is not None:
        profile_updates["targetWeightKg"] = dto.targetWeightKg
    if dto.dailyCalorieTarget is not None:
        profile_updates["dailyCalorieTarget"] = dto.dailyCalorieTarget
    if dto.dailyWaterMlTarget is not None:
        profile_updates["dailyWaterMlTarget"] = dto.dailyWaterMlTarget
    if dto.dailySleepMinutesTarget is not None:
        profile_updates["dailySleepMinutesTarget"] = dto.dailySleepMinutesTarget
    if dto.activityLevel is not None:
        profile_updates["activityLevel"] = dto.activityLevel

    # Merge profile updates
    merged_profile = {**existing_profile, **profile_updates}
    update_fields["profile"] = merged_profile

    await db.users.update_one(
        {"id": user_id},
        {"$set": update_fields}
    )

    updated_user = await db.users.find_one({"id": user_id})
    return {
        "id": updated_user.get("id"),
        "name": updated_user.get("name"),
        "email": updated_user.get("email"),
        "username": updated_user.get("username"),
        "role": updated_user.get("role", "CUSTOMER"),
        "timezone": updated_user.get("timezone", "Asia/Kolkata"),
        "preferredLanguage": updated_user.get("preferredLanguage", "en"),
        "profile": updated_user.get("profile", {}),
    }
