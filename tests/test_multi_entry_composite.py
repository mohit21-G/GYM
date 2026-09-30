import pytest
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, os.path.abspath("."))

from backend.app.services.time_service import TimeService
from backend.app.services.agent_nlp import AgentNLP
from backend.app.services.food_service import FoodService
from backend.app.services.activity_service import ActivityService
from backend.app.services.chat_service import ChatService
from backend.app.services.ai_service import AIService

IST = ZoneInfo("Asia/Kolkata")

TEST_INPUT = """Today morning

At 6:45 lamon water 1 glass
7:00 400ml black cofee
7:15 am 1 skoop pre workout with 300ml watter
7:30 to 9:00 gym back amd biceps and 20min walk
8:00am 1 ltr watwr
9:30 1 skoop protin powdr with 400ml watter
10:00am 3 khapli roti and 1 cup milkk"""

def test_multi_entry_food_extraction():
    """Verify all 6 food items are accurately extracted from the exact typo benchmark input."""
    foods = AgentNLP.extract_food_entities_heuristically(TEST_INPUT)
    food_names = [f.get("food", f.get("food_name", "")) for f in foods]

    # Verify Lemon Water 1 glass
    lw = next((f for f in foods if "lemon water" in f["food"].lower()), None)
    assert lw is not None, f"Lemon Water not found in {food_names}"
    assert lw["quantity"] == 1.0
    assert lw["unit"] == "glass"
    assert "06:45" in lw["logged_at"]

    # Verify Black Coffee 400ml
    bc = next((f for f in foods if "black coffee" in f["food"].lower()), None)
    assert bc is not None, f"Black Coffee not found in {food_names}"
    assert bc["quantity"] == 400.0
    assert bc["unit"] == "ml"
    assert "07:00" in bc["logged_at"]

    # Verify Pre Workout 1 scoop
    pw = next((f for f in foods if "pre workout" in f["food"].lower() or "pre-workout" in f["food"].lower()), None)
    assert pw is not None, f"Pre Workout not found in {food_names}"
    assert pw["quantity"] == 1.0
    assert pw["unit"] == "scoop"
    assert "07:15" in pw["logged_at"]

    # Verify Protein Powder 1 scoop
    pp = next((f for f in foods if "protein" in f["food"].lower() and "powder" in f["food"].lower()), None)
    assert pp is not None, f"Protein Powder not found in {food_names}"
    assert pp["quantity"] == 1.0
    assert pp["unit"] == "scoop"
    assert "09:30" in pp["logged_at"]

    # Verify Khapli Roti 3 pieces
    kr = next((f for f in foods if "khapli" in f["food"].lower() or "roti" in f["food"].lower()), None)
    assert kr is not None, f"Khapli Roti not found in {food_names}"
    assert kr["quantity"] == 3.0
    assert "10:00" in kr["logged_at"]

    # Verify Milk 1 cup
    mk = next((f for f in foods if "milk" in f["food"].lower() or "doodh" in f["food"].lower()), None)
    assert mk is not None, f"Milk not found in {food_names}"
    assert mk["quantity"] == 1.0
    assert mk["unit"] == "cup"
    assert "10:00" in mk["logged_at"]

    assert len(foods) == 6, f"Expected exactly 6 foods, got {len(foods)}: {food_names}"

def test_multi_entry_hydration_extraction():
    """Verify all 4 distinct hydration logs are extracted with their specific beverage names, amounts, and times."""
    hyds = AgentNLP.extract_hydration_entities(TEST_INPUT)
    assert len(hyds) == 4, f"Expected 4 hydration entries, got {len(hyds)}: {hyds}"

    # 1. Lemon Water 250ml at 6:45
    h0 = hyds[0]
    assert h0["amount_ml"] == 250.0
    assert h0.get("beverage_name") == "Lemon Water"
    assert "06:45" in h0["logged_at"]

    # 2. 300ml water at 7:15
    h1 = hyds[1]
    assert h1["amount_ml"] == 300.0
    assert h1.get("beverage_name") == "Water"
    assert "07:15" in h1["logged_at"]

    # 3. 1 ltr water at 8:00
    h2 = hyds[2]
    assert h2["amount_ml"] == 1000.0
    assert h2.get("beverage_name") == "Water"
    assert "08:00" in h2["logged_at"]

    # 4. 400ml water at 9:30
    h3 = hyds[3]
    assert h3["amount_ml"] == 400.0
    assert h3.get("beverage_name") == "Water"
    assert "09:30" in h3["logged_at"]

    total_water = sum(h["amount_ml"] for h in hyds)
    assert total_water == 1950.0

def test_multi_entry_activity_extraction():
    """Verify separate exercise detection (Back Workout, Biceps Workout, Walking) without generic Gym."""
    acts = AgentNLP.extract_activity_entities(TEST_INPUT)
    assert len(acts) == 3, f"Expected 3 activities, got {len(acts)}: {acts}"

    act_names = [a["activity"] for a in acts]
    assert "Gym" not in act_names, f"Generic Gym should not be logged: {act_names}"

    back_act = next((a for a in acts if a["activity"] == "Back Workout"), None)
    assert back_act is not None, f"Back Workout missing: {act_names}"
    assert back_act["durationMinutes"] == 45.0
    assert "07:30" in back_act["logged_at"]

    biceps_act = next((a for a in acts if a["activity"] == "Biceps Workout"), None)
    assert biceps_act is not None, f"Biceps Workout missing: {act_names}"
    assert biceps_act["durationMinutes"] == 45.0
    assert "07:30" in biceps_act["logged_at"]

    walk_act = next((a for a in acts if a["activity"] == "Walking"), None)
    assert walk_act is not None, f"Walking missing: {act_names}"
    assert walk_act["durationMinutes"] == 20.0

def test_multi_entry_structured_actions():
    """Verify extract_structured_actions outputs all 13 individual records."""
    actions = AgentNLP.extract_structured_actions(TEST_INPUT)
    types = [a["type"] for a in actions]
    assert types.count("CREATE_FOOD_LOG") == 6
    assert types.count("CREATE_ACTIVITY_LOG") == 3
    assert types.count("CREATE_HYDRATION_LOG") == 4
    assert len(actions) == 13

@pytest.mark.asyncio
async def test_multi_log_end_to_end(monkeypatch):
    """
    Verify full end-to-end multi-log execution in ChatService:
    - 6 foods logged to DB
    - 3 exercises logged to DB (Back Workout, Biceps Workout, Walking)
    - 4 hydrations logged to DB (Lemon Water + 3 Waters)
    - Dashboard totals reflect all items
    """
    import backend.app.database as db_mod
    mock_db = db_mod.MockDatabase()
    await mock_db.users.insert_one({"id": "test_user_composite", "profile": {"dailyCalorieTarget": 2000, "currentWeightKg": 70}})

    monkeypatch.setattr(db_mod.db_instance, "db", mock_db)
    monkeypatch.setattr(db_mod, "get_db", lambda: mock_db)

    inserted_food = mock_db.daily_food_logs.docs
    inserted_exercises = mock_db.daily_exercise_logs.docs
    inserted_hydration = mock_db.hydration_logs.docs

    # Process AI intent detection
    ai_res = await AIService.process_message(TEST_INPUT)
    assert ai_res["intent"] == "CREATE_MULTI_LOG"

    # Route intent in ChatService
    res = await ChatService.route_intent(
        user_id="test_user_composite",
        session_id="test_session_composite",
        intent=ai_res["intent"],
        entities=ai_res["entities"],
        ai_res=ai_res,
        user_message=TEST_INPUT,
    )

    assert res["success"] is True

    # 1. Verify 6 food items saved to database
    assert len(inserted_food) == 6, f"Expected 6 foods inserted into DB, got {len(inserted_food)}"
    food_names_inserted = [f["food_name"] for f in inserted_food]
    assert any("Lemon Water" in n for n in food_names_inserted)
    assert any("Black Coffee" in n for n in food_names_inserted)
    assert any("Pre Workout" in n for n in food_names_inserted)
    assert any("Protein" in n for n in food_names_inserted)
    assert any("Khapli" in n for n in food_names_inserted)
    assert any("Milk" in n for n in food_names_inserted)

    # 2. Verify 3 exercises saved to database (No generic Gym)
    assert len(inserted_exercises) == 3, f"Expected 3 exercises inserted into DB, got {len(inserted_exercises)}"
    act_names_inserted = [a["exercise_name"] for a in inserted_exercises]
    assert "Gym" not in act_names_inserted
    assert any("Back Workout" in n for n in act_names_inserted)
    assert any("Biceps Workout" in n for n in act_names_inserted)
    assert any("Walking" in n for n in act_names_inserted)

    # 3. Verify 4 water records saved to database with beverage names
    assert len(inserted_hydration) == 4, f"Expected 4 hydration logs inserted into DB, got {len(inserted_hydration)}"
    water_amounts = [h["amount_ml"] for h in inserted_hydration]
    assert 250.0 in water_amounts
    assert 300.0 in water_amounts
    assert 1000.0 in water_amounts
    assert 400.0 in water_amounts
    assert sum(water_amounts) == 1950.0

    lemon_water_h = next((h for h in inserted_hydration if h.get("amount_ml") == 250.0), None)
    assert lemon_water_h is not None
    assert lemon_water_h.get("beverage_name") == "Lemon Water"

    # 4. Verify UI cards
    ui = res.get("ui", {})
    grouped_food_cards = ui.get("groupedFoodCards", [])
    assert len(grouped_food_cards) > 0, "Expected food cards in response"

    cards = ui.get("cards", [])
    act_cards = [c for c in cards if c.get("type") == "ACTIVITY"]
    hyd_cards = [c for c in cards if c.get("type") == "HYDRATION"]
    assert len(act_cards) == 3, f"Expected 3 activity cards, got {len(act_cards)}"
    assert len(hyd_cards) == 1, f"Expected 1 aggregated hydration card, got {len(hyd_cards)}"
    assert hyd_cards[0]["totalMl"] == 1950.0
    assert len(hyd_cards[0]["entries"]) == 4

    # 5. Verify message response summary has all categories
    msg = res.get("message", "")
    assert "Food:" in msg
    assert "Exercise:" in msg
    assert "Hydration:" in msg

@pytest.mark.asyncio
async def test_history_endpoints_and_time_edit_flow(monkeypatch):
    """
    Verify the complete Chat -> DB -> History Flow:
    1. ChatService logs all items into DB.
    2. Hydration history router lists exact beverage names (Lemon Water, Water) and counts water.
    3. Activity history router lists separate records (Back Workout, Biceps Workout, Walking) - NEVER generic Gym.
    4. Food logs carry hasExplicitTime=True for explicit times, and False when no time is given.
    5. Editing time updates the food log accurately.
    """
    import backend.app.database as db_mod
    from backend.app.routers.hydration_logs import list_hydration_logs
    from backend.app.routers.activity_logs import list_activity_logs
    from backend.app.routers.food_logs import update_food_log
    from backend.app.schemas.food_log import UpdateFoodLogDto

    mock_db = db_mod.MockDatabase()
    user_id = "test_history_user"
    user_doc = {"id": user_id, "user_id": user_id, "profile": {"dailyCalorieTarget": 2000, "currentWeightKg": 70}}
    await mock_db.users.insert_one(user_doc)

    monkeypatch.setattr(db_mod.db_instance, "db", mock_db)
    monkeypatch.setattr(db_mod, "get_db", lambda: mock_db)

    # 1. Process message through chat service
    ai_res = await AIService.process_message(TEST_INPUT)
    res = await ChatService.route_intent(
        user_id=user_id,
        session_id="test_session_history",
        intent=ai_res["intent"],
        entities=ai_res["entities"],
        ai_res=ai_res,
        user_message=TEST_INPUT,
    )
    assert res["success"] is True

    # 2. Verify Hydration History API endpoint
    hyd_resp = await list_hydration_logs(page=1, limit=15, current_user=user_doc)
    hyd_items = hyd_resp["items"]
    assert len(hyd_items) == 4, f"Expected 4 hydration history items, got {len(hyd_items)}"
    bev_names = [it.get("beverageName") for it in hyd_items]
    assert "Lemon Water" in bev_names, f"Lemon Water should be in hydration history: {bev_names}"
    lemon_item = next(it for it in hyd_items if it.get("beverageName") == "Lemon Water")
    assert lemon_item["amountMl"] == 250.0

    # 3. Verify Activity History API endpoint
    act_resp = await list_activity_logs(page=1, limit=15, current_user=user_doc)
    act_items = act_resp["items"]
    assert len(act_items) == 3, f"Expected 3 workout history items, got {len(act_items)}"
    exercise_names = [it.get("activityName") or it.get("name") for it in act_items]
    assert "Gym" not in exercise_names, f"Generic Gym must not appear in history: {exercise_names}"
    assert "Back Workout" in exercise_names
    assert "Biceps Workout" in exercise_names
    assert "Walking" in exercise_names

    # Check durations and calories in history
    back_it = next(it for it in act_items if (it.get("activityName") or it.get("name")) == "Back Workout")
    assert back_it["durationMinutes"] == 45.0
    assert back_it["caloriesBurned"] > 0

    biceps_it = next(it for it in act_items if (it.get("activityName") or it.get("name")) == "Biceps Workout")
    assert biceps_it["durationMinutes"] == 45.0
    assert biceps_it["caloriesBurned"] > 0

    walk_it = next(it for it in act_items if (it.get("activityName") or it.get("name")) == "Walking")
    assert walk_it["durationMinutes"] == 20.0
    assert walk_it["caloriesBurned"] > 0

    # 4. Verify Food History hasExplicitTime
    today_str = TimeService.get_current_local_date_str()
    grouped_cards_res = await FoodService.get_daily_grouped_food_cards(user_id, today_str)
    all_entries = []
    for card in grouped_cards_res["groupedFoodCards"]:
        all_entries.extend(card.entries)

    # All items from TEST_INPUT had explicit times
    for entry in all_entries:
        assert entry.hasExplicitTime is True
        assert len(entry.timeFormatted) > 0

    # 5. Verify un-timed item has hasExplicitTime=False
    un_timed_res = await AIService.process_message("Aaje 1 glass protein shake lidho")
    await ChatService.route_intent(
        user_id=user_id,
        session_id="test_session_history",
        intent=un_timed_res["intent"],
        entities=un_timed_res["entities"],
        ai_res=un_timed_res,
        user_message="Aaje 1 glass protein shake lidho",
    )
    grouped_cards_res2 = await FoodService.get_daily_grouped_food_cards(user_id, today_str)
    shake_card = next(c for c in grouped_cards_res2["groupedFoodCards"] if "shake" in c.foodName.lower())
    assert shake_card.entries[0].hasExplicitTime is False
    assert shake_card.entries[0].timeFormatted == ""

    # 6. Verify Time Edit API updates the time
    first_entry = all_entries[0]
    update_res = await update_food_log(
        id=first_entry.id,
        dto=UpdateFoodLogDto(loggedAt="08:15 AM"),
        current_user=user_doc,
    )
    assert update_res["success"] is True
    assert update_res["entry"]["hasExplicitTime"] is True
    assert "8:15" in update_res["entry"]["timeFormatted"]

@pytest.mark.asyncio
async def test_smart_default_food_servings_never_ask_quantity():
    """
    Requirement 2: Never ask normal food quantity when food is clearly identified.
    Must automatically use reasonable default serving size from food profile/database.
    Examples:
    - 'dal khadhu' -> 1 bowl
    - 'rice khadhu' -> 1 bowl
    - 'roti khai' -> 1 piece
    - 'milk pidhu' -> 1 glass
    - 'banana khadhu' -> 1 piece
    - 'protein shake lidho' -> 1 scoop
    - 'coffee pidhi' -> 1 cup
    """
    cases = [
        ("dal khadhu", "bowl", 1.0),
        ("rice khadhu", "bowl", 1.0),
        ("roti khai", "piece", 1.0),
        ("milk pidhu", "glass", 1.0),
        ("banana khadhu", "piece", 1.0),
        ("protein shake lidho", "scoop", 1.0),
        ("coffee pidhi", "cup", 1.0),
    ]

    for user_input, expected_unit, expected_qty in cases:
        extracted = AgentNLP.extract_food_entities_heuristically(user_input)
        assert len(extracted) == 1, f"Failed for {user_input}: got {extracted}"
        item = extracted[0]
        assert item["is_recognized"] is True, f"Food should be recognized for {user_input}"
        assert item["quantity"] == expected_qty, f"Expected {expected_qty} for {user_input}, got {item['quantity']}"
        assert item["unit"] == expected_unit, f"Expected {expected_unit} for {user_input}, got {item['unit']}"
        assert item["requires_clarification"] is False, f"Must NEVER ask quantity clarification for {user_input}"

@pytest.mark.asyncio
async def test_single_hydration_card_and_timeline_underneath(monkeypatch):
    """
    Requirement 3 & 4: ONE Aggregated Hydration Card with timeline underneath.
    Shows Total: 1950 / 2500 ml and individual timeline/details underneath:
    - 6:45 AM — 250 ml Lemon Water
    - 7:15 AM — 300 ml Water
    - 8:00 AM — 1000 ml Water
    - 9:30 AM — 400 ml Water
    """
    import backend.app.database as db_mod
    mock_db = db_mod.MockDatabase()
    user_id = "test_user_single_hyd"
    await mock_db.users.insert_one({"id": user_id, "profile": {"dailyCalorieTarget": 2000, "currentWeightKg": 70}})

    monkeypatch.setattr(db_mod.db_instance, "db", mock_db)
    monkeypatch.setattr(db_mod, "get_db", lambda: mock_db)

    ai_res = await AIService.process_message(TEST_INPUT)
    res = await ChatService.route_intent(
        user_id=user_id,
        session_id="test_sess_single_hyd",
        intent=ai_res["intent"],
        entities=ai_res["entities"],
        ai_res=ai_res,
        user_message=TEST_INPUT,
    )

    cards = res.get("ui", {}).get("cards", [])
    hyd_cards = [c for c in cards if c.get("type") == "HYDRATION"]
    assert len(hyd_cards) == 1, f"Expected exactly ONE hydration card, got {len(hyd_cards)}"

    hyd_card = hyd_cards[0]
    assert hyd_card["title"] == "Hydration"
    assert hyd_card["totalMl"] == 1950.0
    assert hyd_card["targetMl"] == 2500.0

    entries = hyd_card.get("entries", [])
    assert len(entries) == 4, f"Expected 4 timeline entries, got {len(entries)}: {entries}"

    # Verify times, amounts, and beverage names
    assert entries[0]["time"] == "6:45 AM"
    assert entries[0]["amountMl"] == 250
    assert entries[0]["beverageName"] == "Lemon Water"

    assert entries[1]["time"] == "7:15 AM"
    assert entries[1]["amountMl"] == 300
    assert entries[1]["beverageName"] == "Water"

    assert entries[2]["time"] == "8:00 AM"
    assert entries[2]["amountMl"] == 1000
    assert entries[2]["beverageName"] == "Water"

    assert entries[3]["time"] == "9:30 AM"
    assert entries[3]["amountMl"] == 400
    assert entries[3]["beverageName"] == "Water"

