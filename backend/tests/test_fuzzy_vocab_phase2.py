"""
tests/test_fuzzy_vocab_phase2.py
---------------------------------
Second-generation fuzzy vocabulary test suite (Phase 2).

Categories:
  A. Roman Gujarati sentences
  B. Gujarati script (expanded coverage)
  C. Mixed Gujarati-English
  D. Phonetic spelling variants
  E. Multi-token fuzzy phrases
  F. Context-dependent terms
  G. Ambiguous food phrases
  H. Unknown vocabulary (must NOT be force-corrected)
  I. False-positive protection
  J. Intent + entity completeness checks
  K. Rare Gujlish / edge cases
  L. paneer sabzi disambiguation (was incorrectly mapped to Paneer Bhurji)
  M. Complete pipeline: normalize → intent → entities

Run with:
    cd backend
    pytest tests/test_fuzzy_vocab_phase2.py -v
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.agent_nlp import AgentNLP, INDIAN_FOOD_SYNONYMS
from app.services.food_service import fuzzy_canonical, CANONICAL_INDIAN_FOOD_PROFILES
from app.services.food_matcher import normalize


# ---------------------------------------------------------------------------
# A. Roman Gujarati sentences
# ---------------------------------------------------------------------------
class TestRomanGujaratiSentences:
    """Complete Gujlish sentences — intent + entity + language detection."""

    def test_mare_aaje_rotli_khadhi(self):
        intent = AgentNLP.detect_intent("mare aaje 2 rotli khadhi")
        assert intent == "CREATE_FOOD_LOG"

    def test_mare_aaje_rotli_khadhi_entities(self):
        ents = AgentNLP.extract_food_entities_heuristically("mare aaje 2 rotli khadhi")
        assert len(ents) >= 1
        assert ents[0]["quantity"] == 2.0

    def test_aaje_chaas_pidhi(self):
        intent = AgentNLP.detect_intent("aaje 1 glass chaas pidhi")
        assert intent == "CREATE_FOOD_LOG"

    def test_aaj_gym_karyu(self):
        intent = AgentNLP.detect_intent("aaj 30 min gym karyu")
        assert intent == "CREATE_ACTIVITY_LOG"

    def test_rotli_ane_dal(self):
        intent = AgentNLP.detect_intent("2 rotli ane 1 bowl dal khadha")
        assert intent in ("CREATE_FOOD_LOG", "CREATE_MULTI_LOG")

    def test_rotli_ane_dal_entities(self):
        ents = AgentNLP.extract_food_entities_heuristically("2 rotli ane 1 bowl dal khadha")
        assert len(ents) >= 2

    def test_aaj_no_summary(self):
        intent = AgentNLP.detect_intent("aaj no summary aapo")
        assert intent == "DAILY_SUMMARY"

    def test_ketlu_pani_pidhu(self):
        intent = AgentNLP.detect_intent("aaj ketlu pani pidhu")
        assert intent == "QUERY_HYDRATION_LOG"

    def test_gujlish_language_detection(self):
        assert AgentNLP.detect_language("2 rotli ane chaas khadhi") in ("gu-Latn", "gu")

    def test_gujlish_kasrat(self):
        intent = AgentNLP.detect_intent("aaj kasrat kari 30 minute")
        assert intent == "CREATE_ACTIVITY_LOG"

    def test_rotlee_phonetic_synonym(self):
        """rotlee (phonetic) must resolve to Roti."""
        assert INDIAN_FOOD_SYNONYMS.get("rotlee") == "Roti"

    def test_rotlii_phonetic_synonym(self):
        """rotlii must resolve to Roti."""
        assert INDIAN_FOOD_SYNONYMS.get("rotlii") == "Roti"


# ---------------------------------------------------------------------------
# B. Gujarati script (expanded)
# ---------------------------------------------------------------------------
class TestGujaratiScriptExpanded:
    """Gujarati script terms — synonym coverage and language detection."""

    def test_cha_gujarati_synonym(self):
        """ચા (tea in Gujarati script) must be in synonyms."""
        assert "ચા" in INDIAN_FOOD_SYNONYMS
        assert "Tea" in INDIAN_FOOD_SYNONYMS["ચા"]

    def test_choxa_gujarati_synonym(self):
        """ચોખા (rice in Gujarati) must be in synonyms."""
        assert "ચોખા" in INDIAN_FOOD_SYNONYMS
        assert "Rice" in INDIAN_FOOD_SYNONYMS["ચોખા"]

    def test_pauva_gujarati_synonym(self):
        """પૌઆ (poha alternate spelling) must be in synonyms."""
        assert "પૌઆ" in INDIAN_FOOD_SYNONYMS
        assert INDIAN_FOOD_SYNONYMS["પૌઆ"] == "Poha"

    def test_rotli_gujarati_synonym(self):
        assert "રોટલી" in INDIAN_FOOD_SYNONYMS

    def test_bhakri_gujarati_synonym(self):
        assert "ભાખરી" in INDIAN_FOOD_SYNONYMS

    def test_chaas_gujarati_synonym(self):
        assert "છાશ" in INDIAN_FOOD_SYNONYMS

    def test_thepla_gujarati_synonym(self):
        assert "થેપલા" in INDIAN_FOOD_SYNONYMS

    def test_paneer_gujarati_synonym(self):
        assert "પનીર" in INDIAN_FOOD_SYNONYMS

    def test_shaak_gujarati_synonym(self):
        assert "શાક" in INDIAN_FOOD_SYNONYMS

    def test_dal_gujarati_synonym(self):
        assert "દાળ" in INDIAN_FOOD_SYNONYMS

    def test_khichdi_gujarati_synonym(self):
        assert "ખીચડી" in INDIAN_FOOD_SYNONYMS

    def test_detect_language_gujarati_rotli(self):
        assert AgentNLP.detect_language("મારે 2 રોટલી ખાધી") == "gu"

    def test_detect_language_gujarati_tea(self):
        assert AgentNLP.detect_language("ચા પીધી") == "gu"

    def test_detect_intent_gujarati_food(self):
        intent = AgentNLP.detect_intent("2 રોટલી ખાધી")
        assert intent == "CREATE_FOOD_LOG"

    def test_fuzzy_canonical_blocks_gujarati_safely(self):
        """Gujarati script input correctly bypasses ASCII-only fuzzy_canonical."""
        assert fuzzy_canonical("રોટલી") is None   # bypass — synonym dict handles it
        assert fuzzy_canonical("ચા") is None        # too short AND non-ASCII

    def test_all_18_gujarati_terms_present(self):
        """All 18 audited Gujarati script terms must be in synonyms."""
        required = [
            "રોટલી", "ભાખરી", "છાશ", "થેપલા", "પનીર", "શાક",
            "દાળ", "ખીચડી", "ભાત", "ઈંડું", "ચા", "દહીં",
            "ભીંડી", "ચોખા", "ફૂલકા", "ઉપમા", "પૌઆ", "ઇડલી",
        ]
        missing = [t for t in required if t not in INDIAN_FOOD_SYNONYMS]
        assert not missing, f"Missing Gujarati synonyms: {missing}"


# ---------------------------------------------------------------------------
# C. Mixed Gujarati-English
# ---------------------------------------------------------------------------
class TestMixedGujaratiEnglish:
    """Messages combining Gujarati food names with English grammar."""

    def test_had_rotli(self):
        intent = AgentNLP.detect_intent("had 2 rotli for dinner")
        assert intent == "CREATE_FOOD_LOG"

    def test_ate_chaas(self):
        intent = AgentNLP.detect_intent("drank 1 glass chaas")
        assert intent == "CREATE_FOOD_LOG"

    def test_mixed_protein_gujlish(self):
        intent = AgentNLP.detect_intent("1 scoop protein liya ane gym gayo")
        assert intent in ("CREATE_FOOD_LOG", "CREATE_MULTI_LOG", "CREATE_ACTIVITY_LOG")

    def test_english_food_gujlish_verb(self):
        """English food name + Gujarati verb."""
        intent = AgentNLP.detect_intent("apple khadhu")
        assert intent == "CREATE_FOOD_LOG"

    def test_gujlish_food_english_verb(self):
        """Gujlish food name + English verb."""
        intent = AgentNLP.detect_intent("ate rotli for lunch")
        assert intent == "CREATE_FOOD_LOG"

    def test_mixed_calories_query(self):
        intent = AgentNLP.detect_intent("aaj ketli calories thai")
        assert intent in ("QUERY_FOOD_LOG", "DAILY_SUMMARY")


# ---------------------------------------------------------------------------
# D. Phonetic spelling variants
# ---------------------------------------------------------------------------
class TestPhoneticVariants:
    """Pronunciation-based spellings that differ from standard forms."""

    def test_rotlee_resolves_via_synonym(self):
        assert INDIAN_FOOD_SYNONYMS.get("rotlee") == "Roti"

    def test_rotlii_resolves_via_synonym(self):
        assert INDIAN_FOOD_SYNONYMS.get("rotlii") == "Roti"

    def test_chaass_resolves_via_fuzzy(self):
        result = fuzzy_canonical("chaass")
        assert result is not None and "Chaas" in result

    def test_theepla_resolves_via_fuzzy(self):
        result = fuzzy_canonical("theepla")
        assert result is not None and "Thepla" in result

    def test_kheechdi_resolves_via_fuzzy(self):
        result = fuzzy_canonical("kheechdi")
        assert result is not None
        assert "Khichdi" in result or "Dal" in result

    def test_bhakhri_resolves_via_fuzzy(self):
        result = fuzzy_canonical("bhakhri")
        assert result is not None and "Bhakri" in result

    def test_daal_resolves_via_synonym(self):
        assert INDIAN_FOOD_SYNONYMS.get("daal") is not None

    def test_woekout_normalized(self):
        """Phonetic 'woekout' → 'workout' via difflib pass."""
        result = AgentNLP.normalize_text("woekout 30 min")
        assert "workout" in result.lower()

    def test_panner_normalized(self):
        result = AgentNLP.normalize_text("panner sabzi")
        assert "paneer" in result.lower()

    def test_chiken_normalized(self):
        result = AgentNLP.normalize_text("chiken brest")
        assert "chicken" in result.lower()


# ---------------------------------------------------------------------------
# E. Multi-token fuzzy phrases
# ---------------------------------------------------------------------------
class TestMultiTokenFuzzyPhrases:
    """Compound food names that must not be split incorrectly."""

    def test_aloo_paratha_synonym(self):
        assert INDIAN_FOOD_SYNONYMS.get("aloo paratha") is not None

    def test_paneer_tikka_synonym(self):
        assert INDIAN_FOOD_SYNONYMS.get("paneer tikka") is not None

    def test_aloo_sabzi_synonym(self):
        assert INDIAN_FOOD_SYNONYMS.get("aloo sabzi") is not None

    def test_paneer_tikka_entity(self):
        ents = AgentNLP.extract_food_entities_heuristically("paneer tikka khadha")
        assert len(ents) >= 1
        assert any("paneer" in e["food"].lower() or "tikka" in e["food"].lower() for e in ents)

    def test_aloo_paratha_entity(self):
        ents = AgentNLP.extract_food_entities_heuristically("2 aloo paratha khadha")
        assert len(ents) >= 1
        names = [e["food"].lower() for e in ents]
        assert any("aloo" in n or "paratha" in n for n in names)

    def test_sev_tameta_multi_word(self):
        assert INDIAN_FOOD_SYNONYMS.get("sev tameta") is not None

    def test_dal_rice_entity(self):
        ents = AgentNLP.extract_food_entities_heuristically("dal rice khadha")
        assert len(ents) >= 1

    def test_chiken_brest_fuzzy(self):
        result = fuzzy_canonical("chiken brest")
        assert result is not None and "Chicken" in result


# ---------------------------------------------------------------------------
# F. Context-dependent terms
# ---------------------------------------------------------------------------
class TestContextDependentTerms:
    """Same surface form, different meaning depending on context."""

    def test_pre_workout_is_hydration(self):
        """'pre workout' is a hydration item (mixed into water), not an exercise
        activity and not a separate food/calorie entry."""
        intent = AgentNLP.detect_intent("had 1 scoop pre workout")
        assert intent == "CREATE_HYDRATION_LOG"

    def test_plain_workout_is_activity(self):
        intent = AgentNLP.detect_intent("30 min workout done")
        assert intent == "CREATE_ACTIVITY_LOG"

    def test_black_tea_not_workout(self):
        """'back' in 'black tea' must NOT trigger back-workout intent."""
        intent = AgentNLP.detect_intent("1 cup black tea")
        assert intent == "CREATE_FOOD_LOG"

    def test_chest_exercise(self):
        """'chest' in exercise context → activity."""
        intent = AgentNLP.detect_intent("did chest workout 45 min")
        assert intent == "CREATE_ACTIVITY_LOG"

    def test_protein_food_context(self):
        intent = AgentNLP.detect_intent("2 scoops protein shake khadha")
        assert intent == "CREATE_FOOD_LOG"

    def test_water_query_not_log(self):
        """Asking about water status → query, not new log."""
        intent = AgentNLP.detect_intent("how much water did i drink today")
        assert intent == "QUERY_HYDRATION_LOG"

    def test_water_logging(self):
        intent = AgentNLP.detect_intent("drank 500ml water")
        assert intent == "CREATE_HYDRATION_LOG"


# ---------------------------------------------------------------------------
# G. Ambiguous food phrases — must NOT be silently mapped to specific dishes
# ---------------------------------------------------------------------------
class TestAmbiguousFoodPhrases:
    """Generic or ambiguous food phrases that require careful handling."""

    def test_paneer_sabzi_does_not_map_to_paneer_bhurji(self):
        """'paneer sabzi' is generic — fuzzy must NOT silently return 'Paneer Bhurji'.
        The ratio 72 is correctly below the 80 cutoff."""
        result = fuzzy_canonical("paneer sabzi")
        assert result is None or result != "Paneer Bhurji", (
            "fuzzy_canonical must not silently map 'paneer sabzi' to 'Paneer Bhurji'"
        )

    def test_paneer_sabzi_entity_is_recognized_ingredient(self):
        """Entity extraction for 'paneer sabzi' should identify at least the
        recognisable ingredient 'Paneer', not an incorrect compound dish."""
        ents = AgentNLP.extract_food_entities_heuristically("paneer sabzi khadhi")
        assert len(ents) >= 1
        recognized = [e for e in ents if e["is_recognized"]]
        assert len(recognized) >= 1
        # Must not create "Paneer Bhurji" from a generic phrase
        for e in recognized:
            assert e["food"] != "Paneer Bhurji", (
                f"Incorrect specific dish inferred from generic phrase: {e['food']}"
            )

    def test_sabzi_alone_resolves_to_generic_vegetable(self):
        """'sabzi' alone → Mixed Vegetable Sabzi (generic), which is correct."""
        syn = INDIAN_FOOD_SYNONYMS.get("sabzi")
        assert syn is not None
        assert "Sabzi" in syn or "Vegetable" in syn

    def test_dal_alone_resolves_generically(self):
        """'dal' alone → generic dal, not a specific sub-type without evidence."""
        syn = INDIAN_FOOD_SYNONYMS.get("dal")
        assert syn is not None  # must resolve

    def test_unknown_dish_not_force_corrected(self):
        """An uncommon but plausible Indian dish name must not be corrupted."""
        result = fuzzy_canonical("sukhadi")  # Gujarati sweet dish — 7 chars, ASCII
        # May or may not match; if it matches it must be in canonical set
        if result is not None:
            assert result in CANONICAL_INDIAN_FOOD_PROFILES

    def test_generic_shak_does_not_create_specific_dish(self):
        """'shak' (generic Gujarati for vegetable curry) → should resolve to generic
        Mixed Vegetable Sabzi, not a specific dish like Bhindi Masala."""
        syn = INDIAN_FOOD_SYNONYMS.get("shak")
        assert syn is not None
        # shak → "Mixed Vegetable Sabzi" is correct (generic)
        assert "Sabzi" in syn or "Vegetable" in syn


# ---------------------------------------------------------------------------
# H. Unknown vocabulary — must NOT be force-corrected
# ---------------------------------------------------------------------------
class TestUnknownVocabularyProtection:
    """Words the system has never seen must be passed through safely."""

    def test_quinoa_not_corrected(self):
        assert fuzzy_canonical("quinoa") is None

    def test_avocado_not_corrected(self):
        assert fuzzy_canonical("avocado") is None

    def test_tempeh_not_corrected(self):
        assert fuzzy_canonical("tempeh") is None

    def test_kefir_not_corrected(self):
        assert fuzzy_canonical("kefir") is None

    def test_miso_not_corrected(self):
        assert fuzzy_canonical("miso") is None

    def test_new_slang_not_corrupted(self):
        """New user-created slang must not be silently altered."""
        result = AgentNLP.normalize_text("ate my bigmac")
        assert "bigmac" in result.lower() or "big mac" in result.lower()

    def test_english_fitness_term_not_corrupted(self):
        result = AgentNLP.normalize_text("did my macros today")
        assert "macros" in result.lower()

    def test_keto_not_corrupted(self):
        result = AgentNLP.normalize_text("eating keto today")
        assert "keto" in result.lower()


# ---------------------------------------------------------------------------
# I. False-positive protection
# ---------------------------------------------------------------------------
class TestFalsePositiveProtection:
    """Valid words that must NOT be altered by any normalization step."""

    def test_dabbu_not_corrupted_to_khapli(self):
        """'dabbu' (tiffin box in Gujlish) must NOT become 'khapli' (a wheat variant)."""
        result = AgentNLP.normalize_text("dabbu khali karyu")
        assert "khapli" not in result.lower(), (
            f"False positive: 'dabbu' was corrupted. Got: {result!r}"
        )
        assert "dabbu" in result.lower()

    def test_khali_not_corrupted_to_khapli(self):
        """'khali' (empty/finished in Gujarati/Hindi) must NOT become 'khapli'."""
        result = AgentNLP.normalize_text("khali karyu")
        assert "khapli" not in result.lower(), (
            f"False positive: 'khali' was corrupted to 'khapli'. Got: {result!r}"
        )
        assert "khali" in result.lower()

    def test_thakor_name_not_corrupted(self):
        """'thakor' is a Gujarati proper noun and must not become a food name."""
        result = AgentNLP.normalize_text("thakor nu dabbu")
        assert "thakor" in result.lower()

    def test_rotli_not_corrupted_to_roti(self):
        """'rotli' is a valid Gujlish word — must NOT be changed to 'roti'."""
        result = AgentNLP.normalize_text("2 rotli khadhi")
        assert "rotli" in result.lower(), (
            f"False positive: 'rotli' was corrupted. Got: {result!r}"
        )

    def test_chaas_not_corrupted(self):
        result = AgentNLP.normalize_text("1 glass chaas pidhi")
        assert "chaas" in result.lower()

    def test_thepla_not_corrupted(self):
        result = AgentNLP.normalize_text("2 thepla khadha")
        assert "thepla" in result.lower()

    def test_bhakri_not_corrupted(self):
        result = AgentNLP.normalize_text("1 bhakri")
        assert "bhakri" in result.lower()

    def test_names_not_corrupted(self):
        for name in ["rahul", "priya", "amit", "neha"]:
            result = AgentNLP.normalize_text(f"i am {name}")
            assert name in result.lower(), f"Name {name!r} was corrupted to {result!r}"

    def test_short_words_not_force_matched(self):
        for w in ["pb", "bmi", "ab", "cd"]:
            assert fuzzy_canonical(w) is None, f"{w!r} should return None (too short)"


# ---------------------------------------------------------------------------
# J. Intent + entity completeness
# ---------------------------------------------------------------------------
class TestIntentEntityCompleteness:
    """The complete structured output for representative messages."""

    def test_2_rotli_khadhi_structure(self):
        intent = AgentNLP.detect_intent("2 rotli khadhi")
        ents = AgentNLP.extract_food_entities_heuristically("2 rotli khadhi")
        assert intent == "CREATE_FOOD_LOG"
        assert len(ents) == 1
        assert ents[0]["quantity"] == 2.0
        assert ents[0]["is_recognized"] is True

    def test_1_bowl_dal_structure(self):
        ents = AgentNLP.extract_food_entities_heuristically("1 bowl dal khadha")
        assert len(ents) == 1
        assert ents[0]["unit"] == "bowl"

    def test_egg_quantity(self):
        ents = AgentNLP.extract_food_entities_heuristically("3 ande khadha")
        assert len(ents) >= 1
        assert ents[0]["quantity"] == 3.0

    def test_multi_item_all_extracted(self):
        ents = AgentNLP.extract_food_entities_heuristically(
            "2 rotli ane 1 bowl dal ane 1 glass chaas khadha"
        )
        assert len(ents) >= 3, f"Expected >=3 items, got {len(ents)}: {[(e['food'], e['quantity']) for e in ents]}"

    def test_paneer_sabzi_is_recognized(self):
        """At least 'Paneer' should be recognized from 'paneer sabzi'."""
        ents = AgentNLP.extract_food_entities_heuristically("paneer sabzi khadhi")
        recognized = [e for e in ents if e["is_recognized"]]
        assert len(recognized) >= 1

    def test_unknown_food_not_logged_as_recognized(self):
        """A truly unknown food must have is_recognized=False."""
        ents = AgentNLP.extract_food_entities_heuristically("xyzfood khadha")
        assert len(ents) >= 1
        assert all(e["is_recognized"] is False for e in ents)

    def test_requires_clarification_for_unknown(self):
        ents = AgentNLP.extract_food_entities_heuristically("xyzfood khadha")
        assert len(ents) >= 1
        assert ents[0]["requires_clarification"] is True


# ---------------------------------------------------------------------------
# K. Rare Gujlish / edge cases
# ---------------------------------------------------------------------------
class TestRareGujlishEdgeCases:
    """Sentences with unusual combinations or Gujlish slang."""

    def test_dabbu_sentence_does_not_create_food_log_with_wrong_food(self):
        """'aaj thakor nu dabbu khali karyu' — 'dabbu' is a tiffin box.
        After fix, normalization must NOT corrupt it to 'khapli'.
        The pipeline may still classify it as CREATE_FOOD_LOG (since 'karyu'
        resembles eating context) but the entity must be is_recognized=False,
        meaning the system will ask for clarification rather than log fake kcal."""
        norm = AgentNLP.normalize_text("aaj thakor nu dabbu khali karyu")
        # The corruption must not happen:
        assert "khapli" not in norm.lower(), (
            f"'dabbu' or 'khali' was incorrectly converted to 'khapli': {norm!r}"
        )

    def test_dabbu_entity_not_recognized(self):
        """If the pipeline classifies 'dabbu khali karyu' as food, the entity
        must be is_recognized=False so no fake kcal are stored."""
        ents = AgentNLP.extract_food_entities_heuristically("aaj thakor nu dabbu khali karyu")
        # Any entity extracted must NOT be recognized as a real food
        for e in ents:
            assert e["is_recognized"] is False or e["requires_clarification"] is True, (
                f"Entity {e['food']!r} was recognized from a tiffin-box sentence"
            )

    def test_number_words_ek_be_tran(self):
        result = AgentNLP.normalize_text("ek rotli be apple tran anda")
        assert "1" in result
        assert "2" in result
        assert "3" in result

    def test_indic_digits_in_sentence(self):
        result = AgentNLP.normalize_text("૨ rotli ane ૧ bowl dal")
        assert "2" in result
        assert "1" in result

    def test_mixed_number_formats(self):
        ents = AgentNLP.extract_food_entities_heuristically("2 rotli ane be apple")
        qtys = [e["quantity"] for e in ents]
        assert 2.0 in qtys  # both should be 2

    def test_fused_digit_word(self):
        result = AgentNLP.normalize_text("2rotli")
        assert "2" in result
        assert "rotli" in result.lower()


# ---------------------------------------------------------------------------
# L. paneer sabzi — specific disambiguation tests
# ---------------------------------------------------------------------------
class TestPaneerSabziDisambiguation:
    """Verify the correct handling of the 'paneer sabzi' ambiguity."""

    def test_fuzzy_canonical_returns_none_for_paneer_sabzi(self):
        """Ratio 72 is below cutoff 80 — correct to return None rather than
        silently map to 'Paneer Bhurji'."""
        assert fuzzy_canonical("paneer sabzi") is None

    def test_entity_extracts_paneer_not_bhurji(self):
        ents = AgentNLP.extract_food_entities_heuristically("paneer sabzi khadhi")
        foods = [e["food"] for e in ents]
        assert "Paneer Bhurji" not in foods, (
            "Generic 'paneer sabzi' must not be silently mapped to the specific 'Paneer Bhurji'"
        )

    def test_paneer_sabzi_entity_count(self):
        """Should produce at least one entity (paneer)."""
        ents = AgentNLP.extract_food_entities_heuristically("paneer sabzi khadhi")
        assert len(ents) >= 1

    def test_paneer_sabzi_recognized_ingredient(self):
        """The recognised part ('Paneer') must be is_recognized=True."""
        ents = AgentNLP.extract_food_entities_heuristically("paneer sabzi khadhi")
        recognized = [e for e in ents if e["is_recognized"]]
        assert len(recognized) >= 1

    def test_paneer_bhurji_maps_correctly_when_explicit(self):
        """'paneer bhurji' explicitly named → must resolve correctly."""
        result = fuzzy_canonical("paneer bhurji")
        assert result is not None
        assert result == "Paneer Bhurji"
        assert result in CANONICAL_INDIAN_FOOD_PROFILES

    def test_panner_sabzi_after_normalize(self):
        """After normalize_text, 'panner sabzi' → 'paneer sabzi' (panner fixed).
        Then pipeline extracts 'Paneer' as the recognized item."""
        norm = AgentNLP.normalize_text("panner sabzi khadhi")
        assert "paneer" in norm.lower()
        ents = AgentNLP.extract_food_entities_heuristically("panner sabzi khadhi")
        recognized = [e for e in ents if e["is_recognized"]]
        assert len(recognized) >= 1


# ---------------------------------------------------------------------------
# M. Complete pipeline checks
# ---------------------------------------------------------------------------
class TestCompletePipeline:
    """End-to-end: raw input → normalize → intent → entities."""

    def test_pipeline_roti(self):
        msg = "2 rotli khadhi"
        norm = AgentNLP.normalize_text(msg)
        intent = AgentNLP.detect_intent(msg)
        ents = AgentNLP.extract_food_entities_heuristically(msg)
        assert "rotli" in norm.lower()
        assert intent == "CREATE_FOOD_LOG"
        assert len(ents) == 1
        assert ents[0]["is_recognized"]

    def test_pipeline_banana_typo(self):
        msg = "bananna khadhu"
        norm = AgentNLP.normalize_text(msg)
        intent = AgentNLP.detect_intent(msg)
        ents = AgentNLP.extract_food_entities_heuristically(msg)
        # normalize_text fixes banaana (double-a) via typo dict but not bananna (double-n).
        # bananna is resolved downstream by INDIAN_FOOD_SYNONYMS + fuzzy_canonical.
        # The critical check is that intent and entity recognition are correct.
        assert intent == "CREATE_FOOD_LOG"
        assert len(ents) >= 1
        # The entity should resolve to Banana (via synonym lookup or fuzzy_canonical)
        food_names = [e["food"].lower() for e in ents]
        assert any("banana" in n for n in food_names), (
            f"Expected banana in {food_names} — check INDIAN_FOOD_SYNONYMS for 'bananna'"
        )

    def test_pipeline_gujarati_script(self):
        msg = "2 રોટલી ખાધી"
        intent = AgentNLP.detect_intent(msg)
        lang = AgentNLP.detect_language(msg)
        assert intent == "CREATE_FOOD_LOG"
        assert lang == "gu"

    def test_pipeline_workout_gujlish(self):
        msg = "30 min gym karyu"
        intent = AgentNLP.detect_intent(msg)
        assert intent == "CREATE_ACTIVITY_LOG"

    def test_pipeline_multi_item(self):
        msg = "2 rotli ane 1 bowl dal ane chaas khadha"
        intent = AgentNLP.detect_intent(msg)
        ents = AgentNLP.extract_food_entities_heuristically(msg)
        assert intent in ("CREATE_FOOD_LOG", "CREATE_MULTI_LOG")
        assert len(ents) >= 2

    def test_pipeline_summary_gujlish(self):
        msg = "aaj nu summary aapo"
        intent = AgentNLP.detect_intent(msg)
        assert intent == "DAILY_SUMMARY"

    def test_pipeline_unknown_food_safe(self):
        """Unknown food goes through without crashing and is not force-matched."""
        msg = "xyzfood khadhu"
        intent = AgentNLP.detect_intent(msg)
        ents = AgentNLP.extract_food_entities_heuristically(msg)
        assert intent == "CREATE_FOOD_LOG"
        assert len(ents) >= 1
        assert ents[0]["is_recognized"] is False

    def test_pipeline_normalize_preserves_gujlish(self):
        """normalize_text must not destroy valid Gujlish food names."""
        msg = "rotli ane chaas khadhi"
        norm = AgentNLP.normalize_text(msg)
        assert "rotli" in norm.lower()
        assert "chaas" in norm.lower()
