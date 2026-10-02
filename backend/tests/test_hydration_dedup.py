"""
tests/test_hydration_dedup.py
------------------------------
Regression tests for two bugs reported against real chatbot usage:

  1. Flavored "waters" (lemon water, coconut water, jeera water) were logged
     TWICE: once as a food card (via extract_food_entities_heuristically) and
     once as a hydration entry (via extract_hydration_entities). They must now
     be hydration-only.

  2. "Pre workout" was logged as a separate food/calorie item AND as a
     duplicate plain-water hydration entry when water was mentioned alongside
     it ("1 scoop pre-workout with 300ml water"). It must now be a single
     hydration entry named "Pre Workout":
       - with an explicit water amount -> that amount
       - with no water amount mentioned -> defaults to 250 ml

Run with:
    cd backend
    pytest tests/test_hydration_dedup.py -v
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.agent_nlp import AgentNLP


# ---------------------------------------------------------------------------
# Flavored water must be hydration-only (no duplicate food entry)
# ---------------------------------------------------------------------------
class TestFlavoredWaterIsHydrationOnly:
    def test_lemon_water_not_in_food_entities(self):
        foods = AgentNLP.extract_food_entities_heuristically("1 glass of lemon water")
        names = [f["food"].lower() for f in foods]
        assert not any("lemon" in n for n in names), f"Lemon water leaked into foods: {names}"

    def test_lemon_water_in_hydration_entities(self):
        hyds = AgentNLP.extract_hydration_entities("1 glass of lemon water")
        assert len(hyds) == 1
        assert hyds[0]["beverage_name"] == "Lemon Water"
        assert hyds[0]["amount_ml"] == 250.0

    def test_coconut_water_not_in_food_entities(self):
        foods = AgentNLP.extract_food_entities_heuristically("drank 1 glass coconut water")
        names = [f["food"].lower() for f in foods]
        assert not any("coconut" in n for n in names)

    def test_coconut_water_in_hydration_entities(self):
        hyds = AgentNLP.extract_hydration_entities("drank 1 glass coconut water")
        assert len(hyds) == 1
        assert hyds[0]["beverage_name"] == "Coconut Water"

    def test_plain_water_still_not_a_food(self):
        foods = AgentNLP.extract_food_entities_heuristically("drank 500ml water")
        assert foods == []

    def test_plain_water_still_hydration(self):
        hyds = AgentNLP.extract_hydration_entities("drank 500ml water")
        assert len(hyds) == 1
        assert hyds[0]["beverage_name"] == "Water"
        assert hyds[0]["amount_ml"] == 500.0


# ---------------------------------------------------------------------------
# Pre-workout: single hydration entry, never a food entry, never duplicated
# ---------------------------------------------------------------------------
class TestPreWorkoutIsHydrationOnly:
    def test_pre_workout_not_in_food_entities(self):
        foods = AgentNLP.extract_food_entities_heuristically("1 scoop pre-workout with 300 ml water")
        names = [f["food"].lower() for f in foods]
        assert not any("workout" in n for n in names), f"Pre-workout leaked into foods: {names}"

    def test_pre_workout_with_explicit_water_single_entry(self):
        """'1 scoop pre-workout with 300 ml water' must produce exactly ONE
        hydration entry of 300ml named 'Pre Workout' — not a separate 300ml
        plain-water entry too."""
        hyds = AgentNLP.extract_hydration_entities("1 scoop pre-workout with 300 ml water")
        assert len(hyds) == 1, f"Expected exactly 1 hydration entry, got {len(hyds)}: {hyds}"
        assert hyds[0]["beverage_name"] == "Pre Workout"
        assert hyds[0]["amount_ml"] == 300.0

    def test_pre_workout_without_water_defaults_250ml(self):
        """'had 1 scoop pre workout' (no water volume mentioned) must default
        to a 250ml 'Pre Workout' hydration entry."""
        hyds = AgentNLP.extract_hydration_entities("had 1 scoop pre workout")
        assert len(hyds) == 1
        assert hyds[0]["beverage_name"] == "Pre Workout"
        assert hyds[0]["amount_ml"] == 250.0

    def test_pre_workout_intent_is_hydration(self):
        assert AgentNLP.detect_intent("had 1 scoop pre workout") == "CREATE_HYDRATION_LOG"

    def test_pre_workout_with_litre_water(self):
        hyds = AgentNLP.extract_hydration_entities("1 scoop pre workout with 1 litre water")
        assert len(hyds) == 1
        assert hyds[0]["amount_ml"] == 1000.0


# ---------------------------------------------------------------------------
# Full multi-line routine message (the exact reported bug report)
# ---------------------------------------------------------------------------
class TestFullMorningRoutineMessage:
    MSG = (
        "Today I did in morning\n"
        "6:45 AM: 1 glass of lemon water\n"
        "7:00 AM: 400 ml black coffee\n"
        "7:15 AM: 1 scoop pre-workout with 300 ml water\n"
        "7:30-9:00 AM: Gym workout - Back & Biceps + 20-minute walk\n"
        "8:00 AM: 1 litre water\n"
        "9:30 AM: 1 scoop protein powder with 400 ml water\n"
        "10:00 AM: 3 Khapli rotis + 1 cup milk"
    )

    def test_intent_is_multi_log(self):
        assert AgentNLP.detect_intent(self.MSG) == "CREATE_MULTI_LOG"

    def test_no_junk_food_entity(self):
        foods = AgentNLP.extract_food_entities_heuristically(self.MSG)
        names = [f["food"].lower() for f in foods]
        assert "did" not in names

    def test_lemon_water_appears_once_only_in_hydration(self):
        foods = AgentNLP.extract_food_entities_heuristically(self.MSG)
        hyds = AgentNLP.extract_hydration_entities(self.MSG)
        food_names = [f["food"].lower() for f in foods]
        hyd_names = [h["beverage_name"] for h in hyds]
        assert not any("lemon" in n for n in food_names), f"Lemon water duplicated into foods: {food_names}"
        assert hyd_names.count("Lemon Water") == 1

    def test_pre_workout_appears_once_only_in_hydration(self):
        foods = AgentNLP.extract_food_entities_heuristically(self.MSG)
        hyds = AgentNLP.extract_hydration_entities(self.MSG)
        food_names = [f["food"].lower() for f in foods]
        hyd_names = [h["beverage_name"] for h in hyds]
        assert not any("workout" in n for n in food_names), f"Pre-workout duplicated into foods: {food_names}"
        assert hyd_names.count("Pre Workout") == 1

    def test_pre_workout_uses_the_300ml_mentioned(self):
        hyds = AgentNLP.extract_hydration_entities(self.MSG)
        pw = [h for h in hyds if h["beverage_name"] == "Pre Workout"]
        assert len(pw) == 1
        assert pw[0]["amount_ml"] == 300.0

    def test_hydration_entry_count_is_exactly_four(self):
        """Lemon water (250), pre-workout (300), 1 litre water (1000),
        protein-powder's 400ml water (400) = 4 hydration entries.
        (Black coffee stays a food item, not hydration.)"""
        hyds = AgentNLP.extract_hydration_entities(self.MSG)
        assert len(hyds) == 4, f"Expected 4 hydration entries, got {len(hyds)}: {hyds}"

    def test_real_foods_still_present(self):
        foods = AgentNLP.extract_food_entities_heuristically(self.MSG)
        names = [f["food"] for f in foods]
        assert any("Coffee" in n for n in names)
        assert any("Rotli" in n or "Roti" in n for n in names)
        assert any("Milk" in n for n in names)
        assert any("Protein" in n for n in names)

    def test_activities_still_present(self):
        acts = AgentNLP.extract_activity_entities(self.MSG)
        activity_names = [a.get("activity") for a in acts]
        assert len(acts) >= 2
        assert any("Walk" in n for n in activity_names)
