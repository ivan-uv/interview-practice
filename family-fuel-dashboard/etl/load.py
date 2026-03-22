"""
DuckDB connection management and table initialization.
"""
import os
import duckdb
from pathlib import Path

DB_PATH = os.getenv("DUCKDB_PATH", str(Path(__file__).parent.parent / "data" / "family_fuel.duckdb"))
SQL_DIR = Path(__file__).parent.parent / "sql"


def get_connection() -> duckdb.DuckDBPyConnection:
    """Return a connection to the local DuckDB file, creating it if needed."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(DB_PATH)


def initialize_schema(con: duckdb.DuckDBPyConnection) -> None:
    """Create all tables if they don't exist and refresh mart views."""
    ddl = (SQL_DIR / "create_tables.sql").read_text()
    con.executescript(ddl)
    marts = (SQL_DIR / "create_marts.sql").read_text()
    con.executescript(marts)


# ─────────────────────────────────────────────
# Raw table upserts
# ─────────────────────────────────────────────

def upsert_raw_recipes(con: duckdb.DuckDBPyConnection, records: list[dict]) -> int:
    """Insert or replace raw recipe JSON blobs. Returns row count inserted."""
    if not records:
        return 0
    import pandas as pd, json
    df = pd.DataFrame([
        {
            "recipe_id": r["id"],
            "title": r.get("title", ""),
            "raw_json": json.dumps(r),
        }
        for r in records
    ])
    con.execute("""
        INSERT OR REPLACE INTO raw_recipes (recipe_id, title, raw_json, fetched_at)
        SELECT recipe_id, title, raw_json::JSON, current_timestamp
        FROM df
    """)
    return len(df)


def upsert_raw_usda(con: duckdb.DuckDBPyConnection, records: list[dict]) -> int:
    """Insert or replace raw USDA nutrient JSON blobs."""
    if not records:
        return 0
    import pandas as pd, json
    df = pd.DataFrame([
        {
            "fdc_id": r["fdcId"],
            "description": r.get("description", ""),
            "raw_json": json.dumps(r),
        }
        for r in records
    ])
    con.execute("""
        INSERT OR REPLACE INTO raw_usda_nutrients (fdc_id, description, raw_json, fetched_at)
        SELECT fdc_id, description, raw_json::JSON, current_timestamp
        FROM df
    """)
    return len(df)


def upsert_raw_off_products(con: duckdb.DuckDBPyConnection, records: list[dict]) -> int:
    """Insert or replace raw Open Food Facts JSON blobs."""
    if not records:
        return 0
    import pandas as pd, json
    rows = []
    for r in records:
        barcode = r.get("code") or r.get("_id", "")
        if not barcode:
            continue
        rows.append({
            "barcode": str(barcode),
            "product_name": r.get("product_name", ""),
            "raw_json": json.dumps(r),
        })
    if not rows:
        return 0
    df = pd.DataFrame(rows)
    con.execute("""
        INSERT OR REPLACE INTO raw_off_products (barcode, product_name, raw_json, fetched_at)
        SELECT barcode, product_name, raw_json::JSON, current_timestamp
        FROM df
    """)
    return len(df)


def log_pipeline_run(
    con: duckdb.DuckDBPyConnection,
    source: str,
    status: str,
    rows_loaded: int = 0,
    error_message: str | None = None,
) -> None:
    """Write an audit row to raw_pipeline_runs."""
    import uuid
    run_id = str(uuid.uuid4())
    con.execute("""
        INSERT INTO raw_pipeline_runs (run_id, source, status, rows_loaded, error_message)
        VALUES (?, ?, ?, ?, ?)
    """, [run_id, source, status, rows_loaded, error_message])


# ─────────────────────────────────────────────
# Staging table helpers (used by transform.py)
# ─────────────────────────────────────────────

def create_staging_tables(con: duckdb.DuckDBPyConnection) -> None:
    """Create temporary staging tables for the transform step."""
    con.execute("""
        CREATE OR REPLACE TEMP TABLE staging_ingredients (
            ingredient_id   INTEGER,
            name            VARCHAR,
            aisle           VARCHAR
        )
    """)
    con.execute("""
        CREATE OR REPLACE TEMP TABLE staging_nutrition (
            recipe_id           INTEGER,
            nutrient_name       VARCHAR,
            amount_per_serving  DOUBLE
        )
    """)
    con.execute("""
        CREATE OR REPLACE TEMP TABLE staging_recipe_ingredients (
            recipe_id       INTEGER,
            ingredient_id   INTEGER,
            quantity        DOUBLE,
            unit            VARCHAR
        )
    """)
    con.execute("""
        CREATE OR REPLACE TEMP TABLE staging_meal_plans (
            plan_id         VARCHAR,
            date_generated  DATE,
            day_of_week     INTEGER,
            meal_slot       VARCHAR,
            recipe_id       INTEGER,
            target_calories INTEGER
        )
    """)


def load_staging_ingredients(con: duckdb.DuckDBPyConnection, df) -> None:
    con.execute("INSERT INTO staging_ingredients SELECT * FROM df")


def load_staging_nutrition(con: duckdb.DuckDBPyConnection, df) -> None:
    con.execute("INSERT INTO staging_nutrition SELECT * FROM df")


def load_staging_recipe_ingredients(con: duckdb.DuckDBPyConnection, df) -> None:
    con.execute("INSERT INTO staging_recipe_ingredients SELECT * FROM df")


def load_staging_meal_plans(con: duckdb.DuckDBPyConnection, df) -> None:
    con.execute("INSERT INTO staging_meal_plans SELECT * FROM df")


def run_sql_transforms(con: duckdb.DuckDBPyConnection) -> None:
    """Execute dim, fact, and mart SQL files in order."""
    for fname in ["transform_dims.sql", "transform_facts.sql", "create_marts.sql"]:
        sql = (SQL_DIR / fname).read_text()
        con.executescript(sql)
