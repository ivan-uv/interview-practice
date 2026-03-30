# %% [markdown]
# # Pandas & Polars: Complete Walkthrough
# **Dataset: 2014 Boston Marathon Results (~32,000 runners)**
#
# This file walks through everything you need to know about pandas and polars,
# side by side, using real marathon data. Run each cell interactively in VS Code
# (Ctrl+Shift+P → "Run Cell" or Shift+Enter).
#
# ## Setup
# ```
# pip install pandas polars requests
# ```

# %%
# === SETUP & DATA LOADING ===
import pandas as pd
import polars as pl
import requests
from io import StringIO

DATA_URL = "https://raw.githubusercontent.com/llimllib/bostonmarathon/master/results/2014/results.csv"

# Download the data once
print("Downloading 2014 Boston Marathon data...")
response = requests.get(DATA_URL)
csv_text = response.text
print(f"Downloaded {len(csv_text)} bytes")

# %% [markdown]
# ---
# # 1. Reading Data
# Pandas and polars both read CSVs easily, but the APIs differ slightly.

# %%
# === PANDAS: Read CSV ===
pdf = pd.read_csv(StringIO(csv_text))
print(f"pandas DataFrame: {pdf.shape[0]} rows × {pdf.shape[1]} columns")
print(f"Type: {type(pdf)}")
pdf.head()

# %%
# === POLARS: Read CSV ===
plf = pl.read_csv(StringIO(csv_text))
print(f"polars DataFrame: {plf.shape[0]} rows × {plf.shape[1]} columns")
print(f"Type: {type(plf)}")
plf.head()

# %% [markdown]
# ---
# # 2. Core Data Structures
#
# | Concept | Pandas | Polars |
# |---------|--------|--------|
# | 1D data | `pd.Series` | `pl.Series` |
# | 2D data | `pd.DataFrame` | `pl.DataFrame` |
# | Lazy eval | No native (use method chaining) | `pl.LazyFrame` |
# | Index | Yes (row labels) | **No index** — polars is index-free |

# %%
# === PANDAS: Series ===
ages_pd = pdf["age"]
print(f"Type: {type(ages_pd)}")
print(f"dtype: {ages_pd.dtype}")
print(f"Index: {ages_pd.index[:5].tolist()}")  # pandas Series have an index
ages_pd.head()

# %%
# === POLARS: Series ===
ages_pl = plf["age"]
print(f"Type: {type(ages_pl)}")
print(f"dtype: {ages_pl.dtype}")
# No index in polars! Rows are accessed by position only.
ages_pl.head()

# %% [markdown]
# ---
# # 3. Inspecting Data
# First things to do with any new dataset.

# %%
# === PANDAS: Inspect ===
print("--- dtypes ---")
print(pdf.dtypes)
print("\n--- info ---")
pdf.info()
print("\n--- describe ---")
pdf.describe()

# %%
# === POLARS: Inspect ===
print("--- dtypes ---")
print(plf.dtypes)
print("\n--- schema ---")
print(plf.schema)
print("\n--- describe ---")
plf.describe()

# %% [markdown]
# ---
# # 4. Selecting Columns
#
# **Key difference**: Polars uses `select()` with expressions, not bracket indexing
# for multiple columns.

# %%
# === PANDAS: Select columns ===
# Single column → Series
print(type(pdf["name"]))

# Multiple columns → DataFrame
subset_pd = pdf[["name", "age", "gender", "official"]]
subset_pd.head()

# %%
# === POLARS: Select columns ===
# Single column → Series
print(type(plf["name"]))

# Multiple columns → DataFrame (use select)
subset_pl = plf.select(["name", "age", "gender", "official"])
# Or with expressions:
subset_pl2 = plf.select(pl.col("name"), pl.col("age"), pl.col("gender"), pl.col("official"))
subset_pl.head()

# %% [markdown]
# ---
# # 5. Filtering Rows
#
# **Key difference**: Polars uses `filter()` with expressions.
# Pandas uses boolean indexing.

# %%
# === PANDAS: Filter ===
# Runners under 25
young_pd = pdf[pdf["age"] < 25]
print(f"Runners under 25: {len(young_pd)}")

# Multiple conditions (use & for AND, | for OR, wrap each in parentheses)
young_fast_pd = pdf[(pdf["age"] < 25) & (pdf["official"] < 180)]
print(f"Under 25 AND sub-3-hour: {len(young_fast_pd)}")

# String filtering
kenya_pd = pdf[pdf["country"] == "KEN"]
print(f"Kenyan runners: {len(kenya_pd)}")

# %%
# === POLARS: Filter ===
# Runners under 25
young_pl = plf.filter(pl.col("age") < 25)
print(f"Runners under 25: {len(young_pl)}")

# Multiple conditions
young_fast_pl = plf.filter((pl.col("age") < 25) & (pl.col("official") < 180))
print(f"Under 25 AND sub-3-hour: {len(young_fast_pl)}")

# String filtering
kenya_pl = plf.filter(pl.col("country") == "KEN")
print(f"Kenyan runners: {len(kenya_pl)}")

# %% [markdown]
# ---
# # 6. Adding / Modifying Columns
#
# **Key difference**: Polars uses `with_columns()`. Pandas assigns directly.

# %%
# === PANDAS: Add columns ===
# Pace in km (data has pace in min/mile)
pdf["pace_km"] = pdf["pace"] * 0.621371

# Compute second-half time (official minus half split)
pdf["second_half"] = pdf["official"] - pdf["half"]

# Negative split flag (second half faster than first)
pdf["negative_split"] = pdf["second_half"] < pdf["half"]

pdf[["name", "half", "second_half", "negative_split"]].head(10)

# %%
# === POLARS: Add columns ===
plf = plf.with_columns(
    # Pace in km
    (pl.col("pace") * 0.621371).alias("pace_km"),

    # Second-half time
    (pl.col("official") - pl.col("half")).alias("second_half"),
)

# Can chain another with_columns (or do it all in one)
plf = plf.with_columns(
    (pl.col("second_half") < pl.col("half")).alias("negative_split"),
)

plf.select("name", "half", "second_half", "negative_split").head(10)

# %% [markdown]
# ---
# # 7. Sorting
#
# Both libraries use `sort_values` (pandas) or `sort` (polars).

# %%
# === PANDAS: Sort ===
# Fastest finishers
fastest_pd = pdf.sort_values("official").head(10)
fastest_pd[["name", "gender", "age", "country", "official"]]

# %%
# === POLARS: Sort ===
fastest_pl = plf.sort("official").head(10)
fastest_pl.select("name", "gender", "age", "country", "official")

# %%
# Sort by multiple columns
# Pandas
pdf.sort_values(["gender", "official"], ascending=[True, True]).head(5)

# %%
# Polars
plf.sort(["gender", "official"]).head(5)

# %% [markdown]
# ---
# # 8. GroupBy & Aggregation
#
# **Key difference**: Polars groupby returns results via `agg()` with expressions.
# Pandas uses a different API with `.agg()` or direct methods.

# %%
# === PANDAS: GroupBy ===
# Average finish time by gender
print(pdf.groupby("gender")["official"].mean())
print()

# Multiple aggregations
gender_stats_pd = pdf.groupby("gender")["official"].agg(["count", "mean", "median", "min", "max"])
print(gender_stats_pd)

# %%
# === POLARS: GroupBy ===
# Average finish time by gender
print(plf.group_by("gender").agg(pl.col("official").mean()))
print()

# Multiple aggregations
gender_stats_pl = plf.group_by("gender").agg(
    pl.col("official").count().alias("count"),
    pl.col("official").mean().alias("mean"),
    pl.col("official").median().alias("median"),
    pl.col("official").min().alias("min"),
    pl.col("official").max().alias("max"),
)
print(gender_stats_pl)

# %%
# === PANDAS: GroupBy with multiple columns ===
country_gender_pd = pdf.groupby(["country", "gender"])["official"].agg(["count", "mean"]).reset_index()
country_gender_pd = country_gender_pd.sort_values("count", ascending=False).head(10)
country_gender_pd

# %%
# === POLARS: GroupBy with multiple columns ===
country_gender_pl = (
    plf.group_by(["country", "gender"])
    .agg(
        pl.col("official").count().alias("count"),
        pl.col("official").mean().alias("mean"),
    )
    .sort("count", descending=True)
    .head(10)
)
country_gender_pl

# %% [markdown]
# ---
# # 9. Aggregation Functions Reference
#
# | Operation | Pandas | Polars |
# |-----------|--------|--------|
# | Count | `.count()` | `.count()` |
# | Sum | `.sum()` | `.sum()` |
# | Mean | `.mean()` | `.mean()` |
# | Median | `.median()` | `.median()` |
# | Min / Max | `.min()` / `.max()` | `.min()` / `.max()` |
# | Std dev | `.std()` | `.std()` |
# | Quantile | `.quantile(0.75)` | `.quantile(0.75)` |
# | Nunique | `.nunique()` | `.n_unique()` |
# | First / Last | `.first()` / `.last()` | `.first()` / `.last()` |

# %%
# Quick aggregation examples
# Pandas
print("=== Pandas ===")
print(f"Total runners: {pdf['name'].count()}")
print(f"Avg age: {pdf['age'].mean():.1f}")
print(f"Fastest time: {pdf['official'].min():.2f} min")
print(f"Countries represented: {pdf['country'].nunique()}")

# %%
# Polars
print("=== Polars ===")
print(f"Total runners: {plf['name'].count()}")
print(f"Avg age: {plf['age'].mean():.1f}")
print(f"Fastest time: {plf['official'].min():.2f} min")
print(f"Countries represented: {plf['country'].n_unique()}")

# %% [markdown]
# ---
# # 10. String Operations
#
# Pandas: `df["col"].str.method()`
# Polars: `pl.col("col").str.method()`

# %%
# === PANDAS: String ops ===
# Uppercase names
pdf["name_upper"] = pdf["name"].str.upper()

# Extract last name (before the comma)
pdf["last_name"] = pdf["name"].str.split(",").str[0].str.strip()

# Check if city contains "Boston"
boston_locals_pd = pdf[pdf["city"].str.contains("Boston", na=False)]
print(f"Runners from cities with 'Boston': {len(boston_locals_pd)}")

pdf[["name", "name_upper", "last_name"]].head()

# %%
# === POLARS: String ops ===
plf = plf.with_columns(
    # Uppercase names
    pl.col("name").str.to_uppercase().alias("name_upper"),

    # Extract last name (before the comma)
    pl.col("name").str.split(",").list.first().str.strip_chars().alias("last_name"),
)

# Check if city contains "Boston"
boston_locals_pl = plf.filter(pl.col("city").str.contains("Boston"))
print(f"Runners from cities with 'Boston': {len(boston_locals_pl)}")

plf.select("name", "name_upper", "last_name").head()

# %% [markdown]
# ---
# # 11. Missing / Null Data
#
# The marathon dataset has some null values (e.g., runners who dropped out
# won't have all split times, some states are missing).

# %%
# === PANDAS: Missing data ===
print("--- Null counts ---")
print(pdf.isnull().sum())
print(f"\nTotal nulls: {pdf.isnull().sum().sum()}")

# %%
# Drop rows with any null in specific columns
clean_pd = pdf.dropna(subset=["official", "half"])
print(f"Before: {len(pdf)}, After dropping nulls: {len(clean_pd)}")

# Fill nulls
filled_pd = pdf["state"].fillna("Unknown")
print(f"Nulls in state before fill: {pdf['state'].isnull().sum()}")
print(f"Nulls in state after fill: {filled_pd.isnull().sum()}")

# %%
# === POLARS: Missing data ===
print("--- Null counts ---")
print(plf.null_count())

# %%
# Drop rows with null in specific columns
clean_pl = plf.drop_nulls(subset=["official", "half"])
print(f"Before: {len(plf)}, After dropping nulls: {len(clean_pl)}")

# Fill nulls
filled_pl = plf.with_columns(
    pl.col("state").fill_null("Unknown").alias("state_filled"),
)
print(f"Nulls in state before: {plf['state'].null_count()}")
print(f"Nulls in state_filled after: {filled_pl['state_filled'].null_count()}")

# %% [markdown]
# ---
# # 12. Joins / Merges
#
# Let's create a secondary DataFrame to demonstrate joins.

# %%
# Create a country info table
country_data = {
    "country": ["USA", "KEN", "ETH", "JPN", "GBR", "CAN", "MEX", "GER", "FRA", "BRA"],
    "country_name": [
        "United States", "Kenya", "Ethiopia", "Japan", "Great Britain",
        "Canada", "Mexico", "Germany", "France", "Brazil"
    ],
    "continent": [
        "North America", "Africa", "Africa", "Asia", "Europe",
        "North America", "North America", "Europe", "Europe", "South America"
    ],
}

# %%
# === PANDAS: Merge ===
country_pd = pd.DataFrame(country_data)

# Left join (keep all runners, add country info where available)
merged_pd = pdf.merge(country_pd, on="country", how="left")
print(f"Rows after merge: {len(merged_pd)}")
merged_pd[["name", "country", "country_name", "continent"]].head(10)

# %%
# === POLARS: Join ===
country_pl = pl.DataFrame(country_data)

# Left join
merged_pl = plf.join(country_pl, on="country", how="left")
print(f"Rows after join: {len(merged_pl)}")
merged_pl.select("name", "country", "country_name", "continent").head(10)

# %% [markdown]
# ### Join Types Reference
#
# | Type | Pandas `how=` | Polars `how=` | Keeps |
# |------|--------------|--------------|-------|
# | Inner | `"inner"` | `"inner"` | Only matching rows |
# | Left | `"left"` | `"left"` | All left + matching right |
# | Right | `"right"` | `"right"` | All right + matching left |
# | Outer | `"outer"` | `"full"` | All rows from both |
# | Cross | `"cross"` | `"cross"` | Cartesian product |

# %% [markdown]
# ---
# # 13. Window Functions
#
# Window functions compute values across a group but return a value
# for every row (unlike groupby which collapses rows).

# %%
# === PANDAS: Window functions ===
# Rank within gender
pdf["gender_rank"] = pdf.groupby("gender")["official"].rank(method="min")

# Running average (rolling) of finish time by overall position
pdf_sorted = pdf.sort_values("overall")
pdf_sorted["rolling_avg_10"] = pdf_sorted["official"].rolling(window=10).mean()

pdf_sorted[["name", "gender", "official", "gender_rank", "rolling_avg_10"]].head(15)

# %%
# === POLARS: Window functions ===
# Rank within gender using over()
plf = plf.with_columns(
    pl.col("official").rank(method="min").over("gender").alias("gender_rank"),
)

# Rolling average (sort first, then use rolling)
plf_sorted = plf.sort("overall")
plf_sorted = plf_sorted.with_columns(
    pl.col("official").rolling_mean(window_size=10).alias("rolling_avg_10"),
)

plf_sorted.select("name", "gender", "official", "gender_rank", "rolling_avg_10").head(15)

# %% [markdown]
# ### `over()` — Polars' Killer Feature
#
# In polars, `over()` applies an expression within groups without collapsing rows.
# It's like a SQL window function. Pandas equivalent requires `groupby().transform()`.

# %%
# === PANDAS: groupby transform ===
pdf["avg_time_by_gender"] = pdf.groupby("gender")["official"].transform("mean")
pdf["time_vs_gender_avg"] = pdf["official"] - pdf["avg_time_by_gender"]
pdf[["name", "gender", "official", "avg_time_by_gender", "time_vs_gender_avg"]].head()

# %%
# === POLARS: over() ===
plf = plf.with_columns(
    pl.col("official").mean().over("gender").alias("avg_time_by_gender"),
    (pl.col("official") - pl.col("official").mean().over("gender")).alias("time_vs_gender_avg"),
)
plf.select("name", "gender", "official", "avg_time_by_gender", "time_vs_gender_avg").head()

# %% [markdown]
# ---
# # 14. Lazy Evaluation (Polars Only)
#
# Polars' **LazyFrame** builds a query plan and optimizes it before execution.
# This is one of polars' biggest advantages — it can reorder operations,
# push down filters, and eliminate unnecessary columns automatically.

# %%
# === POLARS: Lazy evaluation ===
# Convert to LazyFrame
lazy = plf.lazy()
print(f"Type: {type(lazy)}")

# Build a query (nothing executes yet!)
query = (
    lazy
    .filter(pl.col("gender") == "F")
    .filter(pl.col("age") < 30)
    .select("name", "age", "country", "official", "pace")
    .sort("official")
    .head(20)
)

# See the optimized query plan
print("\n--- Query Plan ---")
print(query.explain())

# %%
# Execute with .collect()
result = query.collect()
print(f"Result: {result.shape[0]} rows × {result.shape[1]} columns")
result

# %% [markdown]
# ### Why Lazy Matters
# - **Predicate pushdown**: filters are pushed as early as possible
# - **Projection pushdown**: only needed columns are read
# - **Query optimization**: operations are reordered for efficiency
# - **Parallel execution**: polars automatically parallelizes operations
#
# For large datasets, lazy evaluation can be **dramatically** faster than eager.
# Pandas has no equivalent — every operation executes immediately.

# %% [markdown]
# ---
# # 15. Method Chaining
#
# Both libraries support chaining, but polars is designed around it.

# %%
# === PANDAS: Method chaining ===
result_pd = (
    pdf
    .query("gender == 'M' and age >= 40 and age < 50")
    .groupby("country")["official"]
    .agg(["count", "mean"])
    .reset_index()
    .rename(columns={"count": "num_runners", "mean": "avg_time"})
    .query("num_runners >= 10")
    .sort_values("avg_time")
    .head(10)
)
result_pd

# %%
# === POLARS: Method chaining ===
result_pl = (
    plf
    .filter(
        (pl.col("gender") == "M")
        & (pl.col("age") >= 40)
        & (pl.col("age") < 50)
    )
    .group_by("country")
    .agg(
        pl.col("official").count().alias("num_runners"),
        pl.col("official").mean().alias("avg_time"),
    )
    .filter(pl.col("num_runners") >= 10)
    .sort("avg_time")
    .head(10)
)
result_pl

# %% [markdown]
# ---
# # 16. Reshaping Data (Pivot / Melt)

# %%
# === PANDAS: Pivot ===
# Average finish time by country and gender (top 5 countries)
top_countries = pdf["country"].value_counts().head(5).index.tolist()
pivot_pd = (
    pdf[pdf["country"].isin(top_countries)]
    .pivot_table(values="official", index="country", columns="gender", aggfunc="mean")
    .round(2)
)
pivot_pd

# %%
# === POLARS: Pivot ===
top_countries_pl = (
    plf["country"]
    .value_counts()
    .sort("count", descending=True)
    .head(5)["country"]
    .to_list()
)

pivot_pl = (
    plf
    .filter(pl.col("country").is_in(top_countries_pl))
    .pivot(on="gender", index="country", values="official", aggregate_function="mean")
)
pivot_pl

# %%
# === PANDAS: Melt (unpivot) ===
# Melt split times into long format
split_cols = ["5k", "10k", "half", "20k", "25k", "30k", "35k", "40k"]
melted_pd = pdf[["name"] + split_cols].head(5).melt(
    id_vars=["name"],
    value_vars=split_cols,
    var_name="checkpoint",
    value_name="time_minutes",
)
melted_pd.head(15)

# %%
# === POLARS: Unpivot (melt) ===
split_cols_pl = ["5k", "10k", "half", "20k", "25k", "30k", "35k", "40k"]
melted_pl = (
    plf
    .select(["name"] + split_cols_pl)
    .head(5)
    .unpivot(
        on=split_cols_pl,
        index="name",
        variable_name="checkpoint",
        value_name="time_minutes",
    )
)
melted_pl.head(15)

# %% [markdown]
# ---
# # 17. Applying Custom Functions
#
# **Key difference**: Polars discourages row-wise apply (it's slow).
# Use expressions instead. Pandas `.apply()` is convenient but slow.

# %%
# === PANDAS: Apply ===
# Categorize finish time
def pace_category(minutes):
    if pd.isna(minutes):
        return "DNF"
    elif minutes < 180:
        return "Elite (<3h)"
    elif minutes < 240:
        return "Fast (3-4h)"
    elif minutes < 300:
        return "Average (4-5h)"
    else:
        return "Recreational (5h+)"

pdf["pace_cat"] = pdf["official"].apply(pace_category)
print(pdf["pace_cat"].value_counts())

# %%
# === POLARS: Use when/then/otherwise (preferred over apply!) ===
plf = plf.with_columns(
    pl.when(pl.col("official").is_null())
    .then(pl.lit("DNF"))
    .when(pl.col("official") < 180)
    .then(pl.lit("Elite (<3h)"))
    .when(pl.col("official") < 240)
    .then(pl.lit("Fast (3-4h)"))
    .when(pl.col("official") < 300)
    .then(pl.lit("Average (4-5h)"))
    .otherwise(pl.lit("Recreational (5h+)"))
    .alias("pace_cat")
)
print(plf["pace_cat"].value_counts().sort("pace_cat"))

# %% [markdown]
# ### Performance Note
# Polars `when/then/otherwise` runs as a vectorized operation (fast!).
# Pandas `apply()` runs Python for each row (slow!).
# Always prefer expressions over apply in both libraries when possible.

# %% [markdown]
# ---
# # 18. Concatenation
#
# Stacking DataFrames vertically or horizontally.

# %%
# Split data and recombine
# === PANDAS ===
males_pd = pdf[pdf["gender"] == "M"]
females_pd = pdf[pdf["gender"] == "F"]
combined_pd = pd.concat([males_pd, females_pd], ignore_index=True)
print(f"Pandas concat: {len(males_pd)} + {len(females_pd)} = {len(combined_pd)}")

# %%
# === POLARS ===
males_pl = plf.filter(pl.col("gender") == "M")
females_pl = plf.filter(pl.col("gender") == "F")
combined_pl = pl.concat([males_pl, females_pl])
print(f"Polars concat: {len(males_pl)} + {len(females_pl)} = {len(combined_pl)}")

# %% [markdown]
# ---
# # 19. Writing Data
#
# Both support CSV, Parquet, JSON, and more.

# %%
# === PANDAS: Write ===
# pdf.to_csv("output.csv", index=False)
# pdf.to_parquet("output.parquet", index=False)
# pdf.to_json("output.json", orient="records")
print("Pandas write methods: .to_csv(), .to_parquet(), .to_json(), .to_excel()")

# %%
# === POLARS: Write ===
# plf.write_csv("output.csv")
# plf.write_parquet("output.parquet")
# plf.write_json("output.json")
print("Polars write methods: .write_csv(), .write_parquet(), .write_json()")

# %% [markdown]
# ---
# # 20. Performance Comparison
#
# Polars is typically **5-20x faster** than pandas for common operations,
# especially on larger datasets. Key reasons:
#
# 1. **Written in Rust** — no Python GIL overhead for core operations
# 2. **Columnar memory layout** — cache-friendly, like Apache Arrow
# 3. **Lazy evaluation** — query optimizer eliminates wasted work
# 4. **Automatic parallelism** — uses all CPU cores by default
# 5. **No index overhead** — simpler data model = faster operations
#
# When to use each:
# - **Pandas**: huge ecosystem, more tutorials, better for quick exploration,
#   many libraries expect pandas DataFrames
# - **Polars**: better performance, cleaner API, better for production pipelines,
#   large datasets that don't fit well in pandas

# %%
# === Quick timing comparison ===
import time

# Pandas groupby
start = time.time()
for _ in range(100):
    pdf.groupby(["gender", "country"])["official"].mean()
pd_time = time.time() - start

# Polars groupby
start = time.time()
for _ in range(100):
    plf.group_by(["gender", "country"]).agg(pl.col("official").mean())
pl_time = time.time() - start

print(f"Pandas  100x groupby: {pd_time:.3f}s")
print(f"Polars  100x groupby: {pl_time:.3f}s")
print(f"Polars is {pd_time / pl_time:.1f}x faster")

# %% [markdown]
# ---
# # 21. Quick Reference: Pandas ↔ Polars Translation
#
# | Operation | Pandas | Polars |
# |-----------|--------|--------|
# | Read CSV | `pd.read_csv(f)` | `pl.read_csv(f)` |
# | Select cols | `df[["a","b"]]` | `df.select("a","b")` |
# | Filter rows | `df[df["a"]>5]` | `df.filter(pl.col("a")>5)` |
# | Add column | `df["new"]=expr` | `df.with_columns(expr.alias("new"))` |
# | Sort | `df.sort_values("a")` | `df.sort("a")` |
# | GroupBy | `df.groupby("a")["b"].mean()` | `df.group_by("a").agg(pl.col("b").mean())` |
# | Join | `df.merge(df2,on="a")` | `df.join(df2,on="a")` |
# | Null check | `df.isnull()` | `df.null_count()` |
# | Fill null | `df.fillna(val)` | `df.fill_null(val)` |
# | Drop null | `df.dropna()` | `df.drop_nulls()` |
# | Unique vals | `df["a"].nunique()` | `df["a"].n_unique()` |
# | Value counts | `df["a"].value_counts()` | `df["a"].value_counts()` |
# | Rename cols | `df.rename(columns={"a":"b"})` | `df.rename({"a":"b"})` |
# | Drop cols | `df.drop(columns=["a"])` | `df.drop("a")` |
# | Shape | `df.shape` | `df.shape` |
# | Head | `df.head(n)` | `df.head(n)` |
# | Lazy mode | N/A | `df.lazy()` → `.collect()` |
# | Window fn | `df.groupby("a")["b"].transform("mean")` | `pl.col("b").mean().over("a")` |

# %% [markdown]
# ---
# # Done!
#
# You now know the core of both pandas and polars.
# Head to `practice_questions.py` to test yourself!
