"""
Family Fuel Dashboard — Streamlit entrypoint.

Run with:
    streamlit run dashboard/app.py
"""
import sys
from pathlib import Path

# Make project root importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import duckdb
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

DB_PATH = str(Path(__file__).parent.parent / "data" / "family_fuel.duckdb")

st.set_page_config(
    page_title="Family Fuel Dashboard",
    page_icon="🥦",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def get_db() -> duckdb.DuckDBPyConnection:
    """Shared, cached DuckDB connection for the dashboard session."""
    return duckdb.connect(DB_PATH, read_only=True)


def _data_freshness(con: duckdb.DuckDBPyConnection) -> str:
    try:
        result = con.execute("""
            SELECT strftime(MAX(run_at), '%Y-%m-%d %H:%M') AS last_run
            FROM raw_pipeline_runs
            WHERE status = 'success'
        """).fetchone()
        return result[0] if result and result[0] else "Never"
    except Exception:
        return "No data yet"


def _recipe_count(con: duckdb.DuckDBPyConnection) -> int:
    try:
        return con.execute("SELECT COUNT(*) FROM dim_recipes").fetchone()[0]
    except Exception:
        return 0


# ── Sidebar ───────────────────────────────────────────────────
con = get_db()

st.sidebar.title("🥦 Family Fuel")
st.sidebar.caption("Weekly meal planning powered by real food data")
st.sidebar.divider()
st.sidebar.metric("Recipes in library", _recipe_count(con))
st.sidebar.caption(f"Last pipeline run: {_data_freshness(con)}")
st.sidebar.divider()
st.sidebar.info(
    "**First time?**\n\n"
    "1. Add your API keys to `.env`\n"
    "2. Run `python etl/run_pipeline.py`\n"
    "3. Refresh this page"
)

# ── Home page ─────────────────────────────────────────────────
st.title("Family Fuel Dashboard")
st.subheader("What are we eating this week?")

st.markdown("""
Answer the dinner question — every day — with actual data instead of decision fatigue.

**Use the sidebar to navigate:**

| Page | What it does |
|------|-------------|
| 🗓 Meal Planner | View & regenerate your weekly meal plan |
| 📊 Nutrition | Daily macro breakdown vs. your targets |
| 🛒 Grocery List | Shopping list grouped by aisle, exportable to CSV |
| 👦 Kid-Friendly | Quick recipes the picky eaters will actually eat |
| 🔍 Data Health | Pipeline status, row counts, last ETL run |
""")

st.divider()

col1, col2, col3 = st.columns(3)

try:
    total_recipes = con.execute("SELECT COUNT(*) FROM dim_recipes").fetchone()[0]
    kid_friendly = con.execute("SELECT COUNT(*) FROM mart_kid_friendly").fetchone()[0]
    total_products = con.execute("SELECT COUNT(*) FROM raw_off_products").fetchone()[0]
    col1.metric("Recipes", total_recipes)
    col2.metric("Kid-Friendly Recipes", kid_friendly)
    col3.metric("Food Products", total_products)
except Exception:
    col1.metric("Recipes", "—")
    col2.metric("Kid-Friendly Recipes", "—")
    col3.metric("Food Products", "—")
    st.warning("Run the ETL pipeline first: `python etl/run_pipeline.py`")
