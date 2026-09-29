from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class MacroSummary(BaseModel):
    proteinG: float = 0.0
    carbsG: float = 0.0
    fatG: float = 0.0
    fiberG: float = 0.0

class CalorieSummary(BaseModel):
    consumed: float = 0.0
    burned: float = 0.0
    net: float = 0.0
    target: float = 2000.0
    remaining: float = 2000.0

class HydrationSummary(BaseModel):
    consumedMl: float = 0.0
    targetMl: float = 2500.0
    percent: int = 0

class SleepSummary(BaseModel):
    totalMinutes: float = 0.0
    targetMinutes: float = 480.0
    quality: str = "GOOD"

class WeightSummary(BaseModel):
    currentKg: float = 70.0
    targetKg: Optional[float] = None
    deltaKg: float = 0.0
    trend: str = "STABLE"

class TodayDashboardResponse(BaseModel):
    date: str
    calories: CalorieSummary
    macros: MacroSummary
    hydration: HydrationSummary
    sleep: SleepSummary
    weight: WeightSummary
    recentLogs: List[Dict[str, Any]] = Field(default_factory=list)
