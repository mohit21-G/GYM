from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SendMessageDto(BaseModel):
    message: str
    sessionId: Optional[str] = None

class ChatUiDto(BaseModel):
    type: str = "LOG_RESULT"
    cards: Optional[List[Dict[str, Any]]] = None
    groupedFoodCards: Optional[List[Dict[str, Any]]] = None
    dailyNutritionSummary: Optional[Dict[str, Any]] = None

class ChatResponsePayload(BaseModel):
    success: bool = True
    sessionId: str
    message: str
    data: Optional[Any] = None
    ui: Optional[Dict[str, Any]] = None

class ChatMessageItem(BaseModel):
    id: str
    sessionId: str
    sender: str
    message: str
    rawEntities: Optional[Any] = None
    detectedIntent: Optional[str] = None
    createdAt: str
