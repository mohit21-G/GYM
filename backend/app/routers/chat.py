import json
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from ..database import get_db
from ..schemas.chat import SendMessageDto, ChatResponsePayload
from ..services.auth_service import get_current_user
from ..services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chatbot"])

@router.post("/message")
async def send_message(
    dto: SendMessageDto,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user.get("id") or str(current_user.get("_id"))
    result = await ChatService.handle_user_message(
        user_id=user_id,
        message=dto.message,
        session_id_input=dto.sessionId,
    )
    return result

@router.get("/sessions")
async def get_user_sessions(
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    cursor = db.chat_sessions.find({"user_id": user_id, "is_archived": False}).sort("updated_at", -1)
    sessions = await cursor.to_list(length=100)

    results = []
    for s in sessions:
        results.append({
            "id": s["id"],
            "title": s.get("title", "New Conversation"),
            "createdAt": s.get("created_at").isoformat() if hasattr(s.get("created_at"), "isoformat") else str(s.get("created_at")),
            "updatedAt": s.get("updated_at").isoformat() if hasattr(s.get("updated_at"), "isoformat") else str(s.get("updated_at")),
        })
    return results

@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))

    # Verify session ownership
    session = await db.chat_sessions.find_one({"id": session_id, "user_id": user_id})
    if not session:
        return []

    cursor = db.conversation_messages.find({"session_id": session_id}).sort("created_at", 1)
    messages = await cursor.to_list(length=500)

    results = []
    for m in messages:
        raw_ent = m.get("raw_entities")
        if isinstance(raw_ent, dict):
            raw_ent_str = json.dumps(raw_ent)
        else:
            raw_ent_str = str(raw_ent) if raw_ent else None

        results.append({
            "id": m.get("id") or str(m.get("_id")),
            "sessionId": session_id,
            "sender": m.get("sender", "USER"),
            "message": m.get("message", ""),
            "rawEntities": raw_ent_str,
            "detectedIntent": m.get("detected_intent"),
            "createdAt": m.get("created_at").isoformat() if hasattr(m.get("created_at"), "isoformat") else str(m.get("created_at")),
        })
    return results
