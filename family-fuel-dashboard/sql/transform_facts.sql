-- ============================================================
-- Populate fact tables from dim tables + staging
-- Run after transform_dims.sql
-- ============================================================

-- ── fact_recipe_nutrition ──────────────────────────────────────
-- Map Spoonacular nutrient names to our dim_nutrients IDs
INSERT OR REPLACE INTO fact_recipe_nutrition
SELECT
    sn.recipe_id,
    dn.nutrient_id,
    sn.amount_per_serving
FROM staging_nutrition sn
JOIN dim_nutrients dn
    ON lower(dn.name) = lower(sn.nutrient_name)
WHERE sn.recipe_id IN (SELECT recipe_id FROM dim_recipes);

-- ── fact_recipe_ingredients ────────────────────────────────────
INSERT OR REPLACE INTO fact_recipe_ingredients
SELECT
    si.recipe_id,
    si.ingredient_id,
    si.quantity,
    si.unit
FROM staging_recipe_ingredients si
WHERE si.recipe_id IN (SELECT recipe_id FROM dim_recipes)
  AND si.ingredient_id IN (SELECT ingredient_id FROM dim_ingredients);

-- ── fact_meal_plans ────────────────────────────────────────────
-- Populated directly by run_pipeline.py using generate_meal_plan()
-- This SQL file handles re-inserts from a staging table
INSERT OR REPLACE INTO fact_meal_plans
SELECT
    plan_id,
    date_generated,
    day_of_week,
    meal_slot,
    recipe_id,
    target_calories
FROM staging_meal_plans
WHERE recipe_id IN (SELECT recipe_id FROM dim_recipes);
