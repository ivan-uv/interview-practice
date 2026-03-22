"""
Page 5: Data Health Monitor — pipeline observability
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd
from datetime import datetime, timezone

st.set_page_config(page_title="Data Health | Family Fuel", page_icon="🔍", layout="wide")

from dashboard.app import get_db

con = get_db()

st.title("🔍 Data Health Monitor")
st.caption("Pipeline run history, row counts, and data freshness.")

# ── Top-level metrics ──────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

try:
    recipe_count = con.execute("SELECT COUNT(*) FROM dim_recipes").fetchone()[0]
    col1.metric("Recipes", recipe_count)
except Exception:
    col1.metric("Recipes", "—")

try:
    ingr_count = con.execute("SELECT COUNT(*) FROM dim_ingredients").fetchone()[0]
    col2.metric("Ingredients", ingr_count)
except Exception:
    col2.metric("Ingredients", "—")

try:
    product_count = con.execute("SELECT COUNT(*) FROM raw_off_products").fetchone()[0]
    col3.metric("Food Products", product_count)
except Exception:
    col3.metric("Food Products", "—")

try:
    last_run = con.execute("""
        SELECT MAX(run_at) FROM raw_pipeline_runs WHERE status = 'success'
    """).fetchone()[0]
    if last_run:
        days_ago = (datetime.now(timezone.utc) - pd.Timestamp(last_run).tz_localize("UTC")).days
        col4.metric("Days Since Last Run", days_ago)
    else:
        col4.metric("Days Since Last Run", "Never")
except Exception:
    col4.metric("Days Since Last Run", "—")

st.divider()

# ── Pipeline run log ───────────────────────────────────────────
st.subheader("Pipeline Run Log")
try:
    runs: pd.DataFrame = con.execute("""
        SELECT
            run_at,
            source,
            status,
            rows_loaded,
            error_message
        FROM raw_pipeline_runs
        ORDER BY run_at DESC
        LIMIT 50
    """).df()

    if runs.empty:
        st.info("No pipeline runs recorded yet. Run `python etl/run_pipeline.py`.")
    else:
        # Colour-code status
        def status_icon(s):
            return "✅" if s == "success" else "❌"

        runs["status"] = runs["status"].apply(lambda s: f"{status_icon(s)} {s}")
        runs.columns = ["Run At", "Source", "Status", "Rows Loaded", "Error"]
        st.dataframe(runs, use_container_width=True, hide_index=True)
except Exception as e:
    st.error(f"Could not load pipeline runs: {e}")

st.divider()

# ── Per-source row counts ──────────────────────────────────────
st.subheader("Row Counts by Table")

table_queries = {
    "raw_recipes": "SELECT COUNT(*) FROM raw_recipes",
    "raw_usda_nutrients": "SELECT COUNT(*) FROM raw_usda_nutrients",
    "raw_off_products": "SELECT COUNT(*) FROM raw_off_products",
    "dim_recipes": "SELECT COUNT(*) FROM dim_recipes",
    "dim_ingredients": "SELECT COUNT(*) FROM dim_ingredients",
    "fact_recipe_nutrition": "SELECT COUNT(*) FROM fact_recipe_nutrition",
    "fact_recipe_ingredients": "SELECT COUNT(*) FROM fact_recipe_ingredients",
    "fact_meal_plans": "SELECT COUNT(*) FROM fact_meal_plans",
}

counts = []
for table, query in table_queries.items():
    try:
        count = con.execute(query).fetchone()[0]
    except Exception:
        count = "—"
    counts.append({"Table": table, "Row Count": count})

st.dataframe(pd.DataFrame(counts), use_container_width=True, hide_index=True)
