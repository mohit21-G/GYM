import pytest
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.abspath("."))

from backend.app.services.time_service import TimeService
from backend.app.services.agent_nlp import AgentNLP
from backend.app.services.food_service import FoodService
from backend.app.services.activity_service import ActivityService
from backend.app.schemas.food_log import FoodItemInput

IST = ZoneInfo("Asia/Kolkata")

def test_time_service_current_time_when_omitted():
    """Requirement 1: When user doesn't mention time, use current local time (Asia/Kolkata)."""
    text = "Aaje protein shake lidho"
    dt = TimeService.parse_explicit_or_relative_time(text)
    now_ist = datetime.now(IST)
    assert dt.tzinfo is not None
    assert dt.date() == now_ist.date()
    # Should be close to current time (within 10 seconds)
    diff = abs((now_ist - dt).total_seconds())
    assert diff < 10

def test_time_service_explicit_times():
    """Requirement 2: Explicit times must always win with 24h normalization."""
    # 4:27 PM
    dt1 = TimeService.parse_explicit_or_relative_time("At 4:27 PM protein shake lidho")
    assert dt1.hour == 16 and dt1.minute == 27

    # 4:27 AM
    dt2 = TimeService.parse_explicit_or_relative_time("4:27 AM xyz khadhu")
    assert dt2.hour == 4 and dt2.minute == 27

    # Gujarati script: સાંજે 4:27
    dt3 = TimeService.parse_explicit_or_relative_time("સાંજે 4:27 પ્રોટીન શેક પીધો")
    assert dt3.hour == 16 and dt3.minute == 27

    # Hindi script: शाम 4:27
    dt4 = TimeService.parse_explicit_or_relative_time("शाम 4:27 बजे प्रोटीन शेक लिया")
    assert dt4.hour == 16 and dt4.minute == 27

    # Romanized: sanje 4:27
    dt5 = TimeService.parse_explicit_or_relative_time("sanje 4:27 xyz khadhu")
    assert dt5.hour == 16 and dt5.minute == 27

    # Romanized: savare 8:30
    dt6 = TimeService.parse_explicit_or_relative_time("savare 8:30 breakfast karyu")
    assert dt6.hour == 8 and dt6.minute == 30

    # Romanized: bapore 1:15
    dt7 = TimeService.parse_explicit_or_relative_time("bapore 1:15 rotli khai")
    assert dt7.hour == 13 and dt7.minute == 15

    # Gujarati: સવારે 8:30
    dt8 = TimeService.parse_explicit_or_relative_time("સવારે 8:30 નાસ્તો કર્યો")
    assert dt8.hour == 8 and dt8.minute == 30

    # Gujarati: બપોરે 1:15
    dt9 = TimeService.parse_explicit_or_relative_time("બપોરે 1:15 રોટલી ખાધી")
    assert dt9.hour == 13 and dt9.minute == 15

def test_meal_type_inference():
    """Requirement 3: Meal type inference priority (explicit wording, context/period, clock range)."""
    # Explicit wording
    assert TimeService.infer_meal_type("savare 8:30 breakfast karyu", datetime(2026, 9, 30, 8, 30, tzinfo=IST)) == "BREAKFAST"
    assert TimeService.infer_meal_type("bapore 1:15 lunch lidhu", datetime(2026, 9, 30, 13, 15, tzinfo=IST)) == "LUNCH"
    assert TimeService.infer_meal_type("dinner ma rotli khai", datetime(2026, 9, 30, 20, 0, tzinfo=IST)) == "DINNER"

    # Contextual time/food
    assert TimeService.infer_meal_type("Savare 8:30 poha khadha", datetime(2026, 9, 30, 8, 30, tzinfo=IST)) == "BREAKFAST"
    assert TimeService.infer_meal_type("Bapore 1:15 dal rice khadha", datetime(2026, 9, 30, 13, 15, tzinfo=IST)) == "LUNCH"
    assert TimeService.infer_meal_type("Sanje 4:27 protein shake lidho", datetime(2026, 9, 30, 16, 27, tzinfo=IST)) == "SNACK"
    assert TimeService.infer_meal_type("Ratre 9:00 dal roti khai", datetime(2026, 9, 30, 21, 0, tzinfo=IST)) == "DINNER"

    # Clock time based
    assert TimeService.infer_meal_type("kahi lidhu", datetime(2026, 9, 30, 8, 0, tzinfo=IST)) == "BREAKFAST"
    assert TimeService.infer_meal_type("kahi lidhu", datetime(2026, 9, 30, 13, 0, tzinfo=IST)) == "LUNCH"
    assert TimeService.infer_meal_type("kahi lidhu", datetime(2026, 9, 30, 17, 0, tzinfo=IST)) == "SNACK"
    assert TimeService.infer_meal_type("kahi lidhu", datetime(2026, 9, 30, 21, 0, tzinfo=IST)) == "DINNER"

def test_multiple_food_items_extraction():
    """Requirement 5: Extract multiple food items in a single message."""
    text1 = "2 rotli and 1 bowl dal khai"
    foods1 = AgentNLP.extract_food_entities_heuristically(text1)
    names1 = [f.get("food", f.get("food_name", "")).lower() for f in foods1]
    assert any("rotli" in n or "roti" in n for n in names1)
    assert any("dal" in n for n in names1)
    assert len(foods1) >= 2

    text2 = "Savare 2 eggs, 1 toast ane 1 glass milk lidhu"
    foods2 = AgentNLP.extract_food_entities_heuristically(text2)
    assert len(foods2) >= 3
    names2 = [f.get("food", f.get("food_name", "")).lower() for f in foods2]
    assert any("egg" in n for n in names2)
    assert any("toast" in n for n in names2)
    assert any("milk" in n for n in names2)

    text3 = "Aaje lunch ma 2 rotli, dal, rice ane salad khadhu"
    foods3 = AgentNLP.extract_food_entities_heuristically(text3)
    assert len(foods3) >= 4
    names3 = [f.get("food", f.get("food_name", "")).lower() for f in foods3]
    assert any("rotli" in n or "roti" in n for n in names3)
    assert any("dal" in n for n in names3)
    assert any("rice" in n for n in names3)
    assert any("salad" in n for n in names3)

def test_multiple_exercises_extraction():
    """Requirement 6: Support multiple activities in one message."""
    text1 = "30 min walking and 20 min cycling kari"
    acts1 = AgentNLP.extract_activity_entities(text1)
    assert len(acts1) == 2
    act_names1 = [a["activity_name"].lower() for a in acts1]
    assert "walking" in act_names1
    assert "cycling" in act_names1

    text2 = "20 min running, 15 min strength training and 10 min walking"
    acts2 = AgentNLP.extract_activity_entities(text2)
    assert len(acts2) == 3
    act_names2 = [a["activity_name"].lower() for a in acts2]
    assert "running" in act_names2
    assert any("strength" in a for a in act_names2)
    assert "walking" in act_names2

def test_mixed_food_and_exercise():
    """Requirement 7: Mixed food and exercise detection."""
    text1 = "Savare 2 eggs ane 1 glass milk lidhu, pachi 30 minute walk kari"
    foods1 = AgentNLP.extract_food_entities_heuristically(text1)
    acts1 = AgentNLP.extract_activity_entities(text1)
    assert len(foods1) >= 2
    assert len(acts1) >= 1
    assert any("walk" in a["activity_name"].lower() for a in acts1)

    text2 = "At 4:27 protein shake lidho and 20 min cycling kari"
    foods2 = AgentNLP.extract_food_entities_heuristically(text2)
    acts2 = AgentNLP.extract_activity_entities(text2)
    assert len(foods2) >= 1
    assert len(acts2) >= 1
    assert acts2[0]["logged_at"] is not None
    assert "16:27" in acts2[0]["logged_at"]
    assert foods2[0]["logged_at"] is not None
    assert "16:27" in foods2[0]["logged_at"]

def test_structured_actions_extraction():
    """Requirement 8: AI / NLP extracts structured actions schema."""
    text = "Savare 2 eggs ane 1 glass milk lidhu, pachi 30 minute walk kari"
    actions = AgentNLP.extract_structured_actions(text)
    assert len(actions) >= 3
    action_types = [a["type"] for a in actions]
    assert action_types.count("CREATE_FOOD_LOG") >= 2
    assert action_types.count("CREATE_ACTIVITY_LOG") >= 1

def test_multiline_message_parsing_different_times():
    """Requirement 12: Multiline message parsing with distinct times per line."""
    text = """8:30 AM 2 eggs khadha
1:00 PM dal rice khadhu
6:00 PM 30 min walking kari"""

    foods = AgentNLP.extract_food_entities_heuristically(text)
    acts = AgentNLP.extract_activity_entities(text)

    assert len(foods) >= 3 # eggs, dal, rice
    assert len(acts) >= 1 # walking

    # Check eggs has 08:30
    egg_item = next(f for f in foods if "egg" in f.get("food", f.get("food_name", "")).lower())
    assert "08:30" in egg_item["logged_at"]

    # Check dal or rice has 13:00
    dal_item = next(f for f in foods if "dal" in f.get("food", f.get("food_name", "")).lower())
    assert "13:00" in dal_item["logged_at"]

    # Check walk has 18:00
    walk_act = acts[0]
    assert "18:00" in walk_act["logged_at"]

@pytest.mark.asyncio
async def test_partial_ambiguous_food_handling():
    """Requirement 13: Do not silently lose valid items when one item is ambiguous."""
    valid_item = FoodItemInput(
        food="Roti",
        quantity=2.0,
        unit="piece",
        is_recognized=True,
        requires_clarification=False,
    )
    ambiguous_item = FoodItemInput(
        food="xyzunrealfood",
        quantity=1.0,
        unit="serving",
        is_recognized=False,
        requires_clarification=True,
        clarification_reason="UNKNOWN_FOOD",
    )
    result = await FoodService.process_and_log_food(
        user_id="test_user_partial",
        items=[valid_item, ambiguous_item],
    )
    # The valid item (Roti) should be logged
    assert len(result.loggedItems) == 1
    assert result.loggedItems[0]["food"] == "Roti"
    # Clarification is requested for the unknown item
    assert result.requiresClarification is True
    assert "xyzunrealfood" in result.replyText
