import pytest
import os
import sys
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.abspath("."))

from backend.app.services.time_service import TimeService
from backend.app.services.agent_nlp import AgentNLP
from backend.app.services.food_service import FoodService
from backend.app.services.activity_service import ActivityService
from backend.app.services.chat_service import ChatService
from backend.app.schemas.food_log import FoodItemInput
from backend.app.database import get_db

IST = ZoneInfo("Asia/Kolkata")

def test_fake_clock_testing_and_omitted_time():
    """Requirement 1, 2, 15: Single source of truth with frozen/mock clock test."""
    mock_now = datetime(2026, 9, 30, 10, 8, 35, tzinfo=IST)
    TimeService.set_mock_now(mock_now)
    try:
        now_dt = TimeService.get_current_local_datetime()
        assert now_dt == mock_now
        assert now_dt.hour == 10
        assert now_dt.minute == 8
        assert now_dt.second == 35

        # When time is omitted, message gets approximately the exact frozen timestamp
        text = "Aaje protein shake lidho"
        parsed_dt = TimeService.parse_explicit_or_relative_time(text)
        assert parsed_dt == mock_now
        assert parsed_dt.strftime("%Y-%m-%d %H:%M:%S") == "2026-09-30 10:08:35"
        assert parsed_dt.tzinfo == IST
    finally:
        TimeService.reset_mock_now()

def test_explicit_time_override():
    """Requirement 3: Explicit time always overrides current time."""
    test_cases = [
        "4:27 protein shake lidho",
        "4:27 PM protein shake lidho",
        "at 4:27 PM protein shake lidho",
        "sanje 4:27 protein shake lidho",
        "સાંજે 4:27 પ્રોટીન શેક પીધો",
        "शाम 4:27 प्रोटीन शेक लिया",
    ]
    for msg in test_cases:
        dt = TimeService.parse_explicit_or_relative_time(msg)
        assert dt.hour == 16, f"Failed hour for {msg}: got {dt.hour}"
        assert dt.minute == 27, f"Failed minute for {msg}: got {dt.minute}"

def test_exact_date_rules():
    """Requirement 4: Centralized date rules (today, yesterday, tomorrow, DD/MM/YYYY, ISO)."""
    ref_d = date(2026, 9, 30)

    # Today
    for phrase in ["today", "aaje", "આજે", "aaj", "आज"]:
        d, has = TimeService.parse_date_from_text(f"{phrase} rotli khai", reference_date=ref_d)
        assert has is True
        assert d == ref_d

    # Yesterday
    for phrase in ["yesterday", "gaya kale", "ગઈકાલે", "ગઈ કાલે", "kal"]:
        d, has = TimeService.parse_date_from_text(f"{phrase} rotli khai", reference_date=ref_d)
        assert has is True
        assert d == ref_d - timedelta(days=1)

    # Tomorrow
    for phrase in ["tomorrow", "aavti kale", "આવતીકાલે"]:
        d, has = TimeService.parse_date_from_text(f"{phrase} gym jaavu", reference_date=ref_d)
        assert has is True
        assert d == ref_d + timedelta(days=1)

    # Indian numeric format: DD/MM/YYYY
    d1, has1 = TimeService.parse_date_from_text("30/09/2026 rotli khai")
    assert has1 is True and d1 == date(2026, 9, 30)

    d2, has2 = TimeService.parse_date_from_text("30-09-2026 rotli khai")
    assert has2 is True and d2 == date(2026, 9, 30)

    # Indian format 03/04/2026 must be 3rd April 2026, not 4th March!
    d3, has3 = TimeService.parse_date_from_text("03/04/2026 rotli khai")
    assert has3 is True and d3 == date(2026, 4, 3)

    # ISO format YYYY-MM-DD
    d4, has4 = TimeService.parse_date_from_text("2026-09-30 rotli khai")
    assert has4 is True and d4 == date(2026, 9, 30)

def test_date_plus_time_combinations():
    """Requirement 5: Date + Time combination semantics without leaking yesterday's time to today."""
    ref_now = datetime(2026, 9, 30, 10, 0, 0, tzinfo=IST)
    TimeService.set_mock_now(ref_now)
    try:
        # yesterday 11:30 PM
        dt1, has1 = TimeService.extract_time_from_text("yesterday 11:30 PM protein shake lidho")
        assert has1 is True
        assert dt1.date() == date(2026, 9, 29)
        assert dt1.hour == 23 and dt1.minute == 30

        # 30/09/2026 4:27 PM
        dt2, has2 = TimeService.extract_time_from_text("30/09/2026 4:27 PM protein shake lidho")
        assert has2 is True
        assert dt2.date() == date(2026, 9, 30)
        assert dt2.hour == 16 and dt2.minute == 27

        # ગઈકાલે રાત્રે 11:30 વાગ્યે
        dt3, has3 = TimeService.extract_time_from_text("ગઈકાલે રાત્રે 11:30 વાગ્યે walk kari")
        assert has3 is True
        assert dt3.date() == date(2026, 9, 29)
        assert dt3.hour == 23 and dt3.minute == 30
    finally:
        TimeService.reset_mock_now()

def test_midnight_boundary():
    """Requirement 6: Midnight boundary handling around 23:59, 00:00, 00:01 and 12:05 AM."""
    ref_now = datetime(2026, 9, 30, 15, 0, 0, tzinfo=IST)
    TimeService.set_mock_now(ref_now)
    try:
        # Today at 12:05 AM -> hour 0, minute 5
        dt1 = TimeService.parse_explicit_or_relative_time("Today at 12:05 AM protein shake lidho")
        assert dt1.date() == date(2026, 9, 30)
        assert dt1.hour == 0 and dt1.minute == 5

        # 23:59
        dt2 = TimeService.parse_explicit_or_relative_time("at 23:59 protein shake lidho")
        assert dt2.hour == 23 and dt2.minute == 59

        # 00:01
        dt3 = TimeService.parse_explicit_or_relative_time("at 00:01 protein shake lidho")
        assert dt3.hour == 0 and dt3.minute == 1
    finally:
        TimeService.reset_mock_now()

def test_relative_time_crossing_midnight():
    """Requirement 10 & 15: Relative time crossing local midnight."""
    # Frozen clock: 2026-10-01 01:00:00 Asia/Kolkata
    mock_now = datetime(2026, 10, 1, 1, 0, 0, tzinfo=IST)
    TimeService.set_mock_now(mock_now)
    try:
        # "2 hours ago" must resolve to 2026-09-30 23:00 Asia/Kolkata
        dt, has = TimeService.extract_time_from_text("2 hours ago 30 min walking kari")
        assert has is True
        assert dt.date() == date(2026, 9, 30)
        assert dt.hour == 23 and dt.minute == 0
        assert dt.tzinfo == IST
    finally:
        TimeService.reset_mock_now()

def test_multiline_date_time_context_inheritance():
    """Requirement 11: Blocks inherit nearest header date/time context without leaking."""
    text = """8:30 AM
2 eggs khadha

1:00 PM
dal rice khadhu

6:00 PM
30 min walking kari"""

    foods = AgentNLP.extract_food_entities_heuristically(text)
    acts = AgentNLP.extract_activity_entities(text)

    assert len(foods) >= 3 # eggs, dal, rice
    assert len(acts) >= 1  # walking

    # Eggs inherited 08:30 AM
    egg = next(f for f in foods if "egg" in f.get("food", f.get("food_name", "")).lower())
    assert "08:30" in egg["logged_at"]
    assert egg["meal_type"] == "BREAKFAST"

    # Dal inherited 13:00 PM
    dal = next(f for f in foods if "dal" in f.get("food", f.get("food_name", "")).lower())
    assert "13:00" in dal["logged_at"]
    assert dal["meal_type"] == "LUNCH"

    # Walking inherited 18:00 (6:00 PM) without leaking 8:30 AM or 1:00 PM!
    walk = acts[0]
    assert "18:00" in walk["logged_at"]

def test_prevent_time_quantity_collision():
    """Requirement 12: Ensure time digits are not misidentified as food quantities."""
    f1 = AgentNLP.extract_food_entities_heuristically("8:30 AM 2 eggs khadha")
    assert len(f1) == 1
    assert f1[0]["quantity"] == 2.0
    assert "08:30" in f1[0]["logged_at"]

    f2 = AgentNLP.extract_food_entities_heuristically("4:27 PM 2 rotli khadhi")
    assert len(f2) == 1
    assert f2[0]["quantity"] == 2.0
    assert "16:27" in f2[0]["logged_at"]

@pytest.mark.asyncio
async def test_duplicate_prevention_and_legitimate_separate_logs():
    """Requirement 13: Prevent accidental retries while preserving legitimate separate time logs."""
    user_id = "test_user_dedup_1"
    
    # 1. First log: 10:00 AM 2 eggs
    item1 = FoodItemInput(
        food="Boiled Egg",
        quantity=2.0,
        unit="piece",
        logged_at="2026-09-30T10:00:00+05:30",
        is_recognized=True,
    )
    res1 = await FoodService.process_and_log_food(user_id=user_id, items=[item1])
    assert len(res1.loggedItems) == 1
    first_id = res1.loggedItems[0]["id"]

    # 2. Immediate retry of identical 10:00 AM log -> should be deduplicated (return same log_doc)
    res1_retry = await FoodService.process_and_log_food(user_id=user_id, items=[item1])
    assert len(res1_retry.loggedItems) == 1
    assert res1_retry.loggedItems[0]["id"] == first_id

    # 3. Legitimate separate log: 11:00 AM 2 eggs -> must NOT be discarded
    item2 = FoodItemInput(
        food="Boiled Egg",
        quantity=2.0,
        unit="piece",
        logged_at="2026-09-30T11:00:00+05:30",
        is_recognized=True,
    )
    res2 = await FoodService.process_and_log_food(user_id=user_id, items=[item2])
    assert len(res2.loggedItems) == 1
    second_id = res2.loggedItems[0]["id"]
    assert second_id != first_id

@pytest.mark.asyncio
async def test_end_to_end_chat_service_exact_required_messages():
    """Requirement 14: Real end-to-end execution of all required test phrases."""
    user_id = "test_user_e2e_all"

    # 1. Aaje protein shake lidho
    r1 = await ChatService.handle_user_message(user_id, "Aaje protein shake lidho")
    assert r1["success"] is True

    # 2. At 4:27 PM protein shake lidho
    r2 = await ChatService.handle_user_message(user_id, "At 4:27 PM protein shake lidho")
    assert r2["success"] is True

    # 3. 4:27 protein shake lidho
    r3 = await ChatService.handle_user_message(user_id, "4:27 protein shake lidho")
    assert r3["success"] is True

    # 4. સાંજે 4:27 પ્રોટીન શેક પીધો
    r4 = await ChatService.handle_user_message(user_id, "સાંજે 4:27 પ્રોટીન શેક પીધો")
    assert r4["success"] is True

    # 5. शाम 4:27 बजे प्रोटीन शेक लिया
    r5 = await ChatService.handle_user_message(user_id, "शाम 4:27 बजे प्रोटीन शेक लिया")
    assert r5["success"] is True

    # 6. Savare 8:30 poha khadha
    r6 = await ChatService.handle_user_message(user_id, "Savare 8:30 poha khadha")
    assert r6["success"] is True

    # 7. Bapore 1:15 dal rice khadha
    r7 = await ChatService.handle_user_message(user_id, "Bapore 1:15 dal rice khadha")
    assert r7["success"] is True

    # 8. Ratre 9:00 dal roti khai
    r8 = await ChatService.handle_user_message(user_id, "Ratre 9:00 dal roti khai")
    assert r8["success"] is True

    # 9. Gai kale ratre 11:30 protein shake lidho
    r9 = await ChatService.handle_user_message(user_id, "Gai kale ratre 11:30 protein shake lidho")
    assert r9["success"] is True

    # 10. 2 hours ago 30 min walking kari
    r10 = await ChatService.handle_user_message(user_id, "2 hours ago 30 min walking kari")
    assert r10["success"] is True

    # 11. Multiline message with 3 blocks
    multiline_msg = """8:30 AM 2 eggs khadha
1:00 PM dal rice khadhu
6:00 PM 30 min walking kari"""
    r11 = await ChatService.handle_user_message(user_id, multiline_msg)
    assert r11["success"] is True
    assert "Food:" in r11["message"] or "Logged successfully" in r11["message"]
