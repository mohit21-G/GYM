"""
tests/test_supplement_hydration_macros.py
-------------------------------------------
Regression tests for the supplement-in-water feature:

  1. "1 scoop pre-workout with 300 ml water" and "1 scoop whey protein with
     300 ml water" must each produce exactly ONE hydration entry carrying
     BOTH the water amount AND the supplement's nutrition (calories/protein/
     carbs/fat/fiber) — never a separate food item plus a separate generic
     "Water" entry.

  2. Protein/whey mentioned WITHOUT water in the same clause must remain a
     normal food item (dry scoop, with milk, pre-made shake, etc.) — only the
     "<supplement> with <amount> water" pattern is hydration-only.

  3. The scoop count (quantity) scales the nutrition linearly.

Run with:
    cd backend
    pytest tests/test_supplement_hydration_macros.py -v
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.agent_nlp import AgentNLP


class TestPreWorkoutNutrition:
    def test_pre_workout_with_water_has_calories(self):
        hyds = AgentNLP.extract_hydration_entities("1 scoop pre-workout with 300 ml water")
        assert len(hyds) == 1
        assert hyds[0]["beverage_name"] == "Pre Workout"
        assert hyds[0]["amount_ml"] == 300.0
        assert hyds[0]["calories"] == 10.0
        assert hyds[0]["carbsG"] == 2.0
        assert hyds[0]["quantity"] == 1.0

    def test_pre_workout_not_duplicated_as_food(self):
        foods = AgentNLP.extract_food_entities_heuristically("1 scoop pre-workout with 300 ml water")
        assert foods == []

    def test_two_scoops_pre_workout_scales_nutrition(self):
        hyds = AgentNLP.extract_hydration_entities("2 scoops pre-workout with 500 ml water")
        assert len(hyds) == 1
        assert hyds[0]["quantity"] == 2.0
        assert hyds[0]["calories"] == 20.0
        assert hyds[0]["amount_ml"] == 500.0


class TestWheyProteinWithWaterNutrition:
    def test_whey_protein_with_water_single_hydration_entry(self):
        hyds = AgentNLP.extract_hydration_entities("1 scoop whey protein with 300 ml water")
        assert len(hyds) == 1
        assert hyds[0]["beverage_name"] == "Whey Protein Powder"
        assert hyds[0]["amount_ml"] == 300.0
        assert hyds[0]["calories"] == 120.0
        assert hyds[0]["proteinG"] == 24.0
        assert hyds[0]["carbsG"] == 2.0
        assert hyds[0]["fatG"] == 1.5

    def test_whey_protein_with_water_not_duplicated_as_food(self):
        foods = AgentNLP.extract_food_entities_heuristically("1 scoop whey protein with 300 ml water")
        names = [f["food"] for f in foods]
        assert not any("Protein" in n or "Whey" in n for n in names), f"Protein leaked into foods: {names}"

    def test_whey_protein_with_water_not_also_plain_water(self):
        """The '300 ml water' portion must NOT also appear as a separate
        generic 'Water' hydration entry — only the combined supplement entry."""
        hyds = AgentNLP.extract_hydration_entities("1 scoop whey protein with 300 ml water")
        plain_water = [h for h in hyds if h["beverage_name"] == "Water"]
        assert plain_water == [], f"Unexpected duplicate plain-water entry: {plain_water}"

    def test_protein_powder_alias_also_works(self):
        hyds = AgentNLP.extract_hydration_entities("1 scoop protein powder with 400 ml water")
        assert len(hyds) == 1
        assert hyds[0]["beverage_name"] == "Whey Protein Powder"
        assert hyds[0]["amount_ml"] == 400.0


class TestProteinWithoutWaterStaysFood:
    def test_protein_with_milk_stays_food(self):
        """Protein mixed with milk (not water) is a normal food item, not
        hydration — the supplement-with-water rule is water-specific."""
        foods = AgentNLP.extract_food_entities_heuristically("1 scoop whey protein with milk")
        names = [f["food"] for f in foods]
        assert any("Protein" in n or "Whey" in n for n in names), f"Expected protein in foods: {names}"

    def test_protein_without_water_mention_produces_no_hydration_entry(self):
        hyds = AgentNLP.extract_hydration_entities("1 scoop whey protein with milk")
        assert hyds == []

    def test_dry_protein_scoop_stays_food(self):
        foods = AgentNLP.extract_food_entities_heuristically("had 1 scoop protein powder")
        names = [f["food"] for f in foods]
        assert any("Protein" in n or "Whey" in n for n in names)


class TestFullMorningRoutineWithSupplements:
    """The exact message reported by the user: pre-workout AND whey protein,
    each mixed with water, logged alongside normal foods and a workout."""

    MSG = (
        "6:30 AM: 1 glass warm water\n"
        "6:45 AM: 1 banana\n"
        "7:00 AM: 1 cup black coffee\n"
        "7:15 AM: 1 scoop pre-workout with 300 ml water\n"
        "7:30-8:45 AM: Chest & Triceps workout\n"
        "8:45 AM: 500 ml water\n"
        "9:15 AM: 1 scoop whey protein with 300 ml water\n"
        "10:00 AM: 3 eggs + 2 multigrain rotis\n"
        "10:30 AM: 500 ml water"
    )

    def test_no_junk_chest_food_entity(self):
        """'Chest & Triceps workout' must not leak into foods as 'Am Chest'."""
        foods = AgentNLP.extract_food_entities_heuristically(self.MSG)
        names = [f["food"].lower() for f in foods]
        assert not any("chest" in n for n in names), f"Junk 'chest' food entity: {names}"

    def test_both_supplements_present_with_macros(self):
        hyds = AgentNLP.extract_hydration_entities(self.MSG)
        pre = [h for h in hyds if h["beverage_name"] == "Pre Workout"]
        whey = [h for h in hyds if h["beverage_name"] == "Whey Protein Powder"]
        assert len(pre) == 1 and pre[0]["calories"] == 10.0
        assert len(whey) == 1 and whey[0]["calories"] == 120.0 and whey[0]["proteinG"] == 24.0

    def test_real_foods_present(self):
        foods = AgentNLP.extract_food_entities_heuristically(self.MSG)
        names = [f["food"] for f in foods]
        assert any("Banana" in n for n in names)
        assert any("Coffee" in n for n in names)
        assert any("Egg" in n for n in names)
        assert any("Roti" in n for n in names)

    def test_activities_present(self):
        acts = AgentNLP.extract_activity_entities(self.MSG)
        activity_names = [a.get("activity") for a in acts]
        assert any("Chest" in n for n in activity_names)
        assert any("Triceps" in n for n in activity_names)

    def test_intent_is_multi_log(self):
        assert AgentNLP.detect_intent(self.MSG) == "CREATE_MULTI_LOG"
