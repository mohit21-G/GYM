import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from ..database import get_db
from .ai_service import AIService
from .food_service import FoodService
from .activity_service import ActivityService
from .dashboard_service import DashboardService
from .food_suggestion_service import FoodSuggestionService
from .fitness_advisory_service import FitnessAdvisoryService
from .agent_nlp import AgentNLP
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

        # Prevent duplicate logging when user repeats or double-submits a log message
        is_logging_intent = intent.startswith("CREATE_") or intent == "UPDATE_FOOD_LOG"
        if is_logging_intent and len(recent_docs) > 1:
            prev_user_msgs = [d for d in recent_docs[:-1] if d.get("sender") == "USER"]
            if prev_user_msgs:
                last_user_msg = prev_user_msgs[-1]
                past_dt = last_user_msg.get("created_at")
                if isinstance(past_dt, str):
                    try:
                        past_dt = datetime.fromisoformat(past_dt.replace("Z", "+00:00"))
                    except Exception:
                        past_dt = None
                if isinstance(past_dt, datetime):
                    dt1 = now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)
                    dt2 = past_dt if past_dt.tzinfo is not None else past_dt.replace(tzinfo=timezone.utc)
                    t_diff = (dt1 - dt2).total_seconds()
                else:
                    t_diff = 999.0
                norm_prev = AgentNLP.normalize_text(last_user_msg.get("message", "")).strip().lower()
                norm_curr = AgentNLP.normalize_text(message).strip().lower()
                if norm_prev == norm_curr and t_diff <= 30:
                    lang = AgentNLP.detect_language(message)
                    if lang in ["gu", "gu-Latn"]:
                        dup_msg = "તમે થોડીવાર પહેલા જ આ લોગ કર્યું છે! ડુપ્લિકેટ એન્ટ્રી અટકાવવા માટે ફરીથી ઉમેરવામાં આવ્યું નથી. તમારો આજનો રેકોર્ડ અને ડેશબોર્ડ અપ-ટૂ-ડેટ છે. 👍"
                    elif lang in ["hi", "hi-Latn"]:
                        dup_msg = "आपने कुछ ही देर पहले यह लॉग किया था! डुप्लीकेट एंट्री से बचने के लिए इसे दोबारा नहीं जोड़ा गया है। आपका आज का रिकॉर्ड और डैशबोर्ड बिल्कुल अपडेट है। 👍"
                    else:
                        dup_msg = "You just logged this a moment ago! To avoid duplicate entries, I didn't re-log it. Your daily records and dashboard are completely up to date. 👍"

                    today_str = now.strftime("%Y-%m-%d")
                    dashboard_data = await DashboardService.get_today_dashboard(user_id, today_str)
                    result_payload = {
                        "success": True,
                        "sessionId": session_id,
                        "message": dup_msg,
                        "data": dashboard_data,
                        "dashboard": dashboard_data,
                        "ui": {
                            "type": "SUMMARY",
                            "data": dashboard_data,
                        },
                    }
                    assistant_msg_id = str(uuid.uuid4())
                    await db.conversation_messages.insert_one({
                        "id": assistant_msg_id,
                        "session_id": session_id,
                        "sender": "ASSISTANT",
                        "message": dup_msg,
                        "raw_entities": {},
                        "detected_intent": "DUPLICATE_PREVENTED",
                        "created_at": datetime.now(timezone.utc),
                    })
                    return result_payload

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
        # 1. CREATE_FOOD_LOG
        if intent == "CREATE_FOOD_LOG":
            raw_foods = entities.get("foodItems") or []
            if not raw_foods and entities.get("food"):
                raw_foods = [{
                    "food": entities.get("food"),
                    "quantity": entities.get("quantity", 1),
                    "unit": entities.get("unit", "serving"),
                    "mealType": inferred_meal or entities.get("mealType") or entities.get("meal_type") or "LUNCH",
                    "is_recognized": entities.get("is_recognized", True),
                    "has_explicit_quantity": entities.get("has_explicit_quantity", True),
                    "requires_clarification": entities.get("requires_clarification", False),
                    "clarification_reason": entities.get("clarification_reason"),
                }]

            items = [
                FoodItemInput(
                    food=f.get("food") or f.get("name", "Food"),
                    quantity=f.get("quantity", 1),
                    unit=f.get("unit", "serving"),
                    mealType=inferred_meal or f.get("mealType") or entities.get("mealType") or entities.get("meal_type") or "LUNCH",
                    is_recognized=f.get("is_recognized", True),
                    has_explicit_quantity=f.get("has_explicit_quantity", True),
                    requires_clarification=f.get("requires_clarification", False),
                    clarification_reason=f.get("clarification_reason"),
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

            if food_result.requiresClarification:
                return {
                    "success": True,
                    "sessionId": session_id,
                    "message": food_result.replyText,
                    "data": food_result.model_dump(),
                    "ui": {
                        "type": "MESSAGE",
                        "requiresClarification": True,
                        "clarificationQuestion": food_result.clarificationQuestion,
                    },
                }

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

        lang = AgentNLP.detect_language(user_message or "")

        # 4. DAILY_SUMMARY
        if intent == "DAILY_SUMMARY":
            return await ChatService.handle_daily_summary(user_id, session_id, today_str, lang)

        # 5. QUERY_HYDRATION_LOG (e.g. "Aaj ketlu pani pidhu?", "How much water did I drink today?")
        if intent == "QUERY_HYDRATION_LOG":
            return await ChatService.handle_water_query(user_id, session_id, today_str, lang)

        # 6. FOOD_SUGGESTION
        if intent == "FOOD_SUGGESTION":
            return await ChatService.handle_food_suggestion(user_id, session_id, user_message, lang, today_str)

        # 7. WORKOUT_SUGGESTION
        if intent == "WORKOUT_SUGGESTION":
            return await ChatService.handle_workout_suggestion(user_id, session_id, user_message, lang, today_str)

        # 8. QUERY_FOOD_LOG / GET_TODAY_SUMMARY
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

        # 9. CREATE_ACTIVITY_LOG
        if intent == "CREATE_ACTIVITY_LOG":
            if ai_res.get("requiresClarification") or entities.get("requiresClarification"):
                if lang in ["gu", "gu-Latn"]:
                    clarify_text = "કસરત કરવા બદલ ખૂબ ખૂબ અભિનંદન! ચોક્કસ બર્ન થયેલી કેલરી ગણવા માટે, કૃપા કરીને જણાવો કે તમે કઈ કસરત કરી અને કેટલા સમય (મિનિટ) કે રેપ્સ કર્યા?"
                elif lang in ["hi", "hi-Latn"]:
                    clarify_text = "कसरत करने के लिए बहुत बढ़िया! सटीक कैलोरी बर्न की गणना के लिए, कृपया बताएं कि आपने कौन सी एक्सरसाइज की और कितने समय (मिनट) या कितने रेप्स किए?"
                else:
                    clarify_text = "Great job on working out! To calculate your calories burned accurately, could you please let me know which exercise you did and for how many minutes or reps?"

                return {
                    "success": True,
                    "sessionId": session_id,
                    "message": clarify_text,
                    "data": {},
                    "ui": {"type": "TEXT"},
                }

            activities = entities.get("activities")
            if not activities:
                act_data = entities.get("activity") if isinstance(entities.get("activity"), dict) else {
                    "activity": entities.get("activity", "Workout"),
                    "durationMinutes": entities.get("durationMinutes") or entities.get("duration", 30),
                    "reps": entities.get("reps"),
                    "sets": entities.get("sets"),
                    "intensity": entities.get("intensity", "MEDIUM"),
                }
                activities = [act_data]

            res = await ActivityService.process_and_log_activities(user_id, activities, today_str)
            dashboard_data = await DashboardService.get_today_dashboard(user_id, today_str)
            return {
                "success": True,
                "sessionId": session_id,
                "message": res["replyText"],
                "data": res,
                "dashboard": dashboard_data,
                "ui": {
                    "type": "LOG_RESULT",
                    "cards": res["cards"],
                },
            }

        # 10. CREATE_HYDRATION_LOG
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

            dashboard_data = await DashboardService.get_today_dashboard(user_id, today_str)
            hydration = dashboard_data["hydration"]
            total_water = hydration["amountMl"]
            target_water = hydration["targetMl"]
            remaining_water = hydration["remainingMl"]
            is_met = hydration["targetMet"]

            if is_met:
                if lang in ["gu", "gu-Latn"]:
                    reply = f"💧 **{int(amount)} ml** પાણી લોગ કર્યું! આજનું કુલ પાણી: **{int(total_water)} / {int(target_water)} ml** (100%). અભિનંદન! તમે આજનો વોટર ટાર્ગેટ સફળતાપૂર્વક પૂર્ણ કર્યો છે! 🎉"
                elif lang in ["hi", "hi-Latn"]:
                    reply = f"💧 **{int(amount)} ml** पानी लॉग किया गया! आज का कुल पानी: **{int(total_water)} / {int(target_water)} ml** (100%). बधाई हो! आपका आज का वॉटर टारगेट सफलतापूर्वक पूरा हुआ! 🎉"
                else:
                    reply = f"💧 Logged **{int(amount)} ml** water! Today's total: **{int(total_water)} / {int(target_water)} ml** (100%). Congratulations! You have successfully reached your daily hydration goal! 🎉"
            else:
                pct = hydration["percentTarget"]
                glasses_left = max(1, round(remaining_water / 250))
                if lang in ["gu", "gu-Latn"]:
                    reply = f"💧 **{int(amount)} ml** પાણી લોગ કર્યું! આજનું કુલ પાણી: **{int(total_water)} / {int(target_water)} ml** ({pct}%). લક્ષ્યાંક સુધી પહોંચવા હજી **{remaining_water} ml** (~{glasses_left} ગ્લાસ) પાણી બાકી છે. હાઇડ્રેટેડ રહેવા કૃપા કરીને સમયસર પાણી પીતા રહો! 🚰"
                elif lang in ["hi", "hi-Latn"]:
                    reply = f"💧 **{int(amount)} ml** पानी लॉग किया गया! आज का कुल पानी: **{int(total_water)} / {int(target_water)} ml** ({pct}%). लक्ष्य तक पहुँचने के लिए अभी **{remaining_water} ml** (~{glasses_left} ग्लास) पानी बाकी है। हाइड्रेटेड रहने के लिए कृपया समय-समय पर पानी पीते रहें! 🚰"
                else:
                    reply = f"💧 Logged **{int(amount)} ml** water! Today's total: **{int(total_water)} / {int(target_water)} ml** ({pct}%). You need **{remaining_water} ml** more (~{glasses_left} glasses) to reach your daily goal! Please keep hydrating throughout the day! 🚰"

            return {
                "success": True,
                "sessionId": session_id,
                "message": reply,
                "data": {"amountMl": amount, "totalMl": total_water, "targetMl": target_water, "remainingMl": remaining_water},
                "dashboard": dashboard_data,
                "ui": {
                    "type": "LOG_RESULT",
                    "cards": [{
                        "type": "HYDRATION",
                        "title": "Hydration Logged",
                        "subtitle": f"+{int(amount)} ml",
                        "metric": f"{int(total_water)} ml",
                        "log": {"amountMl": amount},
                        "dailySummary": {"totalMl": total_water, "targetMl": target_water},
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
                    mealType=inferred_meal or f.get("mealType") or "LUNCH",
                    is_recognized=f.get("is_recognized", True),
                    has_explicit_quantity=f.get("has_explicit_quantity", True),
                    requires_clarification=f.get("requires_clarification", False),
                    clarification_reason=f.get("clarification_reason"),
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

            if not food_result.requiresClarification:
                for item in food_result.loggedItems:
                    cards.append({
                        "type": "FOOD",
                        "title": item.get("food_name"),
                        "subtitle": f"{item.get('quantity_amount')} {item.get('quantity_unit')}",
                        "metric": f"{int(item.get('calories', 0))} kcal",
                    })
                summary_lines.append(f"{int(food_result.mealTotals.get('calories', 0))} kcal across {len(food_result.loggedItems)} foods")

        # 2. Process workouts
        raw_acts = entities.get("activities") or entities.get("activityItems") or ([entities.get("activity")] if entities.get("activity") else [])
        if raw_acts:
            acts_to_log = [a if isinstance(a, dict) else {"activity": str(a), "durationMinutes": 30} for a in raw_acts]
            act_res = await ActivityService.process_and_log_activities(user_id, acts_to_log, today_str)
            cards.extend(act_res["cards"])
            for calc in act_res["calculations"]:
                metric = f"{calc['reps']} reps" if calc.get("reps") else f"{int(calc['durationMinutes'])}m"
                summary_lines.append(f"{calc['activityName']} ({metric}, {int(calc['caloriesBurned'])} kcal)")

        # Build clean bullet-point summary if both foods and activities logged
        reply = None
        if latest_food_result and raw_acts:
            reply = f"{latest_food_result.replyText}\n\n{act_res['replyText']}"
        elif latest_food_result:
            reply = latest_food_result.replyText
        elif raw_acts:
            reply = act_res["replyText"]
        else:
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

    @staticmethod
    async def handle_daily_summary(
        user_id: str,
        session_id: str,
        today_str: str,
        lang: str = "en"
    ) -> Dict[str, Any]:
        dashboard = await DashboardService.get_today_dashboard(user_id, today_str)
        cal = dashboard["calories"]
        act = dashboard["activity"]
        hyd = dashboard["hydration"]
        mac = dashboard["macros"]

        is_guj = lang in ["gu", "gu-Latn"]
        is_hi = lang in ["hi", "hi-Latn"]

        # Water reminder string according to requirement 6
        if hyd["targetMet"]:
            water_rem_guj = "🎉 અદ્ભુત! તમે આજનો દૈનિક પાણીનો ટાર્ગેટ સફળતાપૂર્વક પૂર્ણ કર્યો છે!"
            water_rem_hi = "🎉 शानदार! आपने आज का दैनिक पानी का लक्ष्य सफलतापूर्वक पूरा कर लिया है!"
            water_rem_en = "🎉 Fantastic! You have successfully reached your daily hydration target!"
        else:
            rem_glasses = max(1, round(hyd["remainingMl"] / 250))
            water_rem_guj = f"લક્ષ્યાંક સુધી પહોંચવા હજી **{hyd['remainingMl']} ml** (~{rem_glasses} ગ્લાસ) પાણી બાકી છે. હાઇડ્રેટેડ રહેવા વધુ પાણી પીતા રહો! 🚰"
            water_rem_hi = f"लक्ष्य तक पहुँचने के लिए अभी **{hyd['remainingMl']} ml** (~{rem_glasses} ग्लास) पानी बाकी है। हाइड्रेटेड रहने के लिए अधिक पानी पिएं! 🚰"
            water_rem_en = f"You are **{hyd['remainingMl']} ml** away from your goal (~{rem_glasses} glasses). Remember to drink more water to stay well-hydrated! 🚰"

        # Exercise summary text
        if act["caloriesBurned"] > 0:
            act_text_guj = f"* બર્ન થયેલ કેલરી: **{act['caloriesBurned']} kcal** ({act['durationMinutes']} મિનિટ સક્રિય વર્કઆઉટ)"
            act_text_hi = f"* बर्न की गई कैलोरी: **{act['caloriesBurned']} kcal** ({act['durationMinutes']} मिनट सक्रिय कसरत)"
            act_text_en = f"* Calories Burned: **{act['caloriesBurned']} kcal** across {act['durationMinutes']} active minutes"
        else:
            act_text_guj = "* આજે હજુ કોઈ કસરત લોગ કરી નથી. 20-30 મિનિટનું ઝડપી ચાલવું પણ ~100-150 કેલરી બર્ન કરવામાં મદદ કરશે!"
            act_text_hi = "* आज अभी तक कोई कसरत लॉग नहीं हुई है। 20-30 मिनट की वॉक भी ~100-150 कैलोरी बर्न करने में मदद करेगी!"
            act_text_en = "* No workouts logged yet today. Even a 20-30 minute brisk walk can burn ~100–150 kcal!"

        if is_guj:
            reply = (
                f"📊 **આજનો દૈનિક હેલ્થ & ફિટનેસ રિપોર્ટ (Today's Summary)**:\n\n"
                f"🍽️ **ખોરાક & કેલરી (Food & Calories)**:\n"
                f"* લીધેલ કેલરી: **{cal['consumed']} / {int(cal['target'])} kcal** ({cal['percentTarget']}%)\n"
                f"* બાકી બજેટ: **{cal['remaining']} kcal**\n"
                f"* મેક્રોઝ: પ્રોટીન **{mac['proteinG']}g** | કાર્બ્સ **{mac['carbsG']}g** | ફેટ **{mac['fatG']}g**\n\n"
                f"💧 **પાણીનું પ્રમાણ (Water Intake)**:\n"
                f"* પીધેલું પાણી: **{hyd['amountMl']} / {int(hyd['targetMl'])} ml** ({hyd['percentTarget']}%)\n"
                f"* {water_rem_guj}\n\n"
                f"🏃 **કસરત & શારીરિક પ્રવૃત્તિ (Exercise)**:\n"
                f"{act_text_guj}\n\n"
                f"🎯 **ધ્યેયની પ્રગતિ (Daily Goals Progress)**:\n"
                f"* નેટ કેલરી સંતુલન: **{cal['net']} kcal** ({cal['consumed']} ઇન - {cal['burned']} બર્ન)"
            )
        elif is_hi:
            reply = (
                f"📊 **आज का दैनिक हेल्थ और फिटनेस सारांश (Today's Summary)**:\n\n"
                f"🍽️ **आहार और कैलोरी (Food & Calories)**:\n"
                f"* ली गई कैलोरी: **{cal['consumed']} / {int(cal['target'])} kcal** ({cal['percentTarget']}%)\n"
                f"* बची हुई कैलोरी: **{cal['remaining']} kcal**\n"
                f"* मैक्रोज़: प्रोटीन **{mac['proteinG']}g** | कार्ब्स **{mac['carbsG']}g** | फैट **{mac['fatG']}g**\n\n"
                f"💧 **पानी की मात्रा (Water Intake)**:\n"
                f"* पिया गया पानी: **{hyd['amountMl']} / {int(hyd['targetMl'])} ml** ({hyd['percentTarget']}%)\n"
                f"* {water_rem_hi}\n\n"
                f"🏃 **कसरत और गतिविधियां (Exercise)**:\n"
                f"{act_text_hi}\n\n"
                f"🎯 **लक्ष्य प्रगति (Daily Goals Progress)**:\n"
                f"* नेट कैलोरी संतुलन: **{cal['net']} kcal** ({cal['consumed']} इन - {cal['burned']} बर्न)"
            )
        else:
            reply = (
                f"📊 **Today's Daily Health & Fitness Summary**:\n\n"
                f"🍽️ **Nutrition & Calories**:\n"
                f"* Consumed: **{cal['consumed']} / {int(cal['target'])} kcal** ({cal['percentTarget']}%)\n"
                f"* Remaining Budget: **{cal['remaining']} kcal**\n"
                f"* Macros: Protein **{mac['proteinG']}g** | Carbs **{mac['carbsG']}g** | Fat **{mac['fatG']}g**\n\n"
                f"💧 **Water Intake**:\n"
                f"* Intake: **{hyd['amountMl']} / {int(hyd['targetMl'])} ml** ({hyd['percentTarget']}%)\n"
                f"* {water_rem_en}\n\n"
                f"🏃 **Workouts & Activities**:\n"
                f"{act_text_en}\n\n"
                f"🎯 **Daily Goals Progress**:\n"
                f"* Net Calories: **{cal['net']} kcal** ({cal['consumed']} in - {cal['burned']} burned)"
            )

        return {
            "success": True,
            "sessionId": session_id,
            "message": reply,
            "data": dashboard,
            "dashboard": dashboard,
            "ui": {
                "type": "SUMMARY",
                "data": dashboard,
            },
        }

    @staticmethod
    async def handle_water_query(
        user_id: str,
        session_id: str,
        today_str: str,
        lang: str = "en"
    ) -> Dict[str, Any]:
        dashboard = await DashboardService.get_today_dashboard(user_id, today_str)
        hyd = dashboard["hydration"]
        is_guj = lang in ["gu", "gu-Latn"]
        is_hi = lang in ["hi", "hi-Latn"]

        if hyd["targetMet"]:
            if is_guj:
                reply = f"💧 આજે તમે કુલ **{hyd['amountMl']} ml** પાણી પીધું છે (ટાર્ગેટ: {int(hyd['targetMl'])} ml - 100%). અભિનંદન! તમે આજનો વોટર ગોલ પૂરો કર્યો છે! 🎉"
            elif is_hi:
                reply = f"💧 आज आपने कुल **{hyd['amountMl']} ml** पानी पिया है (टारगेट: {int(hyd['targetMl'])} ml - 100%). बधाई हो! आपने आज का वॉटर गोल पूरा कर लिया है! 🎉"
            else:
                reply = f"💧 You have logged **{hyd['amountMl']} / {int(hyd['targetMl'])} ml** of water today (100%). Congratulations! You reached your daily hydration goal! 🎉"
        else:
            rem_glasses = max(1, round(hyd["remainingMl"] / 250))
            if is_guj:
                reply = f"💧 આજે તમે કુલ **{hyd['amountMl']} ml** પાણી પીધું છે (ટાર્ગેટ: {int(hyd['targetMl'])} ml - {hyd['percentTarget']}%). દૈનિક ટાર્ગેટ સુધી પહોંચવા હજી **{hyd['remainingMl']} ml** (~{rem_glasses} ગ્લાસ) પાણી બાકી છે. હાઇડ્રેટેડ રહેવા વધુ પાણી પીતા રહો! 🚰"
            elif is_hi:
                reply = f"💧 आज आपने कुल **{hyd['amountMl']} ml** पानी पिया है (टारगेट: {int(hyd['targetMl'])} ml - {hyd['percentTarget']}%). दैनिक लक्ष्य तक पहुँचने के लिए अभी **{hyd['remainingMl']} ml** (~{rem_glasses} ग्लास) पानी बाकी है। हाइड्रेटेड रहने के लिए कृपया अधिक पानी पिएं! 🚰"
            else:
                reply = f"💧 You have logged **{hyd['amountMl']} / {int(hyd['targetMl'])} ml** of water today ({hyd['percentTarget']}%). You need **{hyd['remainingMl']} ml** more (~{rem_glasses} glasses) to reach your daily target! Please remember to drink more water to stay well-hydrated! 🚰"

        return {
            "success": True,
            "sessionId": session_id,
            "message": reply,
            "data": hyd,
            "dashboard": dashboard,
            "ui": {
                "type": "LOG_RESULT",
                "cards": [{
                    "type": "HYDRATION",
                    "title": "Water Intake Status",
                    "subtitle": f"{hyd['percentTarget']}% of daily target",
                    "metric": f"{hyd['amountMl']} ml",
                    "log": {"amountMl": hyd["amountMl"]},
                    "dailySummary": {"totalMl": hyd["amountMl"], "targetMl": hyd["targetMl"]},
                }],
            },
        }

    @staticmethod
    async def handle_food_suggestion(
        user_id: str,
        session_id: str,
        user_message: str,
        lang: str = "en",
        today_str: str = ""
    ) -> Dict[str, Any]:
        sugg = await FoodSuggestionService.generate_food_suggestion(user_id, user_message, lang, today_str)
        return {
            "success": True,
            "sessionId": session_id,
            "message": sugg["replyText"],
            "data": sugg,
            "ui": {"type": "TEXT"},
        }

    @staticmethod
    async def handle_workout_suggestion(
        user_id: str,
        session_id: str,
        user_message: str,
        lang: str = "en",
        today_str: str = ""
    ) -> Dict[str, Any]:
        dashboard = await DashboardService.get_today_dashboard(user_id, today_str)
        act = dashboard["activity"]
        logged_summary = f"{act['durationMinutes']} mins active ({act['caloriesBurned']} kcal burned)" if act["durationMinutes"] > 0 else None
        workout_reply = FitnessAdvisoryService.generate_workout_suggestion_response(user_message, lang, logged_activities_summary=logged_summary)
        return {
            "success": True,
            "sessionId": session_id,
            "message": workout_reply,
            "data": act,
            "dashboard": dashboard,
            "ui": {"type": "TEXT"},
        }
