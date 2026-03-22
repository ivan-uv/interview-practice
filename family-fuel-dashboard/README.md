# Family Fuel Dashboard

A **weekly meal planning intelligence dashboard** that combines three live food data APIs, a local DuckDB warehouse, and an interactive Streamlit interface — so a parent can answer *"what are we eating this week?"* with actual data instead of decision fatigue.

This is a portfolio data engineering project demonstrating:
- Multi-source API extraction (3 live sources with different auth/rate-limit profiles)
- Daily scheduled ETL pipeline with incremental loading and error logging
- Dimensional data modeling (star schema) in DuckDB
- SQL transformations (raw → dim/fact → mart)
- Interactive Streamlit dashboard with 5 feature pages

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│              DAILY PYTHON ETL JOB                │
│         (cron / scheduler.py)                    │
│                                                  │
│  ┌───────────┐ ┌────────────┐ ┌──────────────┐  │
│  │Spoonacular│ │ USDA FDC   │ │Open Food     │  │
│  │  API      │ │   API      │ │  Facts API   │  │
│  └─────┬─────┘ └─────┬──────┘ └──────┬───────┘  │
│        └──────────────┴───────────────┘          │
│                       │                          │
│             Python Extract + Transform           │
│          (requests, pandas, data validation)     │
│                       │                          │
│              DuckDB (local file)                 │
│                                                  │
│   raw_* tables → dim/fact tables → mart views   │
└────────────────────────┬─────────────────────────┘
                         │
                         ▼
             ┌─────────────────────┐
             │  Streamlit Dashboard │
             │   localhost:8501    │
             └─────────────────────┘
```

---

## Data Sources

| Source | What | Free Tier | Rate Limit |
|--------|------|-----------|------------|
| [Spoonacular](https://spoonacular.com/food-api) | 365K+ recipes with nutrition | **50 points/day** (credit card required) | Points-based |
| [USDA FoodData Central](https://fdc.nal.usda.gov) | Authoritative nutrient data for 380K+ foods | Unlimited | 1,000 req/hr |
| [Open Food Facts](https://world.openfoodfacts.org) | 3M+ crowd-sourced packaged food products | Unlimited | 10 req/min (search) |

> **Spoonacular note**: The free tier is 50 *points*/day (not requests). This pipeline batches nutrition + ingredient data into single calls to stay within limits. Sign-up requires a credit card but is not charged on the free tier.

---

## Data Model (Star Schema)

```
          dim_nutrients
               │
dim_ingredients─┤    dim_recipes
               │         │
    fact_recipe_ingredients   fact_recipe_nutrition
                              │
                         fact_meal_plans
                              │
         mart_weekly_plans, mart_kid_friendly,
         mart_macro_summary, mart_grocery_list
```

---

## Setup

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd interview-practice/family-fuel-dashboard
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
# Edit .env and fill in:
#   SPOONACULAR_KEY — from https://spoonacular.com/food-api (free, credit card required)
#   USDA_KEY        — from https://api.data.gov (free, no credit card)
#   OFF_USER_AGENT  — any descriptive string, e.g. "YourName/1.0 (your@email.com)"
```

### 3. Run the ETL pipeline

```bash
python etl/run_pipeline.py
```

This will:
1. Fetch up to 15 new recipes from Spoonacular (cached incrementally)
2. Look up USDA nutrient data for new ingredients
3. Fetch packaged food products from Open Food Facts
4. Load everything into `data/family_fuel.duckdb`
5. Run SQL transforms to populate dim/fact tables and mart views
6. Generate a weekly meal plan from available recipes

### 4. Launch the dashboard

```bash
streamlit run dashboard/app.py
```

Open http://localhost:8501 in your browser.

---

## Daily Scheduling

**Option A: Python scheduler (cross-platform)**

```bash
python scheduler.py
```

Runs once at startup, then daily at 06:00. Keep the process alive in a `tmux` session or configure as a systemd service.

**Option B: cron (Mac/Linux)**

```bash
crontab -e
# Add:
0 6 * * * cd /path/to/family-fuel-dashboard && /path/to/.venv/bin/python etl/run_pipeline.py >> logs/etl.log 2>&1
```

---

## Dashboard Pages

| Page | Description |
|------|-------------|
| 🗓 Meal Planner | 3×7 week grid (breakfast/lunch/dinner), filterable by prep time, diet, kid-friendly |
| 📊 Nutrition | Daily calorie totals vs. target, macro breakdown table |
| 🛒 Grocery List | Aggregated shopping list grouped by aisle, CSV export |
| 👦 Kid-Friendly | Quick recipes (≤30 min) filtered by allergen exclusions |
| 🔍 Data Health | Pipeline run log, row counts per table, data freshness |

---

## Running Tests

```bash
pytest tests/ -v
```

Tests use mocked API responses — no live API calls required.

---

## Project Structure

```
family-fuel-dashboard/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── scheduler.py              # Cross-platform daily runner
├── etl/
│   ├── run_pipeline.py       # Main orchestrator
│   ├── extract_spoonacular.py
│   ├── extract_usda.py
│   ├── extract_open_food_facts.py
│   ├── transform.py          # pandas cleaning + normalization
│   └── load.py               # DuckDB upserts
├── sql/
│   ├── create_tables.sql     # DDL: raw + dim + fact tables
│   ├── transform_dims.sql    # Populate dim tables from raw
│   ├── transform_facts.sql   # Populate fact tables from staging
│   └── create_marts.sql      # 4 mart views for the dashboard
├── dashboard/
│   ├── app.py                # Streamlit entrypoint
│   └── pages/
│       ├── 1_meal_planner.py
│       ├── 2_nutrition.py
│       ├── 3_grocery_list.py
│       ├── 4_kid_friendly.py
│       └── 5_data_health.py
├── data/                     # family_fuel.duckdb (gitignored)
├── logs/                     # etl.log (gitignored)
├── tests/
│   ├── test_extract.py
│   └── test_transform.py
└── notebooks/
    └── exploration.ipynb
```

---

## Tech Stack Choices

**DuckDB over SQLite**: Columnar storage gives 20-50× speedup on analytical queries. Native Parquet support, vectorized execution, and zero config make it ideal for a local data warehouse. `DuckDB` on a 2026 resume signals familiarity with the modern data stack.

**Streamlit over Dash/Panel**: Fastest path from Python to an interactive app — a working dashboard in under an hour. Keeps focus on data engineering skills, not frontend code. `st.cache_resource` for the DuckDB connection is officially documented by DuckDB.

**`schedule` library**: Lightweight, pure Python, cross-platform. No external broker or daemon required for a local portfolio project.

---

## Stretch Goals

- [ ] **dbt-duckdb**: Replace SQL transform files with dbt models (lineage, testing, docs)
- [ ] **Parquet export**: Write mart tables to Parquet for portability
- [ ] **GitHub Actions**: Move daily job to a free GHA scheduled workflow
- [ ] **LLM recipe search**: Use Claude API for natural-language recipe queries ("something quick with chicken my 4-year-old will eat")
- [ ] **Grocery price API**: Add estimated weekly cost per meal plan
