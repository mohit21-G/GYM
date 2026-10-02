"""
tests/test_coffee_resolution.py
--------------------------------
Regression test: a bare "coffee" must log as a normal/plain Coffee, not get
silently converted to "Coffee With Milk" (and never to "Tea With Milk").

  - "coffee"                 -> Coffee            (plain / normal)
  - "coffee with milk"       -> Coffee With Milk
  - "milk coffee"            -> Coffee With Milk
  - "black coffee"           -> Black Coffee
  - "tea" / "chai"           -> Tea With Milk     (unaffected)

Run with:
    cd backend
    pytest tests/test_coffee_resolution.py -v
"""

import sys
import os
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.agent_nlp import AgentNLP
from app.services.food_service import FoodService, CANONICAL_INDIAN_FOOD_PROFILES


class TestCoffeeExtraction:
    def test_plain_coffee_is_coffee(self):
        foods = AgentNLP.extract_food_entities_heuristically("1 cup coffee")
        assert [f["food"] for f in foods] == ["Coffee"]

    def test_bare_coffee_is_coffee(self):
        foods = AgentNLP.extract_food_entities_heuristically("coffee")
        assert any(f["food"] == "Coffee" for f in foods)

    def test_coffee_with_milk_explicit(self):
        foods = AgentNLP.extract_food_entities_heuristically("coffee with milk")
        assert any(f["food"] == "Coffee With Milk" for f in foods)

    def test_milk_coffee_explicit(self):
        foods = AgentNLP.extract_food_entities_heuristically("milk coffee")
        assert any(f["food"] == "Coffee With Milk" for f in foods)

    def test_black_coffee_unchanged(self):
        foods = AgentNLP.extract_food_entities_heuristically("black coffee")
        assert any(f["food"] == "Black Coffee" for f in foods)

    def test_tea_unaffected(self):
        foods = AgentNLP.extract_food_entities_heuristically("1 cup tea")
        assert any(f["food"] == "Tea With Milk" for f in foods)


class TestCoffeeCanonicalProfile:
    def test_coffee_profile_exists(self):
        assert "Coffee" in CANONICAL_INDIAN_FOOD_PROFILES
        assert "Coffee With Milk" in CANONICAL_INDIAN_FOOD_PROFILES
        assert "Black Coffee" in CANONICAL_INDIAN_FOOD_PROFILES

    def test_coffee_profile_has_sensible_values(self):
        p = CANONICAL_INDIAN_FOOD_PROFILES["Coffee"]
        assert p["calories"] > 0
        assert p["unit"] == "cup"


def _mock_db():
    coll = MagicMock()
    coll.find_one = AsyncMock(return_value=None)
    coll.find.return_value.to_list = AsyncMock(return_value=[])
    db = MagicMock()
    db.foods = coll
    db.food_aliases = coll
    return db


@pytest.mark.asyncio
class TestResolveCoffee:
    async def test_resolve_plain_coffee(self):
        with patch("app.services.food_service.get_db", return_value=_mock_db()):
            r = await FoodService.resolve_food("coffee")
        assert r["food_name"] == "Coffee"
        assert r["is_recognized"] is True
        assert r["calories"] > 0

    async def test_resolve_coffee_not_tea(self):
        """Guard against the old heuristic that mapped coffee -> Tea With Milk."""
        with patch("app.services.food_service.get_db", return_value=_mock_db()):
            r = await FoodService.resolve_food("coffee")
        assert "Tea" not in r["food_name"]

    async def test_resolve_coffee_with_milk(self):
        with patch("app.services.food_service.get_db", return_value=_mock_db()):
            r = await FoodService.resolve_food("coffee with milk")
        assert r["food_name"] == "Coffee With Milk"

    async def test_resolve_black_coffee(self):
        with patch("app.services.food_service.get_db", return_value=_mock_db()):
            r = await FoodService.resolve_food("black coffee")
        assert r["food_name"] == "Black Coffee"
