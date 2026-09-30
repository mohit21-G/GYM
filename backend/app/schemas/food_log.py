from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class FoodItemInput(BaseModel):
    food: str
    quantity: Optional[float] = 1.0
    unit: Optional[str] = "serving"
    mealType: Optional[str] = "—"
    is_recognized: Optional[bool] = True
    has_explicit_quantity: Optional[bool] = True
    has_explicit_time: Optional[bool] = False
    requires_clarification: Optional[bool] = False
    clarification_reason: Optional[str] = None
    logged_at: Optional[str] = None
    raw_text: Optional[str] = None

class CreateFoodLogDto(BaseModel):
    foodName: str
    foodId: Optional[str] = None
    mealType: Optional[str] = "SNACK"
    quantity: float = 1.0
    unit: str = "serving"
    calories: Optional[float] = 0.0
    proteinG: Optional[float] = 0.0
    carbsG: Optional[float] = 0.0
    fatG: Optional[float] = 0.0
    fiberG: Optional[float] = 0.0
    notes: Optional[str] = None
    source: Optional[str] = "MANUAL"
    loggedAt: Optional[str] = None

class UpdateFoodLogDto(BaseModel):
    foodName: Optional[str] = None
    mealType: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    calories: Optional[float] = None
    proteinG: Optional[float] = None
    carbsG: Optional[float] = None
    fatG: Optional[float] = None
    fiberG: Optional[float] = None
    notes: Optional[str] = None
    loggedAt: Optional[str] = None

class FoodLogEntrySummary(BaseModel):
    id: str
    foodMasterId: Optional[str] = None
    foodName: str
    quantity: float
    unit: str
    calories: float
    mealType: str
    loggedAt: str
    timeFormatted: str
    hasExplicitTime: bool = False
    macros: Dict[str, float] = Field(default_factory=dict)

class GroupedFoodCard(BaseModel):
    foodKey: str
    foodMasterId: Optional[str] = None
    foodName: str
    categoryName: Optional[str] = None
    icon: Optional[str] = "utensils"
    imageUrl: Optional[str] = None
    totalQuantity: float
    unit: str
    totalCalories: float
    entryCount: int
    macros: Dict[str, float] = Field(default_factory=dict)
    entries: List[FoodLogEntrySummary] = Field(default_factory=list)

class DailyNutritionSummaryData(BaseModel):
    date: str
    totalCalories: float = 0.0
    targetCalories: float = 2000.0
    remainingCalories: float = 0.0
    percentOfTarget: int = 0
    macros: Dict[str, float] = Field(default_factory=dict)
    totalEntries: int = 0
    totalEntriesCount: Optional[int] = None
    distinctFoodsCount: int = 0
    totalProteinG: Optional[float] = 0.0
    totalCarbsG: Optional[float] = 0.0
    totalFatG: Optional[float] = 0.0
    totalFiberG: Optional[float] = 0.0

class FoodLoggingResult(BaseModel):
    success: bool
    requiresClarification: bool = False
    clarificationQuestion: Optional[str] = None
    loggedItems: List[Dict[str, Any]] = Field(default_factory=list)
    currentGroupedFoodCards: List[GroupedFoodCard] = Field(default_factory=list)
    groupedFoodCards: List[GroupedFoodCard] = Field(default_factory=list)
    dailyNutritionSummary: DailyNutritionSummaryData
    mealTotals: Dict[str, float] = Field(default_factory=dict)
    dailyProgress: Dict[str, Any] = Field(default_factory=dict)
    replyText: str
