-- ============================================================
-- Populate dimension tables from raw JSON
-- Run after each extract cycle
-- ============================================================

-- ── dim_recipes ──────────────────────────────────────────────
INSERT OR REPLACE INTO dim_recipes
SELECT
    recipe_id,
    title,
    raw_json->>'$.cuisines[0]'                                          AS cuisine,
    CAST(raw_json->>'$.readyInMinutes' AS INTEGER)                      AS prep_minutes,
    CAST(raw_json->>'$.cookingMinutes' AS INTEGER)                      AS cook_minutes,
    CAST(raw_json->>'$.servings' AS INTEGER)                            AS servings,
    -- Build diet_tags array from boolean flags
    list_filter([
        CASE WHEN raw_json->>'$.vegetarian' = 'true' THEN 'vegetarian' END,
        CASE WHEN raw_json->>'$.vegan'      = 'true' THEN 'vegan'      END,
        CASE WHEN raw_json->>'$.glutenFree' = 'true' THEN 'gluten-free' END,
        CASE WHEN raw_json->>'$.dairyFree'  = 'true' THEN 'dairy-free' END,
        CASE WHEN raw_json->>'$.veryHealthy' = 'true' THEN 'healthy'   END
    ], x -> x IS NOT NULL)                                              AS diet_tags,
    []::VARCHAR[]                                                       AS allergens,  -- populated by transform.py
    CASE
        WHEN CAST(raw_json->>'$.readyInMinutes' AS INTEGER) <= 30
         AND raw_json->>'$.veryPopular' = 'true' THEN true
        ELSE false
    END                                                                 AS kid_friendly,
    raw_json->>'$.image'                                                AS image_url,
    raw_json->>'$.sourceUrl'                                            AS source_url,
    current_timestamp                                                   AS updated_at
FROM raw_recipes;

-- ── dim_ingredients ───────────────────────────────────────────
-- Flatten ingredients from Spoonacular's extendedIngredients array
-- This requires the ingredients to be pre-exploded into a staging table by transform.py
INSERT OR REPLACE INTO dim_ingredients
SELECT DISTINCT
    ingredient_id,
    name,
    aisle,
    NULL AS usda_fdc_id,   -- populated by extract_usda.py
    NULL AS off_barcode,   -- populated by extract_open_food_facts.py
    current_timestamp AS updated_at
FROM staging_ingredients
WHERE ingredient_id NOT IN (SELECT ingredient_id FROM dim_ingredients);
