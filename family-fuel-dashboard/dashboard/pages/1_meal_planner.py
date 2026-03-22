"""
Page 1: Weekly Meal Planner
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Meal Planner | Family Fuel", page_icon="🗓", layout="wide")

from dashboard.app import get_db

con = get_db()

st.title("🗓 Weekly Meal Planner")
st.caption("Your week of meals, built from your recipe library.")

# ── Filters ───────────────────────────────────────────────────
with st.sidebar:
    st.subheader("Filters")
    target_cal = st.selectbox(
        "Target calories / day",
        options=[1500, 1800, 2000, 2200, 2500],
        index=2,
    )
    max_prep = st.slider("Max prep time (min)", 15, 60, 45, step=5)
    diet_filters = st.multiselect(
        "Dietary requirements",
        options=["vegetarian", "vegan", "gluten-free", "dairy-free"],
    )
    kid_only = st.checkbox("Kid-friendly only", value=False)

# ── Query mart_weekly_plans ───────────────────────────────────
try:
    df: pd.DataFrame = con.execute("""
        SELECT
            day_of_week,
            meal_slot,
            title,
            cuisine,
            prep_minutes,
            calories_per_serving,
            image_url,
            source_url,
            diet_tags,
            kid_friendly
        FROM mart_weekly_plans
        ORDER BY day_of_week, meal_slot
    """).df()
except Exception as e:
    st.error(f"Could not load meal plan: {e}")
    st.info("Run `python etl/run_pipeline.py` to generate a meal plan.")
    st.stop()

if df.empty:
    st.warning("No meal plan found. Run the ETL pipeline to generate one.")
    st.stop()

# Apply filters
if max_prep < 60:
    df = df[df["prep_minutes"] <= max_prep]
if kid_only:
    df = df[df["kid_friendly"]]

# ── Render 3×7 grid ──────────────────────────────────────────
DAY_NAMES = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
MEAL_ORDER = ["breakfast", "lunch", "dinner"]
MEAL_EMOJI = {"breakfast": "🌅", "lunch": "☀️", "dinner": "🌙"}

cols = st.columns(7)
for day_num, col in zip(range(1, 8), cols):
    col.markdown(f"**{DAY_NAMES[day_num]}**")
    for slot in MEAL_ORDER:
        row = df[(df["day_of_week"] == day_num) & (df["meal_slot"] == slot)]
        if row.empty:
            col.caption(f"{MEAL_EMOJI[slot]} *No meal*")
        else:
            r = row.iloc[0]
            cal = int(r["calories_per_serving"]) if pd.notna(r["calories_per_serving"]) else "?"
            prep = int(r["prep_minutes"]) if pd.notna(r["prep_minutes"]) else "?"
            label = r["title"]
            link = r["source_url"] if pd.notna(r["source_url"]) else "#"
            col.markdown(
                f"{MEAL_EMOJI[slot]} [{label}]({link})\n\n"
                f"*{cal} kcal · {prep} min*"
            )

st.divider()
st.caption(f"Showing {len(df)} meal slots · target {target_cal} kcal/day")
