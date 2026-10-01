"""
tests/test_fuzzy_resolve.py
---------------------------
Tests for the fuzzy spelling-correction additions to food_service.py:

  - fuzzy_canonical() unit tests (no DB required)
  - FoodService.resolve_food() integration tests with a mocked DB

Run with:
    cd backend
    pytest tests/test_fuzzy_resolve.py -v
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# Allow running from backend/ without installing the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.food_service import (
    fuzzy_canonical,
    CANONICAL_INDIAN_FOOD_PROFILES,
    FoodService,
)


# ---------------------------------------------------------------------------
# fuzzy_canonical() — unit tests (no DB, no async)
# ---------------------------------------------------------------------------
class TestFuzzyCanonical:
    """All probed against real vocab via probe_vocab.py before writing assertions."""

    def test_bananna_resolves_to_banana(self):
        """'bananna' is a 1-char typo of 'banana' — must match."""
        result = fuzzy_canonical("bananna")
        assert result is not None
        assert "Banana" in result

    def test_panner_resolves_to_paneer(self):
        """'panner' (common Hinglish typo) -> Paneer (score ~83 with fuzz.ratio)."""
        result = fuzzy_canonical("panner")
        assert result is not None
        assert "Paneer" in result

    def test_chiken_brest_resolves_to_chicken_breast(self):
        """'chiken brest' is in the synonym vocab so it resolves to Chicken Breast."""
        result = fuzzy_canonical("chiken brest")
        assert result is not None
        assert "Chicken" in result

    def test_chapti_resolves_to_chapati(self):
        """'chapti' is a 1-char deletion of 'chapati'."""
        result = fuzzy_canonical("chapti")
        assert result is not None
        assert "Chapati" in result

    def test_buttrmilk_resolves(self):
        """'buttrmilk' (missing 'e') -> Spiced Buttermilk (Chaas)."""
        result = fuzzy_canonical("buttrmilk")
        assert result is not None
        assert "Buttermilk" in result or "Chaas" in result

    def test_xyzfood_returns_none(self):
        """Completely unknown word — must not match anything."""
        result = fuzzy_canonical("xyzfood")
        assert result is None

    def test_pan_too_short_returns_none(self):
        """'pan' is only 3 chars — below the min-length guard of 4."""
        result = fuzzy_canonical("pan")
        assert result is None

    def test_paneer_bhurji_does_not_return_plain_paneer(self):
        """'paneer bhurji' is in CANONICAL_INDIAN_FOOD_PROFILES, so it must
        resolve to itself — NOT to plain 'Paneer'."""
        result = fuzzy_canonical("paneer bhurji")
        # It must be in the canonical vocab (it is: "Paneer Bhurji")
        assert result is not None
        assert result in CANONICAL_INDIAN_FOOD_PROFILES
        # And it must NOT resolve to the bare "Paneer" entry
        assert result != "Paneer"

    def test_non_ascii_returns_none(self):
        """Non-ASCII strings (Gujarati/Devanagari) bypass fuzzy — handled by
        the existing exact synonym step upstream."""
        result = fuzzy_canonical("રોટલી")
        assert result is None

    def test_empty_string_returns_none(self):
        result = fuzzy_canonical("")
        assert result is None

    def test_result_is_always_in_canonical_when_not_none(self):
        """Any non-None result must be a key in CANONICAL_INDIAN_FOOD_PROFILES
        or a synonym target that feeds into it. This validates the vocab contract."""
        cases = ["bananna", "panner", "chapti", "buttrmilk"]
        for case in cases:
            result = fuzzy_canonical(case)
            assert result is not None, f"{case!r} should resolve but got None"
            # The result is the target canonical name
            # (synonym targets like "Banana" are keys in CANONICAL_INDIAN_FOOD_PROFILES)
            assert result in CANONICAL_INDIAN_FOOD_PROFILES, (
                f"{case!r} -> {result!r} is not in CANONICAL_INDIAN_FOOD_PROFILES"
            )


# ---------------------------------------------------------------------------
# FoodService.resolve_food() — integration with mocked DB
# The canonical/synonym/fuzzy steps all return before any DB call, so the
# mock DB just needs to exist and return None for any find_one call.
# ---------------------------------------------------------------------------
def _make_mock_db():
    """Build a MagicMock that behaves like an async Motor database handle.

    resolve_food() calls get_db() then accesses db.foods and db.food_aliases.
    For the canonical/synonym/fuzzy code paths the function returns before any
    await, so the async mocks only need to exist — they will never be awaited
    for bananna/chapti/panner/roti/Banana.
    """
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=None)
    collection.find.return_value.to_list = AsyncMock(return_value=[])

    db = MagicMock()
    db.foods = collection
    db.food_aliases = collection
    return db


@pytest.mark.asyncio
class TestResolveFoodFuzzy:
    async def test_resolve_bananna_is_recognized(self):
        """'bananna' -> fuzzy -> Banana -> canonical hit -> is_recognized True."""
        mock_db = _make_mock_db()
        with patch("app.services.food_service.get_db", return_value=mock_db):
            result = await FoodService.resolve_food("bananna")
        assert result.get("is_recognized") is True, (
            f"Expected is_recognized=True, got {result}"
        )
        assert result.get("requires_clarification") is False
        assert result.get("food_name") == "Banana"

    async def test_resolve_chapti_is_recognized(self):
        """'chapti' -> fuzzy -> Chapati -> canonical hit -> is_recognized True."""
        mock_db = _make_mock_db()
        with patch("app.services.food_service.get_db", return_value=mock_db):
            result = await FoodService.resolve_food("chapti")
        assert result.get("is_recognized") is True, (
            f"Expected is_recognized=True, got {result}"
        )
        assert result.get("requires_clarification") is False
        assert result.get("food_name") == "Chapati"

    async def test_resolve_panner_is_recognized(self):
        """'panner' -> fuzzy -> Paneer -> is_recognized True."""
        mock_db = _make_mock_db()
        with patch("app.services.food_service.get_db", return_value=mock_db):
            result = await FoodService.resolve_food("panner")
        assert result.get("is_recognized") is True, (
            f"Expected is_recognized=True, got {result}"
        )
        assert "Paneer" in (result.get("food_name") or "")

    async def test_resolve_exact_food_still_works(self):
        """Existing exact-match path must not be broken."""
        mock_db = _make_mock_db()
        with patch("app.services.food_service.get_db", return_value=mock_db):
            result = await FoodService.resolve_food("Banana")
        assert result.get("is_recognized") is True
        assert result.get("food_name") == "Banana"

    async def test_resolve_roti_still_works(self):
        """'roti' is a synonym -> Roti canonical. Must still resolve."""
        mock_db = _make_mock_db()
        with patch("app.services.food_service.get_db", return_value=mock_db):
            result = await FoodService.resolve_food("roti")
        assert result.get("is_recognized") is True
