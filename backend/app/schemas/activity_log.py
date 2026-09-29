from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class CreateActivityLogDto(BaseModel):
    activity: Optional[str] = None
    activityName: Optional[str] = None
    durationMinutes: Optional[float] = None
    duration: Optional[float] = None
    caloriesBurned: Optional[float] = None
    intensity: Optional[str] = "MEDIUM"
    distanceKm: Optional[float] = None
    notes: Optional[str] = None
    source: Optional[str] = "MANUAL"
    loggedAt: Optional[str] = None

class CreateWeightLogDto(BaseModel):
    weightKg: float
    notes: Optional[str] = None
    source: Optional[str] = "MANUAL"
    loggedAt: Optional[str] = None

class CreateSleepLogDto(BaseModel):
    durationMinutes: Optional[float] = None
    quality: Optional[str] = "GOOD"
    startTime: Optional[str] = None
    endTime: Optional[str] = None
    notes: Optional[str] = None
    source: Optional[str] = "MANUAL"
    loggedAt: Optional[str] = None

class CreateHydrationLogDto(BaseModel):
    amountMl: float
    notes: Optional[str] = None
    source: Optional[str] = "MANUAL"
    loggedAt: Optional[str] = None
