-- ============================================================
-- Mart views — pre-aggregated for the Streamlit dashboard
-- Run after transform_facts.sql
-- ============================================================

-- ── mart_weekly_plans ──────────────────────────────────────────
-- One row per meal slot across the most recent generated week plan.
-- Dashboard uses this for the 3×7 meal grid.
CREATE OR REPLACE VIEW mart_weekly_plans AS
WITH latest_plan AS (
    SELECT plan_id
    FROM fact_meal_plans
    ORDER BY date_generated DESC
    LIMIT 1
)
SELECT
    fmp.plan_id,
    fmp.date_generated,
    fmp.day_of_week,
    fmp.meal_slot,
    fmp.target_calories,
    dr.recipe_id,
    dr.title,
    dr.cuisine,
    dr.prep_minutes,
    dr.servings,
    dr.diet_tags,
    dr.kid_friendly,
    dr.image_url,
    dr.source_url,
    -- Inline calorie count for the grid display
    COALESCE(nut.amount_per_serving, 0) AS calories_per_serving
FROM fact_meal_plans fmp
JOIN latest_plan lp USING (plan_id)
JOIN dim_recipes dr USING (recipe_id)
LEFT JOIN fact_recipe_nutrition nut
    ON dr.recipe_id = nut.recipe_id AND nut.nutrient_id = 1  -- 1 = Calories
ORDER BY fmp.day_of_week, fmp.meal_slot;


-- ── mart_kid_friendly ──────────────────────────────────────────
-- Recipes suitable for young kids: quick, unambiguously friendly.
CREATE OR REPLACE VIEW mart_kid_friendly AS
SELECT
    dr.recipe_id,
    dr.title,
    dr.cuisine,
    dr.prep_minutes,
    dr.servings,
    dr.diet_tags,
    dr.allergens,
    dr.image_url,
    dr.source_url,
    COALESCE(cal.amount_per_serving, 0) AS calories_per_serving,
    COALESCE(prot.amount_per_serving, 0) AS protein_g,
    COALESCE(fat.amount_per_serving, 0) AS fat_g,
    COALESCE(carb.amount_per_serving, 0) AS carbs_g
FROM dim_recipes dr
LEFT JOIN fact_recipe_nutrition cal  ON dr.recipe_id = cal.recipe_id  AND cal.nutrient_id  = 1
LEFT JOIN fact_recipe_nutrition prot ON dr.recipe_id = prot.recipe_id AND prot.nutrient_id = 2
LEFT JOIN fact_recipe_nutrition fat  ON dr.recipe_id = fat.recipe_id  AND fat.nutrient_id  = 3
LEFT JOIN fact_recipe_nutrition carb ON dr.recipe_id = carb.recipe_id AND carb.nutrient_id = 4
WHERE dr.prep_minutes <= 30
  AND dr.kid_friendly = true;


-- ── mart_macro_summary ──────────────────────────────────────────
-- Daily macro totals for the active week plan.
CREATE OR REPLACE VIEW mart_macro_summary AS
WITH latest_plan AS (
    SELECT plan_id FROM fact_meal_plans ORDER BY date_generated DESC LIMIT 1
)
SELECT
    fmp.day_of_week,
    SUM(CASE WHEN frn.nutrient_id = 1 THEN frn.amount_per_serving ELSE 0 END) AS total_calories,
    SUM(CASE WHEN frn.nutrient_id = 2 THEN frn.amount_per_serving ELSE 0 END) AS total_protein_g,
    SUM(CASE WHEN frn.nutrient_id = 3 THEN frn.amount_per_serving ELSE 0 END) AS total_fat_g,
    SUM(CASE WHEN frn.nutrient_id = 4 THEN frn.amount_per_serving ELSE 0 END) AS total_carbs_g,
    SUM(CASE WHEN frn.nutrient_id = 5 THEN frn.amount_per_serving ELSE 0 END) AS total_fiber_g,
    ANY_VALUE(fmp.target_calories)                                             AS target_calories
FROM fact_meal_plans fmp
JOIN latest_plan lp USING (plan_id)
LEFT JOIN fact_recipe_nutrition frn USING (recipe_id)
GROUP BY fmp.day_of_week
ORDER BY fmp.day_of_week;


-- ── mart_grocery_list ──────────────────────────────────────────
-- Aggregated ingredient shopping list for the active week plan.
CREATE OR REPLACE VIEW mart_grocery_list AS
WITH latest_plan AS (
    SELECT plan_id FROM fact_meal_plans ORDER BY date_generated DESC LIMIT 1
)
SELECT
    di.aisle,
    di.name         AS ingredient,
    SUM(fri.quantity) AS total_quantity,
    fri.unit,
    di.ingredient_id
FROM fact_meal_plans fmp
JOIN latest_plan lp USING (plan_id)
JOIN fact_recipe_ingredients fri USING (recipe_id)
JOIN dim_ingredients di USING (ingredient_id)
GROUP BY di.aisle, di.name, fri.unit, di.ingredient_id
ORDER BY di.aisle, di.name;
