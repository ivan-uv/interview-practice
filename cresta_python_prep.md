# Cresta DS Technical Interview — Python Crash Refresher

**Time budget: ~2 hours. No AI assistance. Type everything by hand.**

---

## Setup

Open [CoderPad Sandbox](https://app.coderpad.io/sandbox) (free, no login required) and set language to Python 3. This is the platform Cresta uses, so get comfortable with it.

Paste this once to create your practice dataset — then close this file and work from memory:

```python
import pandas as pd
import numpy as np
from scipy import stats

# Fake Cresta-style contact center data
np.random.seed(42)
n = 500

data = {
    "agent_id": np.random.choice(["A001", "A002", "A003", "A004", "A005"], n),
    "team": np.random.choice(["sales", "support", "retention"], n, p=[0.4, 0.4, 0.2]),
    "call_duration_sec": np.random.normal(300, 90, n).clip(30),
    "csat_score": np.random.choice([1, 2, 3, 4, 5], n, p=[0.05, 0.1, 0.2, 0.35, 0.3]),
    "used_cresta": np.random.choice([True, False], n, p=[0.6, 0.4]),
    "resolution": np.random.choice(["resolved", "escalated", "callback"], n, p=[0.65, 0.2, 0.15]),
    "handle_date": pd.date_range("2025-01-01", periods=n, freq="h"),
    "revenue": np.where(
        np.random.choice(["sales", "support", "retention"], n, p=[0.4, 0.4, 0.2]) == "sales",
        np.random.exponential(150, n).round(2),
        0
    ),
}

df = pd.DataFrame(data)
print(df.head(10))
print(df.shape)
print(df.dtypes)
```

---

## Part 1: Python Fundamentals (15 min)

These are the things that will sink you if you fumble them. Type each from memory.

### 1.1 Functions

```python
def greet(name, excited=False):
    if excited:
        return f"Hello, {name}!"
    return f"Hello, {name}."

print(greet("interviewer"))
print(greet("interviewer", excited=True))
```

### 1.2 Loops and Conditionals

```python
# for loop with enumerate
fruits = ["apple", "banana", "cherry"]
for i, fruit in enumerate(fruits):
    print(f"{i}: {fruit}")

# while loop
count = 0
while count < 3:
    print(count)
    count += 1
```

### 1.3 List Comprehensions

```python
# Basic
squares = [x**2 for x in range(10)]

# With filter
evens = [x for x in range(20) if x % 2 == 0]

# Nested
pairs = [(x, y) for x in range(3) for y in range(3) if x != y]
```

### 1.4 Dictionaries

```python
# Creating
scores = {"alice": 85, "bob": 92, "carol": 78}

# Iterating
for name, score in scores.items():
    print(f"{name}: {score}")

# Dictionary comprehension
doubled = {k: v * 2 for k, v in scores.items()}

# defaultdict (useful in interviews)
from collections import defaultdict, Counter

word_counts = Counter(["a", "b", "a", "c", "a", "b"])
print(word_counts)  # Counter({'a': 3, 'b': 2, 'c': 1})
print(word_counts.most_common(2))  # [('a', 3), ('b', 2)]
```

### 1.5 String Formatting

```python
name = "Cresta"
val = 0.8567

# f-strings (use these)
print(f"Company: {name}, Accuracy: {val:.2%}")  # "Accuracy: 85.67%"
print(f"Rounded: {val:.3f}")  # "Rounded: 0.857"
```

### Practice — close this file and type from memory:

1. Write a function `classify_score(score)` that returns "low" if < 3, "mid" if 3, "high" if > 3
2. Given a list of strings, use a list comprehension to return only strings longer than 4 characters, uppercased
3. Given a list of tuples `[("a", 1), ("b", 2), ("a", 3)]`, build a dict mapping each key to the sum of its values

---

## Part 2: Pandas Essentials (30 min)

This is the most likely area you'll be tested on. Assume `df` from setup is loaded.

### 2.1 Inspection

```python
df.head()
df.tail(3)
df.shape          # (rows, cols)
df.dtypes         # column types
df.describe()     # summary stats
df.info()         # memory, nulls
df.columns.tolist()
df["team"].value_counts()
df["team"].nunique()
df.isnull().sum()
```

### 2.2 Selecting and Filtering

```python
# Single column (Series)
df["agent_id"]

# Multiple columns (DataFrame)
df[["agent_id", "csat_score"]]

# Boolean filtering
df[df["csat_score"] >= 4]
df[(df["team"] == "sales") & (df["used_cresta"] == True)]
df[df["team"].isin(["sales", "retention"])]
df[df["agent_id"].str.startswith("A00")]

# .loc (label-based) and .iloc (position-based)
df.loc[0:5, ["agent_id", "csat_score"]]
df.iloc[0:5, 0:3]
```

### 2.3 Creating and Modifying Columns

```python
# New column
df["call_duration_min"] = df["call_duration_sec"] / 60

# Conditional column
df["high_csat"] = df["csat_score"] >= 4

# np.where (like SQL CASE WHEN)
df["csat_bucket"] = np.where(df["csat_score"] >= 4, "high", "low")

# Multiple conditions with np.select
conditions = [
    df["csat_score"] <= 2,
    df["csat_score"] == 3,
    df["csat_score"] >= 4,
]
choices = ["detractor", "passive", "promoter"]
df["nps_category"] = np.select(conditions, choices, default="unknown")

# Apply (use sparingly — slower than vectorized ops)
df["agent_id_lower"] = df["agent_id"].apply(lambda x: x.lower())
```

### 2.4 Groupby and Aggregation

```python
# Single agg
df.groupby("team")["csat_score"].mean()

# Multiple aggs
df.groupby("team")["csat_score"].agg(["mean", "median", "count", "std"])

# Multiple columns, multiple aggs
df.groupby("team").agg(
    avg_csat=("csat_score", "mean"),
    avg_duration=("call_duration_sec", "mean"),
    total_calls=("agent_id", "count"),
)

# Groupby multiple columns
df.groupby(["team", "used_cresta"])["csat_score"].mean()

# Reset index to get a flat dataframe
result = df.groupby("team")["csat_score"].mean().reset_index()
```

### 2.5 Sorting

```python
df.sort_values("csat_score", ascending=False)
df.sort_values(["team", "csat_score"], ascending=[True, False])
```

### 2.6 Merging / Joining

```python
# Create a second dataframe to join
agent_info = pd.DataFrame({
    "agent_id": ["A001", "A002", "A003", "A004", "A005"],
    "hire_year": [2020, 2021, 2019, 2022, 2023],
    "region": ["west", "east", "west", "central", "east"],
})

# Inner join (default)
merged = pd.merge(df, agent_info, on="agent_id", how="inner")

# Left join
merged = pd.merge(df, agent_info, on="agent_id", how="left")

# Join on different column names
# pd.merge(df, other, left_on="agent_id", right_on="id", how="left")
```

### 2.7 Pivot Tables

```python
pd.pivot_table(
    df,
    values="csat_score",
    index="team",
    columns="used_cresta",
    aggfunc="mean",
)
```

### 2.8 Handling Dates

```python
df["handle_date"] = pd.to_datetime(df["handle_date"])
df["day_of_week"] = df["handle_date"].dt.day_name()
df["month"] = df["handle_date"].dt.month
df["hour"] = df["handle_date"].dt.hour

# Filter by date range
mask = (df["handle_date"] >= "2025-01-05") & (df["handle_date"] < "2025-01-10")
df[mask]
```

### Practice — do these without looking up syntax:

1. What is the average CSAT score by team for calls that used Cresta vs. didn't?
2. Which agent has the highest resolution rate (% of calls with resolution == "resolved")?
3. Create a new column `call_category`: "short" if < 3 min, "medium" if 3-6 min, "long" if > 6 min. Then count how many of each category per team.
4. Merge `agent_info` onto `df` and find the average call duration by `region`.

<details>
<summary>Solutions (try first!)</summary>

```python
# 1
df.groupby(["team", "used_cresta"])["csat_score"].mean()

# 2
resolution_rates = (
    df.assign(resolved=df["resolution"] == "resolved")
    .groupby("agent_id")["resolved"]
    .mean()
    .sort_values(ascending=False)
)
print(resolution_rates)

# 3
conditions = [
    df["call_duration_sec"] < 180,
    df["call_duration_sec"] <= 360,
    df["call_duration_sec"] > 360,
]
df["call_category"] = np.select(conditions, ["short", "medium", "long"])
df.groupby(["team", "call_category"])["agent_id"].count()

# 4
merged = pd.merge(df, agent_info, on="agent_id", how="left")
merged.groupby("region")["call_duration_sec"].mean()
```

</details>

---

## Part 3: Statistics & Experimentation (30 min)

### 3.1 Descriptive Stats with numpy/pandas

```python
values = df["call_duration_sec"]

np.mean(values)
np.median(values)
np.std(values)         # population std
np.std(values, ddof=1) # sample std (use this one)
np.percentile(values, [25, 50, 75])
np.corrcoef(df["call_duration_sec"], df["csat_score"])
```

### 3.2 T-Test (comparing two groups)

The single most important statistical test for this interview.

```python
# "Does using Cresta improve CSAT scores?"
cresta_scores = df[df["used_cresta"] == True]["csat_score"]
no_cresta_scores = df[df["used_cresta"] == False]["csat_score"]

t_stat, p_value = stats.ttest_ind(cresta_scores, no_cresta_scores)
print(f"t-statistic: {t_stat:.4f}")
print(f"p-value: {p_value:.4f}")
print(f"Significant at 0.05? {p_value < 0.05}")
```

**Know these concepts cold:**
- **Null hypothesis (H0):** No difference between groups
- **Alternative hypothesis (H1):** There IS a difference
- **p-value:** Probability of seeing this result (or more extreme) if H0 is true
- **alpha (significance level):** Threshold for rejecting H0, typically 0.05
- **Type I error:** False positive (rejecting H0 when it's true)
- **Type II error:** False negative (failing to reject H0 when it's false)
- **Power:** Probability of detecting a real effect (1 - Type II error rate)

### 3.3 Chi-Square Test (categorical vs categorical)

```python
# "Is resolution outcome independent of whether Cresta was used?"
contingency = pd.crosstab(df["used_cresta"], df["resolution"])
chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
print(f"Chi-square: {chi2:.4f}, p-value: {p_value:.4f}")
```

### 3.4 A/B Test Design — Talk Track

If asked "how would you design an A/B test for feature X?", hit these points:

1. **Define the metric** — primary (e.g., CSAT) and guardrail metrics (e.g., handle time)
2. **Randomization unit** — agent-level or call-level? (agent-level is cleaner but needs more data)
3. **Sample size calculation** — need: baseline rate, minimum detectable effect (MDE), alpha, power
4. **Duration** — long enough to capture weekly seasonality (at least 2 weeks)
5. **Analyze** — t-test or proportion test, check for novelty effects, segment results
6. **Pitfalls** — Simpson's paradox, peeking (multiple testing), network effects between agents

```python
# Sample size estimation (know this exists, exact syntax is fine to look up)
from statsmodels.stats.power import TTestIndPower

analysis = TTestIndPower()
sample_size = analysis.solve_power(
    effect_size=0.2,  # small effect
    alpha=0.05,
    power=0.8,
    alternative="two-sided",
)
print(f"Need {sample_size:.0f} per group")
```

### Practice:

1. Test whether the average call duration differs between the "sales" and "support" teams. State your conclusion.
2. You're asked: "We rolled out Cresta to 50 agents and CSAT went up 3%. Is that significant?" Walk through what you'd need to know before answering.
3. Build a contingency table of `team` x `resolution` and run a chi-square test. Interpret.

<details>
<summary>Solutions</summary>

```python
# 1
sales = df[df["team"] == "sales"]["call_duration_sec"]
support = df[df["team"] == "support"]["call_duration_sec"]
t, p = stats.ttest_ind(sales, support)
print(f"t={t:.3f}, p={p:.3f}")
# Interpret: if p < 0.05, reject H0, conclude durations differ significantly

# 2 — Talk track, not code:
# - What's the sample size? 50 agents may be too few
# - What's the baseline CSAT? 3% lift from 70% vs 95% is very different
# - Was there a control group, or is this before/after? (before/after is weaker)
# - How long was the measurement period?
# - Were there other changes happening simultaneously?
# - Need to run a proper hypothesis test, not just eyeball the difference

# 3
ct = pd.crosstab(df["team"], df["resolution"])
chi2, p, dof, expected = stats.chi2_contingency(ct)
print(f"chi2={chi2:.3f}, p={p:.3f}, dof={dof}")
# Interpret: if p < 0.05, resolution outcomes depend on team
```

</details>

---

## Part 4: The Balanced Sampling Problem (15 min)

This was actually asked at Cresta. Practice it.

> A dataset has examples labeled with different classes. You want to sample n items
> so that classes are as balanced as possible. Given n and a list of class counts,
> return how many to sample from each class.

Think about it before looking at the solution.

**Hints:**
- If you have 3 classes and want 9 samples, take 3 from each
- If you have 3 classes and want 10 samples, take 3 from two and 4 from one
- But what if a class only has 2 items? You can't take 4 from it
- You need to handle the case where a class has fewer items than the "fair share"

<details>
<summary>Solution</summary>

```python
def balanced_sample(n, class_counts):
    """
    n: total number of samples desired
    class_counts: list of ints, number of examples in each class
    returns: list of ints, number to sample from each class
    """
    k = len(class_counts)
    result = [0] * k
    remaining = n

    # Track which classes still have capacity
    available = list(range(k))

    while remaining > 0 and available:
        # Fair share among remaining classes
        share = remaining // len(available)
        extra = remaining % len(available)

        new_available = []
        allocated_this_round = 0

        for i, idx in enumerate(available):
            # Give each class its fair share, +1 for the first 'extra' classes
            target = share + (1 if i < extra else 0)
            # But can't exceed what the class actually has
            actual = min(target, class_counts[idx] - result[idx])
            result[idx] += actual
            allocated_this_round += actual

            # If class still has room, keep it available
            if result[idx] < class_counts[idx]:
                new_available.append(idx)

        remaining -= allocated_this_round
        available = new_available

        # Safety: if we allocated nothing this round, break (can't fill n)
        if allocated_this_round == 0:
            break

    return result


# Test cases
print(balanced_sample(9, [100, 100, 100]))   # [3, 3, 3]
print(balanced_sample(10, [100, 100, 100]))  # [4, 3, 3]
print(balanced_sample(10, [2, 100, 100]))    # [2, 4, 4]
print(balanced_sample(5, [1, 1, 1]))         # [1, 1, 1] (can only get 3)
print(balanced_sample(0, [10, 10]))          # [0, 0]
```

</details>

---

## Part 5: Quick Reference Card

Print this or keep it open. These are the patterns you'll reach for most often.

```
PANDAS CHEATSHEET
─────────────────────────────────────────────
Read data         pd.read_csv("file.csv")
Filter rows       df[df["col"] > val]
Multiple conds    df[(cond1) & (cond2)]
Select cols       df[["a", "b"]]
New column        df["new"] = expr
Conditional col   np.where(cond, "yes", "no")
Group + agg       df.groupby("col")["val"].mean()
Named agg         df.groupby("c").agg(name=("col", "func"))
Sort              df.sort_values("col", ascending=False)
Merge             pd.merge(df1, df2, on="key", how="left")
Pivot             pd.pivot_table(df, values, index, columns, aggfunc)
Value counts      df["col"].value_counts()
Null check        df.isnull().sum()
Reset index       .reset_index()
Rename            df.rename(columns={"old": "new"})

STATS CHEATSHEET
─────────────────────────────────────────────
t-test            stats.ttest_ind(group1, group2)
chi-square        stats.chi2_contingency(pd.crosstab(...))
correlation       df["a"].corr(df["b"])
p < 0.05 → reject H0 → effect is statistically significant
```

---

## Final Advice

1. **Talk through your approach before coding.** "I'll group by team and used_cresta, then compute the mean CSAT" — this buys you time and shows your thinking.
2. **It's okay to say** "I know pandas has a method for this, let me think about the syntax" — then try it. The interviewer cares about your reasoning, not memorization.
3. **Start simple.** Get a working solution first, then optimize. A correct for-loop beats a broken one-liner.
4. **Print intermediate results.** `print(df.head())` after each step shows you're checking your work.
5. **If you blank on syntax**, describe what you want in plain English. "I need to join these two tables on agent_id, keeping all rows from the left table." The interviewer may nudge you.

Good luck tomorrow. You know this stuff — you just need to shake the rust off tonight.
