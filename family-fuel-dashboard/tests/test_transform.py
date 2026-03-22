"""
Tests for transform.py — fixture-based, no API calls.
"""
import pytest
import pandas as pd

# ── Fixtures ──────────────────────────────────────────────────

RECIPE_FIXTURE = [
    {
        "id": 42,
        "title": "Quick Pasta",
        "readyInMinutes": 25,
        "servings": 4,
        "cuisines": ["Italian"],
        "vegetarian": True,
        "vegan": False,
        "glutenFree": False,
        "dairyFree": False,
        "veryHealthy": False,
        "veryPopular": True,
        "image": "https://example.com/pasta.jpg",
        "sourceUrl": "https://example.com/pasta",
        "nutrition": {
            "nutrients": [
                {"name": "Calories", "amount": 380.0, "unit": "kcal"},
                {"name": "Protein", "amount": 12.0, "unit": "g"},
                {"name": "Fat", "amount": 8.0, "unit": "g"},
                {"name": "Carbohydrates", "amount": 62.0, "unit": "g"},
                {"name": "Fiber", "amount": 3.5, "unit": "g"},
                {"name": "Sodium", "amount": 420.0, "unit": "mg"},
                # Unknown nutrient — should be silently ignored
                {"name": "Unknown Nutrient", "amount": 99.0, "unit": "mg"},
            ]
        },
        "extendedIngredients": [
            {"id": 11, "name": "pasta", "nameClean": "pasta", "aisle": "Pasta and Rice",
             "amount": 200.0, "unit": "g"},
            {"id": 12, "name": "tomato sauce", "nameClean": "tomato sauce", "aisle": "Canned Goods",
             "amount": 400.0, "unit": "ml"},
        ],
    }
]

USDA_FIXTURE = [
    {
        "fdcId": 9001,
        "description": "Pasta, cooked",
        "dataType": "Foundation",
        "foodNutrients": [
            {"nutrientName": "Protein", "value": 5.8},
            {"nutrientName": "Energy", "value": 158.0},
            {"nutrientName": "Total lipid (fat)", "value": 0.9},
            {"nutrientName": "Carbohydrate, by difference", "value": 30.9},
        ],
    }
]

OFF_FIXTURE = [
    {
        "code": "1234567890",
        "product_name": "Oat Flakes",
        "nutriscore_grade": "a",
        "nova_group": 1,
        "nutriments": {
            "energy-kcal_100g": 367.0,
            "proteins_100g": 13.0,
            "fat_100g": 7.0,
            "carbohydrates_100g": 55.0,
        },
        "allergens_tags": ["en:gluten"],
    }
]


# ── transform_recipes tests ───────────────────────────────────

def test_transform_recipes_returns_three_dataframes():
    from etl.transform import transform_recipes
    ing_df, nut_df, ri_df = transform_recipes(RECIPE_FIXTURE)
    assert isinstance(ing_df, pd.DataFrame)
    assert isinstance(nut_df, pd.DataFrame)
    assert isinstance(ri_df, pd.DataFrame)


def test_transform_recipes_ingredient_count():
    from etl.transform import transform_recipes
    ing_df, _, _ = transform_recipes(RECIPE_FIXTURE)
    assert len(ing_df) == 2  # pasta + tomato sauce


def test_transform_recipes_nutrition_maps_known_nutrients():
    from etl.transform import transform_recipes
    _, nut_df, _ = transform_recipes(RECIPE_FIXTURE)
    nutrient_names = set(nut_df["nutrient_name"].tolist())
    assert "Calories" in nutrient_names
    assert "Protein" in nutrient_names
    assert "Total Fat" in nutrient_names
    assert "Carbohydrates" in nutrient_names
    # Unknown nutrient should be dropped
    assert "Unknown Nutrient" not in nutrient_names


def test_transform_recipes_calorie_value():
    from etl.transform import transform_recipes
    _, nut_df, _ = transform_recipes(RECIPE_FIXTURE)
    cal_row = nut_df[nut_df["nutrient_name"] == "Calories"]
    assert len(cal_row) == 1
    assert cal_row.iloc[0]["amount_per_serving"] == pytest.approx(380.0)


def test_transform_recipes_recipe_ingredient_links():
    from etl.transform import transform_recipes
    _, _, ri_df = transform_recipes(RECIPE_FIXTURE)
    assert set(ri_df["recipe_id"].tolist()) == {42}
    assert len(ri_df) == 2


def test_transform_recipes_empty_input():
    from etl.transform import transform_recipes
    ing_df, nut_df, ri_df = transform_recipes([])
    assert len(ing_df) == 0
    assert len(nut_df) == 0
    assert len(ri_df) == 0


def test_transform_recipes_missing_nutrition():
    """Recipes without nutrition data should still yield ingredients."""
    recipe = {**RECIPE_FIXTURE[0], "nutrition": None}
    from etl.transform import transform_recipes
    ing_df, nut_df, ri_df = transform_recipes([recipe])
    assert len(ing_df) == 2
    assert len(nut_df) == 0


# ── transform_usda tests ──────────────────────────────────────

def test_transform_usda_returns_dataframe():
    from etl.transform import transform_usda
    df = transform_usda(USDA_FIXTURE)
    assert isinstance(df, pd.DataFrame)


def test_transform_usda_empty():
    from etl.transform import transform_usda
    df = transform_usda([])
    assert len(df) == 0


# ── transform_off tests ───────────────────────────────────────

def test_transform_off_returns_dataframe():
    from etl.transform import transform_off
    df = transform_off(OFF_FIXTURE)
    assert isinstance(df, pd.DataFrame)
    assert "barcode" in df.columns
    assert "product_name" in df.columns
    assert df.iloc[0]["calories_100g"] == pytest.approx(367.0)


def test_transform_off_empty():
    from etl.transform import transform_off
    df = transform_off([])
    assert len(df) == 0
