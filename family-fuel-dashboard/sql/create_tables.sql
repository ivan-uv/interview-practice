-- ============================================================
-- Family Fuel Dashboard — DDL
-- Layers: raw (staging) → dim/fact (warehouse) → mart (views)
-- ============================================================

-- ─────────────────────────────────────────────
-- RAW TABLES (landing zone, JSON-friendly)
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS raw_recipes (
    recipe_id       INTEGER PRIMARY KEY,
    title           VARCHAR,
    raw_json        JSON,
    fetched_at      TIMESTAMP DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS raw_usda_nutrients (
    fdc_id          INTEGER PRIMARY KEY,
    description     VARCHAR,
    raw_json        JSON,
    fetched_at      TIMESTAMP DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS raw_off_products (
    barcode         VARCHAR PRIMARY KEY,
    product_name    VARCHAR,
    raw_json        JSON,
    fetched_at      TIMESTAMP DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS raw_pipeline_runs (
    run_id          VARCHAR PRIMARY KEY,   -- UUID
    source          VARCHAR,               -- 'spoonacular' | 'usda' | 'open_food_facts'
    status          VARCHAR,               -- 'success' | 'error'
    rows_loaded     INTEGER DEFAULT 0,
    error_message   VARCHAR,
    run_at          TIMESTAMP DEFAULT current_timestamp
);

-- ─────────────────────────────────────────────
-- DIMENSION TABLES
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_recipes (
    recipe_id       INTEGER PRIMARY KEY,
    title           VARCHAR NOT NULL,
    cuisine         VARCHAR,
    prep_minutes    INTEGER,
    cook_minutes    INTEGER,
    servings        INTEGER,
    diet_tags       VARCHAR[],             -- ['vegetarian', 'gluten-free', ...]
    allergens       VARCHAR[],             -- ['dairy', 'nuts', ...]
    kid_friendly    BOOLEAN DEFAULT false,
    image_url       VARCHAR,
    source_url      VARCHAR,
    updated_at      TIMESTAMP DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS dim_ingredients (
    ingredient_id   INTEGER PRIMARY KEY,
    name            VARCHAR NOT NULL,
    aisle           VARCHAR,
    usda_fdc_id     INTEGER,
    off_barcode     VARCHAR,
    updated_at      TIMESTAMP DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS dim_nutrients (
    nutrient_id     INTEGER PRIMARY KEY,
    name            VARCHAR NOT NULL,      -- 'Protein', 'Total Fat', etc.
    unit            VARCHAR               -- 'g', 'mg', 'kcal'
);

-- Seed standard nutrients
INSERT OR IGNORE INTO dim_nutrients VALUES
    (1,  'Calories',        'kcal'),
    (2,  'Protein',         'g'),
    (3,  'Total Fat',       'g'),
    (4,  'Carbohydrates',   'g'),
    (5,  'Fiber',           'g'),
    (6,  'Sugar',           'g'),
    (7,  'Sodium',          'mg'),
    (8,  'Saturated Fat',   'g'),
    (9,  'Cholesterol',     'mg'),
    (10, 'Vitamin C',       'mg');

-- ─────────────────────────────────────────────
-- FACT TABLES
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS fact_recipe_nutrition (
    recipe_id           INTEGER,
    nutrient_id         INTEGER,
    amount_per_serving  DOUBLE,
    PRIMARY KEY (recipe_id, nutrient_id),
    FOREIGN KEY (recipe_id)  REFERENCES dim_recipes(recipe_id),
    FOREIGN KEY (nutrient_id) REFERENCES dim_nutrients(nutrient_id)
);

CREATE TABLE IF NOT EXISTS fact_recipe_ingredients (
    recipe_id       INTEGER,
    ingredient_id   INTEGER,
    quantity        DOUBLE,
    unit            VARCHAR,
    PRIMARY KEY (recipe_id, ingredient_id),
    FOREIGN KEY (recipe_id)     REFERENCES dim_recipes(recipe_id),
    FOREIGN KEY (ingredient_id) REFERENCES dim_ingredients(ingredient_id)
);

CREATE TABLE IF NOT EXISTS fact_meal_plans (
    plan_id         VARCHAR,               -- UUID grouping a week
    date_generated  DATE,
    day_of_week     INTEGER,               -- 1=Mon … 7=Sun
    meal_slot       VARCHAR,               -- 'breakfast' | 'lunch' | 'dinner'
    recipe_id       INTEGER,
    target_calories INTEGER,
    PRIMARY KEY (plan_id, day_of_week, meal_slot),
    FOREIGN KEY (recipe_id) REFERENCES dim_recipes(recipe_id)
);
