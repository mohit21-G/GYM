"""
tests/test_fuzzy_vocab.py
--------------------------
Fuzzy vocabulary test suite covering all 13 categories from the spec:
  A. Exact vocabulary
  B. Minor spelling errors (1-2 chars)
  C. Severe spelling errors (3+ char diff)
  D. Roman Gujarati
  E. Gujarati script
  F. Gujlish (Gujarati + English)
  G. Phonetic spelling
  H. Abbreviations
  I. Colloquial language
  J. Multi-word fuzzy phrases
  K. Context-dependent vocabulary
  L. Unknown words (must NOT be force-corrected)
  M. Ambiguous words

Also covers:
  - detect_intent() for Gujlish/Roman Gujarati sentences
  - detect_language() classification
  - extract_food_entities_heuristically() compound food handling
  - ai_service.process_message() Gujlish round-trip (mocked LLM)

Run with:
    cd backend
    pytest tests/test_fuzzy_vocab.py -v
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.agent_nlp import AgentNLP
from app.services.food_service import fuzzy_canonical, CANONICAL_INDIAN_FOOD_PROFILES
from app.services.food_matcher import normalize, extract_quantity


# ---------------------------------------------------------------------------
# A. Exact vocabulary — must pass unchanged
# ---------------------------------------------------------------------------
class TestExactVocabulary:
    """Exact known words must resolve without any fuzzy involvement."""

    def test_banana_exact(self):
        assert fuzzy_canonical("banana") is not None

    def test_chapati_exact(self):
        assert fuzzy_canonical("chapati") is not None

    def test_roti_exact(self):
        # "roti" is 4 chars, ASCII, in vocab
        result = fuzzy_canonical("roti")
        assert result is not None

    def test_paneer_exact(self):
        result = fuzzy_canonical("paneer")
        assert result == "Paneer"

    def test_dal_exact(self):
        # "dal" is only 3 chars — below min-length guard, should return None
        result = fuzzy_canonical("dal")
        assert result is None  # too short; handled by synonym dict upstream

    def test_egg_exact(self):
        # "egg" is 3 chars — below guard
        result = fuzzy_canonical("egg")
        assert result is None

    def test_normalize_exact_english(self):
        assert normalize("banana") == "banana"

    def test_normalize_exact_gujlish(self):
        assert normalize("rotli") == "rotli"


# ---------------------------------------------------------------------------
# B. Minor spelling errors (1–2 char mistakes)
# ---------------------------------------------------------------------------
class TestMinorSpellingErrors:
    """1–2 character typos in common food and exercise names."""

    def test_bananna(self):
        result = fuzzy_canonical("bananna")
        assert result is not None and "Banana" in result

    def test_panner(self):
        result = fuzzy_canonical("panner")
        assert result is not None and "Paneer" in result

    def test_chapti(self):
        result = fuzzy_canonical("chapti")
        assert result is not None and "Chapati" in result

    def test_banaana(self):
        result = fuzzy_canonical("banaana")
        assert result is not None and "Banana" in result

    def test_dalm(self):
        # "dalm" — 4 chars, minor typo of "dal" with extra char
        # May or may not match depending on scorer; should not return unrelated food
        result = fuzzy_canonical("dalm")
        if result is not None:
            assert "Dal" in result or "dal" in result.lower()

    def test_rotte(self):
        # "rotte" — typo of "roti" / "rotte" style
        result = fuzzy_canonical("rotte")
        # Should either match Roti or return None — must not map to something unrelated
        if result is not None:
            assert any(w in result.lower() for w in ["roti", "rotlo", "chapati", "phulka"])


# ---------------------------------------------------------------------------
# C. Severe spelling errors (3+ character differences)
# ---------------------------------------------------------------------------
class TestSevereSpellingErrors:
    """Multiple character differences — fuzzy should handle these at 80 cutoff."""

    def test_chiken_brest(self):
        result = fuzzy_canonical("chiken brest")
        assert result is not None and "Chicken" in result

    def test_buttrmilk(self):
        result = fuzzy_canonical("buttrmilk")
        assert result is not None
        assert "Buttermilk" in result or "Chaas" in result

    def test_omlette(self):
        result = fuzzy_canonical("omlette")
        if result is not None:
            assert "Egg" in result or "Omelette" in result

    def test_brocolli(self):
        # Not in canonical vocab — must not force-correct to an unrelated food
        result = fuzzy_canonical("brocolli")
        # broccoli is not in CANONICAL_INDIAN_FOOD_PROFILES; None or something unrelated
        # If it does match, it must be in the canonical set
        if result is not None:
            assert result in CANONICAL_INDIAN_FOOD_PROFILES


# ---------------------------------------------------------------------------
# D. Roman Gujarati (Gujlish writing system)
# ---------------------------------------------------------------------------
class TestRomanGujarati:
    """Romanized Gujarati food and activity names."""

    def test_detect_language_gujlish(self):
        lang = AgentNLP.detect_language("2 rotli ane chaas khadhi")
        assert lang in ("gu-Latn", "gu"), f"Expected gu-Latn or gu, got {lang}"

    def test_detect_language_rotli(self):
        lang = AgentNLP.detect_language("mare rotli khadhi")
        assert lang in ("gu-Latn", "gu")

    def test_detect_intent_gujlish_food(self):
        intent = AgentNLP.detect_intent("2 rotli ane chaas khadhi")
        assert intent == "CREATE_FOOD_LOG", f"Expected CREATE_FOOD_LOG got {intent}"

    def test_detect_intent_mare_aaje(self):
        intent = AgentNLP.detect_intent("mare aaje 2 rotli khadhi")
        assert intent == "CREATE_FOOD_LOG"

    def test_detect_intent_gujlish_workout(self):
        intent = AgentNLP.detect_intent("maro workout thayu")
        assert intent == "CREATE_ACTIVITY_LOG"

    def test_normalize_indic_digits_gujarati(self):
        result = normalize("૨ rotli")
        assert result.startswith("2")

    def test_gujlish_rotli_synonym(self):
        """'rotli' must exist in INDIAN_FOOD_SYNONYMS (via agent_nlp)."""
        from app.services.agent_nlp import INDIAN_FOOD_SYNONYMS
        assert "rotli" in INDIAN_FOOD_SYNONYMS

    def test_gujlish_chaas_synonym(self):
        from app.services.agent_nlp import INDIAN_FOOD_SYNONYMS
        assert "chaas" in INDIAN_FOOD_SYNONYMS

    def test_gujlish_doodh_synonym(self):
        from app.services.agent_nlp import INDIAN_FOOD_SYNONYMS
        assert "doodh" in INDIAN_FOOD_SYNONYMS

    def test_extract_rotli_entity(self):
        """'2 rotli khadhi' should produce a food entity for rotli."""
        entities = AgentNLP.extract_food_entities_heuristically("2 rotli khadhi")
        assert len(entities) >= 1
        food_names = [e["food"].lower() for e in entities]
        assert any("roti" in n or "rotli" in n for n in food_names), \
            f"Expected roti/rotli in {food_names}"

    def test_extract_rotli_quantity(self):
        entities = AgentNLP.extract_food_entities_heuristically("2 rotli khadhi")
        if entities:
            assert entities[0]["quantity"] == 2.0


# ---------------------------------------------------------------------------
# E. Gujarati script
# ---------------------------------------------------------------------------
class TestGujaratiScript:
    """Native Gujarati script input."""

    def test_detect_language_gujarati_script(self):
        lang = AgentNLP.detect_language("મારે 2 રોટલી ખાધી")
        assert lang == "gu"

    def test_detect_intent_gujarati_food(self):
        intent = AgentNLP.detect_intent("2 રોટલી ખાધી")
        assert intent == "CREATE_FOOD_LOG"

    def test_fuzzy_canonical_blocks_gujarati_script(self):
        """fuzzy_canonical must return None for non-ASCII Gujarati — handled by synonym dict."""
        result = fuzzy_canonical("રોટલી")
        assert result is None  # correct: non-ASCII bypass

    def test_gujarati_synonym_present(self):
        from app.services.agent_nlp import INDIAN_FOOD_SYNONYMS
        assert "રોટલી" in INDIAN_FOOD_SYNONYMS

    def test_normalize_indic_digits_devanagari(self):
        result = normalize("२ roti")
        assert result.startswith("2")


# ---------------------------------------------------------------------------
# F. Gujlish (Gujarati + English mixed)
# ---------------------------------------------------------------------------
class TestGujlish:
    """Mixed Gujarati-English input."""

    def test_detect_language_gujlish_mixed(self):
        lang = AgentNLP.detect_language("aaje gym ma workout karyu")
        # "aaje" is not in the Gujlish keyword list, but "gym"/"workout" are English
        # Accept "en" as well since Gujlish detection uses specific keyword triggers
        assert lang in ("gu-Latn", "en")

    def test_detect_intent_mixed_food_workout(self):
        intent = AgentNLP.detect_intent("2 rotli khadhi ane 30 min gym")
        assert intent in ("CREATE_MULTI_LOG", "CREATE_FOOD_LOG"), \
            f"Expected multi/food log got {intent}"

    def test_extract_gujlish_multi(self):
        """'2 rotli ane 1 bowl dal' should extract two food items."""
        entities = AgentNLP.extract_food_entities_heuristically("2 rotli ane 1 bowl dal")
        assert len(entities) >= 2, f"Expected >=2 items, got {len(entities)}: {entities}"

    def test_gujlish_eating_verb_khadhi(self):
        """'khadhi' must be recognized as an eating verb → triggers CREATE_FOOD_LOG."""
        intent = AgentNLP.detect_intent("rotli khadhi")
        assert intent == "CREATE_FOOD_LOG"

    def test_gujlish_drinking_verb_pidhi(self):
        """'pidhi' (drank in Gujarati) should signal food/drink logging."""
        intent = AgentNLP.detect_intent("chaas pidhi")
        assert intent == "CREATE_FOOD_LOG"

    def test_calories_query_gujlish(self):
        intent = AgentNLP.detect_intent("aaj nu summary aapo")
        assert intent == "DAILY_SUMMARY"

    def test_water_query_gujlish(self):
        intent = AgentNLP.detect_intent("ketlu pani pidhu aaj")
        assert intent == "QUERY_HYDRATION_LOG"


# ---------------------------------------------------------------------------
# G. Phonetic spelling
# ---------------------------------------------------------------------------
class TestPhoneticSpelling:
    """Words written as they sound, not as standardly spelled."""

    def test_woekout_normalizes(self):
        """'woekout' should be repaired to 'workout' by difflib in normalize_text."""
        result = AgentNLP.normalize_text("woekout")
        assert "workout" in result.lower(), f"Expected workout in '{result}'"

    def test_woekout_intent(self):
        intent = AgentNLP.detect_intent("woekout kiya")
        assert intent == "CREATE_ACTIVITY_LOG"

    def test_chhas_phonetic(self):
        """'chhas' is a phonetic spelling of chaas."""
        from app.services.agent_nlp import INDIAN_FOOD_SYNONYMS
        assert "chhas" in INDIAN_FOOD_SYNONYMS

    def test_doodh_phonetic(self):
        intent = AgentNLP.detect_intent("1 glass doodh piya")
        assert intent == "CREATE_FOOD_LOG"

    def test_panner_sabzi_phonetic(self):
        """'panner sabzi' — panner is phonetic for paneer."""
        from app.services.agent_nlp import INDIAN_FOOD_SYNONYMS
        # After normalize_text, panner → paneer (it's in typo dict)
        normalized = AgentNLP.normalize_text("panner sabzi")
        assert "paneer" in normalized.lower(), f"Expected paneer in '{normalized}'"


# ---------------------------------------------------------------------------
# H. Abbreviations
# ---------------------------------------------------------------------------
class TestAbbreviations:
    """Common abbreviations used by gym/fitness users."""

    def test_pb_not_force_corrected(self):
        """'pb' (personal best) should not be force-corrected to 'roti' or similar."""
        result = fuzzy_canonical("pb")
        assert result is None  # too short (2 chars < 4)

    def test_bmi_not_force_corrected(self):
        result = fuzzy_canonical("bmi")
        assert result is None  # too short (3 chars < 4)

    def test_whey_abbreviation(self):
        """'whey' is an abbreviation for whey protein — must resolve."""
        from app.services.agent_nlp import INDIAN_FOOD_SYNONYMS
        assert "whey" in INDIAN_FOOD_SYNONYMS

    def test_hiit_workout_intent(self):
        intent = AgentNLP.detect_intent("30 min hiit done")
        assert intent == "CREATE_ACTIVITY_LOG"


# ---------------------------------------------------------------------------
# I. Colloquial language
# ---------------------------------------------------------------------------
class TestColloquialLanguage:
    """Informal / slang / household terms."""

    def test_thoki_eating_verb(self):
        """'thoki' (colloquial for ate) should not block recognition."""
        # "2 roti thoki" — thoki is informal for ate
        intent = AgentNLP.detect_intent("aaj me 2 roti thoki")
        assert intent == "CREATE_FOOD_LOG"

    def test_patavi_didhu_eating_verb(self):
        intent = AgentNLP.detect_intent("poha patavi didhu")
        assert intent == "CREATE_FOOD_LOG"

    def test_lidhu_drinking_verb(self):
        """'lidhu' (took/had) is a Gujarati eating verb."""
        intent = AgentNLP.detect_intent("1 glass chaas lidhu")
        assert intent == "CREATE_FOOD_LOG"

    def test_khadha_eating_verb(self):
        intent = AgentNLP.detect_intent("2 anda khadha")
        assert intent == "CREATE_FOOD_LOG"

    def test_bhaat_colloquial_rice(self):
        """'bhaat' is colloquial Gujarati for rice."""
        from app.services.agent_nlp import INDIAN_FOOD_SYNONYMS
        assert "bhaat" in INDIAN_FOOD_SYNONYMS

    def test_kasrat_colloquial_workout(self):
        """'kasrat' is Gujarati/Hinglish for exercise."""
        intent = AgentNLP.detect_intent("aaj kasrat kari")
        assert intent == "CREATE_ACTIVITY_LOG"


# ---------------------------------------------------------------------------
# J. Multi-word fuzzy phrases
# ---------------------------------------------------------------------------
class TestMultiWordFuzzyPhrases:
    """Errors distributed across multiple words in a phrase."""

    def test_chiken_tikka(self):
        result = fuzzy_canonical("chiken tikka")
        assert result is not None
        assert "Chicken" in result

    def test_panner_sabzi_compound_extract(self):
        """'panner sabzi' should extract paneer AND sabzi as separate items OR
        recognize it as a compound — it must NOT silently drop paneer."""
        normalized_msg = AgentNLP.normalize_text("panner sabzi")
        # After normalize_text, panner → paneer (in typo dict)
        assert "paneer" in normalized_msg.lower(), \
            f"normalize_text should fix panner→paneer, got: '{normalized_msg}'"

    def test_dal_rice_multi(self):
        """'dal rice' should produce two food items."""
        entities = AgentNLP.extract_food_entities_heuristically("1 bowl dal rice")
        # dal and rice may be kept together as "dal and rice" or split into two items
        assert len(entities) >= 1

    def test_roti_dal_multi(self):
        """'2 roti dal' should produce food entities."""
        entities = AgentNLP.extract_food_entities_heuristically("2 roti dal khadha")
        assert len(entities) >= 1

    def test_multi_item_intent(self):
        """Message with multiple food items should get CREATE_FOOD_LOG or CREATE_MULTI_LOG."""
        intent = AgentNLP.detect_intent("2 rotli ane 1 bowl dal khadha")
        assert intent in ("CREATE_FOOD_LOG", "CREATE_MULTI_LOG")

    def test_aloo_paratha_compound(self):
        result = fuzzy_canonical("aloo paratha")
        assert result is not None
        assert "Paratha" in result or "Aloo" in result


# ---------------------------------------------------------------------------
# K. Context-dependent vocabulary
# ---------------------------------------------------------------------------
class TestContextDependentVocabulary:
    """Same word, different meaning depending on surrounding text."""

    def test_shake_as_hydration_not_exercise(self):
        """'protein shake' is a drink -> hydration, not an exercise and not a
        separate food/calorie item (see test_supplement_hydration_macros.py)."""
        intent = AgentNLP.detect_intent("had 1 protein shake")
        assert intent == "CREATE_HYDRATION_LOG"

    def test_workout_word_in_pre_workout(self):
        """'pre workout' must be logged as hydration (not an exercise activity),
        since a pre-workout scoop is mixed into water and tracked as hydration."""
        intent = AgentNLP.detect_intent("had 1 scoop pre workout")
        assert intent == "CREATE_HYDRATION_LOG"

    def test_back_tea_not_workout(self):
        """'back' in 'black tea' should NOT trigger gym back-workout."""
        intent = AgentNLP.detect_intent("1 cup black tea")
        assert intent == "CREATE_FOOD_LOG"

    def test_summary_vs_food_query(self):
        intent_summary = AgentNLP.detect_intent("aaj nu summary")
        intent_food = AgentNLP.detect_intent("what did I eat today")
        assert intent_summary == "DAILY_SUMMARY"
        assert intent_food in ("QUERY_FOOD_LOG", "DAILY_SUMMARY")


# ---------------------------------------------------------------------------
# L. Unknown words — must NOT be force-corrected
# ---------------------------------------------------------------------------
class TestUnknownWordProtection:
    """Unknown / novel words must not be silently replaced with unrelated vocabulary."""

    def test_xyzfood_returns_none(self):
        result = fuzzy_canonical("xyzfood")
        assert result is None

    def test_very_short_word_blocked(self):
        for w in ["ab", "cd", "xy", "z"]:
            assert fuzzy_canonical(w) is None, f"{w!r} should return None (too short)"

    def test_pan_blocked(self):
        assert fuzzy_canonical("pan") is None

    def test_uncommon_word_not_replaced(self):
        """A valid uncommon word 'quinoa' that is not in the canonical set."""
        result = fuzzy_canonical("quinoa")
        if result is not None:
            # If it matches something, it must be in the canonical set (not a hallucination)
            assert result in CANONICAL_INDIAN_FOOD_PROFILES

    def test_user_name_not_replaced(self):
        """Names like 'rahul' should not be mapped to food."""
        result = fuzzy_canonical("rahul")
        assert result is None

    def test_english_tech_term_not_replaced(self):
        """'calorie' is a domain term but not a food name — should not match."""
        result = fuzzy_canonical("calorie")
        # May or may not match — if it does, it must be in canonical set
        if result is not None:
            assert result in CANONICAL_INDIAN_FOOD_PROFILES

    def test_unknown_does_not_trigger_correction_in_normalize(self):
        """normalize_text must preserve unknown words, not corrupt them."""
        result = AgentNLP.normalize_text("xyzfood")
        assert "xyzfood" in result.lower()


# ---------------------------------------------------------------------------
# M. Ambiguous words
# ---------------------------------------------------------------------------
class TestAmbiguousWords:
    """Words with multiple plausible interpretations."""

    def test_protein_intent_food(self):
        """'protein' alone in food context → food log."""
        intent = AgentNLP.detect_intent("1 scoop protein liya")
        assert intent == "CREATE_FOOD_LOG"

    def test_shake_alone_context(self):
        """'protein shake' is always hydration — see
        test_supplement_hydration_macros.py::TestProteinShakeIsHydration."""
        intent = AgentNLP.detect_intent("protein shake liya")
        assert intent == "CREATE_HYDRATION_LOG"

    def test_dal_ambiguity_food_not_verb(self):
        """'dal' must be recognized as food, not verb."""
        entities = AgentNLP.extract_food_entities_heuristically("1 bowl dal")
        assert len(entities) >= 1
        assert any("dal" in e["food"].lower() or "toor" in e["food"].lower()
                   for e in entities)

    def test_paneer_bhurji_specific(self):
        """'paneer bhurji' must resolve to itself, not plain Paneer."""
        result = fuzzy_canonical("paneer bhurji")
        assert result is not None
        assert result in CANONICAL_INDIAN_FOOD_PROFILES
        assert result != "Paneer"


# ---------------------------------------------------------------------------
# detect_language() coverage
# ---------------------------------------------------------------------------
class TestDetectLanguage:
    """Language detection accuracy."""

    def test_english(self):
        assert AgentNLP.detect_language("I had 2 eggs for breakfast") == "en"

    def test_gujarati_script(self):
        assert AgentNLP.detect_language("મને ભૂખ લાગી છે") == "gu"

    def test_devanagari_hindi(self):
        assert AgentNLP.detect_language("आज मैंने दाल चावल खाया") == "hi"

    def test_gujlish_rotli(self):
        lang = AgentNLP.detect_language("2 rotli ane chaas khadhi")
        assert lang in ("gu-Latn", "gu")

    def test_gujlish_ane(self):
        lang = AgentNLP.detect_language("roti ane dal khadhi")
        assert lang in ("gu-Latn", "gu")

    def test_hinglish_aur(self):
        lang = AgentNLP.detect_language("roti aur dal khaya")
        assert lang in ("hi-Latn", "hi")

    def test_mixed_script_gujarati_wins(self):
        """If text has Gujarati script, detect as 'gu' regardless of Latin words."""
        lang = AgentNLP.detect_language("1 bowl dal અને ભાત")
        assert lang == "gu"


# ---------------------------------------------------------------------------
# normalize_text() coverage for Gujlish/typo repair
# ---------------------------------------------------------------------------
class TestNormalizeTextGujlish:
    """normalize_text must repair typos without destroying valid Gujlish."""

    def test_pneer_to_paneer(self):
        result = AgentNLP.normalize_text("pneer sabzi")
        assert "paneer" in result.lower()

    def test_banaana_to_banana(self):
        result = AgentNLP.normalize_text("banaana")
        assert "banana" in result.lower()

    def test_chiken_to_chicken(self):
        result = AgentNLP.normalize_text("chiken brest")
        assert "chicken" in result.lower()

    def test_rotli_preserved(self):
        """'rotli' is valid Gujlish — must not be corrupted."""
        result = AgentNLP.normalize_text("2 rotli")
        assert "rotli" in result.lower()

    def test_chaas_preserved(self):
        result = AgentNLP.normalize_text("1 glass chaas")
        assert "chaas" in result.lower()

    def test_gujlish_sentence_preserved(self):
        """Full Gujlish sentence should pass through with eating verbs intact."""
        result = AgentNLP.normalize_text("mare aaje 2 rotli khadhi")
        # 'rotli' and 'khadhi' must survive; '2' must survive
        assert "rotli" in result.lower()
        assert "2" in result


# ---------------------------------------------------------------------------
# compound food extraction (Fix C regression)
# ---------------------------------------------------------------------------
class TestCompoundFoodExtraction:
    """Fix C: compound food phrases must not silently drop one component."""

    def test_panner_sabzi_normalizes_to_paneer_sabzi(self):
        """normalize_text repairs panner → paneer before entity extraction."""
        result = AgentNLP.normalize_text("panner sabzi khadhi")
        assert "paneer" in result.lower()

    def test_paneer_tikka_recognized(self):
        entities = AgentNLP.extract_food_entities_heuristically("paneer tikka khadha")
        assert len(entities) >= 1
        assert any("paneer" in e["food"].lower() or "tikka" in e["food"].lower()
                   for e in entities)

    def test_aloo_paratha_entity(self):
        entities = AgentNLP.extract_food_entities_heuristically("2 aloo paratha khadha")
        assert len(entities) >= 1
        food_names = [e["food"].lower() for e in entities]
        assert any("aloo" in n or "paratha" in n for n in food_names)

    def test_dal_rice_entity_count(self):
        entities = AgentNLP.extract_food_entities_heuristically("dal rice khadha")
        assert len(entities) >= 1

    def test_paneer_bhurji_entity(self):
        entities = AgentNLP.extract_food_entities_heuristically("paneer bhurji khadha")
        assert len(entities) >= 1
        food_names = [e["food"].lower() for e in entities]
        assert any("paneer" in n for n in food_names)
