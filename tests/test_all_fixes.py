import pytest
import os
import sys

sys.path.insert(0, os.path.abspath("."))

from backend.app.services.agent_nlp import AgentNLP
from backend.app.services.food_service import FoodService

def test_false_positive_prevention():
    fps = [
        "I ate 0 Basundi",
        "I ate 0 Cooked White Rice",
        "Sham ko Sev Tameta Nu Shaak khane ka plan hai",
        "Sanju Chole Chana Masala khavu padashe",
        "आज मैंने Basundi नहीं खाया",
        "મેં આજે કંઈ ખાધું નથી",
        "Suppose I have Aloo Sabzi for dinner",
        "Planning to have Moong Dal Khichdi for dinner tonight",
        "is roti healthy?",
        "what if I eat 2 rotis",
        "Drank 0 ml water",
        "haven't eaten anything today",
    ]
    for text in fps:
        intent = AgentNLP.detect_intent(text)
        assert intent == "GENERAL_CHAT", f"Expected GENERAL_CHAT for '{text}', got '{intent}'"

def test_food_intent_multilingual():
    foods = [
        ("1 બાસુંદી", "CREATE_FOOD_LOG"),
        ("1.5 ખીચડી", "CREATE_FOOD_LOG"),
        ("1 ભીંડી", "CREATE_FOOD_LOG"),
        ("2 મોહનથાળ", "CREATE_FOOD_LOG"),
        ("1 पोहा", "CREATE_FOOD_LOG"),
        ("2khakhra lunch me", "CREATE_FOOD_LOG"),
        ("1.5rajma lunch me", "CREATE_FOOD_LOG"),
        ("2chach lunch me", "CREATE_FOOD_LOG"),
        ("1 સમોસા", "CREATE_FOOD_LOG"),
        ("Ate 2 Sev Tameta Nu Shaak'; DROP TABLE daily_food_logs; --", "CREATE_FOOD_LOG"),
    ]
    for text, exp in foods:
        intent = AgentNLP.detect_intent(text)
        assert intent == exp, f"Expected {exp} for '{text}', got '{intent}'"

def test_multi_food_extraction_preserves_all_items():
    # Tests that 2 roti is NOT stripped by unit mapper
    text = "me 2 roti and thodu bateka ni subji khadhi"
    extracted = AgentNLP.extract_food_entities_heuristically(text)
    assert len(extracted) == 2, f"Expected 2 items for '{text}', got {len(extracted)}: {extracted}"
    
    assert extracted[0]["food"] == "Roti"
    assert extracted[0]["quantity"] == 2.0
    assert extracted[0]["unit"] == "piece"
    
    assert extracted[1]["food"] in ["Aloo Sabzi", "Bateka Subji", "Bateka Ni Subji"]
    assert extracted[1]["quantity"] == 0.5

@pytest.mark.asyncio
async def test_canonical_food_resolution():
    cases = [
        ("Sev Tameta Nu Shaak", "Sev Tameta Nu Shaak"),
        ("sev tameta", "Sev Tameta Nu Shaak"),
        ("Mixed Vegetable Sabzi", "Mixed Vegetable Sabzi"),
        ("Butter Naan", "Butter Naan"),
        ("Gujarati Kadhi", "Gujarati Kadhi"),
        ("Basundi", "Basundi"),
        ("Moong Dal Khichdi", "Moong Dal Khichdi"),
        ("Bhindi Masala", "Bhindi Masala"),
        ("Surti Undhiyu", "Surti Undhiyu"),
        ("Onion Tomato Uttapam", "Onion Tomato Uttapam"),
        ("Masala Dosa", "Masala Dosa"),
        ("Poha", "Poha"),
    ]
    for q, exp in cases:
        res = await FoodService.resolve_food(q)
        assert res["food_name"] == exp, f"Expected '{exp}' for '{q}', got '{res.get('food_name')}'"

@pytest.mark.asyncio
async def test_previously_partial_food_cases():
    test_cases = [
        ("Aaje 1 okra sabzi khadhu", "Bhindi Masala"),
        ("1નાયલોન ખમણ બપોરે લીધી", "Khaman Dhokla"),
        ("Had 1.5 bowl of kidney beans", "Rajma"),
        ("2 છોલે snack में लिया", "Chole Chana Masala"),
        ("Aaje 2 jilapi khadhu", "Jalebi"),
        ("I ate 1 piece of paneer paratha for breakfast", "Paneer Paratha"),
        ("Logged 2 pneer paratha", "Paneer Paratha"),
        ("Had 1 bowl of aloo gobi", "Aloo Sabzi"),
        ("I ate 2 piece of egg omelette for dinner", "Egg Omelette"),
        ("મેં 2 દાળ ઢોકળી લીધી", "Gujarati Dal Dhokli"),
    ]
    for text, exp in test_cases:
        items = AgentNLP.extract_food_entities_heuristically(text)
        assert len(items) > 0, f"No food extracted for '{text}'"
        actual_name = items[0]["food"]
        res = await FoodService.resolve_food(actual_name)
        assert res["food_name"] == exp, f"For input '{text}', extracted '{actual_name}' but resolved to '{res.get('food_name')}', expected '{exp}'"


def test_sleep_intent_and_duration():
    sleeps = [
        ("ગઈકાલે રાત્રે 7 કલાક ઊંઘ લીધી", 420),
        ("रात को 8 घंटे की अच्छी नींद ली", 480),
        ("slept 7.5 hours", 450),
    ]
    for text, exp_mins in sleeps:
        intent = AgentNLP.detect_intent(text)
        assert intent == "CREATE_SLEEP_LOG", f"Expected CREATE_SLEEP_LOG for '{text}', got '{intent}'"
        ent = AgentNLP.extract_sleep_entity(text)
        assert ent["durationMinutes"] == exp_mins, f"Expected {exp_mins} mins for '{text}', got {ent.get('durationMinutes')}"

def test_savar_and_sanje_rotlo_bhadthu():
    # Case 1: "aaje me savar ma  bhakri khadhi"
    t1 = "aaje me savar ma  bhakri khadhi"
    ext1 = AgentNLP.extract_food_entities_heuristically(t1)
    assert len(ext1) == 1
    assert ext1[0]["food"] == "Bhakri"
    assert ext1[0]["mealType"] == "BREAKFAST"

    # Case 2: "sanje me bhadthu and rotlo khadho"
    t2 = "sanje me bhadthu and rotlo khadho"
    ext2 = AgentNLP.extract_food_entities_heuristically(t2)
    assert len(ext2) == 2
    assert ext2[0]["food"] == "Baingan Bharta"
    assert ext2[0]["mealType"] == "DINNER"
    assert "Rotlo" in ext2[1]["food"]
    assert ext2[1]["mealType"] == "DINNER"

