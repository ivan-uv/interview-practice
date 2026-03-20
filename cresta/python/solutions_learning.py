"""
solutions_learning.py

A concept-by-concept breakdown of every technique used in solutions.py.
Goal: understand what each line does and WHY, so you can write it from scratch.

Structure mirrors solutions.py:
  1. Pandas / EDA
  2. Hypothesis Testing & A/B Analysis
  3. Difference-in-Differences (DiD)
  4. Segmentation / Clustering
  5. NLP for conversational data
  6. Balanced class sampling (algorithm problem)
"""

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from collections import Counter
import re


# ============================================================
# IMPORTS — what each library is for
# ============================================================
#
# numpy (np)     — fast math on arrays. Most stats functions expect np.arrays.
# pandas (pd)    — DataFrames: labeled 2D tables. The main tool for EDA.
# scipy.stats    — statistical tests (t-test, normal distribution lookups)
# StandardScaler — rescales each feature to mean=0, std=1 before clustering
# KMeans         — the clustering algorithm itself
# Counter        — dict subclass: Counter(["a","a","b"]) → {"a":2, "b":1}
# re             — regex: pattern matching / substitution on strings


# ============================================================
# 1. PANDAS / EDA
# ============================================================

# ── CONCEPT: pd.to_datetime ──────────────────────────────────
#
# Raw data often stores timestamps as strings, e.g. "2024-01-15 09:30:00".
# pandas can't do math on strings, so we convert them first.
#
#   pd.to_datetime(series)  →  converts a column to DatetimeSeries
#
# Once converted, you can:
#   series.dt.total_seconds()   — duration in seconds
#   series.dt.to_period("W")    — snap each date to its ISO week
#   series.dt.start_time        — convert Period → Timestamp (for display)

def demo_datetime():
    s = pd.Series(["2024-01-15 09:00", "2024-01-15 09:30"])
    s = pd.to_datetime(s)
    # Subtraction of two DatetimeSeries → TimedeltaSeries
    delta = s[1] - s[0]
    print(delta.total_seconds())  # 1800.0  (30 minutes)


# ── CONCEPT: df.groupby().agg() ─────────────────────────────
#
# groupby(keys)  — splits the DataFrame into one group per unique key combo
# .agg(...)      — applies one or more aggregation functions per group
#
# Named aggregation syntax (pandas ≥ 0.25):
#   .agg(new_col_name=("source_col", "function"))
#
# Common aggregation strings: "count", "sum", "mean", "median", "std", "min", "max"
# You can also pass a lambda for custom logic:
#   ("source_col", lambda x: x.quantile(0.9))
#
# .reset_index() — turns the groupby keys back into regular columns
#                  (otherwise they become the DataFrame index)

def demo_groupby():
    df = pd.DataFrame({
        "agent_id": ["A", "A", "B", "B"],
        "handle_time": [300, 360, 250, 500],
        "conv_id": [1, 2, 3, 4],
    })

    result = (
        df.groupby("agent_id")
        .agg(
            call_volume=("conv_id", "count"),          # count rows
            avg_aht=("handle_time", "mean"),            # simple mean
            p90_aht=("handle_time", lambda x: x.quantile(0.9)),  # custom
        )
        .reset_index()
    )
    print(result)
    # agent_id  call_volume  avg_aht  p90_aht
    #        A            2    330.0    354.0
    #        B            2    375.0    455.0


# ── CONCEPT: dt.to_period("W") ──────────────────────────────
#
# Snaps each timestamp to a calendar period.
# "W" = week, "M" = month, "Q" = quarter, "Y" = year
#
# to_period() returns a Period object (e.g. "2024-01-15/2024-01-21").
# .dt.start_time converts it back to a Timestamp (the Monday of that week).
# This is useful for grouping by week without caring about the exact day.

def demo_period():
    s = pd.to_datetime(pd.Series(["2024-01-15", "2024-01-17", "2024-01-22"]))
    weeks = s.dt.to_period("W").dt.start_time
    print(weeks)
    # 0   2024-01-15   ← both in the same week
    # 1   2024-01-15
    # 2   2024-01-22   ← next week


# ── CONCEPT: Z-score and outlier flagging ───────────────────
#
# Z-score = how many standard deviations a value is from the mean.
#   z = (x - mean) / std
#
# If |z| > 2.5, the value is unusually extreme (~99% of data falls within ±2.5σ
# for a normal distribution).
#
# df.copy() — always work on a copy to avoid mutating the caller's DataFrame.
# .abs()    — absolute value of a Series, element-wise.

def demo_zscore():
    s = pd.Series([300, 310, 290, 1200, 305])  # 1200 is an outlier
    z = (s - s.mean()) / s.std()
    is_outlier = z.abs() > 2.5
    print(z.round(2))       # [−0.47, −0.39, −0.55,  2.82, −0.44]
    print(is_outlier)       # [False, False, False, True, False]


# ============================================================
# 2. HYPOTHESIS TESTING & A/B ANALYSIS
# ============================================================

# ── CONCEPT: Welch's t-test ──────────────────────────────────
#
# Use when: comparing the means of two independent groups (e.g. control vs treatment)
#           and you're NOT sure the groups have equal variance.
#
# Welch's t-test (equal_var=False) is the safe default — it works whether
# variances are equal or not. Student's t-test (equal_var=True) assumes equal
# variance, which is rarely guaranteed in practice.
#
# scipy.stats.ttest_ind(a, b, equal_var=False)
#   → (t_statistic, p_value)
#
# p_value < alpha (usually 0.05) → "statistically significant"
#   meaning: if the null hypothesis were true (no real difference),
#   we'd see a difference this large less than 5% of the time by chance.

def demo_ttest():
    control   = np.array([420, 400, 450, 410, 430])
    treatment = np.array([380, 370, 390, 360, 385])
    t_stat, p_value = stats.ttest_ind(treatment, control, equal_var=False)
    print(f"t={t_stat:.2f}, p={p_value:.4f}")
    # Large |t| and small p → likely a real difference


# ── CONCEPT: Cohen's d (effect size) ────────────────────────
#
# p-value tells you IF there's a difference. Cohen's d tells you HOW BIG it is.
#
#   d = (mean_A - mean_B) / pooled_std
#
# Rule of thumb:
#   |d| < 0.2  → negligible
#   |d| ~ 0.5  → medium
#   |d| > 0.8  → large
#
# Pooled std = sqrt((std_A² + std_B²) / 2)
# This is a simplified version; the exact formula weights by sample size.

def demo_cohens_d():
    a = np.array([390, 380, 385, 375])
    b = np.array([420, 430, 410, 425])
    pooled_std = np.sqrt((a.std()**2 + b.std()**2) / 2)
    d = (a.mean() - b.mean()) / pooled_std
    print(f"Cohen's d = {d:.2f}")  # negative → a has lower mean


# ── CONCEPT: Confidence Interval ────────────────────────────
#
# A 95% CI for the difference in means:
#   diff ± 1.96 × SE
#
# SE (standard error of the difference) = sqrt(var_A/n_A + var_B/n_B)
#
# 1.96 = the 97.5th percentile of the standard normal distribution,
# so ±1.96σ captures 95% of the distribution.
#
# If the 95% CI does NOT include 0 → consistent with a significant result.

def demo_ci():
    a = np.random.normal(390, 60, 100)
    b = np.random.normal(420, 60, 100)
    diff = a.mean() - b.mean()
    se = np.sqrt(a.var() / len(a) + b.var() / len(b))
    ci_low  = diff - 1.96 * se
    ci_high = diff + 1.96 * se
    print(f"Diff = {diff:.1f}, 95% CI = ({ci_low:.1f}, {ci_high:.1f})")


# ── CONCEPT: Sample size calculation ─────────────────────────
#
# Before running an experiment, calculate how many observations you need
# to reliably detect an effect of size `mde` (minimum detectable effect).
#
# Formula (two-sample t-test):
#   n = 2 × ((z_alpha + z_beta) / effect_size)²
#
# Where:
#   z_alpha = stats.norm.ppf(1 - alpha/2)  → critical value for significance
#             alpha=0.05 → z_alpha ≈ 1.96
#   z_beta  = stats.norm.ppf(power)        → critical value for power
#             power=0.80 → z_beta ≈ 0.84
#   effect_size = mde / baseline_std       → standardized effect
#
# stats.norm.ppf(q)  — percent point function (inverse CDF) of the normal dist.
#   i.e., "what z-value has q% of the distribution below it?"
#   ppf(0.975) = 1.96,  ppf(0.80) = 0.84
#
# np.ceil() — round up to the next integer (you can't have half a user)

def demo_sample_size():
    alpha, power = 0.05, 0.80
    baseline_std = 60   # std of the metric (e.g. handle time in seconds)
    mde = 25            # we want to detect a 25-second change

    z_alpha = stats.norm.ppf(1 - alpha / 2)   # 1.96
    z_beta  = stats.norm.ppf(power)            # 0.84
    effect_size = mde / baseline_std           # 25/60 ≈ 0.417

    n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    print(f"Need {int(np.ceil(n))} observations per group")


# ============================================================
# 3. DIFFERENCE-IN-DIFFERENCES (DiD)
# ============================================================

# ── CONCEPT: DiD estimator ───────────────────────────────────
#
# DiD is used when you can't randomize — you have a treated group and a
# control group, and you observe both before and after an intervention.
#
# DiD estimate = (post_T - pre_T) - (post_C - pre_C)
#             = treatment's change MINUS control's natural change
#
# This removes confounders that affected both groups equally over time
# (e.g. seasonality, macroeconomic trends).
#
# Key assumption: "parallel trends" — without the intervention, the treatment
# group would have changed at the same rate as the control group.

def demo_did():
    pre_T  = np.array([420, 415, 430])
    post_T = np.array([385, 380, 390])
    pre_C  = np.array([410, 415, 420])
    post_C = np.array([412, 418, 415])

    treatment_delta = post_T.mean() - pre_T.mean()   # how much T changed
    control_delta   = post_C.mean() - pre_C.mean()   # how much C changed naturally
    did_estimate    = treatment_delta - control_delta  # net effect of intervention

    print(f"Treatment Δ = {treatment_delta:.1f}")
    print(f"Control Δ   = {control_delta:.1f}")
    print(f"DiD         = {did_estimate:.1f}")


# ── CONCEPT: Bootstrap confidence interval ──────────────────
#
# Bootstrap = resample your data WITH replacement, compute the statistic
# many times, and use the spread of results as your confidence interval.
#
# "With replacement" means a value can be drawn more than once.
# np.random.choice(arr, size, replace=True) does this.
#
# Why bootstrap instead of a formula?
#   - Works for any statistic (DiD, median, ratio, etc.) without closed-form math.
#   - Robust when you don't know the distribution.
#
# To get a 95% CI from 2000 bootstrap samples:
#   np.percentile(samples, [2.5, 97.5])
#   → the 2.5th and 97.5th percentile of the bootstrap distribution
#
# Bootstrap p-value (two-tailed):
#   fraction of bootstrap samples where |bootstrap_stat| ≥ |observed_stat|
#   i.e., "how often does pure chance produce a result at least this extreme?"

def demo_bootstrap():
    np.random.seed(42)
    data = np.array([10, 12, 9, 11, 13, 8, 15, 10])
    observed_mean = data.mean()

    bootstrap_means = []
    for _ in range(2000):
        sample = np.random.choice(data, size=len(data), replace=True)
        bootstrap_means.append(sample.mean())

    ci_low, ci_high = np.percentile(bootstrap_means, [2.5, 97.5])
    print(f"Mean = {observed_mean:.2f}, 95% CI = ({ci_low:.2f}, {ci_high:.2f})")


# ============================================================
# 4. SEGMENTATION / CLUSTERING
# ============================================================

# ── CONCEPT: StandardScaler ──────────────────────────────────
#
# K-means uses Euclidean distance. If one feature is in the thousands
# (e.g. revenue) and another is 0–1 (e.g. CSAT), the large-scale feature
# will dominate distance calculations, biasing the clusters.
#
# StandardScaler rescales each feature to: mean=0, std=1
#   X_scaled = (X - mean) / std
#
# .fit_transform(X) — computes mean/std from X, then applies the scaling.
# .fit(X).transform(Y) — fit on training data, apply same scale to new data.
#
# Input: 2D array or DataFrame. Output: numpy array (same shape).

def demo_scaler():
    X = np.array([[1000, 0.8], [2000, 0.6], [500, 0.9]])
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    print(X_scaled.mean(axis=0))  # ≈ [0, 0]  — mean zeroed out
    print(X_scaled.std(axis=0))   # ≈ [1, 1]  — std normalized


# ── CONCEPT: KMeans clustering ───────────────────────────────
#
# K-means partitions n points into k clusters by minimizing within-cluster
# variance (sum of squared distances to the cluster centroid).
#
# Algorithm:
#   1. Randomly initialize k centroids
#   2. Assign each point to its nearest centroid
#   3. Recompute centroids as the mean of assigned points
#   4. Repeat until centroids stabilize
#
# Key parameters:
#   n_clusters  — how many clusters to create (you choose this)
#   random_state=42 — seed for reproducibility (centroids start randomly)
#   n_init=10   — run the algorithm 10 times with different seeds,
#                 keep the best result (avoids bad local optima)
#
# .fit_predict(X) — fits the model AND returns cluster labels in one call.
#   Returns array of integers: [0, 2, 1, 0, ...] — one label per row.
#
# How to choose k? Common approach: "elbow method" — plot inertia
# (total within-cluster variance) vs k, pick where it stops decreasing fast.

def demo_kmeans():
    np.random.seed(42)
    X = np.vstack([
        np.random.normal([0, 0], 0.5, (30, 2)),    # cluster A
        np.random.normal([5, 5], 0.5, (30, 2)),    # cluster B
        np.random.normal([0, 5], 0.5, (30, 2)),    # cluster C
    ])
    X_scaled = StandardScaler().fit_transform(X)
    labels = KMeans(n_clusters=3, random_state=42, n_init=10).fit_predict(X_scaled)
    print(labels[:5])  # e.g. [0, 0, 0, 2, 0]


# ── CONCEPT: select_dtypes ───────────────────────────────────
#
# df.select_dtypes(include=[np.number]) — returns only numeric columns.
# Useful before clustering or scaling (can't pass strings to KMeans).
# .columns.tolist() — convert the resulting Index to a plain Python list.

def demo_select_dtypes():
    df = pd.DataFrame({"name": ["Alice", "Bob"], "age": [25, 30], "score": [0.8, 0.9]})
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    print(numeric_cols)  # ['age', 'score']


# ── CONCEPT: Relabeling clusters by a metric ─────────────────
#
# KMeans labels are arbitrary integers (0, 1, 2...). To make them meaningful,
# compute a metric per cluster and rank.
#
# Example: sort clusters by avg_csat descending → label the best one "Tier 1".
#   groupby("segment")["avg_csat"].mean().sort_values(ascending=False)
#   → Series: {cluster_id: mean_csat, ...} sorted best-first
#
# Build a label map:
#   {cluster_id: "Tier 1", ...}
# Apply it:
#   df["segment_label"] = df["segment"].map(label_map)

def demo_cluster_labeling():
    df = pd.DataFrame({"segment": [0, 1, 2, 0, 1], "csat": [4.5, 3.2, 4.8, 4.3, 3.0]})
    rank = df.groupby("segment")["csat"].mean().sort_values(ascending=False)
    # rank.index gives cluster ids in order of best csat
    label_map = {seg: f"Tier {i+1}" for i, seg in enumerate(rank.index)}
    df["segment_label"] = df["segment"].map(label_map)
    print(df)


# ============================================================
# 5. NLP FOR CONVERSATIONAL DATA
# ============================================================

# ── CONCEPT: Regular expressions (re module) ─────────────────
#
# re.sub(pattern, replacement, string)
#   — replaces all matches of `pattern` in `string` with `replacement`
#
# Patterns used in clean_transcript():
#
#   r"\b(agent|customer|rep|caller)\s*:"
#     \b       — word boundary (match whole words only)
#     (a|b|c)  — alternation: match any of these
#     \s*      — zero or more whitespace characters
#     :        — literal colon
#     → removes speaker labels like "Agent:" or "Customer :"
#
#   r"[^a-z\s]"
#     [...]    — character class (match any ONE of these)
#     ^        — inside [], means NOT (negate)
#     a-z      — lowercase letters
#     \s       — whitespace characters
#     → removes anything that's NOT a letter or space (punctuation, digits)
#
#   r"\s+"
#     \s+      — one or more whitespace characters
#     → collapses multiple spaces/newlines into a single space

def demo_regex():
    text = "Agent: Hi there! Customer: I need help with my bill #1234."
    text = text.lower()
    text = re.sub(r"\b(agent|customer)\s*:", "", text)  # remove speaker labels
    text = re.sub(r"[^a-z\s]", " ", text)               # remove punctuation/digits
    text = re.sub(r"\s+", " ", text).strip()            # collapse whitespace
    print(text)  # "hi there   need help with my bill"


# ── CONCEPT: N-grams ─────────────────────────────────────────
#
# An n-gram is a sequence of n consecutive tokens.
# Bigrams (n=2): ["not", "working"] → "not working"
#
# The zip trick for generating n-grams from a token list:
#   tokens[0:], tokens[1:], tokens[2:]  → 3 lists offset by 1
#   zip(*[tokens[i:] for i in range(n)]) → tuples of n consecutive tokens
#
# Example with n=2, tokens = ["charge", "twice", "this", "month"]:
#   tokens[0:] = ["charge", "twice", "this", "month"]
#   tokens[1:] = ["twice", "this", "month"]
#   zip(...)   = [("charge","twice"), ("twice","this"), ("this","month")]
#   " ".join(gram) = "charge twice", "twice this", "this month"

def demo_ngrams():
    tokens = ["charge", "twice", "this", "month"]
    n = 2
    ngrams = [" ".join(gram) for gram in zip(*[tokens[i:] for i in range(n)])]
    print(ngrams)  # ['charge twice', 'twice this', 'this month']


# ── CONCEPT: Counter and most_common ─────────────────────────
#
# Counter is a dict subclass that counts hashable items.
#   Counter(["a", "b", "a", "c", "a"]) → Counter({"a": 3, "b": 1, "c": 1})
#
# .most_common(k) — returns the k most frequent items as list of (item, count) tuples.
#
# All n-grams across a corpus are collected in a flat list, then counted.
# list.extend(iterable) — appends all items of iterable to the list
#   (vs. .append() which would add the whole iterable as a single element)

def demo_counter():
    words = ["billing", "cancel", "billing", "transfer", "billing", "cancel"]
    c = Counter(words)
    print(c.most_common(2))  # [('billing', 3), ('cancel', 2)]


# ── CONCEPT: Set intersection for sentiment ──────────────────
#
# Converting a list of tokens to a set removes duplicates and enables
# fast membership testing (O(1) vs O(n) for lists).
#
# set_a & set_b — intersection: elements in BOTH sets
# len(tokens & positive_words) — count of positive words present in the text
#
# This approach is a "bag of words" — it ignores order and repetition.
# The sentiment score is: (pos - neg) / (pos + neg), ranging from -1 to +1.

def demo_set_intersection():
    positive = {"great", "helpful", "resolved"}
    tokens = {"my", "issue", "was", "resolved", "great"}  # set of words

    pos_count = len(tokens & positive)  # intersection
    print(pos_count)  # 2


# ── CONCEPT: Rule-based classification ──────────────────────
#
# The simplest possible classifier: check if any keyword is present.
# "First match wins" means ORDER of the rules dict matters.
#
# any(kw in text for kw in keywords)
#   — generator expression inside any() — short-circuits on first True
#   — more efficient than building a full list just to check one value
#
# dict iteration in Python 3.7+ preserves insertion order, so the first
# matching intent wins.

def demo_intent():
    rules = {
        "billing":   ["charge", "invoice", "bill"],
        "technical": ["error", "not working"],
    }
    text = "I got an unexpected charge on my invoice"
    for intent, keywords in rules.items():
        if any(kw in text for kw in keywords):
            print(f"Intent: {intent}")
            break  # first match wins


# ============================================================
# 6. BALANCED CLASS SAMPLING ALGORITHM
# ============================================================

# ── CONCEPT: The problem ─────────────────────────────────────
#
# Given n total samples and k classes with capacity limits [c0, c1, ..., ck-1],
# distribute n samples as evenly as possible, without exceeding any class limit.
#
# Example: n=10, capacities=[3, 10, 10]
#   Ideal even split: 10/3 ≈ 3.33 per class
#   Class 0 is capped at 3 → give it 3, redistribute the rest
#   Remaining 7 across 2 classes: 3 each + 1 extra → [3, 4, 3] or [3, 3, 4]

# ── CONCEPT: Integer division and remainder ──────────────────
#
# share = remaining // len(eligible)   — floor division: how many each class gets
# extra = remaining % len(eligible)    — remainder: this many classes get 1 more
#
# Example: remaining=7, eligible=2
#   share = 7 // 2 = 3
#   extra = 7 % 2  = 1   → first 1 eligible class gets 3+1=4, rest get 3

def demo_integer_division():
    remaining, n_classes = 7, 2
    share = remaining // n_classes   # 3
    extra = remaining % n_classes    # 1
    allocs = [share + (1 if i < extra else 0) for i in range(n_classes)]
    print(allocs)  # [4, 3]


# ── CONCEPT: The iterative "drain" approach ──────────────────
#
# Why a loop? Because after capping some classes, you have leftover samples
# that need to be redistributed. This can cascade multiple times.
#
# Each iteration:
#   1. Find classes still under their cap (available[i] > 0)
#   2. Split remaining evenly among them, cap each at their limit
#   3. Reduce `remaining` by what was actually allocated
#   4. Repeat until remaining = 0 or no eligible classes left
#
# Tracking `available[i]` (remaining capacity) is key — it starts as a copy
# of class_counts so we can decrement it without mutating the original.

def demo_balanced_sampling():
    n = 10
    class_counts = [3, 10, 10]

    k = len(class_counts)
    result = [0] * k
    remaining = n
    available = list(class_counts)  # mutable copy

    while remaining > 0:
        eligible = [i for i in range(k) if available[i] > 0]
        if not eligible:
            break

        share = remaining // len(eligible)
        extra = remaining % len(eligible)
        allocated = 0

        for idx, i in enumerate(eligible):
            alloc = share + (1 if idx < extra else 0)  # base + possible +1
            alloc = min(alloc, available[i])            # cap at class limit
            result[i] += alloc
            available[i] -= alloc
            allocated += alloc

        remaining -= allocated
        if allocated == 0:
            break

    print(result)  # [3, 4, 3]  — sums to 10, respects cap of 3 for class 0


# ── CONCEPT: list comprehension vs for loop ─────────────────
#
# These are equivalent:
#
#   eligible = [i for i in range(k) if available[i] > 0]
#
#   eligible = []
#   for i in range(k):
#       if available[i] > 0:
#           eligible.append(i)
#
# List comprehensions are idiomatic Python — prefer them for simple filtering.


# ── CONCEPT: enumerate() ────────────────────────────────────
#
# for idx, i in enumerate(eligible):
#   idx — the position within the eligible list (0, 1, 2, ...)
#   i   — the actual class index
#
# Without enumerate, you'd need a separate counter variable.
# Used here to give the "extra" (+1) to the first `extra` eligible classes.


# ============================================================
# PANDAS PATTERNS CHEAT SHEET
# ============================================================

# df.copy()                          — always copy before mutating
# pd.to_datetime(col)                — parse strings to datetime
# (end - start).dt.total_seconds()   — duration in seconds
# col.dt.to_period("W").dt.start_time — snap to week, get Monday date
# df.groupby(keys).agg(new=("col","fn")).reset_index()  — aggregate
# df.select_dtypes(include=[np.number]).columns.tolist() — numeric cols
# df["col"].map(dict)                — remap values using a dictionary
# df.merge(other, on="key", how="inner")  — SQL-style JOIN
# df.sort_values("col", ascending=False).reset_index(drop=True)

# ============================================================
# STATS PATTERNS CHEAT SHEET
# ============================================================

# stats.ttest_ind(a, b, equal_var=False)  → (t, p)   Welch's t-test
# stats.norm.ppf(0.975)                   → 1.96      z critical value
# np.percentile(arr, [2.5, 97.5])         → (lo, hi)  bootstrap CI
# np.random.choice(arr, n, replace=True)  → bootstrap resample
# (s - s.mean()) / s.std()               → z-scores
# np.sqrt(a.var()/na + b.var()/nb)       → SE of difference


if __name__ == "__main__":
    print("=== datetime ===")
    demo_datetime()

    print("\n=== groupby/agg ===")
    demo_groupby()

    print("\n=== period ===")
    demo_period()

    print("\n=== z-score ===")
    demo_zscore()

    print("\n=== t-test ===")
    demo_ttest()

    print("\n=== Cohen's d ===")
    demo_cohens_d()

    print("\n=== confidence interval ===")
    demo_ci()

    print("\n=== sample size ===")
    demo_sample_size()

    print("\n=== DiD ===")
    demo_did()

    print("\n=== bootstrap ===")
    demo_bootstrap()

    print("\n=== scaler ===")
    demo_scaler()

    print("\n=== kmeans ===")
    demo_kmeans()

    print("\n=== cluster labeling ===")
    demo_cluster_labeling()

    print("\n=== regex ===")
    demo_regex()

    print("\n=== n-grams ===")
    demo_ngrams()

    print("\n=== counter ===")
    demo_counter()

    print("\n=== set intersection ===")
    demo_set_intersection()

    print("\n=== intent classifier ===")
    demo_intent()

    print("\n=== integer division ===")
    demo_integer_division()

    print("\n=== balanced sampling ===")
    demo_balanced_sampling()
