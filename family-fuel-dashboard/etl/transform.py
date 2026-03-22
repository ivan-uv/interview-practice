"""
Transform raw API JSON into normalized pandas DataFrames
ready to be loaded into DuckDB staging tables.
"""
import logging
import pandas as pd

log = logging.getLogger(__name__)

# Spoonacular nutrient name → our canonical dim_nutrients name
NUTRIENT_NAME_MAP = {
    "Calories": "Calories",
    "Protein": "Protein",
    "Fat": "Total Fat",
    "Carbohydrates": "Carbohydrates",
    "Carbohydrates (net)": "Carbohydrates",
    "Fiber": "Fiber",
    "Sugar": "Sugar",
    "Sodium": "Sodium",
    "Saturated Fat": "Saturated Fat",
    "Cholesterol": "Cholesterol",
    "Vitamin C": "Vitamin C",
}

# Allergen keywords → standardized tag
ALLERGEN_KEYWORDS = {
    "milk": "dairy", "dairy": "dairy", "cheese": "dairy", "butter": "dairy",
    "peanut": "nuts", "nut": "nuts", "almond": "nuts", "walnut": "nuts",
    "egg": "eggs",
    "wheat": "gluten", "gluten": "gluten", "flour": "gluten",
    "shellfish": "shellfish", "shrimp": "shellfish", "lobster": "shellfish",
    "fish": "fish", "salmon": "fish", "tuna": "fish",
    "soy": "soy",
}


def _detect_allergens(ingredient_names: list[str]) -> list[str]:
    found: set[str] = set()
    for name in ingredient_names:
        lower = name.lower()
        for keyword, tag in ALLERGEN_KEYWORDS.items():
            if keyword in lower:
                found.add(tag)
    return sorted(found)


def transform_recipes(
    raw_recipes: list[dict],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Parse Spoonacular recipe dicts into three staging DataFrames:
      - ingredients_df: ingredient_id, name, aisle
      - nutrition_df:   recipe_id, nutrient_name, amount_per_serving
      - recipe_ingr_df: recipe_id, ingredient_id, quantity, unit

    Args:
        raw_recipes: List of raw recipe dicts from Spoonacular complexSearch.

    Returns:
        (ingredients_df, nutrition_df, recipe_ingr_df)
    """
    ing_rows: list[dict] = []
    nut_rows: list[dict] = []
    ri_rows: list[dict] = []
    seen_ing_ids: set[int] = set()

    for recipe in raw_recipes:
        recipe_id = recipe.get("id")
        if not recipe_id:
            continue

        # ── Nutrition ──────────────────────────────────────────
        nutrition_data = recipe.get("nutrition") or {}
        nutrients = nutrition_data.get("nutrients", [])
        for nutrient in nutrients:
            raw_name = nutrient.get("name", "")
            canonical = NUTRIENT_NAME_MAP.get(raw_name)
            if canonical:
                nut_rows.append({
                    "recipe_id": recipe_id,
                    "nutrient_name": canonical,
                    "amount_per_serving": float(nutrient.get("amount", 0)),
                })

        # ── Ingredients ────────────────────────────────────────
        extended = recipe.get("extendedIngredients") or []
        for ingr in extended:
            ing_id = ingr.get("id")
            if not ing_id:
                continue

            if ing_id not in seen_ing_ids:
                seen_ing_ids.add(ing_id)
                ing_rows.append({
                    "ingredient_id": ing_id,
                    "name": ingr.get("nameClean") or ingr.get("name", ""),
                    "aisle": ingr.get("aisle", "Other"),
                })

            ri_rows.append({
                "recipe_id": recipe_id,
                "ingredient_id": ing_id,
                "quantity": float(ingr.get("amount", 0)),
                "unit": ingr.get("unit", ""),
            })

    ingredients_df = pd.DataFrame(
        ing_rows, columns=["ingredient_id", "name", "aisle"]
    ).drop_duplicates("ingredient_id")

    nutrition_df = pd.DataFrame(
        nut_rows, columns=["recipe_id", "nutrient_name", "amount_per_serving"]
    )

    recipe_ingr_df = pd.DataFrame(
        ri_rows, columns=["recipe_id", "ingredient_id", "quantity", "unit"]
    ).drop_duplicates(["recipe_id", "ingredient_id"])

    log.info(
        f"Transform: {len(ingredients_df)} ingredients, "
        f"{len(nutrition_df)} nutrition rows, "
        f"{len(recipe_ingr_df)} recipe-ingredient links"
    )
    return ingredients_df, nutrition_df, recipe_ingr_df


def transform_usda(raw_usda: list[dict]) -> pd.DataFrame:
    """
    Flatten USDA food dicts into a simple DataFrame with key nutrients.

    Returns:
        DataFrame with columns: fdc_id, name, nutrient_name, amount_per_100g
    """
    rows: list[dict] = []
    for food in raw_usda:
        fdc_id = food.get("fdcId")
        name = food.get("description", "")
        for nutrient in food.get("foodNutrients", []):
            nutrient_name = nutrient.get("nutrientName") or nutrient.get("name", "")
            canonical = NUTRIENT_NAME_MAP.get(nutrient_name)
            if canonical:
                rows.append({
                    "fdc_id": fdc_id,
                    "name": name,
                    "nutrient_name": canonical,
                    "amount_per_100g": float(nutrient.get("value") or nutrient.get("amount", 0)),
                })
    return pd.DataFrame(rows, columns=["fdc_id", "name", "nutrient_name", "amount_per_100g"])


def transform_off(raw_products: list[dict]) -> pd.DataFrame:
    """
    Flatten Open Food Facts product dicts into a summary DataFrame.

    Returns:
        DataFrame with columns: barcode, product_name, nutriscore, nova_group,
                                calories_100g, protein_100g, fat_100g, carbs_100g, allergens
    """
    rows: list[dict] = []
    for product in raw_products:
        nutriments = product.get("nutriments", {})
        rows.append({
            "barcode": str(product.get("code", "")),
            "product_name": product.get("product_name", ""),
            "nutriscore": product.get("nutriscore_grade", "").upper(),
            "nova_group": product.get("nova_group"),
            "calories_100g": float(nutriments.get("energy-kcal_100g") or nutriments.get("energy_100g", 0) or 0),
            "protein_100g": float(nutriments.get("proteins_100g", 0) or 0),
            "fat_100g": float(nutriments.get("fat_100g", 0) or 0),
            "carbs_100g": float(nutriments.get("carbohydrates_100g", 0) or 0),
            "allergens": ", ".join(product.get("allergens_tags", [])),
        })
    return pd.DataFrame(rows)
