"""
tests/test_food_matcher.py
--------------------------
Pytest tests for food_matcher.py:
  - normalize()
  - extract_quantity()
  - synonym lookups (food + exercise)
  - fuzzy match_food() / match_exercise() statuses
  - parse_llm_json()
  - is_absurd_quantity()

Run with:
    cd backend
    pip install rapidfuzz pytest
    pytest tests/test_food_matcher.py -v
"""

import sys
import os
import pytest

# Allow running from the backend/ directory without installing the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.food_matcher import (
    normalize,
    extract_quantity,
    match_food,
    match_exercise,
    is_absurd_quantity,
    parse_llm_json,
    get_llm_cache,
    set_llm_cache,
    FOOD_SYNONYMS,
    EXERCISE_SYNONYMS,
)


# ---------------------------------------------------------------------------
# normalize()
# ---------------------------------------------------------------------------
class TestNormalize:
    def test_lowercase(self):
        assert normalize("Banana") == "banana"

    def test_strips_emojis(self):
        assert normalize("banana 🍌") == "banana"

    def test_strips_extra_spaces(self):
        assert normalize("  2   rotli  ") == "2 rotli"

    def test_fused_digit_word(self):
        assert normalize("2rotli") == "2 rotli"

    def test_fused_word_digit(self):
        assert normalize("rotli2") == "rotli 2"

    def test_indic_digits_gujarati(self):
        # ૨ = 2 in Gujarati
        assert normalize("૨ rotli") == "2 rotli"

    def test_indic_digits_devanagari(self):
        # २ = 2 in Devanagari
        assert normalize("२ roti") == "2 roti"

    def test_empty_string(self):
        assert normalize("") == ""

    def test_none_like_empty(self):
        # Should not raise
        assert normalize("   ") == ""

    def test_punctuation_preserved_in_words(self):
        # Hyphens in "push-ups" should survive (not emoji/indic)
        result = normalize("push-ups")
        assert "push" in result


# ---------------------------------------------------------------------------
# extract_quantity()
# ---------------------------------------------------------------------------
class TestExtractQuantity:
    def test_numeric_quantity(self):
        qty, unit, name = extract_quantity("2 rotli")
        assert qty == 2.0
        assert name == "rotli"

    def test_number_word_ek(self):
        qty, unit, name = extract_quantity("ek bowl rice")
        assert qty == 1.0
        assert unit == "bowl"
        assert name == "rice"

    def test_number_word_be(self):
        qty, unit, name = extract_quantity("be rotli")
        assert qty == 2.0
        assert name == "rotli"

    def test_number_word_tran(self):
        qty, unit, name = extract_quantity("tran chapati")
        assert qty == 3.0
        assert name == "chapati"

    def test_number_word_half(self):
        qty, unit, name = extract_quantity("half glass chaas")
        assert qty == 0.5
        assert unit == "glass"
        assert name == "chaas"

    def test_number_word_adhu(self):
        qty, unit, name = extract_quantity("adhu bowl dal")
        assert qty == 0.5
        assert unit == "bowl"

    def test_unit_katori(self):
        qty, unit, name = extract_quantity("1 katori dal")
        assert unit == "bowl"
        assert name == "dal"

    def test_unit_glass(self):
        qty, unit, name = extract_quantity("2 glass milk")
        assert unit == "glass"

    def test_grams(self):
        qty, unit, name = extract_quantity("200g paneer")
        assert qty == 200.0
        assert unit == "g"
        assert "paneer" in name

    def test_exercise_minutes(self):
        qty, unit, name = extract_quantity("20 min pushap")
        assert qty == 20.0
        assert unit == "min"
        assert "pushap" in name

    def test_no_quantity(self):
        qty, unit, name = extract_quantity("paneer sabzi")
        assert qty is None
        assert "paneer" in name or "sabzi" in name

    def test_float_quantity(self):
        qty, unit, name = extract_quantity("1.5 cup oats")
        assert qty == 1.5
        assert unit == "cup"


# ---------------------------------------------------------------------------
# Synonym lookups
# ---------------------------------------------------------------------------
class TestSynonyms:
    def test_food_synonyms_loaded(self):
        assert len(FOOD_SYNONYMS) > 10

    def test_exercise_synonyms_loaded(self):
        assert len(EXERCISE_SYNONYMS) > 5

    def test_rotli_maps_to_roti(self):
        assert FOOD_SYNONYMS.get("rotli") == "Roti"

    def test_chaas_maps_to_buttermilk(self):
        result = FOOD_SYNONYMS.get("chaas")
        assert result is not None
        assert "Buttermilk" in result or "Chaas" in result

    def test_dahi_maps_to_curd(self):
        result = FOOD_SYNONYMS.get("dahi")
        assert result is not None
        assert "Curd" in result or "Dahi" in result

    def test_bhaat_maps_to_rice(self):
        result = FOOD_SYNONYMS.get("bhaat")
        assert result is not None
        assert "Rice" in result

    def test_daal_maps_to_dal(self):
        result = FOOD_SYNONYMS.get("daal")
        assert result is not None

    def test_anda_maps_to_egg(self):
        result = FOOD_SYNONYMS.get("anda")
        assert result is not None
        assert "Egg" in result

    def test_pushap_exercise_synonym(self):
        result = EXERCISE_SYNONYMS.get("pushap")
        assert result is not None
        assert "push" in result.lower()

    def test_skwat_exercise_synonym(self):
        result = EXERCISE_SYNONYMS.get("skwat")
        assert result is not None
        assert "squat" in result.lower()

    def test_runing_exercise_synonym(self):
        result = EXERCISE_SYNONYMS.get("runing")
        assert result is not None
        assert "running" in result.lower()


# ---------------------------------------------------------------------------
# match_food() — the main required test cases
# ---------------------------------------------------------------------------
class TestMatchFood:
    def test_banana_typo_matched(self):
        """'bananna' -> Banana (matched)"""
        result = match_food("bananna")
        assert result.status == "matched"
        assert result.matched_name is not None
        assert "Banana" in result.matched_name

    def test_banaana_typo_matched(self):
        """'banaana' -> Banana (synonym hit)"""
        result = match_food("banaana")
        assert result.status == "matched"
        assert "Banana" in (result.matched_name or "")

    def test_panner_typo_matched_or_confirm(self):
        """'panner' -> Paneer (matched or confirm, never not_found)"""
        result = match_food("panner")
        assert result.status in ("matched", "confirm")
        # Best suggestion should contain paneer
        candidates = [result.matched_name] + result.suggestions
        assert any("Paneer" in (c or "") for c in candidates)

    def test_2_rotli_qty_matched(self):
        """'2 rotli' -> Roti, qty 2"""
        qty, unit, name_part = extract_quantity(normalize("2 rotli"))
        assert qty == 2.0
        result = match_food(name_part)
        assert result.status == "matched"
        assert "Roti" in (result.matched_name or "")

    def test_chiken_brest_matched(self):
        """'chiken brest' -> Chicken Breast"""
        result = match_food("chiken brest")
        assert result.status in ("matched", "confirm")
        candidates = [result.matched_name] + result.suggestions
        assert any("Chicken" in (c or "") for c in candidates)

    def test_dal_exact_matched(self):
        result = match_food("dal")
        assert result.status == "matched"

    def test_chaas_matched(self):
        result = match_food("chaas")
        assert result.status == "matched"
        assert "Buttermilk" in (result.matched_name or "") or "Chaas" in (result.matched_name or "")

    def test_not_found_xyzfood(self):
        """'xyzfood' -> not_found"""
        result = match_food("xyzfood")
        assert result.status == "not_found"

    def test_not_found_returns_suggestions_list(self):
        result = match_food("xyzfood")
        assert isinstance(result.suggestions, list)

    def test_paneer_exact(self):
        result = match_food("paneer")
        assert result.status == "matched"
        assert result.matched_name == "Paneer"

    def test_rice_exact(self):
        result = match_food("rice")
        assert result.status == "matched"

    def test_egg_exact(self):
        result = match_food("egg")
        assert result.status == "matched"

    def test_score_present(self):
        result = match_food("banana")
        assert result.score > 0


# ---------------------------------------------------------------------------
# match_exercise()
# ---------------------------------------------------------------------------
class TestMatchExercise:
    def test_pushap_20_min(self):
        """'pushap 20 min' -> push-ups (matched or confirm)"""
        qty, unit, name_part = extract_quantity(normalize("pushap 20 min"))
        # qty might be 20 min; name_part should contain "pushap"
        result = match_exercise(name_part or "pushap")
        assert result.status in ("matched", "confirm")
        candidates = [result.matched_name] + result.suggestions
        assert any("push" in (c or "").lower() for c in candidates)

    def test_skwat_matched(self):
        result = match_exercise("skwat")
        assert result.status == "matched"
        assert "squat" in (result.matched_name or "").lower()

    def test_runing_matched(self):
        result = match_exercise("runing")
        assert result.status == "matched"
        assert "running" in (result.matched_name or "").lower()

    def test_walking_exact(self):
        result = match_exercise("walking")
        assert result.status == "matched"

    def test_gym_matched(self):
        result = match_exercise("gym")
        assert result.status == "matched"

    def test_unknown_exercise_not_found(self):
        result = match_exercise("zxzxzxzx")
        assert result.status == "not_found"


# ---------------------------------------------------------------------------
# is_absurd_quantity()
# ---------------------------------------------------------------------------
class TestAbsurdQuantity:
    def test_50_roti_is_absurd(self):
        assert is_absurd_quantity("roti", 50.0, "food") is True

    def test_5_roti_not_absurd(self):
        assert is_absurd_quantity("roti", 5.0, "food") is False

    def test_10_hours_running_is_absurd(self):
        assert is_absurd_quantity("running", 600.1, "exercise") is True

    def test_30_min_running_not_absurd(self):
        assert is_absurd_quantity("running", 30.0, "exercise") is False

    def test_zero_quantity_is_absurd(self):
        assert is_absurd_quantity("banana", 0.0, "food") is True

    def test_negative_quantity_is_absurd(self):
        assert is_absurd_quantity("banana", -1.0, "food") is True

    def test_10_hours_gym_is_absurd(self):
        assert is_absurd_quantity("gym workout", 601.0, "exercise") is True


# ---------------------------------------------------------------------------
# parse_llm_json()
# ---------------------------------------------------------------------------
class TestParseLlmJson:
    def test_clean_json(self):
        raw = '{"intent": "CREATE_FOOD_LOG", "entities": {"food": "Banana"}}'
        result = parse_llm_json(raw)
        assert result is not None
        assert result["intent"] == "CREATE_FOOD_LOG"

    def test_fenced_json(self):
        raw = '```json\n{"intent": "CREATE_FOOD_LOG", "entities": {}}\n```'
        result = parse_llm_json(raw)
        assert result is not None
        assert result["intent"] == "CREATE_FOOD_LOG"

    def test_strips_think_tags(self):
        raw = (
            "<think>Let me think about this carefully...</think>\n"
            '{"intent": "CREATE_FOOD_LOG", "entities": {}}'
        )
        result = parse_llm_json(raw)
        assert result is not None
        assert result["intent"] == "CREATE_FOOD_LOG"

    def test_json_with_surrounding_prose(self):
        raw = 'Here is the result: {"intent": "GENERAL_CHAT", "entities": {}} done.'
        result = parse_llm_json(raw)
        assert result is not None
        assert result["intent"] == "GENERAL_CHAT"

    def test_invalid_json_returns_none(self):
        result = parse_llm_json("{not valid json}")
        assert result is None

    def test_empty_string_returns_none(self):
        result = parse_llm_json("")
        assert result is None

    def test_entities_injected_when_missing(self):
        raw = '{"intent": "DAILY_SUMMARY"}'
        result = parse_llm_json(raw)
        assert result is not None
        assert "entities" in result

    def test_llm_items_array(self):
        """Parse the LLM fallback correction JSON format."""
        raw = (
            '{"items": ['
            '{"original": "bananna", "corrected": "banana", '
            '"type": "food", "quantity": 1, "unit": null, "confidence": "high"}'
            "]}"
        )
        result = parse_llm_json(raw)
        assert result is not None
        assert "items" in result
        assert result["items"][0]["corrected"] == "banana"

    def test_none_input_returns_none(self):
        result = parse_llm_json(None)  # type: ignore[arg-type]
        assert result is None


# ---------------------------------------------------------------------------
# LLM correction cache
# ---------------------------------------------------------------------------
class TestLlmCache:
    def test_set_and_get(self):
        set_llm_cache("bananaa", "Banana")
        assert get_llm_cache("bananaa") == "Banana"

    def test_cache_is_case_insensitive_on_get(self):
        set_llm_cache("panneer", "Paneer")
        assert get_llm_cache("PANNEER") == "Paneer"

    def test_cache_miss_returns_none(self):
        assert get_llm_cache("__nonexistent_xyz__") is None

    def test_cached_typo_gives_matched_status(self):
        set_llm_cache("bananaaaa", "Banana")
        result = match_food("bananaaaa")
        assert result.status == "matched"
        assert result.matched_name == "Banana"
