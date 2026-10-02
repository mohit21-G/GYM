"""
tests/test_llm_fallback_multilog.py
------------------------------------
Regression test for a bug where, whenever the LLM call failed or returned
non-JSON prose for a multi-item routine message, the fallback branch in
AIService.process_message() only checked `foods` and built a plain
CREATE_FOOD_LOG — silently discarding activities and hydration items that the
deterministic parsers (AgentNLP.extract_activity_entities /
extract_hydration_entities) had already found correctly.

This reproduces the exact failure mode by monkeypatching the LLM calls to
fail (as happens in real usage when Cloudflare/Groq return invalid JSON or
hit a quota/network error), and asserts the fallback still preserves foods,
activities, AND hydration together as CREATE_MULTI_LOG.

Run with:
    cd backend
    pytest tests/test_llm_fallback_multilog.py -v
"""

import sys
import os
import pytest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.ai_service import AIService

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


@pytest.mark.asyncio
class TestLlmFallbackPreservesMultiLog:
    async def test_fallback_keeps_food_activity_and_hydration(self):
        """When both LLM providers fail/return invalid JSON, the deterministic
        foods/activities/hydration already extracted upstream must all survive
        into a CREATE_MULTI_LOG result — none of the three categories may be
        silently dropped."""
        with patch.object(AIService, "_call_cloudflare", new=AsyncMock(return_value=None)), \
             patch.object(AIService, "_call_groq", new=AsyncMock(return_value=None)):
            res = await AIService.process_message(MSG, [])

        assert res["intent"] == "CREATE_MULTI_LOG"
        ents = res["entities"]
        assert len(ents.get("foodItems") or []) >= 1, "Food items were dropped by the LLM fallback"
        assert len(ents.get("activities") or []) >= 1, "Activities were dropped by the LLM fallback"
        assert len(ents.get("hydrationItems") or []) >= 1, "Hydration items were dropped by the LLM fallback"

    async def test_fallback_food_only_message_stays_food_log(self):
        """A simple food-only message must still fall back to CREATE_FOOD_LOG
        (not be forced into CREATE_MULTI_LOG) when the LLM fails."""
        with patch.object(AIService, "_call_cloudflare", new=AsyncMock(return_value=None)), \
             patch.object(AIService, "_call_groq", new=AsyncMock(return_value=None)):
            res = await AIService.process_message("2 roti ane dal khadhi", [])

        assert res["intent"] == "CREATE_FOOD_LOG"
        assert len(res["entities"].get("foodItems") or []) >= 1

    async def test_fallback_activity_only_message_stays_activity_log(self):
        """A simple activity-only message must fall back to
        CREATE_ACTIVITY_LOG, not lose the workout."""
        with patch.object(AIService, "_call_cloudflare", new=AsyncMock(return_value=None)), \
             patch.object(AIService, "_call_groq", new=AsyncMock(return_value=None)):
            res = await AIService.process_message("30 min gym workout done", [])

        assert res["intent"] in ("CREATE_ACTIVITY_LOG", "CREATE_MULTI_LOG")
        assert len(res["entities"].get("activities") or res["entities"].get("activityItems") or []) >= 1
