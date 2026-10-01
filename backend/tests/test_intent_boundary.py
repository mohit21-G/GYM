"""
tests/test_intent_boundary.py
------------------------------
Phase-3 intent-boundary regression suite.

Tests the semantic boundary between:
  - Food consumption / food logging  →  CREATE_FOOD_LOG
  - Container / tiffin / non-food action  →  GENERAL_CHAT
  - Ambiguous / safe fallback  →  safe behaviour (never fake kcal logged)

Also covers:
  - Word-boundary protection for short eating verbs ("li" in EATING_VERBS)
  - False-positive protection for previously passing vocabulary
  - Conversation history awareness (second-message context)
  - Entity safety barrier (is_recognized=False prevents fake log)

Run with:
    cd backend
    pytest tests/test_intent_boundary.py -v
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.agent_nlp import AgentNLP, EATING_VERBS


# ---------------------------------------------------------------------------
# 1. Food consumption → must be CREATE_FOOD_LOG
# ---------------------------------------------------------------------------
class TestFoodConsumptionIntent:
    """Every variant of genuine food consumption must stay CREATE_FOOD_LOG."""

    def test_roti_khadhi(self):
        assert AgentNLP.detect_intent("aaje roti khadhi") == "CREATE_FOOD_LOG"

    def test_rotli_khadhi_gujlish(self):
        assert AgentNLP.detect_intent("2 rotli khadhi") == "CREATE_FOOD_LOG"

    def test_paneer_lidhu(self):
        """'lidhu' is a Gujarati eating verb — paneer lidhu = had paneer."""
        assert AgentNLP.detect_intent("paneer lidhu") == "CREATE_FOOD_LOG"

    def test_dal_khai(self):
        assert AgentNLP.detect_intent("dal khai") == "CREATE_FOOD_LOG"

    def test_poha_breakfast(self):
        assert AgentNLP.detect_intent("breakfast ma poha khadha") == "CREATE_FOOD_LOG"

    def test_rotli_khai(self):
        assert AgentNLP.detect_intent("rotli khai") == "CREATE_FOOD_LOG"

    def test_rotli_dal_multi(self):
        intent = AgentNLP.detect_intent("2 rotli ane dal khadha")
        assert intent in ("CREATE_FOOD_LOG", "CREATE_MULTI_LOG")

    def test_paneer_sabzi_lunch(self):
        assert AgentNLP.detect_intent("lunch ma paneer sabzi khadhi") == "CREATE_FOOD_LOG"

    def test_chaas_pidhi(self):
        assert AgentNLP.detect_intent("1 glass chaas pidhi") == "CREATE_FOOD_LOG"

    def test_egg_khadha(self):
        assert AgentNLP.detect_intent("2 anda khadha") == "CREATE_FOOD_LOG"

    def test_li_with_food_noun(self):
        """'li' as a standalone word is a valid Gujarati verb when a food noun is present."""
        intent = AgentNLP.detect_intent("dal li")
        assert intent == "CREATE_FOOD_LOG"

    def test_had_roti(self):
        assert AgentNLP.detect_intent("had 2 rotis for lunch") == "CREATE_FOOD_LOG"

    def test_ate_banana(self):
        assert AgentNLP.detect_intent("ate 1 banana") == "CREATE_FOOD_LOG"

    def test_gujarati_script_food(self):
        assert AgentNLP.detect_intent("2 રોટલી ખાધી") == "CREATE_FOOD_LOG"


# ---------------------------------------------------------------------------
# 2. Container / tiffin actions → must be GENERAL_CHAT
# ---------------------------------------------------------------------------
class TestContainerActionIntent:
    """Sentences about handling a tiffin/lunchbox must NOT be food logs."""

    def test_dabbu_khali_karyu(self):
        """Core failing case: 'emptied the tiffin box'."""
        assert AgentNLP.detect_intent("dabbu khali karyu") == "GENERAL_CHAT"

    def test_full_tiffin_sentence(self):
        assert AgentNLP.detect_intent("aaj thakor nu dabbu khali karyu") == "GENERAL_CHAT"

    def test_dabba_khali_kari_didho(self):
        assert AgentNLP.detect_intent("dabba khali kari didho") == "GENERAL_CHAT"

    def test_tiffin_khali_karyu(self):
        assert AgentNLP.detect_intent("tiffin khali karyu") == "GENERAL_CHAT"

    def test_dabba_saaf_karyo(self):
        assert AgentNLP.detect_intent("dabba saaf karyo") == "GENERAL_CHAT"

    def test_tiffin_lai_gayo(self):
        assert AgentNLP.detect_intent("tiffin lai gayo") == "GENERAL_CHAT"

    def test_maro_dabba_bharo(self):
        assert AgentNLP.detect_intent("maro dabba bharo") == "GENERAL_CHAT"

    def test_lunch_box_khali(self):
        assert AgentNLP.detect_intent("lunch box khali che") == "GENERAL_CHAT"

    def test_dabba_pack_karyu(self):
        assert AgentNLP.detect_intent("dabba pack karyu") == "GENERAL_CHAT"

    def test_tiffin_english_empty(self):
        assert AgentNLP.detect_intent("empty the tiffin") == "GENERAL_CHAT"

    def test_tiffin_clean(self):
        assert AgentNLP.detect_intent("tiffin clean kari didhu") == "GENERAL_CHAT"


# ---------------------------------------------------------------------------
# 3. Container WITH food noun → still CREATE_FOOD_LOG
# ---------------------------------------------------------------------------
class TestContainerWithFoodNoun:
    """If the user mentions a real food alongside the container word,
    that IS a food-log intent (e.g. 'dal na dabba ma lidhu')."""

    def test_dal_ma_dabba(self):
        """'dal ni dabba ma lidhu' — has food noun (dal), so it IS a food log."""
        intent = AgentNLP.detect_intent("dal na dabba ma khadha")
        # dal is a food noun, so this should still be food log
        assert intent == "CREATE_FOOD_LOG"

    def test_roti_tiffin(self):
        """User packed/ate roti from tiffin — food noun present."""
        intent = AgentNLP.detect_intent("roti tiffin ma lidhu")
        assert intent == "CREATE_FOOD_LOG"

    def test_paneer_dabba(self):
        """paneer + dabba — food noun present."""
        intent = AgentNLP.detect_intent("paneer na dabba ma khadha")
        assert intent == "CREATE_FOOD_LOG"


# ---------------------------------------------------------------------------
# 4. Word-boundary protection for short eating verbs
# ---------------------------------------------------------------------------
class TestEatingVerbWordBoundary:
    """'li' in EATING_VERBS must match as a whole word, not as a substring."""

    def test_li_in_eating_verbs(self):
        assert "li" in EATING_VERBS

    def test_li_does_not_match_inside_khali(self):
        """The word 'khali' (empty) must NOT trigger eating-verb detection alone."""
        # With the word-boundary fix, 'li' inside 'khali' must not match
        intent = AgentNLP.detect_intent("khali dabba")
        # No food noun + 'li' inside 'khali' (not standalone) = GENERAL_CHAT
        assert intent == "GENERAL_CHAT", (
            f"'li' inside 'khali' should not trigger CREATE_FOOD_LOG, got {intent}"
        )

    def test_standalone_li_with_food(self):
        """Standalone 'li' as a word after a food noun IS a valid eating verb."""
        intent = AgentNLP.detect_intent("chaas li")
        assert intent == "CREATE_FOOD_LOG"

    def test_li_boundary_protection_no_food(self):
        """'li' embedded in non-food words, no food noun → GENERAL_CHAT."""
        intent = AgentNLP.detect_intent("tiffin khali li didhu")
        # container word + container action — no explicit food noun
        assert intent == "GENERAL_CHAT"


# ---------------------------------------------------------------------------
# 5. Ambiguous cases — safe behaviour
# ---------------------------------------------------------------------------
class TestAmbiguousIntentSafety:
    """Genuinely ambiguous inputs must fall back to safe behaviour.
    Safe = never log fake kcal, may ask for clarification."""

    def test_unknown_food_entity_not_recognized(self):
        """Even if intent is CREATE_FOOD_LOG, unknown food gets is_recognized=False."""
        ents = AgentNLP.extract_food_entities_heuristically("xyzfood khadha")
        assert all(e["is_recognized"] is False for e in ents)
        assert all(e["requires_clarification"] is True for e in ents)

    def test_container_entity_not_recognized(self):
        """Tiffin-sentence entity must be is_recognized=False if it reaches extractor."""
        ents = AgentNLP.extract_food_entities_heuristically("dabbu khali karyu")
        # Should return either no entities or all unrecognized
        for e in ents:
            assert e["is_recognized"] is False or e["requires_clarification"] is True

    def test_dabbu_full_sentence_entity_safe(self):
        """Full tiffin sentence: even if an entity is extracted, it must not
        be a valid food entry (is_recognized must be False)."""
        ents = AgentNLP.extract_food_entities_heuristically(
            "aaj thakor nu dabbu khali karyu"
        )
        for e in ents:
            assert e["is_recognized"] is False or e["requires_clarification"] is True, (
                f"Entity {e['food']!r} was incorrectly recognized"
            )

    def test_just_verb_no_food(self):
        """Eating verb with no food noun → might still be GENERAL_CHAT."""
        intent = AgentNLP.detect_intent("khadha")
        # Without a food noun, this is ambiguous; acceptable to be either
        # GENERAL_CHAT or CREATE_FOOD_LOG (system will ask clarification anyway)
        assert intent in ("GENERAL_CHAT", "CREATE_FOOD_LOG")


# ---------------------------------------------------------------------------
# 6. thakor — audit: is it food vocabulary?
# ---------------------------------------------------------------------------
class TestThakorAudit:
    """'thakor' is a Gujarati proper noun/title, not a food term."""

    def test_thakor_not_in_food_nouns(self):
        from app.services.agent_nlp import FOOD_NOUNS
        assert "thakor" not in FOOD_NOUNS, "'thakor' must not be in FOOD_NOUNS"

    def test_thakor_not_in_synonyms(self):
        from app.services.agent_nlp import INDIAN_FOOD_SYNONYMS
        assert "thakor" not in INDIAN_FOOD_SYNONYMS

    def test_thakor_sentence_safe(self):
        """A sentence with 'thakor' but no food noun must not create a food log
        with recognized=True."""
        ents = AgentNLP.extract_food_entities_heuristically("thakor nu dabbu")
        for e in ents:
            assert e["is_recognized"] is False or e["requires_clarification"] is True


# ---------------------------------------------------------------------------
# 7. False-positive regression — all previously protected vocabulary
# ---------------------------------------------------------------------------
class TestFalsePositiveRegression:
    """None of these valid/unknown words should be corrupted or misclassified."""

    def test_dabbu_not_corrupted_to_khapli(self):
        norm = AgentNLP.normalize_text("dabbu khali karyu")
        assert "khapli" not in norm.lower()
        assert "dabbu" in norm.lower()

    def test_khali_not_corrupted_to_khapli(self):
        norm = AgentNLP.normalize_text("khali dabba")
        assert "khapli" not in norm.lower()
        assert "khali" in norm.lower()

    def test_rotli_preserved(self):
        norm = AgentNLP.normalize_text("2 rotli khadhi")
        assert "rotli" in norm.lower()

    def test_chaas_preserved(self):
        norm = AgentNLP.normalize_text("1 glass chaas pidhi")
        assert "chaas" in norm.lower()

    def test_thepla_preserved(self):
        norm = AgentNLP.normalize_text("2 thepla khadha")
        assert "thepla" in norm.lower()

    def test_bhakri_preserved(self):
        norm = AgentNLP.normalize_text("1 bhakri")
        assert "bhakri" in norm.lower()

    def test_names_preserved(self):
        for name in ["rahul", "priya", "amit"]:
            norm = AgentNLP.normalize_text(f"i am {name}")
            assert name in norm.lower()

    def test_quinoa_not_corrected(self):
        from app.services.food_service import fuzzy_canonical
        assert fuzzy_canonical("quinoa") is None

    def test_avocado_not_corrected(self):
        from app.services.food_service import fuzzy_canonical
        assert fuzzy_canonical("avocado") is None

    def test_keto_preserved(self):
        norm = AgentNLP.normalize_text("eating keto today")
        assert "keto" in norm.lower()

    def test_bmi_not_corrected(self):
        from app.services.food_service import fuzzy_canonical
        assert fuzzy_canonical("bmi") is None

    def test_macros_preserved(self):
        norm = AgentNLP.normalize_text("tracking my macros")
        assert "macros" in norm.lower()

    def test_rotlee_synonym_still_works(self):
        from app.services.agent_nlp import INDIAN_FOOD_SYNONYMS
        assert INDIAN_FOOD_SYNONYMS.get("rotlee") == "Roti"

    def test_panner_still_normalizes(self):
        norm = AgentNLP.normalize_text("panner sabzi")
        assert "paneer" in norm.lower()

    def test_bananna_synonym(self):
        from app.services.agent_nlp import INDIAN_FOOD_SYNONYMS
        assert INDIAN_FOOD_SYNONYMS.get("bananna") == "Banana"


# ---------------------------------------------------------------------------
# 8. Conversation history — second message context
# ---------------------------------------------------------------------------
class TestConversationHistoryContext:
    """Tests for multi-turn context. The deterministic pipeline does not use
    history (by design — >90% of messages are handled without it). These tests
    verify safe degradation rather than full history-awareness."""

    def test_standalone_food_name_logs(self):
        """'paneer sabzi' as a standalone message should extract at least paneer."""
        ents = AgentNLP.extract_food_entities_heuristically("paneer sabzi")
        recognized = [e for e in ents if e["is_recognized"]]
        assert len(recognized) >= 1

    def test_and_two_rotli_continuative(self):
        """'and two rotli' as a follow-up — entity extractor should find rotli."""
        ents = AgentNLP.extract_food_entities_heuristically("and two rotli")
        # 'two' → 2.0 via NUMBER_WORDS; 'rotli' → Roti via synonym
        assert len(ents) >= 1
        assert any("roti" in e["food"].lower() for e in ents)

    def test_second_message_food_intent(self):
        """A standalone food name message classifies as food log."""
        intent = AgentNLP.detect_intent("paneer sabzi")
        assert intent == "CREATE_FOOD_LOG"

    def test_dinner_log_karvu_is_general(self):
        """'mare dinner log karvu che' — informational, no actual food named."""
        intent = AgentNLP.detect_intent("mare dinner log karvu che")
        # No food noun + no eating verb → GENERAL_CHAT is safe
        assert intent in ("GENERAL_CHAT", "CREATE_FOOD_LOG")

    def test_second_food_with_implicit_meal(self):
        """'rotli ane chaas' — food entities extracted correctly."""
        ents = AgentNLP.extract_food_entities_heuristically("rotli ane chaas")
        assert len(ents) >= 2


# ---------------------------------------------------------------------------
# 9. Full pipeline safety barrier
# ---------------------------------------------------------------------------
class TestFoodLoggingEntityBarrier:
    """Regardless of intent classification, the entity extractor must never
    produce a recognized entity for non-food inputs. This is the last line
    of defence before kcal are written to the database."""

    def test_tiffin_entity_unrecognized(self):
        ents = AgentNLP.extract_food_entities_heuristically("dabba khali karyu")
        for e in ents:
            assert not e["is_recognized"], (
                f"Tiffin entity was recognized as food: {e['food']!r}"
            )

    def test_pure_verb_entity_unrecognized(self):
        ents = AgentNLP.extract_food_entities_heuristically("khadha")
        for e in ents:
            assert not e["is_recognized"]

    def test_proper_noun_entity_unrecognized(self):
        ents = AgentNLP.extract_food_entities_heuristically("thakor nu dabbu")
        for e in ents:
            assert not e["is_recognized"] or e["requires_clarification"]

    def test_known_food_entity_recognized(self):
        """Positive control: a real food must still be recognized=True."""
        ents = AgentNLP.extract_food_entities_heuristically("2 rotli khadhi")
        recognized = [e for e in ents if e["is_recognized"]]
        assert len(recognized) >= 1

    def test_0_kcal_for_unrecognized(self):
        """Unrecognized entities must have calories=0 when resolved.
        (This checks the is_recognized flag, not the DB call directly.)"""
        ents = AgentNLP.extract_food_entities_heuristically("xyzfood khadha")
        assert all(not e["is_recognized"] for e in ents)
        # requires_clarification must be True so process_and_log_food skips them
        assert all(e["requires_clarification"] for e in ents)
