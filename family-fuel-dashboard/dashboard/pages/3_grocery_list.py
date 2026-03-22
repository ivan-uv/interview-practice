"""
Page 3: Grocery List — aggregated shopping list by aisle
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Grocery List | Family Fuel", page_icon="🛒", layout="wide")

from dashboard.app import get_db

con = get_db()

st.title("🛒 Grocery List")
st.caption("Aggregated ingredients for your current weekly meal plan, grouped by aisle.")

# ── Load grocery list ─────────────────────────────────────────
try:
    df: pd.DataFrame = con.execute("""
        SELECT aisle, ingredient, total_quantity, unit
        FROM mart_grocery_list
        ORDER BY aisle, ingredient
    """).df()
except Exception as e:
    st.error(f"Could not load grocery list: {e}")
    st.info("Run `python etl/run_pipeline.py` first.")
    st.stop()

if df.empty:
    st.warning("No grocery data available yet.")
    st.stop()

# ── CSV download ──────────────────────────────────────────────
csv = df.to_csv(index=False)
st.download_button(
    label="⬇ Download as CSV",
    data=csv,
    file_name="grocery_list.csv",
    mime="text/csv",
)

st.divider()

# ── Group by aisle ────────────────────────────────────────────
aisles = sorted(df["aisle"].dropna().unique())

for aisle in aisles:
    with st.expander(f"🏪 {aisle}", expanded=True):
        aisle_df = df[df["aisle"] == aisle][["ingredient", "total_quantity", "unit"]].copy()
        aisle_df["total_quantity"] = aisle_df["total_quantity"].round(2)
        aisle_df.columns = ["Ingredient", "Quantity", "Unit"]

        # Checkboxes for "already have" — stored in session state
        for _, row in aisle_df.iterrows():
            key = f"have_{aisle}_{row['Ingredient']}"
            checked = st.checkbox(
                f"{row['Ingredient']}  —  {row['Quantity']} {row['Unit']}",
                key=key,
            )

st.divider()
st.caption(f"{len(df)} ingredients across {len(aisles)} aisles")
