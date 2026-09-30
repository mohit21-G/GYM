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

    # Pre-fetch all active food logs for this user to reconcile any message food cards with the database truth
    active_logs_cursor = db.daily_food_logs.find({"user_id": user_id})
    active_logs = await active_logs_cursor.to_list(length=1000)
    active_logs_map = {}
    for d in active_logs:
        lid = str(d.get("id") or d.get("_id"))
        active_logs_map[lid] = d
        if d.get("id"):
            active_logs_map[str(d["id"])] = d
        if d.get("_id"):
            active_logs_map[str(d["_id"])] = d

    cursor = db.conversation_messages.find({"session_id": session_id}).sort("created_at", 1)
    messages = await cursor.to_list(length=500)

    results = []
    for m in messages:
        raw_ent = m.get("raw_entities")
        if isinstance(raw_ent, str):
            try:
                raw_ent = json.loads(raw_ent)
            except Exception:
                pass

        if raw_ent and isinstance(raw_ent, dict) and "groupedFoodCards" in raw_ent:
            from datetime import datetime, timezone
            from ..services.food_service import FoodService
            from ..services.time_service import TimeService

            cards = raw_ent.get("groupedFoodCards", [])
            new_cards = []
            for card in cards:
                entries = card.get("entries", [])
                new_entries = []
                for entry in entries:
                    eid = str(entry.get("id", ""))
                    if eid in active_logs_map:
                        live_doc = active_logs_map[eid]
                        dt = live_doc.get("logged_at") or live_doc.get("created_at") or datetime.now(timezone.utc)
                        has_exp = live_doc.get("has_explicit_time", False)
                        tf = FoodService.format_time(dt) if has_exp else ""
                        new_entries.append({
                            **entry,
                            "foodName": live_doc.get("food_name"),
                            "foodMasterId": live_doc.get("food_id"),
                            "quantity": live_doc.get("quantity_amount"),
                            "unit": live_doc.get("quantity_unit"),
                            "calories": live_doc.get("calories"),
                            "mealType": live_doc.get("meal_type", "—"),
                            "timeFormatted": tf,
                            "macros": {
                                "proteinG": live_doc.get("protein_g", 0.0),
                                "carbsG": live_doc.get("carbs_g", 0.0),
                                "fatG": live_doc.get("fat_g", 0.0),
                                "fiberG": live_doc.get("fiber_g", 0.0),
                            },
                        })
                if new_entries:
                    total_qty = sum(float(e.get("quantity", 0)) for e in new_entries)
                    total_cal = sum(float(e.get("calories", 0)) for e in new_entries)
                    total_p = sum(float(e.get("macros", {}).get("proteinG", 0)) for e in new_entries)
                    total_c = sum(float(e.get("macros", {}).get("carbsG", 0)) for e in new_entries)
                    total_f = sum(float(e.get("macros", {}).get("fatG", 0)) for e in new_entries)
                    total_fib = sum(float(e.get("macros", {}).get("fiberG", 0)) for e in new_entries)

                    first_entry = new_entries[0]
                    new_cards.append({
                        **card,
                        "foodName": first_entry.get("foodName", card.get("foodName")),
                        "foodMasterId": first_entry.get("foodMasterId", card.get("foodMasterId")),
                        "foodKey": f"food_{first_entry.get('foodMasterId') or first_entry.get('foodName', '').lower()}",
                        "icon": FoodService.resolve_food_icon(first_entry.get("foodName", "")),
                        "totalQuantity": int(total_qty) if total_qty.is_integer() else round(total_qty, 1),
                        "totalCalories": round(total_cal),
                        "entryCount": len(new_entries),
                        "unit": first_entry.get("unit", card.get("unit")),
                        "macros": {
                            "proteinG": round(total_p, 1),
                            "carbsG": round(total_c, 1),
                            "fatG": round(total_f, 1),
                            "fiberG": round(total_fib, 1),
                        },
                        "entries": new_entries,
                    })

            raw_ent["groupedFoodCards"] = new_cards
            
            # Recalculate dailyNutritionSummary for this message
            msg_date = TimeService.get_current_local_date_str()
            if m.get("created_at"):
                try:
                    c_dt = m["created_at"] if isinstance(m["created_at"], datetime) else datetime.fromisoformat(str(m["created_at"]).replace("Z", "+00:00"))
                    msg_date = c_dt.astimezone(TimeService.get_timezone()).strftime("%Y-%m-%d")
                except Exception:
                    pass
            daily_sum_res = await FoodService.get_daily_grouped_food_cards(user_id, msg_date)
            raw_ent["dailyNutritionSummary"] = daily_sum_res["dailyNutritionSummary"].model_dump()

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
