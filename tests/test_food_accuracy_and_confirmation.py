import pytest
import os
import sys

sys.path.insert(0, os.path.abspath("."))

from backend.app.services.agent_nlp import AgentNLP
from backend.app.services.food_service import FoodService
from backend.app.schemas.food_log import FoodItemInput

class TestFoodIdentificationAccuracy:
    """Test suite covering the 7 specific requirements for food identification accuracy."""

    def test_protein_shake_gujlish(self):
        """1 spoon protein shake lidhu -> must identify Protein Shake, not Roti or Sabzi."""
        query = "1 spoon protein shake lidhu"
        extracted = AgentNLP.extract_food_entities_heuristically(query)
        assert len(extracted) == 1, f"Expected 1 item, got {len(extracted)}"
        item = extracted[0]
        assert item["food"] == "Protein Shake", f"Expected Protein Shake, got {item['food']}"
        assert item["quantity"] == 1.0
        assert item["unit"] == "tbsp"
        assert item["is_recognized"] is True
        assert item["requires_clarification"] is False

    def test_protein_powder_english(self):
        """I drank one scoop of protein powder -> must identify Whey Protein Powder."""
        query = "I drank one scoop of protein powder"
        extracted = AgentNLP.extract_food_entities_heuristically(query)
        assert len(extracted) == 1
        item = extracted[0]
        assert item["food"] == "Whey Protein Powder"
        assert item["quantity"] == 1.0
        assert item["unit"] == "scoop"
        assert item["is_recognized"] is True

    def test_protein_shake_hinglish(self):
        """Ek chamach protein shake piya -> must identify Protein Shake."""
        query = "Ek chamach protein shake piya"
        extracted = AgentNLP.extract_food_entities_heuristically(query)
        assert len(extracted) == 1
        item = extracted[0]
        assert item["food"] == "Protein Shake"
        assert item["quantity"] == 1.0
        assert item["unit"] == "tbsp"
        assert item["is_recognized"] is True

    def test_protein_shake_gujarati_script(self):
        """મેં એક ચમચી પ્રોટીન શેક પીધો -> must identify Protein Shake."""
        query = "મેં એક ચમચી પ્રોટીન શેક પીધો"
        extracted = AgentNLP.extract_food_entities_heuristically(query)
        assert len(extracted) == 1
        item = extracted[0]
        assert item["food"] == "Protein Shake"
        assert item["quantity"] == 1.0
        assert item["unit"] == "tbsp"
        assert item["is_recognized"] is True

    def test_rotli_gujlish(self):
        """2 rotli khai -> must identify Roti, 2 pieces."""
        query = "2 rotli khai"
        extracted = AgentNLP.extract_food_entities_heuristically(query)
        assert len(extracted) == 1
        item = extracted[0]
        assert item["food"] == "Roti"
        assert item["quantity"] == 2.0
        assert item["unit"] == "piece"

    def test_thepla_gujlish(self):
        """2 thepla khadha -> must identify Methi Thepla, 2 pieces."""
        query = "2 thepla khadha"
        extracted = AgentNLP.extract_food_entities_heuristically(query)
        assert len(extracted) == 1
        item = extracted[0]
        assert item["food"] == "Methi Thepla"
        assert item["quantity"] == 2.0
        assert item["unit"] == "piece"

    def test_multi_food_dal_and_rotis(self):
        """1 bowl dal and 2 rotis -> must extract Toor Dal (1 bowl) and Roti (2 pieces)."""
        query = "1 bowl dal and 2 rotis"
        extracted = AgentNLP.extract_food_entities_heuristically(query)
        assert len(extracted) == 2, f"Expected 2 items, got {len(extracted)}"
        assert extracted[0]["food"] == "Toor Dal"
        assert extracted[0]["quantity"] == 1.0
        assert extracted[0]["unit"] == "bowl"

        assert extracted[1]["food"] == "Roti"
        assert extracted[1]["quantity"] == 2.0
        assert extracted[1]["unit"] == "piece"

    def test_distinguish_chapati_from_roti(self):
        """Distinct foods must have distinct catalog entries (Chapati != Roti)."""
        extracted_chapati = AgentNLP.extract_food_entities_heuristically("1 chapati")
        extracted_roti = AgentNLP.extract_food_entities_heuristically("1 roti")
        assert extracted_chapati[0]["food"] == "Chapati"
        assert extracted_roti[0]["food"] == "Roti"

    def test_unknown_food_flagged_for_clarification(self):
        """Unknown food names must NOT be silently matched to a random food."""
        query = "1 bowl unknownxyzfood khadhu"
        extracted = AgentNLP.extract_food_entities_heuristically(query)
        assert len(extracted) == 1
        item = extracted[0]
        assert item["is_recognized"] is False
        assert item["requires_clarification"] is True
        assert item["clarification_reason"] == "UNKNOWN_FOOD"

    def test_missing_quantity_uses_reasonable_default(self):
        """Identified food without explicit quantity must use reasonable default serving without clarification."""
        query = "protein shake lidhu"
        extracted = AgentNLP.extract_food_entities_heuristically(query)
        assert len(extracted) == 1
        item = extracted[0]
        assert item["food"] == "Protein Shake"
        assert item["has_explicit_quantity"] is False
        assert item["quantity"] == 1.0
        assert item["unit"] == "scoop"
        assert item["requires_clarification"] is False

class TestFoodServiceResolutionAndPortions:
    """Tests for FoodService.resolve_food and calculate_portion_multiplier."""

    @pytest.mark.asyncio
    async def test_resolve_protein_shake(self):
        res = await FoodService.resolve_food("protein shake")
        assert res["food_name"] == "Protein Shake"
        assert res["is_recognized"] is True
        assert res["calories"] == 160.0

    @pytest.mark.asyncio
    async def test_resolve_protein_powder(self):
        res = await FoodService.resolve_food("protein powder")
        assert res["food_name"] == "Whey Protein Powder"
        assert res["is_recognized"] is True
        assert res["calories"] == 120.0
        assert res["protein_g"] == 24.0

    @pytest.mark.asyncio
    async def test_resolve_chapati_vs_roti(self):
        res_chapati = await FoodService.resolve_food("chapati")
        res_roti = await FoodService.resolve_food("roti")
        assert res_chapati["food_name"] == "Chapati"
        assert res_chapati["calories"] == 85.0
        assert res_roti["food_name"] == "Roti"
        assert res_roti["calories"] == 104.0

    @pytest.mark.asyncio
    async def test_resolve_unknown_food_returns_zero_calories(self):
        res = await FoodService.resolve_food("randomfakexyzfood")
        assert res["is_recognized"] is False
        assert res["requires_clarification"] is True
        assert res["calories"] == 0.0

    def test_portion_multiplier_shake_spoon(self):
        """1 spoon protein shake should yield portion proportional to spoon, not a full glass."""
        mult = FoodService.calculate_portion_multiplier(
            base_unit="glass",
            requested_unit="tbsp",
            quantity=1.0,
            food_name="Protein Shake",
        )
        assert round(160.0 * mult, 1) == 45.0
        assert round(25.0 * mult, 1) == 7.0

    def test_portion_multiplier_powder_tablespoon(self):
        """1 tbsp protein powder should be ~1/3 scoop (approx 40 kcal, 8g protein)."""
        mult = FoodService.calculate_portion_multiplier(
            base_unit="scoop",
            requested_unit="tbsp",
            quantity=1.0,
            food_name="Whey Protein Powder",
        )
        cal = round(120.0 * mult, 1)
        protein = round(24.0 * mult, 1)
        assert 35.0 <= cal <= 45.0
        assert 7.0 <= protein <= 9.0

    def test_portion_multiplier_powder_scoop(self):
        """1 scoop protein powder should be exact 1.0 scoop."""
        mult = FoodService.calculate_portion_multiplier(
            base_unit="scoop",
            requested_unit="scoop",
            quantity=1.0,
            food_name="Whey Protein Powder",
        )
        assert mult == 1.0

@pytest.mark.asyncio
class TestConfirmationBeforeLogging:
    """Verifies that unknown food or ambiguous quantity asks for clarification without logging."""

    async def test_unknown_food_does_not_log_to_db(self):
        input_item = FoodItemInput(
            food="randomunknownsuperfood",
            quantity=1.0,
            unit="bowl",
            is_recognized=False,
            requires_clarification=True,
            clarification_reason="UNKNOWN_FOOD",
        )
        result = await FoodService.process_and_log_food(
            user_id="test_user_confirmation",
            items=[input_item],
        )
        assert result.requiresClarification is True
        assert len(result.loggedItems) == 0
        assert "randomunknownsuperfood" in result.replyText or "identify the food" in result.replyText

    async def test_ambiguous_quantity_does_not_log_to_db(self):
        input_item = FoodItemInput(
            food="Protein Shake",
            quantity=1.0,
            has_explicit_quantity=False,
            requires_clarification=True,
            clarification_reason="AMBIGUOUS_QUANTITY",
        )
        result = await FoodService.process_and_log_food(
            user_id="test_user_confirmation",
            items=[input_item],
        )
        assert result.requiresClarification is True
        assert len(result.loggedItems) == 0
        assert "How much" in result.replyText
