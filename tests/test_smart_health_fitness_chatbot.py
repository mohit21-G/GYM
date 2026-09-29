import pytest
import os
import sys

sys.path.insert(0, os.path.abspath("."))

from backend.app.services.agent_nlp import AgentNLP
from backend.app.services.food_suggestion_service import FoodSuggestionService
from backend.app.services.fitness_advisory_service import FitnessAdvisoryService
from backend.app.services.dashboard_service import DashboardService
from backend.app.services.chat_service import ChatService


def test_multilingual_daily_summary_intent():
    """Requirement 1 & 2: Detect daily summary in Gujarati, Hindi, English, Hinglish, Gujlish."""
    queries = [
        "Aaj ni summary aap",
        "Aaj nu summary aapo",
        "What did I do today?",
        "what have i done today",
        "Give me today's summary",
        "Daily summary",
        "Aaj ka summary batao",
        "Aaj maine kya kiya?",
        "Aaje su karyu?",
        "આજની સમરી આપો",
        "આજે મેં શું કર્યું?",
        "आज का सारांश बताओ",
        "आज मैंने क्या किया?",
    ]
    for q in queries:
        intent = AgentNLP.detect_intent(q)
        assert intent == "DAILY_SUMMARY", f"Expected DAILY_SUMMARY for '{q}', got '{intent}'"


def test_multilingual_water_query_intent():
    """Requirement 1, 2 & 6: Detect water queries without falsely logging water."""
    queries = [
        "Aaj ketlu pani pidhu?",
        "Ketlu pani pidhu aaje?",
        "How much water did I drink today?",
        "Water intake today",
        "Aaj kitna pani piya?",
        "Kitna paani piya aaj?",
        "Did I drink enough water today?",
        "How much water is left?",
        "આજે કેટલું પાણી પીધું?",
        "કેટલું પાણી પીધું?",
        "आज कितना पानी पिया?",
    ]
    for q in queries:
        intent = AgentNLP.detect_intent(q)
        assert intent == "QUERY_HYDRATION_LOG", f"Expected QUERY_HYDRATION_LOG for '{q}', got '{intent}'"


def test_multilingual_food_suggestions_intent():
    """Requirement 1 & 3: Detect food suggestions in various languages and styles."""
    queries = [
        "What should I eat for dinner?",
        "What to eat?",
        "Suggest healthy food",
        "Healthy breakfast ideas",
        "What can I eat for lunch?",
        "Su khavu joiye?",
        "Lunch ma su khau?",
        "Dinner ma su banavu?",
        "Nasta ma su levu?",
        "Kya khana chahiye?",
        "Dinner me kya banau?",
        "Lunch me kya khau?",
        "Kuch healthy batao khane ke liye",
        "શું ખાવું જોઈએ?",
        "ડિનરમાં શું બનાવવું?",
        "क्या खाना चाहिए?",
        "लंच में क्या खाऊं?",
    ]
    for q in queries:
        intent = AgentNLP.detect_intent(q)
        assert intent == "FOOD_SUGGESTION", f"Expected FOOD_SUGGESTION for '{q}', got '{intent}'"


def test_multilingual_workout_suggestions_intent():
    """Requirement 1 & 4: Detect exercise suggestions in various languages."""
    queries = [
        "Suggest an exercise",
        "Suggest a workout",
        "What workout should I do today?",
        "Which exercise should I do?",
        "Give me workout suggestions",
        "Aaje kai kasrat karu?",
        "Kai exercise karvi joiye?",
        "Kasrat suggest karo",
        "Koi exercise batao",
        "Aaj kaunsa workout karu?",
        "Exercise suggest karo",
        "કઈ કસરત કરું?",
        "કસરત સજેસ્ટ કરો",
        "कौन सी एक्सरसाइज करूं?",
        "कोई एक्सरसाइज बताओ",
    ]
    for q in queries:
        intent = AgentNLP.detect_intent(q)
        assert intent == "WORKOUT_SUGGESTION", f"Expected WORKOUT_SUGGESTION for '{q}', got '{intent}'"


@pytest.mark.asyncio
async def test_food_suggestion_service_estimation_disclaimer():
    """Requirement 3: Food suggestions contain estimated macros and explicit estimation caveat."""
    user_id = "test_user_food_sugg"
    
    # 1. English
    res_en = await FoodSuggestionService.generate_food_suggestion(user_id, "What should I eat for dinner?", lang="en")
    assert "estimate" in res_en["replyText"].lower() or "approximate" in res_en["replyText"].lower()
    assert len(res_en["suggestions"]) >= 1
    assert res_en["mealType"] == "DINNER"
    assert "kcal" in res_en["replyText"]

    # 2. Gujarati
    res_gu = await FoodSuggestionService.generate_food_suggestion(user_id, "Dinner ma su banavu?", lang="gu")
    assert "અંદાજિત" in res_gu["replyText"]
    assert "kcal" in res_gu["replyText"]

    # 3. Hindi
    res_hi = await FoodSuggestionService.generate_food_suggestion(user_id, "Dinner me kya khau?", lang="hi")
    assert "अनुमानित" in res_hi["replyText"] or "estimates" in res_hi["replyText"].lower()
    assert "kcal" in res_hi["replyText"]


def test_workout_suggestion_service_calorie_burn_disclaimer():
    """Requirement 4: Exercise suggestions include activity, duration, calories burned, and caveat that burn is estimate."""
    # 1. English
    reply_en = FitnessAdvisoryService.generate_workout_suggestion_response("Suggest an exercise", lang="en")
    assert "Brisk Walking" in reply_en or "Squats" in reply_en
    assert "kcal" in reply_en
    assert "minute" in reply_en or "min" in reply_en
    assert "estimate" in reply_en.lower()

    # 2. Gujarati
    reply_gu = FitnessAdvisoryService.generate_workout_suggestion_response("Aaje kai kasrat karu?", lang="gu")
    assert "કસરત" in reply_gu or "વૉકિંગ" in reply_gu or "સ્ક્વોટ્સ" in reply_gu
    assert "અંદાજિત" in reply_gu
    assert "kcal" in reply_gu

    # 3. Hindi
    reply_hi = FitnessAdvisoryService.generate_workout_suggestion_response("Koi exercise batao", lang="hi")
    assert "एक्सरसाइज" in reply_hi or "ब्रिस्क वॉक" in reply_hi or "स्क्वैट्स" in reply_hi
    assert "अनुमानित" in reply_hi or "estimates" in reply_hi.lower()
    assert "kcal" in reply_hi


@pytest.mark.asyncio
async def test_dashboard_today_data_structure():
    """Requirement 5: Dashboard returns activity, calories, and hydration matching frontend expectations."""
    today_data = await DashboardService.get_today_dashboard("sample_user_123", "2026-09-29")
    
    # Check top-level keys
    assert "calories" in today_data
    assert "activity" in today_data
    assert "hydration" in today_data
    assert "macros" in today_data

    # Check calories fields
    assert "consumed" in today_data["calories"]
    assert "burned" in today_data["calories"]
    assert "target" in today_data["calories"]
    assert "remaining" in today_data["calories"]
    assert "percentTarget" in today_data["calories"]

    # Check activity fields
    assert "caloriesBurned" in today_data["activity"]
    assert "durationMinutes" in today_data["activity"]

    # Check hydration fields
    assert "amountMl" in today_data["hydration"]
    assert "targetMl" in today_data["hydration"]
    assert "percentTarget" in today_data["hydration"]
    assert "remainingMl" in today_data["hydration"]
    assert "targetMet" in today_data["hydration"]


@pytest.mark.asyncio
async def test_daily_summary_handler():
    """Requirement 2 & 6: Daily summary provides food, water vs target, exercise, and goal progress."""
    user_id = "test_user_summary_1"
    session_id = "test_sess_1"
    
    res = await ChatService.handle_daily_summary(user_id, session_id, "2026-09-29", lang="en")
    assert res["success"] is True
    reply = res["message"]
    
    # Must cover the 4 required areas
    assert "Nutrition & Calories" in reply or "Food & Calories" in reply
    assert "Water Intake" in reply
    assert "Workouts & Activities" in reply or "Exercise" in reply
    assert "Daily Goals Progress" in reply or "Goal Progress" in reply
    assert "Net Calories" in reply
    assert res["ui"]["type"] == "SUMMARY"
    assert "hydration" in res["dashboard"]
    assert "activity" in res["dashboard"]


@pytest.mark.asyncio
async def test_water_goal_suggestions_when_below_and_when_met():
    """Requirement 6: Water goal suggestions politely remind when below target, and never claim met unless confirmed."""
    user_id = "test_user_water_goal"
    session_id = "test_sess_water"
    
    # 1. When below target (0 / 2500 ml)
    res_below = await ChatService.handle_water_query(user_id, session_id, "2026-09-29", lang="en")
    assert res_below["success"] is True
    msg_below = res_below["message"]
    assert "more" in msg_below or "away from" in msg_below
    assert "Congratulations" not in msg_below, "Must never claim target reached when below target!"
    assert "2500" in msg_below
    assert res_below["ui"]["type"] == "LOG_RESULT"
    assert res_below["ui"]["cards"][0]["type"] == "HYDRATION"


def test_clarification_on_vague_messages():
    """Requirement 1: Unclear / unmeasured physical activity requests clarification instead of guessing."""
    unclear_queries = [
        "I did exercise",
        "Aaje me kasrat kari",
        "Maine workout kiya",
    ]
    for q in unclear_queries:
        acts = AgentNLP.extract_activity_entities(q)
        assert len(acts) > 0
        assert acts[0]["requiresClarification"] is True, f"Expected requiresClarification=True for '{q}'"


@pytest.mark.asyncio
async def test_water_logging_updates_dashboard():
    """Requirement 5: Logging water saves to DB and returns updated dashboard hydration card immediately."""
    user_id = "test_user_water_sync"
    session_id = "sess_water_sync"
    
    # 1. Log 500ml water
    res = await ChatService.route_intent(
        user_id=user_id,
        session_id=session_id,
        intent="CREATE_HYDRATION_LOG",
        entities={"amountMl": 500.0},
        ai_res={},
        user_message="drank 500ml water"
    )
    assert res["success"] is True
    assert "dashboard" in res
    assert res["dashboard"]["hydration"]["amountMl"] >= 500
    assert res["dashboard"]["hydration"]["percentTarget"] >= 20
    assert res["ui"]["cards"][0]["metric"] == f"{int(res['dashboard']['hydration']['amountMl'])} ml"


@pytest.mark.asyncio
async def test_activity_logging_calculates_and_updates_dashboard():
    """Requirement 5: Logging exercise calculates calories burned and returns updated dashboard calories burned card."""
    user_id = "test_user_activity_sync"
    session_id = "sess_act_sync"
    
    # 1. Log 30 minutes of running
    res = await ChatService.route_intent(
        user_id=user_id,
        session_id=session_id,
        intent="CREATE_ACTIVITY_LOG",
        entities={
            "activities": [{
                "activity": "Running",
                "durationMinutes": 30.0,
                "intensity": "MEDIUM",
                "metValue": 8.5
            }]
        },
        ai_res={},
        user_message="Ran for 30 minutes"
    )
    assert res["success"] is True
    assert "dashboard" in res
    assert res["dashboard"]["activity"]["caloriesBurned"] > 0
    assert res["dashboard"]["activity"]["durationMinutes"] >= 30


@pytest.mark.asyncio
async def test_duplicate_logging_prevention():
    """Requirement 5: Prevent duplicate logging when user repeats a message."""
    user_id = "test_user_dup_check"
    
    # Message 1
    res1 = await ChatService.handle_user_message(user_id, "250ml water")
    assert res1["success"] is True
    
    # Message 2 (exact duplicate immediately after)
    res2 = await ChatService.handle_user_message(user_id, "250ml water")
    assert res2["success"] is True
    assert "duplicate" in res2["message"].lower() or "થોડીવાર પહેલા" in res2["message"] or "पहले" in res2["message"] or "moment ago" in res2["message"].lower()


@pytest.mark.asyncio
async def test_daily_summary_gujarati_and_hindi():
    """Requirement 2: Daily summary properly formats in Gujarati and Hindi."""
    user_id = "test_user_summary_lang"
    session_id = "sess_summary_lang"
    
    # Gujarati
    res_gu = await ChatService.handle_daily_summary(user_id, session_id, "2026-09-29", lang="gu")
    assert "ખોરાક & કેલરી" in res_gu["message"]
    assert "પાણીનું પ્રમાણ" in res_gu["message"]
    assert "કસરત" in res_gu["message"]
    assert "ધ્યેયની પ્રગતિ" in res_gu["message"]

    # Hindi
    res_hi = await ChatService.handle_daily_summary(user_id, session_id, "2026-09-29", lang="hi")
    assert "आहार और कैलोरी" in res_hi["message"]
    assert "पानी की मात्रा" in res_hi["message"]
    assert "कसरत" in res_hi["message"]
    assert "लक्ष्य प्रगति" in res_hi["message"]
