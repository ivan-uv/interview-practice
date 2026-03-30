"""
Visa Python Practice — Solutions
Senior Analyst, Global Interchange Compliance

Topics:
1. Pandas / EDA — transaction data analysis
2. Anomaly detection — interchange compliance monitoring
3. Statistical testing — rate change impact analysis
4. Automation — data quality and pipeline helpers
5. Interchange calculations — rate computation and validation
"""

import numpy as np
import pandas as pd
from scipy import stats
from collections import Counter
import re
import hashlib


# ============================================================
# 1. PANDAS / EDA — Transaction Data Analysis
# ============================================================

def compute_interchange_summary(transactions: pd.DataFrame) -> pd.DataFrame:
    """
    Monthly interchange summary per issuer.
    """
    df = transactions.copy()
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    df["month"] = df["transaction_date"].dt.to_period("M").dt.start_time

    summary = (
        df.groupby(["issuer_id", "month"])
        .agg(
            txn_count=("transaction_id", "count"),
            total_volume=("amount_usd", "sum"),
            total_interchange=("interchange_amount_usd", "sum"),
            avg_ticket=("amount_usd", "mean"),
        )
        .reset_index()
    )
    summary["effective_rate"] = summary["total_interchange"] / summary["total_volume"]
    return summary


def compute_qualification_rates(transactions: pd.DataFrame) -> pd.DataFrame:
    """
    Qualification and downgrade rates per acquirer.
    """
    df = transactions.copy()

    summary = df.groupby("acquirer_id").agg(
        total_txns=("transaction_id", "count"),
        qualified_count=("qualification_status", lambda x: (x == "qualified").sum()),
        downgraded_count=("qualification_status", lambda x: (x == "downgraded").sum()),
        total_volume=("amount_usd", "sum"),
        total_interchange=("interchange_amount_usd", "sum"),
    ).reset_index()

    summary["qualification_rate"] = summary["qualified_count"] / summary["total_txns"]
    summary["downgrade_rate"] = summary["downgraded_count"] / summary["total_txns"]

    return summary.sort_values("qualification_rate").reset_index(drop=True)


# ============================================================
# 2. ANOMALY DETECTION — Compliance Monitoring
# ============================================================

def detect_interchange_anomalies(
    monthly_data: pd.DataFrame,
    z_threshold: float = 2.5,
) -> pd.DataFrame:
    """
    Detect months where interchange rate deviates from historical norm.
    Uses rolling 6-month z-score with min_periods=3.
    """
    df = monthly_data.copy()
    df = df.sort_values(["issuer_id", "month_start"]).reset_index(drop=True)

    df["rolling_mean"] = df.groupby("issuer_id")["avg_interchange_rate"].transform(
        lambda x: x.rolling(6, min_periods=3).mean()
    )
    df["rolling_std"] = df.groupby("issuer_id")["avg_interchange_rate"].transform(
        lambda x: x.rolling(6, min_periods=3).std()
    )
    df["z_score"] = (df["avg_interchange_rate"] - df["rolling_mean"]) / df["rolling_std"]
    df["is_anomaly"] = df["z_score"].abs() > z_threshold

    return df


def detect_duplicate_transactions(
    transactions: pd.DataFrame,
    time_window_seconds: int = 300,
) -> pd.DataFrame:
    """
    Identify potential duplicate transactions within a time window.
    """
    df = transactions.copy()
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    df = df.sort_values(
        ["card_number_hash", "merchant_id", "amount_usd", "transaction_date"]
    ).reset_index(drop=True)

    df["time_diff_seconds"] = (
        df.groupby(["card_number_hash", "merchant_id", "amount_usd"])["transaction_date"]
        .diff()
        .dt.total_seconds()
    )

    df["is_duplicate"] = (df["time_diff_seconds"].notna()) & (
        df["time_diff_seconds"] < time_window_seconds
    )

    dupes = df[df["is_duplicate"]].copy()
    return dupes[
        ["transaction_id", "card_number_hash", "merchant_id", "amount_usd",
         "transaction_date", "time_diff_seconds", "is_duplicate"]
    ].reset_index(drop=True)


def detect_mcc_misclassification(
    transactions: pd.DataFrame,
    merchants: pd.DataFrame,
    z_threshold: float = 2.0,
    min_txn_count: int = 30,
) -> pd.DataFrame:
    """
    Flag merchants with suspicious avg ticket for their MCC group.
    """
    # Compute per-merchant stats
    merchant_stats = (
        transactions.groupby("merchant_id")
        .agg(
            txn_count=("transaction_id", "count"),
            avg_ticket=("amount_usd", "mean"),
        )
        .reset_index()
    )
    merchant_stats = merchant_stats[merchant_stats["txn_count"] >= min_txn_count]

    # Join merchant info
    merged = merchant_stats.merge(
        merchants[["merchant_id", "merchant_name", "mcc", "mcc_description"]],
        on="merchant_id",
        how="inner",
    )

    # Compute MCC-level stats
    mcc_stats = merged.groupby("mcc")["avg_ticket"].agg(
        mcc_mean_ticket="mean", mcc_std_ticket="std"
    ).reset_index()

    result = merged.merge(mcc_stats, on="mcc", how="left")
    result["z_score"] = (
        (result["avg_ticket"] - result["mcc_mean_ticket"]) / result["mcc_std_ticket"]
    )
    result["is_suspect"] = result["z_score"].abs() > z_threshold

    return (
        result[
            ["merchant_id", "merchant_name", "mcc", "mcc_description", "txn_count",
             "avg_ticket", "mcc_mean_ticket", "mcc_std_ticket", "z_score", "is_suspect"]
        ]
        .sort_values("z_score", key=abs, ascending=False)
        .reset_index(drop=True)
    )


# ============================================================
# 3. STATISTICAL TESTING — Rate Change Impact
# ============================================================

def rate_change_impact_test(
    pre_rates: np.ndarray,
    post_rates: np.ndarray,
    alpha: float = 0.05,
) -> dict:
    """
    Welch's t-test on effective interchange rates before/after a change.
    """
    t_stat, p_value = stats.ttest_ind(post_rates, pre_rates, equal_var=False)

    diff = post_rates.mean() - pre_rates.mean()
    se = np.sqrt(post_rates.var() / len(post_rates) + pre_rates.var() / len(pre_rates))
    ci_low = diff - 1.96 * se
    ci_high = diff + 1.96 * se

    return {
        "pre_mean": round(pre_rates.mean(), 4),
        "post_mean": round(post_rates.mean(), 4),
        "difference": round(diff, 4),
        "difference_bps": round(diff * 10000, 4),
        "t_statistic": round(t_stat, 4),
        "p_value": round(p_value, 4),
        "significant": p_value < alpha,
        "ci_95": (round(ci_low, 4), round(ci_high, 4)),
    }


def durbin_compliance_check(transactions: pd.DataFrame) -> dict:
    """
    Check regulated debit transactions against the Durbin cap.
    """
    df = transactions.copy()

    # Filter to regulated debit
    regulated = df[
        (df["is_regulated"] == True) &
        (df["card_type"].isin(["consumer_debit", "prepaid"]))
    ].copy()

    # Compute cap: $0.21 + 0.05% of amount + $0.01
    regulated["durbin_cap"] = 0.21 + (regulated["amount_usd"] * 0.0005) + 0.01
    regulated["exceeds_cap"] = regulated["interchange_amount_usd"] > regulated["durbin_cap"]
    regulated["excess_usd"] = np.maximum(
        regulated["interchange_amount_usd"] - regulated["durbin_cap"], 0
    )

    violations = regulated[regulated["exceeds_cap"]]

    return {
        "total_regulated_txns": len(regulated),
        "violation_count": len(violations),
        "violation_rate": round(len(violations) / max(len(regulated), 1), 4),
        "total_excess_usd": round(violations["excess_usd"].sum(), 4),
        "max_excess_usd": round(violations["excess_usd"].max(), 4) if len(violations) > 0 else 0.0,
        "avg_excess_usd": round(violations["excess_usd"].mean(), 4) if len(violations) > 0 else 0.0,
    }


# ============================================================
# 4. AUTOMATION — Data Quality & Pipeline Helpers
# ============================================================

def validate_transaction_record(record: dict) -> dict:
    """
    Validate a single transaction record against business rules.
    """
    errors = []

    required_fields = [
        "transaction_id", "amount_usd", "card_type", "entry_mode",
        "issuer_id", "merchant_id", "transaction_date",
    ]
    valid_card_types = {
        "consumer_credit", "consumer_debit", "commercial_credit",
        "commercial_debit", "prepaid",
    }
    valid_entry_modes = {"chip", "contactless", "swipe", "keyed", "ecommerce"}

    # Check required fields
    for field in required_fields:
        if field not in record or record[field] is None:
            errors.append(f"Missing required field: {field}")

    # Validate amount
    if "amount_usd" in record and record["amount_usd"] is not None:
        try:
            amt = float(record["amount_usd"])
            if amt <= 0:
                errors.append("amount_usd must be positive")
            if amt > 1_000_000:
                errors.append("amount_usd exceeds maximum ($1,000,000)")
        except (ValueError, TypeError):
            errors.append("amount_usd must be numeric")

    # Validate card_type
    if "card_type" in record and record["card_type"] is not None:
        if record["card_type"] not in valid_card_types:
            errors.append(f"Invalid card_type: {record['card_type']}")

    # Validate entry_mode
    if "entry_mode" in record and record["entry_mode"] is not None:
        if record["entry_mode"] not in valid_entry_modes:
            errors.append(f"Invalid entry_mode: {record['entry_mode']}")

    # Validate transaction_date
    if "transaction_date" in record and record["transaction_date"] is not None:
        try:
            pd.to_datetime(record["transaction_date"])
        except (ValueError, TypeError):
            errors.append("transaction_date is not a valid datetime")

    return {"is_valid": len(errors) == 0, "errors": errors}


def generate_daily_quality_report(
    transactions: pd.DataFrame,
    report_date: str,
) -> dict:
    """
    Daily data quality summary for a given date.
    """
    df = transactions.copy()
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    report_dt = pd.to_datetime(report_date).date()

    day_data = df[df["transaction_date"].dt.date == report_dt]

    if len(day_data) == 0:
        return {
            "total_transactions": 0,
            "total_volume": 0.0,
            "null_settlement_rate": 0.0,
            "null_expected_ic_rate": 0.0,
            "interchange_variance": 0.0,
            "downgrade_rate": 0.0,
            "avg_ticket": 0.0,
            "issues": ["NO_DATA_FOR_DATE"],
        }

    n = len(day_data)
    null_settlement = day_data["settlement_date"].isnull().sum() / n
    null_expected_ic = day_data["expected_interchange_usd"].isnull().sum() / n

    # Interchange variance: only for rows where both actual and expected are non-null
    both_present = day_data.dropna(
        subset=["interchange_amount_usd", "expected_interchange_usd"]
    )
    ic_variance = (
        (both_present["interchange_amount_usd"] - both_present["expected_interchange_usd"])
        .abs()
        .sum()
    )

    downgrade_rate = (day_data["qualification_status"] == "downgraded").mean()
    avg_ticket = day_data["amount_usd"].mean()

    issues = []
    if null_settlement > 0.10:
        issues.append("HIGH_NULL_SETTLEMENT")
    if null_expected_ic > 0.20:
        issues.append("HIGH_NULL_EXPECTED_IC")
    if downgrade_rate > 0.15:
        issues.append("HIGH_DOWNGRADE_RATE")
    if ic_variance > 100_000:
        issues.append("INTERCHANGE_VARIANCE_ALERT")

    return {
        "total_transactions": n,
        "total_volume": round(day_data["amount_usd"].sum(), 4),
        "null_settlement_rate": round(null_settlement, 4),
        "null_expected_ic_rate": round(null_expected_ic, 4),
        "interchange_variance": round(ic_variance, 4),
        "downgrade_rate": round(downgrade_rate, 4),
        "avg_ticket": round(avg_ticket, 4),
        "issues": issues,
    }


# ============================================================
# 5. INTERCHANGE CALCULATIONS — Rate Computation & Validation
# ============================================================

def compute_expected_interchange(
    transactions: pd.DataFrame,
    rate_schedule: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compute expected interchange using the rate schedule.
    """
    df = transactions.copy()
    rates = rate_schedule[["rate_id", "pct_rate", "flat_fee_usd"]].copy()

    merged = df.merge(
        rates,
        left_on="interchange_rate_id",
        right_on="rate_id",
        how="left",
    )

    merged["expected_interchange_usd"] = (
        merged["amount_usd"] * merged["pct_rate"] + merged["flat_fee_usd"]
    )

    if "interchange_amount_usd" in merged.columns:
        merged["variance_usd"] = (
            merged["interchange_amount_usd"] - merged["expected_interchange_usd"]
        )
    else:
        merged["variance_usd"] = np.nan

    return merged


def estimate_rate_change_revenue_impact(
    transactions: pd.DataFrame,
    old_pct_rate: float,
    new_pct_rate: float,
    old_flat_fee: float,
    new_flat_fee: float,
) -> dict:
    """
    Estimate revenue impact of a rate change on a set of transactions.
    """
    df = transactions.copy()
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])

    txn_count = len(df)
    total_volume = df["amount_usd"].sum()

    old_total = (df["amount_usd"] * old_pct_rate + old_flat_fee).sum()
    new_total = (df["amount_usd"] * new_pct_rate + new_flat_fee).sum()
    delta = new_total - old_total

    date_range = (df["transaction_date"].max() - df["transaction_date"].min()).days
    days_in_sample = max(date_range, 1)
    annualized_delta = delta * (365 / days_in_sample)

    return {
        "txn_count": txn_count,
        "total_volume": round(total_volume, 2),
        "days_in_sample": days_in_sample,
        "old_total_interchange": round(old_total, 2),
        "new_total_interchange": round(new_total, 2),
        "delta": round(delta, 2),
        "delta_per_txn": round(delta / max(txn_count, 1), 2),
        "annualized_delta": round(annualized_delta, 2),
    }


def build_compliance_scorecard(
    monthly_summary: pd.DataFrame,
) -> pd.DataFrame:
    """
    Composite compliance health score per issuer from recent 3 months.
    """
    df = monthly_summary.copy()
    df["month_start"] = pd.to_datetime(df["month_start"])

    # Get the most recent 3 months per issuer
    df = df.sort_values(["issuer_id", "month_start"])
    df["month_rank"] = df.groupby("issuer_id")["month_start"].rank(
        ascending=False, method="dense"
    )
    recent = df[df["month_rank"] <= 3].copy()

    # Compute per-issuer metrics
    agg = recent.groupby("issuer_id").agg(
        avg_qualification_rate=("qualification_rate", "mean"),
        avg_downgrade_rate=("downgrade_rate", "mean"),
        total_case_count=("compliance_case_count", "sum"),
    ).reset_index()

    # Rate trend: last month - first month in bps
    first_last = recent.groupby("issuer_id").agg(
        first_rate=("avg_interchange_rate", "first"),
        last_rate=("avg_interchange_rate", "last"),
    ).reset_index()
    first_last["rate_trend_bps"] = (first_last["last_rate"] - first_last["first_rate"]) * 10000

    result = agg.merge(first_last[["issuer_id", "rate_trend_bps"]], on="issuer_id")

    # Min-max normalization
    def minmax(s):
        r = s.max() - s.min()
        return (s - s.min()) / r if r != 0 else pd.Series(0.5, index=s.index)

    norm_qual = minmax(result["avg_qualification_rate"])
    norm_down = minmax(result["avg_downgrade_rate"])
    norm_cases = minmax(result["total_case_count"])
    norm_trend = minmax(result["rate_trend_bps"])

    result["health_score"] = (
        0.30 * norm_qual
        + 0.25 * (1 - norm_down)
        + 0.25 * (1 - norm_cases)
        + 0.20 * norm_trend
    )

    return (
        result[
            ["issuer_id", "avg_qualification_rate", "avg_downgrade_rate",
             "total_case_count", "rate_trend_bps", "health_score"]
        ]
        .sort_values("health_score", ascending=False)
        .reset_index(drop=True)
    )


# ============================================================
# DEMO
# ============================================================

if __name__ == "__main__":
    np.random.seed(42)

    # --- Rate change impact test ---
    pre_rates = np.random.normal(loc=0.0175, scale=0.003, size=200)
    post_rates = np.random.normal(loc=0.0168, scale=0.003, size=200)
    result = rate_change_impact_test(pre_rates, post_rates)
    print("=== Rate Change Impact Test ===")
    for k, v in result.items():
        print(f"  {k}: {v}")

    # --- Durbin compliance check ---
    n_txns = 500
    durbin_df = pd.DataFrame({
        "transaction_id": [f"txn_{i:06d}" for i in range(n_txns)],
        "issuer_id": np.random.choice(["iss_001", "iss_002"], n_txns),
        "amount_usd": np.random.uniform(10, 200, n_txns).round(2),
        "interchange_amount_usd": np.random.uniform(0.15, 0.35, n_txns).round(4),
        "card_type": np.random.choice(["consumer_debit", "consumer_credit", "prepaid"], n_txns, p=[0.6, 0.3, 0.1]),
        "is_regulated": np.random.choice([True, False], n_txns, p=[0.7, 0.3]),
    })
    durbin_result = durbin_compliance_check(durbin_df)
    print("\n=== Durbin Compliance Check ===")
    for k, v in durbin_result.items():
        print(f"  {k}: {v}")

    # --- Transaction validation ---
    print("\n=== Transaction Validation ===")
    test_records = [
        {
            "transaction_id": "txn_001", "amount_usd": 47.50,
            "card_type": "consumer_credit", "entry_mode": "chip",
            "issuer_id": "iss_001", "merchant_id": "mch_001",
            "transaction_date": "2024-06-15 14:23:11"
        },
        {
            "transaction_id": "txn_002", "amount_usd": -10.00,
            "card_type": "invalid_type", "entry_mode": "teleport",
            "issuer_id": "iss_002", "merchant_id": None,
            "transaction_date": "not-a-date"
        },
        {
            "transaction_id": "txn_003", "amount_usd": 2_000_000,
            "card_type": "consumer_debit",
        },
    ]
    for rec in test_records:
        v = validate_transaction_record(rec)
        status = "VALID" if v["is_valid"] else f"INVALID ({len(v['errors'])} errors)"
        print(f"  {rec.get('transaction_id', 'unknown')}: {status}")
        for err in v["errors"]:
            print(f"    - {err}")

    # --- Duplicate detection ---
    print("\n=== Duplicate Detection ===")
    dup_df = pd.DataFrame({
        "transaction_id": ["txn_1", "txn_2", "txn_3", "txn_4", "txn_5"],
        "card_number_hash": ["hash_a", "hash_a", "hash_a", "hash_b", "hash_b"],
        "merchant_id": ["mch_1", "mch_1", "mch_1", "mch_2", "mch_2"],
        "amount_usd": [47.50, 47.50, 47.50, 30.00, 30.00],
        "transaction_date": [
            "2024-06-15 14:23:11", "2024-06-15 14:25:30",  # 2min apart — duplicate
            "2024-06-15 15:00:00",  # 35min later — not duplicate
            "2024-06-15 10:00:00", "2024-06-15 10:01:00",  # 1min apart — duplicate
        ],
    })
    dupes = detect_duplicate_transactions(dup_df)
    print(f"  Found {len(dupes)} potential duplicates:")
    for _, row in dupes.iterrows():
        print(f"    {row['transaction_id']}: {row['time_diff_seconds']:.0f}s apart")

    # --- Revenue impact estimate ---
    print("\n=== Rate Change Revenue Impact ===")
    impact_df = pd.DataFrame({
        "transaction_id": [f"txn_{i}" for i in range(1000)],
        "amount_usd": np.random.uniform(20, 200, 1000).round(2),
        "transaction_date": pd.date_range("2024-03-01", periods=1000, freq="h"),
    })
    impact = estimate_rate_change_revenue_impact(
        impact_df,
        old_pct_rate=0.0165, new_pct_rate=0.0155,
        old_flat_fee=0.10, new_flat_fee=0.10,
    )
    for k, v in impact.items():
        print(f"  {k}: {v}")
