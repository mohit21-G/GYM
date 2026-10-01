"""
tests/test_temporal_intent.py
------------------------------
Tests for past / present / future / suggestion temporal handling.

Covers:
  - PAST logging resolves to yesterday's Asia/Kolkata date
  - FUTURE/PLANNED statements classify as FUTURE_LOG (never a completed log)
  - Suggestion questions classify as FOOD_SUGGESTION / WORKOUT_SUGGESTION (no log)
  - Present/today statements resolve to today
  - "kal" / "kale" disambiguation by verb tense (not assumed past)
  - Multilingual + typo tolerance for date & intent phrases
  - TimeService.get_message_date_context() correctness
  - ChatService._handle_future_intent() produces no log

Uses a frozen Asia/Kolkata clock via TimeService.set_mock_now so dates are
deterministic regardless of when the suite runs.

Run with:
    cd backend
    pytest tests/test_temporal_intent.py -v
"""

import sys
import os
from datetime import datetime, timedelta
import zoneinfo
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.agent_nlp import AgentNLP
from app.services.time_service import TimeService
from app.services.chat_service import ChatService

IST = zoneinfo.ZoneInfo("Asia/Kolkata")
# Frozen reference: Thu, 1 Oct 2026, 14:00 IST
FROZEN = datetime(2026, 10, 1, 14, 0, 0, tzinfo=IST)
TODAY = "2026-10-01"
YESTERDAY = "2026-09-30"
TOMORROW = "2026-10-02"


@pytest.fixture(autouse=True)
def freeze_clock():
    """Freeze TimeService to a deterministic IST instant for every test."""
    TimeService.set_mock_now(FROZEN)
    yield
    TimeService.reset_mock_now()


# ---------------------------------------------------------------------------
# TimeService.get_message_date_context()
# ---------------------------------------------------------------------------
class TestDateContext:
    def test_yesterday_english(self):
        d, past, fut = TimeService.get_message_date_context("yesterday I ate 2 roti")
        assert d == YESTERDAY and past is True and fut is False

    def test_kal_past_hinglish(self):
        d, past, fut = TimeService.get_message_date_context("kal maine 2 roti khaya")
        assert d == YESTERDAY and past is True

    def test_kale_past_gujlish(self):
        d, past, fut = TimeService.get_message_date_context("kale 2 roti khadhi")
        assert d == YESTERDAY and past is True

    def test_gaya_kale_past(self):
        d, past, fut = TimeService.get_message_date_context("gaya kale hu gym gyo")
        assert d == YESTERDAY and past is True

    def test_kale_future(self):
        d, past, fut = TimeService.get_message_date_context("kale hu gym karish")
        assert d == TOMORROW and fut is True and past is False

    def test_kale_khaysh_future(self):
        d, past, fut = TimeService.get_message_date_context("kale aa khaysh")
        assert d == TOMORROW and fut is True

    def test_tomorrow_english_future(self):
        d, past, fut = TimeService.get_message_date_context("tomorrow I will eat paneer")
        assert d == TOMORROW and fut is True

    def test_aavti_kale_future(self):
        d, past, fut = TimeService.get_message_date_context("aavti kale gym javano chhu")
        assert d == TOMORROW and fut is True

    def test_today_explicit(self):
        d, past, fut = TimeService.get_message_date_context("aaj poha khadha")
        assert d == TODAY and past is False and fut is False

    def test_no_date_word_defaults_today(self):
        d, past, fut = TimeService.get_message_date_context("2 roti khadhi")
        assert d == TODAY and past is False and fut is False


# ---------------------------------------------------------------------------
# PAST logging intent
# ---------------------------------------------------------------------------
class TestPastLogging:
    def test_kal_khaya_is_food_log(self):
        assert AgentNLP.detect_intent("kal maine ye khaya") == "CREATE_FOOD_LOG"

    def test_kale_khadhi_is_food_log(self):
        assert AgentNLP.detect_intent("kale 2 roti khadhi") == "CREATE_FOOD_LOG"

    def test_yesterday_is_food_log(self):
        assert AgentNLP.detect_intent("yesterday I ate 2 roti") == "CREATE_FOOD_LOG"

    def test_gaya_kale_gym_is_activity(self):
        assert AgentNLP.detect_intent("gaya kale hu gym gyo") == "CREATE_ACTIVITY_LOG"

    def test_kale_exercise_past(self):
        assert AgentNLP.detect_intent("kale aa exercise kari") == "CREATE_ACTIVITY_LOG"

    def test_past_food_date_is_yesterday(self):
        d, past, _ = TimeService.get_message_date_context("kal maine 2 roti khadhi")
        assert d == YESTERDAY and past is True


# ---------------------------------------------------------------------------
# FUTURE / PLANNED intent
# ---------------------------------------------------------------------------
class TestFutureIntent:
    def test_kale_gym_karish_is_future(self):
        assert AgentNLP.detect_intent("kale hu gym karish") == "FUTURE_LOG"

    def test_kale_khaysh_is_future(self):
        assert AgentNLP.detect_intent("kale aa khaysh") == "FUTURE_LOG"

    def test_tomorrow_will_eat_is_future(self):
        assert AgentNLP.detect_intent("tomorrow I will eat paneer") == "FUTURE_LOG"

    def test_kale_exercise_karish_is_future(self):
        assert AgentNLP.detect_intent("kale aa exercise karish") == "FUTURE_LOG"

    def test_future_helper_does_not_log(self):
        r = ChatService._handle_future_intent("sess-1", "kale hu gym karish", TOMORROW)
        assert r["data"]["planned"] is True
        assert r["ui"]["type"] == "TEXT"
        # No groupedFoodCards / no log cards in a future response
        assert "groupedFoodCards" not in r.get("ui", {})
        assert r["data"].get("plannedDate") == TOMORROW

    def test_future_helper_message_mentions_not_logged(self):
        r = ChatService._handle_future_intent("sess-1", "tomorrow I will eat", TOMORROW)
        assert "plan" in r["message"].lower() or "later" in r["message"].lower()


# ---------------------------------------------------------------------------
# SUGGESTION questions — never a log
# ---------------------------------------------------------------------------
class TestSuggestionIntent:
    def test_kale_su_khavu_joiye(self):
        assert AgentNLP.detect_intent("kale mare su khavu joiye?") == "FOOD_SUGGESTION"

    def test_kale_su_exercise_karvi_joiye(self):
        assert AgentNLP.detect_intent("mare kale su exercise karvi joiye?") == "WORKOUT_SUGGESTION"

    def test_sanje_su_khavu(self):
        assert AgentNLP.detect_intent("sanje mare su khavu joiye?") == "FOOD_SUGGESTION"

    def test_aaje_su_exercise(self):
        assert AgentNLP.detect_intent("mare aaje su exercise karvi?") == "WORKOUT_SUGGESTION"

    def test_have_su_khavu(self):
        assert AgentNLP.detect_intent("mare have su khavu?") == "FOOD_SUGGESTION"

    def test_what_should_i_eat_tomorrow(self):
        assert AgentNLP.detect_intent("what should i eat tomorrow?") == "FOOD_SUGGESTION"


# ---------------------------------------------------------------------------
# PRESENT / today logging
# ---------------------------------------------------------------------------
class TestPresentLogging:
    def test_walking_today(self):
        assert AgentNLP.detect_intent("me 30 min walking kari") == "CREATE_ACTIVITY_LOG"

    def test_roti_today(self):
        assert AgentNLP.detect_intent("hu 2 roti khadhi") == "CREATE_FOOD_LOG"

    def test_aaj_poha_today(self):
        assert AgentNLP.detect_intent("aaj poha khadha") == "CREATE_FOOD_LOG"

    def test_today_date_resolves_today(self):
        d, past, fut = TimeService.get_message_date_context("hu 2 roti khadhi")
        assert d == TODAY and not past and not fut


# ---------------------------------------------------------------------------
# Multilingual + typo tolerance
# ---------------------------------------------------------------------------
class TestTypoTolerance:
    def test_kal_exersise_typo_future(self):
        # "kal mare su exersise karvi" — question form → suggestion
        intent = AgentNLP.detect_intent("kal mare su exersise karvi?")
        assert intent in ("WORKOUT_SUGGESTION", "FOOD_SUGGESTION", "FITNESS_ADVISORY")

    def test_tomorow_typo_suggestion(self):
        # "tomorow su khavu" — typo of tomorrow, question → suggestion
        intent = AgentNLP.detect_intent("tomorow su khavu?")
        assert intent == "FOOD_SUGGESTION"

    def test_kale_gym_karis_typo_future(self):
        # "kale hu gym karis" (karis = karish typo) → future
        assert AgentNLP.detect_intent("kale hu gym karis") == "FUTURE_LOG"

    def test_gaya_kale_gym_typo_past(self):
        assert AgentNLP.detect_intent("gaya kale hu gym gyo") == "CREATE_ACTIVITY_LOG"

    def test_kale_exercize_past(self):
        # past exercise with typo
        intent = AgentNLP.detect_intent("kale aa exercize kari")
        assert intent == "CREATE_ACTIVITY_LOG"


# ---------------------------------------------------------------------------
# Regression: temporal words must not break non-temporal messages
# ---------------------------------------------------------------------------
class TestNoRegression:
    def test_plain_food_still_logs(self):
        assert AgentNLP.detect_intent("2 rotli ane dal khadha") == "CREATE_FOOD_LOG"

    def test_plain_workout_still_logs(self):
        assert AgentNLP.detect_intent("30 min walking") == "CREATE_ACTIVITY_LOG"

    def test_summary_still_works(self):
        assert AgentNLP.detect_intent("aaj nu summary aapo") == "DAILY_SUMMARY"

    def test_water_query_still_works(self):
        assert AgentNLP.detect_intent("aaj ketlu pani pidhu") == "QUERY_HYDRATION_LOG"

    def test_tiffin_guard_still_works(self):
        assert AgentNLP.detect_intent("dabbu khali karyu") == "GENERAL_CHAT"
