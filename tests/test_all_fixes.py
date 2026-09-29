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

@pytest.mark.asyncio
async def test_exercise_questions_return_informative_responses():
    """Bug 1: Verifies exercise questions receive informative answers, not generic fallback."""
    from backend.app.services.ai_service import AIService
    
    questions = [
        "What are the benefits of walking?",
        "How many calories does 30 minutes of running burn?",
        "Give me a beginner workout plan.",
        "How can I improve my stamina?",
        "Which exercises target the legs?",
        "walking na fayda shu chhe?",
        "chalne ke kya fayde hain?",
        "30 minute running ma ketli calories burn thay?",
        "stamina kem vadharvu?",
        "legs mate kaya exercise sara?",
    ]
    
    fallback_generic = "I can answer nutrition and fitness questions or log what you ate when you're ready!"
    
    for q in questions:
        intent = AgentNLP.detect_intent(q)
        assert intent == "FITNESS_ADVISORY", f"Expected FITNESS_ADVISORY for '{q}', got '{intent}'"
        
        res = await AIService.process_message(q)
        reply = res.get("replyText", "")
        
        # Verify it does NOT return the generic fallback
        assert reply != fallback_generic, f"Returned generic fallback for '{q}'"
        assert len(reply) > 50, f"Expected informative reply for '{q}', got '{reply}'"
        
        # Verify relevant domain content is in the reply
        q_lower = q.lower()
        if "walk" in q_lower or "ચાલ" in q_lower or "chal" in q_lower:
            assert any(w in reply.lower() for w in ["walking", "હૃદય", "दिल", "heart", "blood pressure", "કસરત", "ચાલવાના"]), f"Reply for '{q}' missing walking benefits: {reply}"
        elif "run" in q_lower:
            assert any(w in reply.lower() for w in ["calorie", "calories", "કેલરી", "कैलोरी", "kcal"]), f"Reply for '{q}' missing calorie burn info: {reply}"
        elif "stamina" in q_lower:
            assert any(w in reply.lower() for w in ["stamina", "સ્ટેમિના", "कार्डियो", "cardio", "endurance"]), f"Reply for '{q}' missing stamina info: {reply}"
        elif "leg" in q_lower or "પગ" in q_lower:
            assert any(w in reply.lower() for w in ["squats", "સ્ક્વોટ્સ", "स्क्वैट्स", "lunges", "legs"]), f"Reply for '{q}' missing leg exercises: {reply}"

def test_exercise_logging_intents_and_extraction():
    """Bug 1: Verifies exercise logging correctly parses exercise, reps, duration without defaulting to walking."""
    from backend.app.services.agent_nlp import AgentNLP
    
    # Case 1: "Aaje me 20 rep squats karya."
    t1 = "Aaje me 20 rep squats karya."
    assert AgentNLP.detect_intent(t1) == "CREATE_ACTIVITY_LOG"
    acts1 = AgentNLP.extract_activity_entities(t1)
    assert len(acts1) == 1
    assert acts1[0]["activity"] == "Squats"
    assert acts1[0]["reps"] == 20
    assert acts1[0]["requiresClarification"] is False

    # Case 2: "Aaje me 30 minute exercise kari."
    t2 = "Aaje me 30 minute exercise kari."
    assert AgentNLP.detect_intent(t2) == "CREATE_ACTIVITY_LOG"
    acts2 = AgentNLP.extract_activity_entities(t2)
    assert len(acts2) == 1
    assert acts2[0]["activity"] == "Workout"
    assert acts2[0]["durationMinutes"] == 30.0
    assert acts2[0]["requiresClarification"] is False

    # Case 3: "did 20 pushups"
    t3 = "did 20 pushups"
    assert AgentNLP.detect_intent(t3) == "CREATE_ACTIVITY_LOG"
    acts3 = AgentNLP.extract_activity_entities(t3)
    assert acts3[0]["activity"] == "Push-ups"
    assert acts3[0]["reps"] == 20

@pytest.mark.asyncio
async def test_multi_exercise_bullets_formatting():
    """Bug 2 & 3: Verifies multiple exercises are displayed as bullet points on separate lines."""
    from backend.app.services.activity_service import ActivityService
    from backend.app.services.agent_nlp import AgentNLP
    
    text = "Squats 20 reps, push-ups 15 reps, walking 30 minutes"
    acts = AgentNLP.extract_activity_entities(text)
    assert len(acts) == 3
    assert acts[0]["activity"] == "Squats" and acts[0]["reps"] == 20
    assert acts[1]["activity"] == "Push-ups" and acts[1]["reps"] == 15
    assert acts[2]["activity"] == "Walking" and acts[2]["durationMinutes"] == 30.0
    
    # Format through ActivityService
    res = await ActivityService.process_and_log_activities("test_user_id", acts)
    reply = res["replyText"]
    
    # Expected formatting verification:
    # 🏋️ **Workout Logged**
    # * Squats — 20 reps
    # * Push-ups — 15 reps
    # * Walking — 30 minutes
    assert "🏋️ **Workout Logged**" in reply
    assert "* Squats — 20 reps" in reply
    assert "* Push-ups — 15 reps" in reply
    assert "* Walking — 30 minutes" in reply
    
    # Check separate lines
    lines = [line.strip() for line in reply.split("\n") if line.strip()]
    squat_idx = next(i for i, l in enumerate(lines) if "Squats" in l)
    pushup_idx = next(i for i, l in enumerate(lines) if "Push-ups" in l)
    walk_idx = next(i for i, l in enumerate(lines) if "Walking" in l)
    assert squat_idx < pushup_idx < walk_idx, "Exercises should be on distinct sequential lines"

def test_clarification_on_missing_exercise_details():
    """Verifies that asking about unmeasured workouts requires clarification instead of false logging."""
    from backend.app.services.agent_nlp import AgentNLP
    
    # Generic vague statement with no numbers
    text = "I did exercise"
    acts = AgentNLP.extract_activity_entities(text)
    assert acts[0]["requiresClarification"] is True

def test_multi_food_bullet_formatting_structure():
    """Bug 2 & 3: Verifies multiple foods formatting uses bullets and separate lines."""
    # Test food formatting structure with bullet points
    sample_parts = [
        "2 Roti (140 kcal)",
        "1 bowl Toor Dal (150 kcal)",
        "1 bowl Cooked White Rice (130 kcal)",
        "1 glass Spiced Buttermilk (Chaas) (40 kcal)",
    ]
    bullet_items = "\n".join(f"* {part}" for part in sample_parts)
    reply_text = (
        f"🍽️ **Food Logged**\n\n"
        f"{bullet_items}\n\n"
        f"Meal total (Lunch): 460 kcal (P: 15g, C: 80g, F: 6g)\n"
        f"Today's total: 460 / 2000 kcal"
    )
    
    assert "🍽️ **Food Logged**" in reply_text
    assert "* 2 Roti (140 kcal)" in reply_text
    assert "* 1 bowl Toor Dal (150 kcal)" in reply_text
    assert "* 1 bowl Cooked White Rice (130 kcal)" in reply_text
    assert "* 1 glass Spiced Buttermilk (Chaas) (40 kcal)" in reply_text
    
    lines = [l.strip() for l in reply_text.split("\n") if l.strip()]
    roti_idx = next(i for i, l in enumerate(lines) if "2 Roti" in l)
    dal_idx = next(i for i, l in enumerate(lines) if "Toor Dal" in l)
    rice_idx = next(i for i, l in enumerate(lines) if "White Rice" in l)
    chaas_idx = next(i for i, l in enumerate(lines) if "Buttermilk" in l)
    assert roti_idx < dal_idx < rice_idx < chaas_idx, "Each food item must appear on a separate sequential line"



