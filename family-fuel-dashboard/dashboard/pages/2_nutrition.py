"""
Page 2: Nutrition Breakdown — daily macros vs. target
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Nutrition | Family Fuel", page_icon="📊", layout="wide")

from dashboard.app import get_db

con = get_db()

st.title("📊 Nutrition Breakdown")
st.caption("Daily and weekly macro totals for your current meal plan.")

# ── Sidebar: calorie target ───────────────────────────────────
with st.sidebar:
    st.subheader("Targets")
    cal_target = st.number_input("Daily calorie target", 1200, 3500, 2000, step=100)
    protein_pct = st.slider("Protein %", 10, 40, 25)
    carb_pct = st.slider("Carb %", 20, 60, 45)
    fat_pct = 100 - protein_pct - carb_pct
    st.metric("Fat % (auto)", f"{fat_pct}%")

# ── Load macro summary ────────────────────────────────────────
try:
    df: pd.DataFrame = con.execute("""
        SELECT
            day_of_week,
            total_calories,
            total_protein_g,
            total_fat_g,
            total_carbs_g,
            total_fiber_g
        FROM mart_macro_summary
        ORDER BY day_of_week
    """).df()
except Exception as e:
    st.error(f"Could not load nutrition data: {e}")
    st.info("Run `python etl/run_pipeline.py` first.")
    st.stop()

if df.empty:
    st.warning("No nutrition data available yet.")
    st.stop()

DAY_NAMES = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
df["day_name"] = df["day_of_week"].map(DAY_NAMES)

# ── KPI cards ─────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Avg Daily Calories", f"{df['total_calories'].mean():.0f} kcal",
            delta=f"{df['total_calories'].mean() - cal_target:+.0f} vs target")
col2.metric("Avg Protein", f"{df['total_protein_g'].mean():.1f} g")
col3.metric("Avg Carbs", f"{df['total_carbs_g'].mean():.1f} g")
col4.metric("Avg Fat", f"{df['total_fat_g'].mean():.1f} g")

st.divider()

# ── Daily calorie bar chart ───────────────────────────────────
st.subheader("Daily Calorie Totals")
chart_df = df.set_index("day_name")[["total_calories"]].rename(
    columns={"total_calories": "Calories (kcal)"}
)
st.bar_chart(chart_df)
st.caption(f"Target: {cal_target} kcal/day (red reference line not shown in basic bar chart)")

# ── Weekly macro table ────────────────────────────────────────
st.subheader("Daily Macro Detail")
display_df = df[["day_name", "total_calories", "total_protein_g", "total_carbs_g",
                 "total_fat_g", "total_fiber_g"]].copy()
display_df.columns = ["Day", "Calories (kcal)", "Protein (g)", "Carbs (g)", "Fat (g)", "Fiber (g)"]
st.dataframe(display_df, use_container_width=True, hide_index=True)

# ── Top recipes by protein ────────────────────────────────────
st.subheader("Top Recipes by Protein")
try:
    top_protein: pd.DataFrame = con.execute("""
        SELECT dr.title, frn.amount_per_serving AS protein_g
        FROM fact_recipe_nutrition frn
        JOIN dim_recipes dr USING (recipe_id)
        WHERE frn.nutrient_id = 2
        ORDER BY frn.amount_per_serving DESC
        LIMIT 5
    """).df()
    st.dataframe(top_protein, use_container_width=True, hide_index=True)
except Exception:
    st.caption("No recipe data yet.")
