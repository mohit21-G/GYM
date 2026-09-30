import pytest
import uuid
from datetime import datetime, timezone
from backend.app.database import get_db
from backend.app.services.time_service import TimeService
from backend.app.services.food_service import FoodService
from backend.app.services.chat_service import ChatService
from backend.app.schemas.food_log import FoodItemInput, UpdateFoodLogDto

@pytest.mark.asyncio
async def test_case_1_omitted_meal_and_time():
    """
    TEST 1:
    User: "me aaje 1 cup green tea pidhi"
    Expected:
    Food = Green Tea
    Quantity = 1 cup
    Meal = —
    No user-event time shown (has_explicit_time = False)
    No quantity question
    Current response contains only this newly logged Green Tea
    """
    user_id = f"test_user_c1_{uuid.uuid4().hex[:6]}"
    session_id = f"session_c1_{uuid.uuid4().hex[:6]}"
    user_msg = "me aaje 1 cup green tea pidhi"

    # Step 1: verify time extraction: 'aaje' gives date, but NOT explicit clock time
    local_now = TimeService.get_current_local_time()
    res_dt, has_explicit_time = TimeService.extract_time_from_text(user_msg, reference_time=local_now)
    assert not has_explicit_time, f"Expected has_explicit_time=False, got {has_explicit_time}"

    # Step 2: verify meal inference returns "—" (NEVER clock meal)
    meal = TimeService.infer_meal_type(user_msg, dt=res_dt if has_explicit_time else None)
    assert meal == "—", f"Expected meal='—', got {meal}"

    # Step 3: process through ChatService
    res = await ChatService.handle_user_message(user_id, user_msg, session_id_input=session_id)
    assert res["success"] is True
    assert not res.get("ui", {}).get("requiresClarification", False)

    grouped_cards = res["ui"].get("groupedFoodCards", [])
    assert len(grouped_cards) == 1
    card = grouped_cards[0]
    assert "Green Tea" in card["foodName"]
    assert card["totalQuantity"] == 1.0
    assert card["totalCalories"] == 2  # 2 kcal per cup
    assert len(card["entries"]) == 1
    entry = card["entries"][0]
    assert entry["mealType"] == "—"
    assert entry["timeFormatted"] == ""  # No user-event time shown

@pytest.mark.asyncio
async def test_case_2_explicit_clock_time():
    """
    TEST 2:
    User: "me 4:27 PM 1 cup green tea pidhi"
    Expected:
    Food = Green Tea
    Quantity = 1 cup
    Time = 4:27 PM
    Meal should only be inferred if explicit time/context rules define it
    No quantity question
    """
    user_id = f"test_user_c2_{uuid.uuid4().hex[:6]}"
    session_id = f"session_c2_{uuid.uuid4().hex[:6]}"
    user_msg = "me 4:27 PM 1 cup green tea pidhi"

    local_now = TimeService.get_current_local_time()
    res_dt, has_explicit_time = TimeService.extract_time_from_text(user_msg, reference_time=local_now)
    assert has_explicit_time, "Expected has_explicit_time=True for 4:27 PM"
    assert res_dt.hour == 16 and res_dt.minute == 27

    meal = TimeService.infer_meal_type(user_msg, dt=res_dt)
    assert meal == "SNACK"  # 16:27 falls into afternoon SNACK window

    res = await ChatService.handle_user_message(user_id, user_msg, session_id_input=session_id)
    assert res["success"] is True
    grouped_cards = res["ui"].get("groupedFoodCards", [])
    assert len(grouped_cards) == 1
    entry = grouped_cards[0]["entries"][0]
    assert entry["timeFormatted"] == "4:27 PM"
    assert entry["mealType"] == "SNACK"

@pytest.mark.asyncio
async def test_case_3_contextual_time_savare_830_poha():
    """
    TEST 3:
    User: "me savare 8:30 poha khadha"
    Expected:
    Food = Poha
    Time = 8:30 AM
    Meal = Breakfast
    """
    user_id = f"test_user_c3_{uuid.uuid4().hex[:6]}"
    session_id = f"session_c3_{uuid.uuid4().hex[:6]}"
    user_msg = "me savare 8:30 1 bowl poha khadha"

    res_dt, has_explicit_time = TimeService.extract_time_from_text(user_msg)
    assert has_explicit_time
    assert res_dt.hour == 8 and res_dt.minute == 30

    meal = TimeService.infer_meal_type(user_msg, dt=res_dt)
    assert meal == "BREAKFAST"

    res = await ChatService.handle_user_message(user_id, user_msg, session_id_input=session_id)
    assert res["success"] is True
    grouped_cards = res["ui"].get("groupedFoodCards", [])
    assert len(grouped_cards) == 1
    entry = grouped_cards[0]["entries"][0]
    assert entry["timeFormatted"] == "8:30 AM"
    assert entry["mealType"] == "BREAKFAST"

@pytest.mark.asyncio
async def test_case_4_bapore_2_rotli():
    """
    TEST 4:
    User: "me bapore 2 rotli khai"
    Expected:
    Food = Roti
    Quantity = 2
    Meal = Lunch
    No quantity question
    """
    user_id = f"test_user_c4_{uuid.uuid4().hex[:6]}"
    session_id = f"session_c4_{uuid.uuid4().hex[:6]}"
    user_msg = "me bapore 2 rotli khai"

    # Contextual meal from 'bapore' is LUNCH
    meal = TimeService.infer_meal_type(user_msg)
    assert meal == "LUNCH"

    # Crucial test: 'bapore 2 rotli' should NOT treat 2 as hour 2:00 PM
    res_dt, has_explicit_time = TimeService.extract_time_from_text(user_msg)
    assert not has_explicit_time, "Quantity '2 rotli' must not collide as hour 2:00"

    res = await ChatService.handle_user_message(user_id, user_msg, session_id_input=session_id)
    assert res["success"] is True
    grouped_cards = res["ui"].get("groupedFoodCards", [])
    assert len(grouped_cards) == 1
    card = grouped_cards[0]
    assert card["totalQuantity"] == 2.0
    assert card["entries"][0]["mealType"] == "LUNCH"
    assert card["entries"][0]["timeFormatted"] == ""

@pytest.mark.asyncio
async def test_case_5_food_specific_quantity_question():
    """
    TEST 5:
    User: "me green tea pidhi"
    Expected:
    Ask a Green Tea-specific quantity question:
    "How much green tea did you have? (e.g. 1 cup, 2 cups)"
    NOT: "1 glass, 1 scoop, 1 bowl, 2 pieces"
    """
    # Test food-specific questions across all foods in specification
    gt_q = FoodService.get_quantity_clarification_question("Green Tea", lang="en")
    assert "How much green tea did you have? (e.g. 1 cup, 2 cups)" in gt_q

    tea_q = FoodService.get_quantity_clarification_question("Tea", lang="en")
    assert "How much tea did you have? (e.g. 1 cup, 2 cups)" in tea_q

    coffee_q = FoodService.get_quantity_clarification_question("Coffee", lang="en")
    assert "How much coffee did you have? (e.g. 1 cup, 2 cups)" in coffee_q

    water_q = FoodService.get_quantity_clarification_question("Water", lang="en")
    assert "How much water did you drink? (e.g. 1 glass, 2 glasses, 1 bottle)" in water_q

    roti_q = FoodService.get_quantity_clarification_question("Roti", lang="en")
    assert "How many rotis did you have? (e.g. 1 roti, 2 rotis)" in roti_q

    bhakri_q = FoodService.get_quantity_clarification_question("Bhakri", lang="en")
    assert "How many bhakris did you have? (e.g. 1 bhakri, 2 bhakris)" in bhakri_q

    egg_q = FoodService.get_quantity_clarification_question("Egg", lang="en")
    assert "How many eggs did you have? (e.g. 1 egg, 2 eggs)" in egg_q

    banana_q = FoodService.get_quantity_clarification_question("Banana", lang="en")
    assert "How many bananas did you have? (e.g. 1 banana, 2 bananas)" in banana_q

    apple_q = FoodService.get_quantity_clarification_question("Apple", lang="en")
    assert "How many apples did you have? (e.g. 1 apple, 2 apples)" in apple_q

    rice_q = FoodService.get_quantity_clarification_question("Rice", lang="en")
    assert "How much rice did you have? (e.g. 1 bowl, 2 bowls)" in rice_q

    dal_q = FoodService.get_quantity_clarification_question("Dal", lang="en")
    assert "How much dal did you have? (e.g. 1 bowl, 2 bowls)" in dal_q

    milk_q = FoodService.get_quantity_clarification_question("Milk", lang="en")
    assert "How much milk did you have? (e.g. 1 glass, 2 glasses)" in milk_q

    shake_q = FoodService.get_quantity_clarification_question("Protein shake", lang="en")
    assert "How much protein shake did you have? (e.g. 1 scoop, 2 scoops, 1 glass)" in shake_q

    poha_q = FoodService.get_quantity_clarification_question("Poha", lang="en")
    assert "How much poha did you have? (e.g. 1 bowl, 2 bowls)" in poha_q

    upma_q = FoodService.get_quantity_clarification_question("Upma", lang="en")
    assert "How much upma did you have? (e.g. 1 bowl, 2 bowls)" in upma_q

    oats_q = FoodService.get_quantity_clarification_question("Oats", lang="en")
    assert "How much oats did you have? (e.g. 1 bowl, 2 bowls)" in oats_q

    # Now verify ChatService returns the question when user logs food without quantity
    user_id = f"test_user_c5_{uuid.uuid4().hex[:6]}"
    session_id = f"session_c5_{uuid.uuid4().hex[:6]}"
    res = await ChatService.handle_user_message(user_id, "me green tea pidhi", session_id_input=session_id)
    assert "How much green tea did you have?" in res["message"]
    assert "1 scoop" not in res["message"]

@pytest.mark.asyncio
async def test_case_6_nutrition_recalculates_after_edit():
    """
    TEST 6:
    Edit: Green Tea 1 cup -> Tea With Milk 2 cups
    Expected:
    Calories/macros/fiber recalculated according to 2 cups.
    """
    user_id = f"test_user_c6_{uuid.uuid4().hex[:6]}"
    session_id = f"session_c6_{uuid.uuid4().hex[:6]}"

    # Initial log: 1 cup green tea (2 kcal)
    res = await ChatService.handle_user_message(user_id, "me 1 cup green tea pidhi", session_id_input=session_id)
    grouped_cards = res["ui"]["groupedFoodCards"]
    entry_id = grouped_cards[0]["entries"][0]["id"]

    # Now simulate edit endpoint / update via FoodService and database
    db = get_db()
    existing = await db.daily_food_logs.find_one({"id": entry_id})
    assert existing is not None
    assert existing["calories"] == 2.0

    # User edits food to "Tea With Milk" and quantity to 2 cups
    target_food = "Tea With Milk"
    new_qty = 2.0
    resolved = await FoodService.resolve_food(target_food)
    multiplier = FoodService.calculate_portion_multiplier(
        base_unit=resolved.get("unit", "serving"),
        requested_unit="cup",
        quantity=new_qty,
        food_name=resolved["food_name"],
    )
    new_cal = round(resolved["calories"] * multiplier, 1)
    new_p = round(resolved["protein_g"] * multiplier, 1)

    # 1 cup Tea With Milk is ~60 kcal, so 2 cups is ~120 kcal
    assert new_cal >= 100, f"Expected recalculated calories >= 100, got {new_cal}"

    # Update in DB
    await db.daily_food_logs.update_one(
        {"id": entry_id},
        {"$set": {
            "food_name": resolved["food_name"],
            "food_id": resolved["food_id"],
            "quantity_amount": new_qty,
            "quantity_unit": "cup",
            "calories": new_cal,
            "protein_g": new_p,
        }}
    )

    updated_doc = await db.daily_food_logs.find_one({"id": entry_id})
    assert updated_doc["food_name"] == "Tea With Milk"
    assert updated_doc["quantity_amount"] == 2.0
    assert updated_doc["calories"] == new_cal

@pytest.mark.asyncio
async def test_case_7_delete_food_log():
    """
    TEST 7:
    Delete: Delete Green Tea.
    Expected:
    Only Green Tea is deleted.
    Previous food logs remain untouched.
    """
    user_id = f"test_user_c7_{uuid.uuid4().hex[:6]}"
    session_id = f"session_c7_{uuid.uuid4().hex[:6]}"

    # Log two distinct foods
    await ChatService.handle_user_message(user_id, "me 2 bhakri khadhi", session_id_input=session_id)
    res_gt = await ChatService.handle_user_message(user_id, "me 1 cup green tea pidhi", session_id_input=session_id)
    gt_entry_id = res_gt["ui"]["groupedFoodCards"][0]["entries"][0]["id"]

    db = get_db()
    # Delete only Green Tea
    del_res = await db.daily_food_logs.delete_one({"id": gt_entry_id, "user_id": user_id})
    assert del_res.deleted_count == 1

    # Verify Bhakri remains untouched
    remaining = await db.daily_food_logs.find({"user_id": user_id}).to_list(10)
    assert len(remaining) == 1
    assert "Bhakri" in remaining[0]["food_name"]

@pytest.mark.asyncio
async def test_case_8_current_log_card_does_not_show_previous_logs():
    """
    TEST 8:
    Log a new food after previous foods already exist.
    Expected:
    Current chat response shows ONLY the newly logged food.
    Previous foods are not displayed inside the new response card.
    """
    user_id = f"test_user_c8_{uuid.uuid4().hex[:6]}"
    session_id = f"session_c8_{uuid.uuid4().hex[:6]}"

    # 1. Log Bhakri
    await ChatService.handle_user_message(user_id, "me 2 bhakri khadhi", session_id_input=session_id)

    # 2. Log Tea With Milk
    await ChatService.handle_user_message(user_id, "me 1 cup tea with milk pidhi", session_id_input=session_id)

    # 3. Now log Green Tea
    res_green = await ChatService.handle_user_message(user_id, "me khali 1 cup green tea kari", session_id_input=session_id)

    # Check the UI cards returned for THIS response
    current_cards = res_green["ui"]["groupedFoodCards"]
    assert len(current_cards) == 1, f"Expected exactly 1 card in current response, got {len(current_cards)}"
    assert "Green Tea" in current_cards[0]["foodName"]
    assert "Bhakri" not in current_cards[0]["foodName"]
    assert "Tea With Milk" not in current_cards[0]["foodName"]

    # Verify daily dashboard still has all 3 foods
    all_daily = await FoodService.get_daily_grouped_food_cards(user_id, TimeService.get_current_local_date_str())
    assert len(all_daily["groupedFoodCards"]) == 3

@pytest.mark.asyncio
async def test_scenario_a_single_food_instant_and_persistence():
    """TEST A — SINGLE FOOD INSTANT DISPLAY & PERSISTENCE:
    Send: 'me aaje 1 cup green tea pidhi'
    Verify: Green Tea - 1 cup, meal = '—', has_explicit_time = False.
    Verify DB record exists in daily_food_logs.
    Simulate reload: read DB record, assert Green Tea still exists with 1 cup.
    """
    user_id = f"test_a_{uuid.uuid4().hex[:6]}"
    session_id = f"session_a_{uuid.uuid4().hex[:6]}"
    user_msg = "me aaje 1 cup green tea pidhi"

    res = await ChatService.handle_user_message(user_id, user_msg, session_id_input=session_id)
    assert res["success"] is True
    cards = res["ui"]["groupedFoodCards"]
    assert len(cards) == 1
    assert "Green Tea" in cards[0]["foodName"]
    assert cards[0]["totalQuantity"] == 1.0
    assert cards[0]["entries"][0]["mealType"] == "—"
    assert cards[0]["entries"][0]["timeFormatted"] == ""

    # Check database persistence
    db = get_db()
    logs = await db.daily_food_logs.find({"user_id": user_id}).to_list(10)
    assert len(logs) == 1
    assert logs[0]["food_name"] == "Green Tea"
    assert logs[0]["quantity_amount"] == 1.0

@pytest.mark.asyncio
async def test_scenario_b_edit_persistence():
    """TEST B — EDIT PERSISTENCE:
    Create: 1 Bhakri (130 kcal).
    Edit: Bhakri -> Roti 2 pieces via PATCH /food-logs/{id}.
    Expected immediately: Roti (208 kcal).
    Verify in DB: document now contains Roti.
    Simulate refresh: GET single food log returns Roti.
    Simulate chat refresh: get_session_messages returns Roti, NOT Bhakri.
    """
    from backend.app.routers.food_logs import update_food_log
    from backend.app.routers.chat import get_session_messages

    user_id = f"test_b_{uuid.uuid4().hex[:6]}"
    session_id = f"session_b_{uuid.uuid4().hex[:6]}"
    current_user = {"id": user_id}

    # 1. Create 1 Bhakri
    res = await ChatService.handle_user_message(user_id, "me 1 bhakri khadhi", session_id_input=session_id)
    log_id = res["ui"]["groupedFoodCards"][0]["entries"][0]["id"]

    # 2. PATCH Bhakri -> Roti, 2 pieces
    dto = UpdateFoodLogDto(foodName="Roti", quantity=2.0, unit="piece", mealType="—")
    patch_res = await update_food_log(id=log_id, dto=dto, current_user=current_user)
    assert patch_res["success"] is True
    assert patch_res["foodName"] == "Roti"
    assert patch_res["quantity"] == 2.0
    assert patch_res["calories"] == 208.0

    # 3. Read directly from Database: verify persisted
    db = get_db()
    db_doc = await db.daily_food_logs.find_one({"id": log_id, "user_id": user_id})
    assert db_doc is not None
    assert db_doc["food_name"] == "Roti"
    assert db_doc["quantity_amount"] == 2.0
    assert db_doc["calories"] == 208.0

    # 4. Simulate page refresh: call get_session_messages
    session_msgs = await get_session_messages(session_id=session_id, current_user=current_user)
    assistant_msg = [m for m in session_msgs if m["sender"] == "ASSISTANT"][0]
    import json
    raw_ent = json.loads(assistant_msg["rawEntities"])
    cards = raw_ent["groupedFoodCards"]
    assert len(cards) == 1
    assert cards[0]["foodName"] == "Roti"
    assert cards[0]["totalQuantity"] == 2.0
    assert cards[0]["totalCalories"] == 208
    assert cards[0]["entries"][0]["foodName"] == "Roti"

@pytest.mark.asyncio
async def test_scenario_c_edit_nutrition_and_total_kcal():
    """TEST C — EDIT NUTRITION & TOTAL KCAL:
    Create: 1 Bhakri (130 kcal) + 1 bowl Dal (120 kcal) -> total 250 kcal.
    Edit: Bhakri -> Roti 2 pieces (208 kcal) -> new total should be 208 + 120 = 328 kcal.
    Verify: dailyNutritionSummary.totalCalories is updated to 328 immediately and after refresh.
    """
    from backend.app.routers.food_logs import update_food_log
    from backend.app.routers.chat import get_session_messages

    user_id = f"test_c_{uuid.uuid4().hex[:6]}"
    session_id = f"session_c_{uuid.uuid4().hex[:6]}"
    current_user = {"id": user_id}

    # Log Bhakri and Dal
    res1 = await ChatService.handle_user_message(user_id, "me 1 bhakri khadhi", session_id_input=session_id)
    bhakri_id = res1["ui"]["groupedFoodCards"][0]["entries"][0]["id"]
    await ChatService.handle_user_message(user_id, "me 1 bowl dal pidhi", session_id_input=session_id)

    # Edit Bhakri -> Roti 2 pieces
    dto = UpdateFoodLogDto(foodName="Roti", quantity=2.0, unit="piece", mealType="—")
    patch_res = await update_food_log(id=bhakri_id, dto=dto, current_user=current_user)

    assert patch_res["dailyNutritionSummary"]["totalCalories"] == 328  # 208 (Roti) + 120 (Dal)

    # Simulate refresh: get_session_messages
    session_msgs = await get_session_messages(session_id=session_id, current_user=current_user)
    import json
    raw_ent = json.loads(session_msgs[-1]["rawEntities"])
    assert raw_ent["dailyNutritionSummary"]["totalCalories"] == 328

@pytest.mark.asyncio
async def test_scenario_d_delete_persistence():
    """TEST D — DELETE PERSISTENCE:
    Create: Bhakri.
    Delete Bhakri via DELETE /food-logs/{id}.
    Verify: DB document deleted.
    Simulate refresh: get_session_messages removes the card, Bhakri does not come back!
    """
    from backend.app.routers.food_logs import delete_food_log
    from backend.app.routers.chat import get_session_messages

    user_id = f"test_d_{uuid.uuid4().hex[:6]}"
    session_id = f"session_d_{uuid.uuid4().hex[:6]}"
    current_user = {"id": user_id}

    res = await ChatService.handle_user_message(user_id, "me 1 bhakri khadhi", session_id_input=session_id)
    bhakri_id = res["ui"]["groupedFoodCards"][0]["entries"][0]["id"]

    # Delete
    del_res = await delete_food_log(id=bhakri_id, current_user=current_user)
    assert del_res["deleted"] is True

    # Verify DB
    db = get_db()
    existing = await db.daily_food_logs.find_one({"id": bhakri_id})
    assert existing is None

    # Simulate refresh
    session_msgs = await get_session_messages(session_id=session_id, current_user=current_user)
    import json
    raw_ent = json.loads(session_msgs[-1]["rawEntities"])
    assert len(raw_ent["groupedFoodCards"]) == 0

@pytest.mark.asyncio
async def test_scenario_e_multiple_foods():
    """TEST E — MULTIPLE FOODS:
    Send: "me 2 rotli ane 1 bowl dal khai"
    Expected:
    Two separate records in DB: Roti (qty: 2) and Dal (qty: 1).
    Both immediately visible in response.
    Both present after refresh.
    """
    from backend.app.routers.chat import get_session_messages

    user_id = f"test_e_{uuid.uuid4().hex[:6]}"
    session_id = f"session_e_{uuid.uuid4().hex[:6]}"
    current_user = {"id": user_id}

    res = await ChatService.handle_user_message(user_id, "me 2 rotli ane 1 bowl dal khai", session_id_input=session_id)
    assert res["success"] is True

    cards = res["ui"]["groupedFoodCards"]
    assert len(cards) == 2
    names = [c["foodName"] for c in cards]
    assert "Roti" in names
    assert any("Dal" in n for n in names)

    # Check DB
    db = get_db()
    db_items = await db.daily_food_logs.find({"user_id": user_id}).to_list(10)
    assert len(db_items) == 2
    db_names = [d["food_name"] for d in db_items]
    assert "Roti" in db_names
    assert any("Dal" in n for n in db_names)

    # Verify both have unique IDs
    assert db_items[0]["id"] != db_items[1]["id"]

    # Simulate refresh
    session_msgs = await get_session_messages(session_id=session_id, current_user=current_user)
    import json
    raw_ent = json.loads(session_msgs[-1]["rawEntities"])
    ref_cards = raw_ent["groupedFoodCards"]
    assert len(ref_cards) == 2

@pytest.mark.asyncio
async def test_scenario_f_three_foods():
    """TEST F — THREE FOODS:
    Send: "me 2 eggs, 1 cup tea and 1 banana khadha"
    Expected:
    3 separate food records.
    All appear immediately, persist in DB, contribute to total calories.
    """
    user_id = f"test_f_{uuid.uuid4().hex[:6]}"
    session_id = f"session_f_{uuid.uuid4().hex[:6]}"

    res = await ChatService.handle_user_message(user_id, "me 2 eggs, 1 cup tea and 1 banana khadha", session_id_input=session_id)
    assert res["success"] is True

    cards = res["ui"]["groupedFoodCards"]
    assert len(cards) == 3
    names = [c["foodName"] for c in cards]
    assert any("Egg" in n for n in names)
    assert any("Tea" in n for n in names)
    assert any("Banana" in n for n in names)

    # Check DB
    db = get_db()
    db_items = await db.daily_food_logs.find({"user_id": user_id}).to_list(10)
    assert len(db_items) == 3

@pytest.mark.asyncio
async def test_scenario_g_edit_one_of_multiple_foods():
    """TEST G — EDIT ONE OF MULTIPLE FOODS:
    Existing: Roti, Dal, Green Tea.
    Edit: Roti -> Bhakri (1 piece).
    Expected:
    Bhakri, Dal, Green Tea.
    Only Roti changes; Dal and Green Tea remain unchanged.
    """
    from backend.app.routers.food_logs import update_food_log

    user_id = f"test_g_{uuid.uuid4().hex[:6]}"
    session_id = f"session_g_{uuid.uuid4().hex[:6]}"
    current_user = {"id": user_id}

    # Log 3 foods
    r1 = await ChatService.handle_user_message(user_id, "me 2 rotli khai", session_id_input=session_id)
    roti_id = r1["ui"]["groupedFoodCards"][0]["entries"][0]["id"]
    await ChatService.handle_user_message(user_id, "me 1 bowl dal khai", session_id_input=session_id)
    await ChatService.handle_user_message(user_id, "me 1 cup green tea pidhi", session_id_input=session_id)

    # Edit only Roti -> Bhakri
    dto = UpdateFoodLogDto(foodName="Bhakri", quantity=1.0, unit="piece")
    patch_res = await update_food_log(id=roti_id, dto=dto, current_user=current_user)

    db = get_db()
    all_logs = await db.daily_food_logs.find({"user_id": user_id}).to_list(10)
    assert len(all_logs) == 3
    names = [d["food_name"] for d in all_logs]
    assert "Bhakri" in names
    assert any("Dal" in n for n in names)
    assert "Green Tea" in names
    assert "Roti" not in names

