"""
tests/test_protein_shake_hydration_and_workout_fix.py
-------------------------------------------------------
Regression tests for two bugs reported against real chatbot usage:

  1. "Protein Shake" was logged as a FOOD item while "whey protein powder" was
     logged as HYDRATION for the same kind of drink — inconsistent behaviour.
     ANY protein/pre-workout drink or powder must now be hydration-only:
     "protein shake", "protein drink", "whey protein shake", and the powder
     forms, all behave the same as "pre workout" already did. Only bare
     "protein" (no shake/drink/powder word) stays an ambiguous food item.

  2. A message with food/hydration but NO workout mention was getting a
     phantom "30 min Workout" auto-added to the exercise list. This happened
     because AgentNLP.extract_activity_entities() always returns a fallback
     "Workout" placeholder (requiresClarification=True) when no real exercise
     keyword is found, and several call sites in ai_service.py filtered only
     on `activity != "Workout"` with an `or acts` fallback that let the
     placeholder slip back in whenever every item got filtered out.

Run with:
    cd backend
    pytest tests/test_protein_shake_hydration_and_workout_fix.py -v
"""

import sys
import os
import asyncio
import pytest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.agent_nlp import AgentNLP
from app.services.ai_service import AIService


class TestProteinShakeIsAlwaysHydration:
    def test_protein_shake_intent_is_hydration(self):
        assert AgentNLP.detect_intent("1 scoop protein shake") == "CREATE_HYDRATION_LOG"

    def test_protein_shake_not_a_food_entity(self):
        foods = AgentNLP.extract_food_entities_heuristically("1 scoop protein shake")
        assert foods == []

    def test_protein_shake_is_a_hydration_entity_with_macros(self):
        hyds = AgentNLP.extract_hydration_entities("1 scoop protein shake")
        assert len(hyds) == 1
        assert hyds[0]["beverage_name"] == "Protein Shake"
        assert hyds[0]["calories"] == 160.0
        assert hyds[0]["proteinG"] == 25.0

    def test_whey_protein_powder_and_protein_shake_consistent(self):
        """Both forms of the same kind of supplement drink must behave
        identically — this was the exact inconsistency reported."""
        shake_intent = AgentNLP.detect_intent("1 scoop whey protein powder")
        powder_intent = AgentNLP.detect_intent("1 scoop protein shake")
        assert shake_intent == powder_intent == "CREATE_HYDRATION_LOG"


@pytest.mark.asyncio
class TestNoPhantomWorkoutInjection:
    async def test_protein_shake_alone_has_no_activities(self):
        with patch.object(AIService, "_call_cloudflare", new=AsyncMock(return_value=None)), \
             patch.object(AIService, "_call_groq", new=AsyncMock(return_value=None)):
            res = await AIService.process_message("1 scoop protein shake", [])
        activities = res["entities"].get("activities") or res["entities"].get("activityItems")
        assert not activities, f"Phantom workout injected: {activities}"

    async def test_multi_supplement_message_has_no_activities(self):
        """The exact reported message: multiple hydration items, no workout
        mentioned at all — must NOT get a phantom 30-min Workout."""
        msg = "1 scoop protein shake, 1 scoop whey protein powder, 1 scoop whey protein powder with 300ml water"
        with patch.object(AIService, "_call_cloudflare", new=AsyncMock(return_value=None)), \
             patch.object(AIService, "_call_groq", new=AsyncMock(return_value=None)):
            res = await AIService.process_message(msg, [])
        activities = res["entities"].get("activities") or res["entities"].get("activityItems")
        assert not activities, f"Phantom workout injected: {activities}"

    async def test_multi_supplement_message_preserves_all_hydration_items(self):
        """All three supplement/drink entries from one message must survive
        — not just the first one."""
        msg = "1 scoop protein shake, 1 scoop whey protein powder, 1 scoop whey protein powder with 300ml water"
        with patch.object(AIService, "_call_cloudflare", new=AsyncMock(return_value=None)), \
             patch.object(AIService, "_call_groq", new=AsyncMock(return_value=None)):
            res = await AIService.process_message(msg, [])
        hyds = res["entities"].get("hydrationItems") or []
        assert len(hyds) == 3, f"Expected 3 hydration entries, got {len(hyds)}: {hyds}"
        names = [h["beverage_name"] for h in hyds]
        assert names.count("Protein Shake") == 1
        assert names.count("Whey Protein Powder") == 2

    async def test_genuine_workout_still_detected(self):
        """A message that DOES mention a real workout must still log it —
        the fix must not suppress genuine activities."""
        msg = "2 roti ane dal khadhi, 30 min gym kari"
        with patch.object(AIService, "_call_cloudflare", new=AsyncMock(return_value=None)), \
             patch.object(AIService, "_call_groq", new=AsyncMock(return_value=None)):
            res = await AIService.process_message(msg, [])
        activities = res["entities"].get("activities") or res["entities"].get("activityItems")
        assert activities, "Genuine workout should still be detected"
        assert all(not a.get("requiresClarification") for a in activities)

    async def test_food_only_message_has_no_activities(self):
        msg = "2 roti khadhi"
        with patch.object(AIService, "_call_cloudflare", new=AsyncMock(return_value=None)), \
             patch.object(AIService, "_call_groq", new=AsyncMock(return_value=None)):
            res = await AIService.process_message(msg, [])
        assert res["intent"] == "CREATE_FOOD_LOG"
        activities = res["entities"].get("activities") or res["entities"].get("activityItems")
        assert not activities
