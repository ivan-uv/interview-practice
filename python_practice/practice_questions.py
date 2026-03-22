# %% [markdown]
# # Pandas & Polars Practice Questions
# **Dataset: 2014 Boston Marathon Results**
#
# For each question, write the solution in **both pandas AND polars**.
# Try to answer without looking at the solutions file!
#
# Difficulty levels: 🟢 Easy | 🟡 Medium | 🔴 Hard
#
# ## Setup
# ```
# pip install pandas polars requests
# ```

# %%
# === SETUP — Run this first! ===
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

print(f"Loaded {len(pdf)} rows × {pdf.shape[1]} columns")
print(f"Columns: {list(pdf.columns)}")

# %% [markdown]
# ---
# # Section 1: Selection & Filtering
# ---

# %% [markdown]
# ### Q1 🟢 — Select just the name, age, and gender columns.
# Expected: A DataFrame with 3 columns for all runners.

# %%
# PANDAS:
# Your answer here...


# %%
# POLARS:
# Your answer here...


# %% [markdown]
# ### Q2 🟢 — How many runners are from the USA?

# %%
# PANDAS:
# Your answer here...


# %%
# POLARS:
# Your answer here...


# %% [markdown]
# ### Q3 🟢 — Find all runners aged 60 or older. How many are there?

# %%
# PANDAS:
# Your answer here...


# %%
# POLARS:
# Your answer here...


# %% [markdown]
# ### Q4 🟡 — Find all female runners from Kenya (KEN) who finished under 3 hours (180 minutes).

# %%
# PANDAS:
# Your answer here...


# %%
# POLARS:
# Your answer here...


# %% [markdown]
# ### Q5 🟡 — Find runners whose name contains "Smith". How many are there?

# %%
# PANDAS:
# Your answer here...


# %%
# POLARS:
# Your answer here...


# %% [markdown]
# ---
# # Section 2: Sorting & Ranking
# ---

# %% [markdown]
# ### Q6 🟢 — Who were the top 5 fastest finishers? Show their name, country, and official time.

# %%
# PANDAS:
# Your answer here...


# %%
# POLARS:
# Your answer here...


# %% [markdown]
# ### Q7 🟡 — Who was the fastest runner aged 70 or older? Show their name, age, country, and time.

# %%
# PANDAS:
# Your answer here...


# %%
# POLARS:
# Your answer here...


# %% [markdown]
# ### Q8 🟡 — Rank all runners within their gender by finish time (1 = fastest).
# Add a column called `gender_rank`.

# %%
# PANDAS:
# Your answer here...


# %%
# POLARS:
# Your answer here...


# %% [markdown]
# ---
# # Section 3: GroupBy & Aggregation
# ---

# %% [markdown]
# ### Q9 🟢 — What is the average finish time for each gender?

# %%
# PANDAS:
# Your answer here...


# %%
# POLARS:
# Your answer here...


# %% [markdown]
# ### Q10 🟡 — Which country has the fastest average finish time?
# Only include countries with at least 20 runners.

# %%
# PANDAS:
# Your answer here...


# %%
# POLARS:
# Your answer here...


# %% [markdown]
# ### Q11 🟡 — Create an age bracket column (20-29, 30-39, 40-49, 50-59, 60+)
# and find the average finish time per age bracket.

# %%
# PANDAS:
# Your answer here...


# %%
# POLARS:
# Your answer here...


# %% [markdown]
# ### Q12 🔴 — For each country with at least 10 runners, find:
# - Number of runners
# - Average finish time
# - Fastest finish time
# - Percentage of runners who ran a negative split (second half faster than first half)
#
# Sort by average time ascending.

# %%
# PANDAS:
# Your answer here...


# %%
# POLARS:
# Your answer here...


# %% [markdown]
# ---
# # Section 4: Adding Columns & Transformations
# ---

# %% [markdown]
# ### Q13 🟢 — Add a column `finish_hours` that converts the official time from minutes to hours.

# %%
# PANDAS:
# Your answer here...


# %%
# POLARS:
# Your answer here...


# %% [markdown]
# ### Q14 🟡 — Add a `second_half` column (official - half) and a `split_diff` column
# (second_half - half). A negative split_diff means the runner got faster.

# %%
# PANDAS:
# Your answer here...


# %%
# POLARS:
# Your answer here...


# %% [markdown]
# ### Q15 🟡 — Categorize runners by pace:
# - "Sub-elite" if pace < 6 min/mile
# - "Fast" if pace < 8
# - "Moderate" if pace < 10
# - "Recreational" otherwise
#
# Add as a new column called `pace_group`.

# %%
# PANDAS:
# Your answer here...


# %%
# POLARS:
# Your answer here...


# %% [markdown]
# ---
# # Section 5: Window Functions
# ---

# %% [markdown]
# ### Q16 🟡 — For each runner, add a column showing the average finish time of
# their country. Call it `country_avg_time`.

# %%
# PANDAS:
# Your answer here...


# %%
# POLARS:
# Your answer here...


# %% [markdown]
# ### Q17 🔴 — For each runner, compute how many minutes faster or slower they
# were compared to the average of their gender AND age bracket (20-29, 30-39, etc.).
# Call it `vs_peer_avg`.

# %%
# PANDAS:
# Your answer here...


# %%
# POLARS:
# Your answer here...


# %% [markdown]
# ---
# # Section 6: Joins
# ---

# %% [markdown]
# ### Q18 🟡 — Create a DataFrame with the top 3 countries by runner count, and their
# average finish time. Then join it back to the main DataFrame so each runner from
# those countries has a `top_country_avg` column. Runners from other countries
# should have null.

# %%
# PANDAS:
# Your answer here...


# %%
# POLARS:
# Your answer here...


# %% [markdown]
# ---
# # Section 7: Reshaping
# ---

# %% [markdown]
# ### Q19 🟡 — Create a pivot table showing the average finish time by gender (columns)
# and age bracket (rows). Age brackets: 18-29, 30-39, 40-49, 50-59, 60+.

# %%
# PANDAS:
# Your answer here...


# %%
# POLARS:
# Your answer here...


# %% [markdown]
# ### Q20 🟡 — Take the first 10 runners and melt/unpivot their checkpoint split
# times (5k, 10k, half, 20k, 25k, 30k, 35k, 40k) into long format with columns:
# name, checkpoint, time_minutes.

# %%
# PANDAS:
# Your answer here...


# %%
# POLARS:
# Your answer here...


# %% [markdown]
# ---
# # Section 8: Advanced / Polars-Specific
# ---

# %% [markdown]
# ### Q21 🔴 — (Polars only) Rewrite Q12 using lazy evaluation.
# Use `.lazy()`, build the full query, print `.explain()`, then `.collect()`.

# %%
# POLARS LAZY:
# Your answer here...


# %% [markdown]
# ### Q22 🔴 — For each runner, compute the time between each checkpoint
# (5k→10k, 10k→half, half→20k, etc.) and find who had the biggest slowdown
# between any two consecutive checkpoints. Return their name, which segment,
# and how much they slowed down.

# %%
# PANDAS:
# Your answer here...


# %%
# POLARS:
# Your answer here...


# %% [markdown]
# ### Q23 🔴 — Find the "most consistent" runner: the person with the smallest
# standard deviation across their checkpoint split *paces* (time per km for each
# segment). Only include runners who have all checkpoint times.
#
# Checkpoint distances in km: 5k=5, 10k=10, half=21.1, 20k=20, 25k=25, 30k=30, 35k=35, 40k=40

# %%
# PANDAS:
# Your answer here...


# %%
# POLARS:
# Your answer here...


# %% [markdown]
# ---
# # Done!
# Check your answers against `solutions.py`
