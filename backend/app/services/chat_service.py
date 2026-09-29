import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from ..database import get_db
from .ai_service import AIService
from .food_service import FoodService
from .activity_service import ActivityService
from ..schemas.food_log import FoodItemInput

logger = logging.getLogger("chat_service")

class ChatService:
    @staticmethod
    async def get_or_create_session(user_id: str, session_id: Optional[str] = None) -> str:
        db = get_db()
        if session_id:
            existing = await db.chat_sessions.find_one({"id": session_id, "user_id": user_id})
            if existing:
                return existing["id"]

        # Find latest active session
        latest = await db.chat_sessions.find_one({"user_id": user_id, "is_archived": False}, sort=[("updated_at", -1)])
        if latest:
            return latest["id"]

        new_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        await db.chat_sessions.insert_one({
            "id": new_id,
            "user_id": user_id,
            "title": "Fitness Conversation",
            "is_archived": False,
            "created_at": now,
            "updated_at": now,
        })
        return new_id

    @staticmethod
    async def handle_user_message(user_id: str, message: str, session_id_input: Optional[str] = None) -> Dict[str, Any]:
        db = get_db()
        now = datetime.now(timezone.utc)
        session_id = await ChatService.get_or_create_session(user_id, session_id_input)

        # 1. Save User Message
        user_msg_id = str(uuid.uuid4())
        await db.conversation_messages.insert_one({
            "id": user_msg_id,
            "session_id": session_id,
            "sender": "USER",
            "message": message,
            "created_at": now,
        })

        # 2. Load recent sliding-window conversation history
        cursor = db.conversation_messages.find({"session_id": session_id}).sort("created_at", -1).limit(6)
        recent_docs = await cursor.to_list(length=6)
        recent_docs.reverse()
        history = [{"role": "user" if d["sender"] == "USER" else "assistant", "content": d["message"]} for d in recent_docs]

        # 3. Call AI Intent Extractor
        ai_res = await AIService.process_message(message, history)
        intent = ai_res.get("intent", "GENERAL_CHAT")
        entities = ai_res.get("entities", {})

        result_payload = await ChatService.route_intent(user_id, session_id, intent, entities, ai_res, user_message=message)

        # 4. Save Assistant Message with structured cards for session reload
        assistant_msg_id = str(uuid.uuid4())
        raw_entities = {}
        if result_payload.get("ui", {}).get("groupedFoodCards"):
            raw_entities = {
                "intent": intent,
                "groupedFoodCards": result_payload["ui"]["groupedFoodCards"],
                "dailyNutritionSummary": result_payload["ui"].get("dailyNutritionSummary"),
                "cards": result_payload["ui"].get("cards"),
            }
        else:
            raw_entities = entities

        await db.conversation_messages.insert_one({
            "id": assistant_msg_id,
            "session_id": session_id,
            "sender": "ASSISTANT",
            "message": result_payload["message"],
            "raw_entities": raw_entities,
            "detected_intent": intent,
            "created_at": datetime.now(timezone.utc),
        })

        # Update session timestamp
        await db.chat_sessions.update_one(
            {"id": session_id},
            {"$set": {"updated_at": datetime.now(timezone.utc)}}
        )

        return result_payload

    @staticmethod
    async def route_intent(
        user_id: str,
        session_id: str,
        intent: str,
        entities: Dict[str, Any],
        ai_res: Dict[str, Any],
        user_message: str = "",
    ) -> Dict[str, Any]:
        db = get_db()
        now = datetime.now(timezone.utc)
        today_str = now.strftime("%Y-%m-%d")

        # Infer meal type from user message explicitly if present
        msg_lower = (user_message or "").lower()
        inferred_meal = None
        if any(w in msg_lower for w in ["morning", "breakfast", "savar", "savare", "saware", "sawar", "savaar", "subah", "subha", "nasto", "nashta", "સવાર", "સવારે", "નાસ્તો", "सुबह", "नाश्ता"]):
            inferred_meal = "BREAKFAST"
        elif any(w in msg_lower for w in ["dinner", "sanj", "sanje", "saanj", "saanje", "sanju", "shaam", "sham", "raat", "raate", "raatri", "valoo", "valo", "vaalu", "વાળુ", "વાળું", "સાંજ", "સાંજે", "રાત", "રાત્રે", "रात", "शाम"]):
            inferred_meal = "DINNER"
        elif any(w in msg_lower for w in ["snack", "snacks", "chaai", "tea", "ચા"]):
            inferred_meal = "SNACK"
        elif any(w in msg_lower for w in ["lunch", "bapor", "bapore", "dopahar", "બપોર", "બપોરે"]):
            inferred_meal = "LUNCH"

        # Multi-log routing (foods + workouts or hydration)
        has_food = bool(entities.get("foodItems") or entities.get("food"))
        has_act = bool(entities.get("activityItems") or entities.get("activity"))
        has_water = bool(entities.get("waterAmount") or entities.get("hydration"))

        if intent == "CREATE_MULTI_LOG" or (has_food and has_act):
            return await ChatService.handle_multi_log(user_id, session_id, entities, ai_res, user_message=user_message, inferred_meal=inferred_meal)

        # 1. CREATE_FOOD_LOG
        if intent == "CREATE_FOOD_LOG":
            raw_foods = entities.get("foodItems") or []
            if not raw_foods and entities.get("food"):
                raw_foods = [{
                    "food": entities.get("food"),
                    "quantity": entities.get("quantity", 1),
                    "unit": entities.get("unit", "serving"),
                    "mealType": inferred_meal or entities.get("mealType") or entities.get("meal_type") or "LUNCH"
                }]

            items = [
                FoodItemInput(
                    food=f.get("food") or f.get("name", "Food"),
                    quantity=f.get("quantity", 1),
                    unit=f.get("unit", "serving"),
                    mealType=inferred_meal or f.get("mealType") or entities.get("mealType") or entities.get("meal_type") or "LUNCH"
                )
                for f in raw_foods
            ]
            detected_meal = inferred_meal
            if not detected_meal:
                for it in items:
                    m = getattr(it, "mealType", None)
                    if m and m != "LUNCH":
                        detected_meal = m
                        break
            if not detected_meal and items:
                detected_meal = getattr(items[0], "mealType", None) or "LUNCH"

            food_result = await FoodService.process_and_log_food(
                user_id, items, meal_type_override=detected_meal, log_date_str=today_str
            )

            cards = [
                {
                    "type": "FOOD",
                    "title": item.get("food_name"),
                    "subtitle": f"{item.get('quantity_amount')} {item.get('quantity_unit')} ({item.get('meal_type')})",
                    "metric": f"{int(item.get('calories', 0))} kcal",
                    "macros": {
                        "protein": f"{item.get('protein_g', 0)}g",
                        "carbs": f"{item.get('carbs_g', 0)}g",
                        "fat": f"{item.get('fat_g', 0)}g",
                    },
                }
                for item in food_result.loggedItems
            ]

            return {
                "success": True,
                "sessionId": session_id,
                "message": food_result.replyText,
                "data": food_result.model_dump(),
                "ui": {
                    "type": "FOOD_LOG_CARDS",
                    "cards": cards,
                    "groupedFoodCards": [c.model_dump() for c in food_result.groupedFoodCards],
                    "dailyNutritionSummary": food_result.dailyNutritionSummary.model_dump(),
                },
            }

        # 2. UPDATE_FOOD_LOG
        if intent == "UPDATE_FOOD_LOG":
            target_food = entities.get("targetFood") or entities.get("food") or (entities.get("foodItems", [{}])[0].get("food") if entities.get("foodItems") else "food")
            new_qty = float(entities.get("newQuantity") or entities.get("quantity") or (entities.get("foodItems", [{}])[0].get("quantity") if entities.get("foodItems") else 1.0))
            unit = entities.get("unit")

            food_result = await FoodService.update_food_log(user_id, target_food, new_qty, unit, today_str)
            return {
                "success": True,
                "sessionId": session_id,
                "message": food_result.replyText,
                "data": food_result.model_dump(),
                "ui": {
                    "type": "FOOD_LOG_CARDS",
                    "groupedFoodCards": [c.model_dump() for c in food_result.groupedFoodCards],
                    "dailyNutritionSummary": food_result.dailyNutritionSummary.model_dump(),
                },
            }

        # 3. DELETE_FOOD_LOG
        if intent == "DELETE_FOOD_LOG":
            target_food = entities.get("targetFood") or entities.get("food") or (entities.get("foodItems", [{}])[0].get("food") if entities.get("foodItems") else "food")
            food_result = await FoodService.delete_food_log(user_id, target_food, today_str)
            return {
                "success": True,
                "sessionId": session_id,
                "message": food_result.replyText,
                "data": food_result.model_dump(),
                "ui": {
                    "type": "FOOD_LOG_CARDS",
                    "groupedFoodCards": [c.model_dump() for c in food_result.groupedFoodCards],
                    "dailyNutritionSummary": food_result.dailyNutritionSummary.model_dump(),
                },
            }

        # 4. QUERY_FOOD_LOG / GET_TODAY_SUMMARY
        if intent in ["QUERY_FOOD_LOG", "GET_TODAY_SUMMARY"]:
            summary_result = await FoodService.get_daily_grouped_food_cards(user_id, today_str)
            cards = summary_result["groupedFoodCards"]
            nut = summary_result["dailyNutritionSummary"]

            if nut.totalCalories > 0:
                reply = (
                    f"Today you have logged {nut.totalCalories} kcal across {nut.distinctFoodsCount} distinct foods "
                    f"({nut.percentOfTarget}% of your {nut.targetCalories} kcal goal). "
                    f"Remaining budget: {nut.remainingCalories} kcal. "
                    f"Macros: {nut.totalProteinG}g Protein, {nut.totalCarbsG}g Carbs, {nut.totalFatG}g Fat."
                )
            else:
                reply = "You haven't logged any meals yet today. Tell me what you ate and I will track it for you!"

            return {
                "success": True,
                "sessionId": session_id,
                "message": reply,
                "data": {
                    "groupedFoodCards": [c.model_dump() for c in cards],
                    "dailyNutritionSummary": nut.model_dump(),
                },
                "ui": {
                    "type": "FOOD_LOG_CARDS",
                    "groupedFoodCards": [c.model_dump() for c in cards],
                    "dailyNutritionSummary": nut.model_dump(),
                },
            }

        # 5. CREATE_ACTIVITY_LOG
        if intent == "CREATE_ACTIVITY_LOG":
            act_data = entities.get("activity") if isinstance(entities.get("activity"), dict) else {
                "activity": entities.get("activity", "Workout"),
                "durationMinutes": entities.get("durationMinutes") or entities.get("duration", 30),
                "intensity": entities.get("intensity", "MEDIUM"),
            }
            res = await ActivityService.process_and_log_activity(user_id, act_data, today_str)
            calc = res["calculation"]
            return {
                "success": True,
                "sessionId": session_id,
                "message": res["replyText"],
                "data": res,
                "ui": {
                    "type": "LOG_RESULT",
                    "cards": [{
                        "type": "ACTIVITY",
                        "title": calc["activityName"],
                        "subtitle": f"{int(calc['durationMinutes'])} mins · MET {calc['metValue']}",
                        "metric": f"{int(calc['caloriesBurned'])} kcal burned",
                    }],
                },
            }

        # 6. CREATE_HYDRATION_LOG
        if intent == "CREATE_HYDRATION_LOG":
            amount = float(entities.get("waterAmount") or entities.get("amountMl") or 250.0)
            log_id = str(uuid.uuid4())
            await db.hydration_logs.insert_one({
                "id": log_id,
                "user_id": user_id,
                "amount_ml": amount,
                "log_date": today_str,
                "created_at": now,
            })
            
            cursor = db.hydration_logs.find({"user_id": user_id, "log_date": today_str})
            logs = await cursor.to_list(length=100)
            total_water = sum(l.get("amount_ml", 0) for l in logs)

            return {
                "success": True,
                "sessionId": session_id,
                "message": f"Logged {int(amount)} ml water. Today's total: {int(total_water)} / 2500 ml.",
                "data": {"amountMl": amount, "totalMl": total_water},
                "ui": {
                    "type": "LOG_RESULT",
                    "cards": [{
                        "type": "HYDRATION",
                        "title": "Hydration Logged",
                        "subtitle": f"+{int(amount)} ml",
                        "metric": f"{int(total_water)} ml",
                        "log": {"amountMl": amount},
                        "dailySummary": {"totalMl": total_water, "targetMl": 2500},
                    }],
                },
            }

        # 7. CREATE_WEIGHT_LOG
        if intent == "CREATE_WEIGHT_LOG":
            weight = float(entities.get("weightKg") or entities.get("weight") or 70.0)
            log_id = str(uuid.uuid4())
            await db.weight_logs.insert_one({
                "id": log_id,
                "user_id": user_id,
                "weight_kg": weight,
                "log_date": today_str,
                "created_at": now,
            })
            await db.users.update_one({"id": user_id}, {"$set": {"profile.currentWeightKg": weight}})

            return {
                "success": True,
                "sessionId": session_id,
                "message": f"Logged body weight of {weight} kg.",
                "data": {"weightKg": weight},
                "ui": {
                    "type": "LOG_RESULT",
                    "cards": [{
                        "type": "WEIGHT",
                        "title": "Weight Logged",
                        "metric": f"{weight} kg",
                        "log": {"weightKg": weight},
                    }],
                },
            }

        # 8. CREATE_SLEEP_LOG
        if intent == "CREATE_SLEEP_LOG":
            mins = float(entities.get("durationMinutes") or entities.get("duration", 480))
            quality = entities.get("quality", "GOOD")
            log_id = str(uuid.uuid4())
            await db.sleep_logs.insert_one({
                "id": log_id,
                "user_id": user_id,
                "duration_minutes": mins,
                "quality": quality,
                "log_date": today_str,
                "created_at": now,
            })
            h = int(mins // 60)
            m = int(mins % 60)

            return {
                "success": True,
                "sessionId": session_id,
                "message": f"Recorded {h}h {m}m of {quality.lower()} sleep.",
                "data": {"durationMinutes": mins, "quality": quality},
                "ui": {
                    "type": "LOG_RESULT",
                    "cards": [{
                        "type": "SLEEP",
                        "title": "Sleep Recorded",
                        "metric": f"{h}h {m}m",
                        "log": {"durationMinutes": mins, "quality": quality},
                        "analysis": {"hours": h, "remainingMinutes": m, "quality": quality},
                    }],
                },
            }

        # 9. GENERAL_CHAT / Fallback
        reply_msg = ai_res.get("replyText") or "I am here to help you log your meals, track your workouts, and hit your fitness goals."
        return {
            "success": True,
            "sessionId": session_id,
            "message": reply_msg,
            "data": {},
            "ui": {"type": "TEXT"},
        }

    @staticmethod
    async def handle_multi_log(
        user_id: str,
        session_id: str,
        entities: Dict[str, Any],
        ai_res: Dict[str, Any],
        user_message: str = "",
        inferred_meal: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        today_str = now.strftime("%Y-%m-%d")
        cards = []
        summary_lines = []
        latest_food_result = None

        # 1. Process foods
        raw_foods = entities.get("foodItems") or []
        food_items_to_log = [f for f in raw_foods if (f.get("food") or f.get("name", "")).lower() not in ["water", "pani"]]
        if food_items_to_log:
            items = [
                FoodItemInput(
                    food=f.get("food") or f.get("name"),
                    quantity=f.get("quantity", 1),
                    unit=f.get("unit", "serving"),
                    mealType=inferred_meal or f.get("mealType") or "LUNCH"
                )
                for f in food_items_to_log
            ]
            detected_meal = inferred_meal
            if not detected_meal:
                for it in items:
                    m = getattr(it, "mealType", None)
                    if m and m != "LUNCH":
                        detected_meal = m
                        break
            if not detected_meal and items:
                detected_meal = getattr(items[0], "mealType", None) or "LUNCH"

            food_result = await FoodService.process_and_log_food(
                user_id, items, meal_type_override=detected_meal, log_date_str=today_str
            )
            latest_food_result = food_result

            for item in food_result.loggedItems:
                cards.append({
                    "type": "FOOD",
                    "title": item.get("food_name"),
                    "subtitle": f"{item.get('quantity_amount')} {item.get('quantity_unit')}",
                    "metric": f"{int(item.get('calories', 0))} kcal",
                })
            summary_lines.append(f"{int(food_result.mealTotals.get('calories', 0))} kcal across {len(food_result.loggedItems)} foods")

        # 2. Process workouts
        raw_acts = entities.get("activityItems") or ([entities.get("activity")] if entities.get("activity") else [])
        for act in raw_acts:
            act_data = act if isinstance(act, dict) else {"activity": str(act), "durationMinutes": 30}
            act_res = await ActivityService.process_and_log_activity(user_id, act_data, today_str)
            calc = act_res["calculation"]
            cards.append({
                "type": "ACTIVITY",
                "title": calc["activityName"],
                "subtitle": f"{int(calc['durationMinutes'])} mins · MET {calc['metValue']}",
                "metric": f"{int(calc['caloriesBurned'])} kcal burned",
            })
            summary_lines.append(f"{calc['activityName']} ({int(calc['durationMinutes'])}m, {int(calc['caloriesBurned'])} kcal)")

        reply = ai_res.get("replyText") or f"Logged your routine: {', '.join(summary_lines)}."
        return {
            "success": True,
            "sessionId": session_id,
            "message": reply,
            "data": {
                "cards": cards,
                "summary": summary_lines,
                "groupedFoodCards": [c.model_dump() for c in latest_food_result.groupedFoodCards] if latest_food_result else None,
                "dailyNutritionSummary": latest_food_result.dailyNutritionSummary.model_dump() if latest_food_result else None,
            },
            "ui": {
                "type": "LOG_RESULT",
                "cards": cards,
                "groupedFoodCards": [c.model_dump() for c in latest_food_result.groupedFoodCards] if latest_food_result else None,
                "dailyNutritionSummary": latest_food_result.dailyNutritionSummary.model_dump() if latest_food_result else None,
            },
        }
