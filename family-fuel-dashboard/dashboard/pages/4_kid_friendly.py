"""
Page 4: Kid-Friendly Finder — quick recipes the picky eaters will eat
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Kid-Friendly | Family Fuel", page_icon="👦", layout="wide")

from dashboard.app import get_db

con = get_db()

st.title("👦 Kid-Friendly Recipes")
st.caption("Pre-filtered: ≤30 min prep, high ratings, no hard-to-sell ingredients.")

# ── Sidebar filters ───────────────────────────────────────────
with st.sidebar:
    st.subheader("Allergen Exclusions")
    exclude_dairy = st.checkbox("Exclude dairy")
    exclude_nuts = st.checkbox("Exclude nuts")
    exclude_eggs = st.checkbox("Exclude eggs")
    exclude_gluten = st.checkbox("Exclude gluten")

    st.subheader("Nutrition")
    max_cal = st.slider("Max calories per serving", 200, 900, 700, step=50)

# ── Load kid-friendly mart ────────────────────────────────────
try:
    df: pd.DataFrame = con.execute("""
        SELECT
            recipe_id,
            title,
            cuisine,
            prep_minutes,
            calories_per_serving,
            protein_g,
            fat_g,
            carbs_g,
            allergens,
            diet_tags,
            image_url,
            source_url
        FROM mart_kid_friendly
        ORDER BY prep_minutes
    """).df()
except Exception as e:
    st.error(f"Could not load kid-friendly recipes: {e}")
    st.info("Run `python etl/run_pipeline.py` first.")
    st.stop()

if df.empty:
    st.warning("No kid-friendly recipes in the library yet. Run the ETL pipeline.")
    st.stop()

# Apply allergen filters
if exclude_dairy:
    df = df[~df["allergens"].apply(lambda a: "dairy" in str(a).lower())]
if exclude_nuts:
    df = df[~df["allergens"].apply(lambda a: "nuts" in str(a).lower())]
if exclude_eggs:
    df = df[~df["allergens"].apply(lambda a: "eggs" in str(a).lower())]
if exclude_gluten:
    df = df[~df["allergens"].apply(lambda a: "gluten" in str(a).lower())]

df = df[df["calories_per_serving"] <= max_cal]

st.caption(f"{len(df)} recipes match your filters")
st.divider()

# ── Card layout (3 per row) ───────────────────────────────────
for i in range(0, len(df), 3):
    cols = st.columns(3)
    for j, col in enumerate(cols):
        if i + j >= len(df):
            break
        row = df.iloc[i + j]
        with col:
            if pd.notna(row["image_url"]) and row["image_url"]:
                st.image(row["image_url"], use_container_width=True)
            st.markdown(f"**[{row['title']}]({row['source_url'] or '#'})**")
            st.caption(
                f"🕐 {int(row['prep_minutes'] or 0)} min  "
                f"· 🔥 {int(row['calories_per_serving'] or 0)} kcal  "
                f"· 💪 {row['protein_g']:.0f}g protein"
            )
            if row["cuisine"]:
                st.caption(f"🌍 {row['cuisine']}")
            st.markdown("---")
