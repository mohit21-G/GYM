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

class UpdateActivityLogDto(BaseModel):
    """All-optional patch DTO for editing an existing activity/workout log.
    Mirrors UpdateFoodLogDto in food_log.py so the frontend edit flow for
    activity cards matches the food-log edit pattern."""
    activity: Optional[str] = None
    durationMinutes: Optional[float] = None
    reps: Optional[int] = None
    sets: Optional[int] = None
    intensity: Optional[str] = None
    notes: Optional[str] = None
    loggedAt: Optional[str] = None

class UpdateHydrationLogDto(BaseModel):
    """All-optional patch DTO for editing an existing hydration log entry.

    `quantity` is the scoop count for supplement entries (Pre Workout / Whey
    Protein Powder mixed into water). When provided (or when beverageName is
    changed to/from a supplement name), nutrition (calories/protein/carbs/fat/
    fiber) is automatically recalculated from the canonical profile, the same
    way PATCH /food-logs/{id} recalculates nutrition on edit.
    """
    amountMl: Optional[float] = None
    beverageName: Optional[str] = None
    quantity: Optional[float] = None
    notes: Optional[str] = None
    loggedAt: Optional[str] = None
