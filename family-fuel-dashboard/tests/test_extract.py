"""
Tests for extract modules — all API calls are mocked.
"""
import pytest
from unittest.mock import patch, MagicMock

# ── Spoonacular ───────────────────────────────────────────────

def _mock_spoonacular_response(num_recipes=3):
    """Build a minimal Spoonacular complexSearch response."""
    return {
        "results": [
            {
                "id": 100 + i,
                "title": f"Test Recipe {i}",
                "readyInMinutes": 30,
                "servings": 4,
                "image": f"https://example.com/img/{i}.jpg",
                "sourceUrl": f"https://example.com/recipe/{i}",
                "vegetarian": False,
                "vegan": False,
                "glutenFree": False,
                "dairyFree": False,
                "veryHealthy": True,
                "veryPopular": True,
                "cuisines": ["Italian"],
                "nutrition": {
                    "nutrients": [
                        {"name": "Calories", "amount": 450.0, "unit": "kcal"},
                        {"name": "Protein", "amount": 25.0, "unit": "g"},
                        {"name": "Fat", "amount": 15.0, "unit": "g"},
                        {"name": "Carbohydrates", "amount": 55.0, "unit": "g"},
                    ]
                },
                "extendedIngredients": [
                    {"id": 200 + i, "name": f"ingredient_{i}", "nameClean": f"ingredient {i}",
                     "aisle": "Produce", "amount": 2.0, "unit": "cups"},
                ],
            }
            for i in range(num_recipes)
        ]
    }


def test_fetch_recipes_returns_list():
    """fetch_recipes should return a list of dicts."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = _mock_spoonacular_response(3)

    with patch("etl.extract_spoonacular.requests.get", return_value=mock_resp), \
         patch("etl.extract_spoonacular._get_api_key", return_value="test_key"), \
         patch("time.sleep"):
        from etl.extract_spoonacular import fetch_recipes
        results = fetch_recipes(exclude_ids=set(), max_new=5)

    assert isinstance(results, list)
    assert len(results) > 0
    assert "id" in results[0]
    assert "title" in results[0]


def test_fetch_recipes_skips_cached_ids():
    """fetch_recipes should not return recipes already in exclude_ids."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = _mock_spoonacular_response(3)

    with patch("etl.extract_spoonacular.requests.get", return_value=mock_resp), \
         patch("etl.extract_spoonacular._get_api_key", return_value="test_key"), \
         patch("time.sleep"):
        from etl.extract_spoonacular import fetch_recipes
        # Exclude all recipe IDs that will be returned
        results = fetch_recipes(exclude_ids={100, 101, 102}, max_new=10)

    assert all(r["id"] not in {100, 101, 102} for r in results)


def test_fetch_recipes_quota_exhausted():
    """fetch_recipes should stop gracefully when Spoonacular returns 402."""
    import requests as req_module

    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = req_module.HTTPError(
        response=MagicMock(status_code=402)
    )

    with patch("etl.extract_spoonacular.requests.get", return_value=mock_resp), \
         patch("etl.extract_spoonacular._get_api_key", return_value="test_key"), \
         patch("time.sleep"):
        from etl.extract_spoonacular import fetch_recipes
        results = fetch_recipes(exclude_ids=set(), max_new=5)

    assert results == []


# ── USDA ──────────────────────────────────────────────────────

def _mock_usda_response():
    return {
        "foods": [
            {
                "fdcId": 9001,
                "description": "chicken breast",
                "dataType": "Foundation",
                "foodNutrients": [
                    {"nutrientName": "Protein", "value": 31.0},
                    {"nutrientName": "Total lipid (fat)", "value": 3.6},
                    {"nutrientName": "Energy", "value": 165.0},
                ],
            }
        ]
    }


def test_fetch_usda_nutrients_returns_list():
    """fetch_usda_nutrients should return a list of food dicts."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = _mock_usda_response()

    with patch("etl.extract_usda.requests.post", return_value=mock_resp), \
         patch("time.sleep"):
        from etl.extract_usda import fetch_usda_nutrients
        results = fetch_usda_nutrients(["chicken breast"])

    assert len(results) == 1
    assert results[0]["fdcId"] == 9001


def test_fetch_usda_empty_ingredients():
    """fetch_usda_nutrients should return empty list for empty input."""
    from etl.extract_usda import fetch_usda_nutrients
    results = fetch_usda_nutrients([])
    assert results == []
