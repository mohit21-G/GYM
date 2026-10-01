"""Quick integration smoke-test — run with: python tests/verify_integration.py"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 1. config
from app.config import settings
assert settings.CF_MODEL == "@cf/zai-org/glm-4.7-flash", f"Wrong model: {settings.CF_MODEL}"
print("OK config.py  CF_MODEL =", settings.CF_MODEL)

# 2. food_matcher
from app.services.food_matcher import (
    normalize, extract_quantity, match_food, match_exercise,
    is_absurd_quantity, parse_llm_json, FOOD_SYNONYMS, EXERCISE_SYNONYMS,
)
assert len(FOOD_SYNONYMS) > 10
assert len(EXERCISE_SYNONYMS) > 5
print(f"OK food_matcher  food_synonyms={len(FOOD_SYNONYMS)}  exercise_synonyms={len(EXERCISE_SYNONYMS)}")

# 3. ai_service prompt loading
from app.services.ai_service import FITBOT_SYSTEM_PROMPT, SYSTEM_PROMPT, AIService
assert len(FITBOT_SYSTEM_PROMPT) > 50, "FitBot prompt too short"
print(f"OK ai_service  FITBOT_SYSTEM_PROMPT={len(FITBOT_SYSTEM_PROMPT)} chars")
assert SYSTEM_PROMPT.startswith("You are Google Fitness AI"), "Legacy SYSTEM_PROMPT missing"
print("OK ai_service  SYSTEM_PROMPT (legacy) present")

# 4. key match cases from the task spec
r = match_food("bananna")
assert r.status == "matched" and r.matched_name and "Banana" in r.matched_name, f"bananna failed: {r}"
print("OK match_food('bananna') ->", r.matched_name)

qty, unit, name_part = extract_quantity(normalize("2 rotli"))
assert qty == 2.0, f"qty expected 2.0 got {qty}"
r2 = match_food(name_part)
assert r2.status == "matched" and r2.matched_name and "Roti" in r2.matched_name, f"rotli failed: {r2}"
print(f"OK extract_quantity('2 rotli') qty={qty}, match_food('{name_part}') ->", r2.matched_name)

r3 = match_exercise("pushap")
assert r3.status == "matched" and r3.matched_name and "push" in r3.matched_name.lower(), f"pushap failed: {r3}"
print("OK match_exercise('pushap') ->", r3.matched_name)

r4 = match_food("xyzfood")
assert r4.status == "not_found", f"xyzfood should be not_found: {r4}"
print("OK match_food('xyzfood') -> not_found, suggestions:", r4.suggestions)

r5 = match_food("chiken brest")
assert r5.status in ("matched", "confirm"), f"chiken brest failed: {r5}"
print("OK match_food('chiken brest') ->", r5.status, r5.matched_name)

assert is_absurd_quantity("roti", 50.0, "food") is True
assert is_absurd_quantity("roti", 3.0, "food") is False
assert is_absurd_quantity("running", 601.0, "exercise") is True
print("OK is_absurd_quantity() all checks")

parsed = parse_llm_json('<think>reasoning here</think>{"intent":"CREATE_FOOD_LOG","entities":{}}')
assert parsed is not None and parsed["intent"] == "CREATE_FOOD_LOG"
print("OK parse_llm_json() strips think tags correctly")

# 5. existing service imports still work
from app.services.agent_nlp import AgentNLP
from app.services.food_service import FoodService
from app.services.activity_service import ActivityService
from app.services.chat_service import ChatService
from app.services.dashboard_service import DashboardService
print("OK all existing service imports intact")

print()
print("=" * 50)
print("ALL INTEGRATION CHECKS PASSED")
print("=" * 50)
