"""
Visa Python Practice — Questions
Senior Analyst, Global Interchange Compliance

Implement each function below. Do not modify signatures or docstrings.
Run solutions.py to compare your output.

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
    Given a DataFrame with columns:
        transaction_id, issuer_id, merchant_id, transaction_date (str/datetime),
        amount_usd, card_type, interchange_amount_usd

    Return a monthly summary per issuer with columns:
        issuer_id | month (month-start date) | txn_count | total_volume |
        total_interchange | effective_rate | avg_ticket

    Notes:
    - effective_rate = total_interchange / total_volume
    - Use pd.Grouper or to_period('M') to floor to month
    """
    raise NotImplementedError


def compute_qualification_rates(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """
    Given a DataFrame with columns:
        transaction_id, acquirer_id, qualification_status ('qualified', 'downgraded', 'standard'),
        amount_usd, interchange_amount_usd

    Return a summary per acquirer with columns:
        acquirer_id | total_txns | qualified_count | downgraded_count |
        qualification_rate | downgrade_rate | total_volume | total_interchange

    Sort by qualification_rate ascending (worst acquirers first).
    """
    raise NotImplementedError


# ============================================================
# 2. ANOMALY DETECTION — Compliance Monitoring
# ============================================================

def detect_interchange_anomalies(
    monthly_data: pd.DataFrame,
    z_threshold: float = 2.5,
) -> pd.DataFrame:
    """
    Given a DataFrame of monthly interchange summary with columns:
        issuer_id, month_start (datetime), avg_interchange_rate

    Detect months where the interchange rate deviates from the issuer's
    historical mean by more than z_threshold standard deviations.

    For each issuer, compute:
    - rolling_mean: rolling 6-month mean of avg_interchange_rate
    - rolling_std: rolling 6-month std of avg_interchange_rate
    - z_score: (current rate - rolling_mean) / rolling_std

    Return a copy with columns added: rolling_mean, rolling_std, z_score, is_anomaly
    where is_anomaly = True if abs(z_score) > z_threshold.

    Use min_periods=3 for the rolling calculations.
    """
    raise NotImplementedError


def detect_duplicate_transactions(
    transactions: pd.DataFrame,
    time_window_seconds: int = 300,
) -> pd.DataFrame:
    """
    Given a DataFrame with columns:
        transaction_id, card_number_hash, merchant_id, amount_usd,
        transaction_date (datetime)

    Identify potential duplicates: same card, same merchant, same amount,
    within time_window_seconds of each other.

    Steps:
    1. Sort by card_number_hash, merchant_id, amount_usd, transaction_date
    2. Group by (card_number_hash, merchant_id, amount_usd)
    3. Compute time diff to previous transaction in each group
    4. Flag as duplicate if time_diff < time_window_seconds

    Return a DataFrame with the potential duplicates only, including columns:
        transaction_id, card_number_hash, merchant_id, amount_usd,
        transaction_date, time_diff_seconds, is_duplicate
    """
    raise NotImplementedError


def detect_mcc_misclassification(
    transactions: pd.DataFrame,
    merchants: pd.DataFrame,
    z_threshold: float = 2.0,
    min_txn_count: int = 30,
) -> pd.DataFrame:
    """
    Identify merchants whose average transaction amount is suspicious
    for their MCC group.

    Steps:
    1. Compute avg_ticket per merchant (only merchants with >= min_txn_count transactions)
    2. Compute MCC-level mean and std of avg_ticket
    3. Z-score each merchant within its MCC
    4. Flag merchants where abs(z_score) > z_threshold

    Return a DataFrame with columns:
        merchant_id, merchant_name, mcc, mcc_description, txn_count,
        avg_ticket, mcc_mean_ticket, mcc_std_ticket, z_score, is_suspect

    Sorted by abs(z_score) descending.
    """
    raise NotImplementedError


# ============================================================
# 3. STATISTICAL TESTING — Rate Change Impact
# ============================================================

def rate_change_impact_test(
    pre_rates: np.ndarray,
    post_rates: np.ndarray,
    alpha: float = 0.05,
) -> dict:
    """
    Test whether a rate change had a statistically significant impact
    on effective interchange rates.

    Run a Welch's two-sample t-test comparing post vs. pre rates.

    Return a dict with keys:
        pre_mean, post_mean, difference, difference_bps (in basis points),
        t_statistic, p_value, significant (bool),
        ci_95 (tuple of floats — 95% CI on the difference)

    Notes:
    - difference_bps = difference * 10000
    - 95% CI: diff +/- 1.96 * SE where SE = sqrt(var_post/n_post + var_pre/n_pre)
    - Round all floats to 4 decimal places
    """
    raise NotImplementedError


def durbin_compliance_check(
    transactions: pd.DataFrame,
) -> dict:
    """
    Check whether regulated debit transactions comply with the Durbin cap.

    Durbin cap formula: $0.21 + 0.05% of transaction amount + $0.01

    Given a DataFrame with columns:
        transaction_id, issuer_id, amount_usd, interchange_amount_usd,
        card_type, is_regulated (bool)

    Steps:
    1. Filter to regulated debit transactions (is_regulated=True AND
       card_type in ['consumer_debit', 'prepaid'])
    2. Compute durbin_cap for each transaction
    3. Flag violations where interchange_amount_usd > durbin_cap

    Return a dict with keys:
        total_regulated_txns, violation_count, violation_rate,
        total_excess_usd (sum of amount over cap for violations),
        max_excess_usd, avg_excess_usd

    Round all floats to 4 decimal places.
    """
    raise NotImplementedError


# ============================================================
# 4. AUTOMATION — Data Quality & Pipeline Helpers
# ============================================================

def validate_transaction_record(record: dict) -> dict:
    """
    Validate a single transaction record against business rules.

    Required fields: transaction_id, amount_usd, card_type, entry_mode,
                     issuer_id, merchant_id, transaction_date

    Validation rules:
    1. All required fields must be present and non-null
    2. amount_usd must be positive and <= 1,000,000
    3. card_type must be one of: consumer_credit, consumer_debit,
       commercial_credit, commercial_debit, prepaid
    4. entry_mode must be one of: chip, contactless, swipe, keyed, ecommerce
    5. transaction_date must be parseable as a datetime

    Return a dict with keys:
        is_valid (bool), errors (list of strings describing each failure)

    An empty errors list means the record is valid.
    """
    raise NotImplementedError


def generate_daily_quality_report(
    transactions: pd.DataFrame,
    report_date: str,
) -> dict:
    """
    Generate a daily data quality summary for a given date.

    Given a transactions DataFrame with columns:
        transaction_id, transaction_date, settlement_date, amount_usd,
        interchange_amount_usd, expected_interchange_usd, qualification_status

    Filter to transactions on report_date, then compute:
    - total_transactions: count
    - total_volume: sum of amount_usd
    - null_settlement_rate: fraction of rows where settlement_date is null
    - null_expected_ic_rate: fraction where expected_interchange_usd is null
    - interchange_variance: sum of abs(interchange_amount_usd - expected_interchange_usd)
      for rows where both are non-null
    - downgrade_rate: fraction of transactions with qualification_status = 'downgraded'
    - avg_ticket: mean of amount_usd
    - issues: list of strings for any quality problems:
      - "HIGH_NULL_SETTLEMENT" if null_settlement_rate > 0.10
      - "HIGH_NULL_EXPECTED_IC" if null_expected_ic_rate > 0.20
      - "HIGH_DOWNGRADE_RATE" if downgrade_rate > 0.15
      - "INTERCHANGE_VARIANCE_ALERT" if interchange_variance > 100000

    Return the dict with all above keys. Round floats to 4 decimal places.
    """
    raise NotImplementedError


# ============================================================
# 5. INTERCHANGE CALCULATIONS — Rate Computation & Validation
# ============================================================

def compute_expected_interchange(
    transactions: pd.DataFrame,
    rate_schedule: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compute expected interchange for each transaction using the rate schedule.

    transactions columns:
        transaction_id, amount_usd, interchange_rate_id

    rate_schedule columns:
        rate_id, pct_rate, flat_fee_usd

    Steps:
    1. Left join transactions to rate_schedule on interchange_rate_id = rate_id
    2. Compute: expected_ic = amount_usd * pct_rate + flat_fee_usd
    3. Compute: variance = interchange_amount_usd - expected_ic (if interchange_amount_usd exists)

    Return a copy of transactions with added columns:
        pct_rate, flat_fee_usd, expected_interchange_usd, variance_usd
    """
    raise NotImplementedError


def estimate_rate_change_revenue_impact(
    transactions: pd.DataFrame,
    old_pct_rate: float,
    new_pct_rate: float,
    old_flat_fee: float,
    new_flat_fee: float,
) -> dict:
    """
    Estimate the revenue impact of changing an interchange rate.

    Given a sample of transactions that would be affected (DataFrame with amount_usd),
    compute:
    - old_total_interchange: sum of (amount * old_pct_rate + old_flat_fee)
    - new_total_interchange: sum of (amount * new_pct_rate + new_flat_fee)
    - delta: new - old
    - delta_per_txn: delta / count
    - annualized_delta: delta * (365 / days_in_sample) where days_in_sample is
      computed from the date range in transaction_date column

    Return a dict with all above keys plus txn_count, total_volume, days_in_sample.
    Round all floats to 2 decimal places.
    """
    raise NotImplementedError


def build_compliance_scorecard(
    monthly_summary: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build a composite compliance health score per issuer.

    Given monthly_interchange_summary with columns:
        issuer_id, month_start, qualification_rate, downgrade_rate,
        compliance_case_count, avg_interchange_rate

    For each issuer, compute over the most recent 3 months:
    - avg_qualification_rate
    - avg_downgrade_rate
    - total_case_count
    - rate_trend: (last_month_rate - first_month_rate) in basis points

    Normalize each to 0-1 using min-max across issuers:
    - norm_qual (higher = better)
    - norm_down (lower = better, so invert: 1 - normalized)
    - norm_cases (lower = better, so invert)
    - norm_trend (positive trend = good)

    health_score = 0.30 * norm_qual + 0.25 * (1 - norm_down) + 0.25 * (1 - norm_cases) + 0.20 * norm_trend

    Return a DataFrame with columns:
        issuer_id, avg_qualification_rate, avg_downgrade_rate,
        total_case_count, rate_trend_bps, health_score

    Sorted by health_score descending.
    """
    raise NotImplementedError
