# %% [markdown]
# # Solutions — Pandas & Polars Practice
# **Dataset: 2014 Boston Marathon Results**
#
# Each question has solutions in both pandas and polars.

# %%
# === SETUP ===
import pandas as pd
import polars as pl
import requests
from io import StringIO

DATA_URL = "https://raw.githubusercontent.com/llimllib/bostonmarathon/master/results/2014/results.csv"

print("Downloading 2014 Boston Marathon data...")
response = requests.get(DATA_URL)
csv_text = response.text

pdf = pd.read_csv(StringIO(csv_text))
plf = pl.read_csv(StringIO(csv_text))
print(f"Loaded {len(pdf)} rows")

# %% [markdown]
# ---
# # Section 1: Selection & Filtering
# ---

# %% [markdown]
# ### Q1 🟢 — Select just the name, age, and gender columns.

# %%
# PANDAS:
q1_pd = pdf[["name", "age", "gender"]]
q1_pd.head()

# %%
# POLARS:
q1_pl = plf.select("name", "age", "gender")
q1_pl.head()

# %% [markdown]
# ### Q2 🟢 — How many runners are from the USA?

# %%
# PANDAS:
q2_pd = len(pdf[pdf["country"] == "USA"])
print(f"USA runners (pandas): {q2_pd}")

# %%
# POLARS:
q2_pl = plf.filter(pl.col("country") == "USA").height
print(f"USA runners (polars): {q2_pl}")

# %% [markdown]
# ### Q3 🟢 — Find all runners aged 60 or older. How many?

# %%
# PANDAS:
q3_pd = pdf[pdf["age"] >= 60]
print(f"Runners 60+: {len(q3_pd)}")
q3_pd[["name", "age", "official"]].head()

# %%
# POLARS:
q3_pl = plf.filter(pl.col("age") >= 60)
print(f"Runners 60+: {q3_pl.height}")
q3_pl.select("name", "age", "official").head()

# %% [markdown]
# ### Q4 🟡 — Female runners from Kenya who finished under 3 hours.

# %%
# PANDAS:
q4_pd = pdf[(pdf["gender"] == "F") & (pdf["country"] == "KEN") & (pdf["official"] < 180)]
print(f"Count: {len(q4_pd)}")
q4_pd[["name", "age", "official"]]

# %%
# POLARS:
q4_pl = plf.filter(
    (pl.col("gender") == "F")
    & (pl.col("country") == "KEN")
    & (pl.col("official") < 180)
)
print(f"Count: {q4_pl.height}")
q4_pl.select("name", "age", "official")

# %% [markdown]
# ### Q5 🟡 — Runners whose name contains "Smith".

# %%
# PANDAS:
q5_pd = pdf[pdf["name"].str.contains("Smith", na=False)]
print(f"Smiths (pandas): {len(q5_pd)}")

# %%
# POLARS:
q5_pl = plf.filter(pl.col("name").str.contains("Smith"))
print(f"Smiths (polars): {q5_pl.height}")

# %% [markdown]
# ---
# # Section 2: Sorting & Ranking
# ---

# %% [markdown]
# ### Q6 🟢 — Top 5 fastest finishers.

# %%
# PANDAS:
q6_pd = pdf.sort_values("official").head(5)[["name", "country", "official"]]
q6_pd

# %%
# POLARS:
q6_pl = plf.sort("official").head(5).select("name", "country", "official")
q6_pl

# %% [markdown]
# ### Q7 🟡 — Fastest runner aged 70+.

# %%
# PANDAS:
q7_pd = (
    pdf[pdf["age"] >= 70]
    .sort_values("official")
    .head(1)[["name", "age", "country", "official"]]
)
q7_pd

# %%
# POLARS:
q7_pl = (
    plf.filter(pl.col("age") >= 70)
    .sort("official")
    .head(1)
    .select("name", "age", "country", "official")
)
q7_pl

# %% [markdown]
# ### Q8 🟡 — Rank runners within their gender by finish time.

# %%
# PANDAS:
pdf["gender_rank"] = pdf.groupby("gender")["official"].rank(method="min")
pdf[["name", "gender", "official", "gender_rank"]].sort_values("gender_rank").head(10)

# %%
# POLARS:
plf = plf.with_columns(
    pl.col("official").rank(method="min").over("gender").alias("gender_rank")
)
plf.select("name", "gender", "official", "gender_rank").sort("gender_rank").head(10)

# %% [markdown]
# ---
# # Section 3: GroupBy & Aggregation
# ---

# %% [markdown]
# ### Q9 🟢 — Average finish time by gender.

# %%
# PANDAS:
print(pdf.groupby("gender")["official"].mean())

# %%
# POLARS:
print(plf.group_by("gender").agg(pl.col("official").mean()))

# %% [markdown]
# ### Q10 🟡 — Country with fastest average time (min 20 runners).

# %%
# PANDAS:
q10_pd = (
    pdf.groupby("country")["official"]
    .agg(["count", "mean"])
    .query("count >= 20")
    .sort_values("mean")
    .head(5)
)
q10_pd

# %%
# POLARS:
q10_pl = (
    plf.group_by("country")
    .agg(
        pl.col("official").count().alias("count"),
        pl.col("official").mean().alias("mean"),
    )
    .filter(pl.col("count") >= 20)
    .sort("mean")
    .head(5)
)
q10_pl

# %% [markdown]
# ### Q11 🟡 — Average finish time per age bracket.

# %%
# PANDAS:
bins = [0, 30, 40, 50, 60, 100]
labels = ["20-29", "30-39", "40-49", "50-59", "60+"]
pdf["age_bracket"] = pd.cut(pdf["age"], bins=bins, labels=labels, right=False)
print(pdf.groupby("age_bracket")["official"].mean())

# %%
# POLARS:
plf = plf.with_columns(
    pl.when(pl.col("age") < 30).then(pl.lit("20-29"))
    .when(pl.col("age") < 40).then(pl.lit("30-39"))
    .when(pl.col("age") < 50).then(pl.lit("40-49"))
    .when(pl.col("age") < 60).then(pl.lit("50-59"))
    .otherwise(pl.lit("60+"))
    .alias("age_bracket")
)
print(plf.group_by("age_bracket").agg(pl.col("official").mean()).sort("age_bracket"))

# %% [markdown]
# ### Q12 🔴 — Country stats with negative split percentage.

# %%
# PANDAS:
pdf["second_half"] = pdf["official"] - pdf["half"]
pdf["negative_split"] = pdf["second_half"] < pdf["half"]

q12_pd = (
    pdf.groupby("country")
    .agg(
        num_runners=("name", "count"),
        avg_time=("official", "mean"),
        fastest=("official", "min"),
        neg_split_pct=("negative_split", "mean"),
    )
    .query("num_runners >= 10")
    .sort_values("avg_time")
    .head(10)
)
q12_pd["neg_split_pct"] = (q12_pd["neg_split_pct"] * 100).round(1)
q12_pd

# %%
# POLARS:
plf = plf.with_columns(
    (pl.col("official") - pl.col("half")).alias("second_half"),
)
plf = plf.with_columns(
    (pl.col("second_half") < pl.col("half")).alias("negative_split"),
)

q12_pl = (
    plf.group_by("country")
    .agg(
        pl.col("name").count().alias("num_runners"),
        pl.col("official").mean().alias("avg_time"),
        pl.col("official").min().alias("fastest"),
        (pl.col("negative_split").mean() * 100).round(1).alias("neg_split_pct"),
    )
    .filter(pl.col("num_runners") >= 10)
    .sort("avg_time")
    .head(10)
)
q12_pl

# %% [markdown]
# ---
# # Section 4: Adding Columns & Transformations
# ---

# %% [markdown]
# ### Q13 🟢 — Convert official time from minutes to hours.

# %%
# PANDAS:
pdf["finish_hours"] = pdf["official"] / 60
pdf[["name", "official", "finish_hours"]].head()

# %%
# POLARS:
plf = plf.with_columns(
    (pl.col("official") / 60).alias("finish_hours")
)
plf.select("name", "official", "finish_hours").head()

# %% [markdown]
# ### Q14 🟡 — Second half time and split difference.

# %%
# PANDAS:
pdf["second_half"] = pdf["official"] - pdf["half"]
pdf["split_diff"] = pdf["second_half"] - pdf["half"]
pdf[["name", "half", "second_half", "split_diff"]].head()

# %%
# POLARS:
plf = plf.with_columns(
    (pl.col("official") - pl.col("half")).alias("second_half"),
    (pl.col("official") - pl.col("half") - pl.col("half")).alias("split_diff"),
)
plf.select("name", "half", "second_half", "split_diff").head()

# %% [markdown]
# ### Q15 🟡 — Categorize by pace group.

# %%
# PANDAS:
import numpy as np

conditions = [
    pdf["pace"] < 6,
    pdf["pace"] < 8,
    pdf["pace"] < 10,
]
choices = ["Sub-elite", "Fast", "Moderate"]
pdf["pace_group"] = np.select(conditions, choices, default="Recreational")
print(pdf["pace_group"].value_counts())

# %%
# POLARS:
plf = plf.with_columns(
    pl.when(pl.col("pace") < 6).then(pl.lit("Sub-elite"))
    .when(pl.col("pace") < 8).then(pl.lit("Fast"))
    .when(pl.col("pace") < 10).then(pl.lit("Moderate"))
    .otherwise(pl.lit("Recreational"))
    .alias("pace_group")
)
print(plf["pace_group"].value_counts().sort("pace_group"))

# %% [markdown]
# ---
# # Section 5: Window Functions
# ---

# %% [markdown]
# ### Q16 🟡 — Average finish time of each runner's country.

# %%
# PANDAS:
pdf["country_avg_time"] = pdf.groupby("country")["official"].transform("mean")
pdf[["name", "country", "official", "country_avg_time"]].head()

# %%
# POLARS:
plf = plf.with_columns(
    pl.col("official").mean().over("country").alias("country_avg_time")
)
plf.select("name", "country", "official", "country_avg_time").head()

# %% [markdown]
# ### Q17 🔴 — Difference from peer (gender + age bracket) average.

# %%
# PANDAS:
pdf["peer_avg"] = pdf.groupby(["gender", "age_bracket"])["official"].transform("mean")
pdf["vs_peer_avg"] = pdf["official"] - pdf["peer_avg"]
pdf[["name", "gender", "age_bracket", "official", "peer_avg", "vs_peer_avg"]].head(10)

# %%
# POLARS:
plf = plf.with_columns(
    pl.col("official").mean().over(["gender", "age_bracket"]).alias("peer_avg"),
)
plf = plf.with_columns(
    (pl.col("official") - pl.col("peer_avg")).alias("vs_peer_avg"),
)
plf.select("name", "gender", "age_bracket", "official", "peer_avg", "vs_peer_avg").head(10)

# %% [markdown]
# ---
# # Section 6: Joins
# ---

# %% [markdown]
# ### Q18 🟡 — Join top 3 countries' average back to main DataFrame.

# %%
# PANDAS:
top3_pd = (
    pdf.groupby("country")["name"]
    .count()
    .reset_index(name="runner_count")
    .sort_values("runner_count", ascending=False)
    .head(3)
)
top3_avg_pd = (
    pdf[pdf["country"].isin(top3_pd["country"])]
    .groupby("country")["official"]
    .mean()
    .reset_index(name="top_country_avg")
)
q18_pd = pdf.merge(top3_avg_pd, on="country", how="left")
q18_pd[["name", "country", "official", "top_country_avg"]].head(10)

# %%
# POLARS:
top3_pl = (
    plf["country"]
    .value_counts()
    .sort("count", descending=True)
    .head(3)
    .select("country")
)
top3_avg_pl = (
    plf.filter(pl.col("country").is_in(top3_pl["country"]))
    .group_by("country")
    .agg(pl.col("official").mean().alias("top_country_avg"))
)
q18_pl = plf.join(top3_avg_pl, on="country", how="left")
q18_pl.select("name", "country", "official", "top_country_avg").head(10)

# %% [markdown]
# ---
# # Section 7: Reshaping
# ---

# %% [markdown]
# ### Q19 🟡 — Pivot: average time by gender (cols) and age bracket (rows).

# %%
# PANDAS:
# Make sure age_bracket exists
if "age_bracket" not in pdf.columns:
    bins = [0, 30, 40, 50, 60, 100]
    labels = ["18-29", "30-39", "40-49", "50-59", "60+"]
    pdf["age_bracket"] = pd.cut(pdf["age"], bins=bins, labels=labels, right=False)

q19_pd = pdf.pivot_table(
    values="official",
    index="age_bracket",
    columns="gender",
    aggfunc="mean",
).round(2)
q19_pd

# %%
# POLARS:
# Make sure age_bracket exists
if "age_bracket" not in plf.columns:
    plf = plf.with_columns(
        pl.when(pl.col("age") < 30).then(pl.lit("18-29"))
        .when(pl.col("age") < 40).then(pl.lit("30-39"))
        .when(pl.col("age") < 50).then(pl.lit("40-49"))
        .when(pl.col("age") < 60).then(pl.lit("50-59"))
        .otherwise(pl.lit("60+"))
        .alias("age_bracket")
    )

q19_pl = plf.pivot(
    on="gender",
    index="age_bracket",
    values="official",
    aggregate_function="mean",
)
q19_pl

# %% [markdown]
# ### Q20 🟡 — Melt/unpivot split times for first 10 runners.

# %%
# PANDAS:
split_cols = ["5k", "10k", "half", "20k", "25k", "30k", "35k", "40k"]
q20_pd = pdf[["name"] + split_cols].head(10).melt(
    id_vars=["name"],
    value_vars=split_cols,
    var_name="checkpoint",
    value_name="time_minutes",
)
q20_pd.sort_values(["name", "time_minutes"]).head(20)

# %%
# POLARS:
split_cols = ["5k", "10k", "half", "20k", "25k", "30k", "35k", "40k"]
q20_pl = (
    plf.select(["name"] + split_cols)
    .head(10)
    .unpivot(
        on=split_cols,
        index="name",
        variable_name="checkpoint",
        value_name="time_minutes",
    )
    .sort(["name", "time_minutes"])
)
q20_pl.head(20)

# %% [markdown]
# ---
# # Section 8: Advanced
# ---

# %% [markdown]
# ### Q21 🔴 — Q12 rewritten with polars lazy evaluation.

# %%
# POLARS LAZY:
q21_lazy = (
    plf.lazy()
    .with_columns(
        (pl.col("official") - pl.col("half")).alias("second_half_l"),
    )
    .with_columns(
        (pl.col("second_half_l") < pl.col("half")).alias("neg_split_l"),
    )
    .group_by("country")
    .agg(
        pl.col("name").count().alias("num_runners"),
        pl.col("official").mean().alias("avg_time"),
        pl.col("official").min().alias("fastest"),
        (pl.col("neg_split_l").mean() * 100).round(1).alias("neg_split_pct"),
    )
    .filter(pl.col("num_runners") >= 10)
    .sort("avg_time")
    .head(10)
)

print("=== Query Plan ===")
print(q21_lazy.explain())
print("\n=== Results ===")
q21_lazy.collect()

# %% [markdown]
# ### Q22 🔴 — Biggest slowdown between consecutive checkpoints.

# %%
# PANDAS:
# Checkpoint distances in km
checkpoints_km = {"5k": 5, "10k": 10, "half": 21.1, "20k": 20, "25k": 25, "30k": 30, "35k": 35, "40k": 40}
ordered_checkpoints = ["5k", "10k", "half", "20k", "25k", "30k", "35k", "40k"]

# Compute segment times (time between checkpoints)
segments_pd = pdf[["name"] + ordered_checkpoints].copy()
for i in range(1, len(ordered_checkpoints)):
    curr = ordered_checkpoints[i]
    prev = ordered_checkpoints[i - 1]
    seg_name = f"{prev}_to_{curr}"
    segments_pd[seg_name] = segments_pd[curr] - segments_pd[prev]

# Find max segment time increase for each runner
seg_cols = [c for c in segments_pd.columns if "_to_" in c]
# Find the segment with the max time for each runner
segments_pd["worst_segment"] = segments_pd[seg_cols].idxmax(axis=1)
segments_pd["worst_segment_time"] = segments_pd[seg_cols].max(axis=1)

# The runner with the biggest single segment time
worst_runner = segments_pd.sort_values("worst_segment_time", ascending=False).head(1)
print(f"Biggest slowdown:")
print(f"  Runner: {worst_runner['name'].values[0]}")
print(f"  Segment: {worst_runner['worst_segment'].values[0]}")
print(f"  Time: {worst_runner['worst_segment_time'].values[0]:.1f} minutes")

# %%
# POLARS:
ordered_checkpoints = ["5k", "10k", "half", "20k", "25k", "30k", "35k", "40k"]

# Compute segment times
seg_exprs = []
seg_names = []
for i in range(1, len(ordered_checkpoints)):
    curr = ordered_checkpoints[i]
    prev = ordered_checkpoints[i - 1]
    seg_name = f"{prev}_to_{curr}"
    seg_names.append(seg_name)
    seg_exprs.append((pl.col(curr) - pl.col(prev)).alias(seg_name))

segments_pl = plf.select(["name"] + ordered_checkpoints).with_columns(seg_exprs)

# Unpivot to find max segment per runner
melted_segs = segments_pl.select(["name"] + seg_names).unpivot(
    on=seg_names,
    index="name",
    variable_name="segment",
    value_name="segment_time",
)

# Find the max segment time overall
worst = melted_segs.sort("segment_time", descending=True, nulls_last=True).head(1)
print("Biggest slowdown (polars):")
print(worst)

# %% [markdown]
# ### Q23 🔴 — Most consistent runner (smallest std dev of segment paces).

# %%
# PANDAS:
import numpy as np

checkpoint_distances = [5, 10, 21.1, 20, 25, 30, 35, 40]
ordered_checkpoints = ["5k", "10k", "half", "20k", "25k", "30k", "35k", "40k"]

# Only runners with all split times
complete_pd = pdf.dropna(subset=ordered_checkpoints)[["name", "official"] + ordered_checkpoints].copy()

# Compute pace (min/km) for each segment
segment_distances = [
    checkpoint_distances[0],  # 0 to 5k = 5km
]
for i in range(1, len(checkpoint_distances)):
    segment_distances.append(checkpoint_distances[i] - checkpoint_distances[i - 1])

pace_cols = []
prev_col = None
for i, cp in enumerate(ordered_checkpoints):
    if i == 0:
        pace_col = f"pace_{cp}"
        complete_pd[pace_col] = complete_pd[cp] / segment_distances[i]
    else:
        pace_col = f"pace_{cp}"
        complete_pd[pace_col] = (complete_pd[cp] - complete_pd[ordered_checkpoints[i - 1]]) / segment_distances[i]
    pace_cols.append(pace_col)

# Standard deviation across pace columns
complete_pd["pace_std"] = complete_pd[pace_cols].std(axis=1)
most_consistent = complete_pd.sort_values("pace_std").head(5)
print("Most consistent runners (pandas):")
most_consistent[["name", "official", "pace_std"]]

# %%
# POLARS:
checkpoint_distances = [5.0, 10.0, 21.1, 20.0, 25.0, 30.0, 35.0, 40.0]
ordered_checkpoints = ["5k", "10k", "half", "20k", "25k", "30k", "35k", "40k"]

segment_distances = [checkpoint_distances[0]]
for i in range(1, len(checkpoint_distances)):
    segment_distances.append(checkpoint_distances[i] - checkpoint_distances[i - 1])

# Only complete runners
complete_pl = plf.select(["name", "official"] + ordered_checkpoints).drop_nulls()

# Compute pace for each segment
pace_exprs = []
pace_names = []
for i, cp in enumerate(ordered_checkpoints):
    pname = f"pace_{cp}"
    pace_names.append(pname)
    if i == 0:
        pace_exprs.append((pl.col(cp) / segment_distances[i]).alias(pname))
    else:
        pace_exprs.append(
            ((pl.col(cp) - pl.col(ordered_checkpoints[i - 1])) / segment_distances[i]).alias(pname)
        )

complete_pl = complete_pl.with_columns(pace_exprs)

# Compute std dev across pace columns using unpivot
# (Polars doesn't have row-wise std directly, so we unpivot and group)
consistency = (
    complete_pl.select(["name", "official"] + pace_names)
    .unpivot(on=pace_names, index=["name", "official"], variable_name="segment", value_name="pace")
    .group_by(["name", "official"])
    .agg(pl.col("pace").std().alias("pace_std"))
    .sort("pace_std")
    .head(5)
)
print("Most consistent runners (polars):")
consistency
