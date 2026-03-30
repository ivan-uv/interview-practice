-- ============================================================
-- Visa SQL Practice — Solutions
-- Senior Analyst, Global Interchange Compliance
-- See schema.md for full table reference
-- ============================================================


-- ============================================================
-- SECTION 1: WARM-UP — Core Interchange Metrics
-- ============================================================

-- 1a. Total interchange by card type and entry mode
-- Straightforward GROUP BY to understand the interchange mix.
SELECT
    card_type,
    entry_mode,
    COUNT(*)                          AS txn_count,
    SUM(amount_usd)                   AS total_volume,
    SUM(interchange_amount_usd)       AS total_interchange,
    ROUND(SUM(interchange_amount_usd) / NULLIF(SUM(amount_usd), 0), 4) AS effective_rate
FROM transactions
GROUP BY 1, 2
ORDER BY total_interchange DESC;


-- 1b. Top 5 merchant categories by total interchange, last 90 days
-- JOIN to merchants for MCC info; ROW_NUMBER to get top 5.
WITH mcc_totals AS (
    SELECT
        m.mcc,
        m.mcc_description,
        COUNT(t.transaction_id)            AS txn_count,
        SUM(t.amount_usd)                  AS total_volume,
        SUM(t.interchange_amount_usd)      AS total_interchange,
        ROW_NUMBER() OVER (ORDER BY SUM(t.interchange_amount_usd) DESC) AS rk
    FROM transactions t
    JOIN merchants m ON t.merchant_id = m.merchant_id
    WHERE t.transaction_date >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY 1, 2
)
SELECT mcc, mcc_description, txn_count, total_volume, total_interchange
FROM mcc_totals
WHERE rk <= 5;


-- 1c. Month-over-month change in average interchange rate per issuer
-- LAG gives us the prior month's rate. Multiply delta by 10000 for basis points.
SELECT
    issuer_id,
    month_start,
    avg_interchange_rate,
    LAG(avg_interchange_rate) OVER (PARTITION BY issuer_id ORDER BY month_start) AS prev_month_rate,
    ROUND(
        (avg_interchange_rate - LAG(avg_interchange_rate) OVER (PARTITION BY issuer_id ORDER BY month_start))
        * 10000, 2
    ) AS rate_change_bps
FROM monthly_interchange_summary
ORDER BY issuer_id, month_start;


-- ============================================================
-- SECTION 2: COMPLIANCE MONITORING
-- ============================================================

-- 2a. Qualification rate by acquirer — flag < 85%
-- Conditional aggregation on qualification_status; join to acquirers for name.
SELECT
    a.acquirer_id,
    a.acquirer_name,
    COUNT(t.transaction_id) AS txn_count,
    ROUND(AVG(CASE WHEN t.qualification_status = 'qualified' THEN 1.0 ELSE 0.0 END), 4) AS qualification_rate,
    CASE
        WHEN AVG(CASE WHEN t.qualification_status = 'qualified' THEN 1.0 ELSE 0.0 END) < 0.85
        THEN true ELSE false
    END AS is_flagged
FROM transactions t
JOIN merchants m ON t.merchant_id = m.merchant_id
JOIN acquirers a ON m.acquirer_id = a.acquirer_id
WHERE t.transaction_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY 1, 2
ORDER BY qualification_rate;


-- 2b. Detect potential duplicate transactions
-- LAG to get the previous transaction for the same card+merchant+amount combo.
-- Then filter where the time gap is < 300 seconds (5 minutes).
WITH ordered_txns AS (
    SELECT
        transaction_id,
        card_number_hash,
        merchant_id,
        amount_usd,
        transaction_date,
        LAG(transaction_date) OVER (
            PARTITION BY card_number_hash, merchant_id, amount_usd
            ORDER BY transaction_date
        ) AS prev_txn_date
    FROM transactions
)
SELECT
    transaction_id,
    card_number_hash,
    merchant_id,
    amount_usd,
    transaction_date,
    prev_txn_date,
    EXTRACT(EPOCH FROM (transaction_date - prev_txn_date)) AS seconds_apart
FROM ordered_txns
WHERE prev_txn_date IS NOT NULL
  AND EXTRACT(EPOCH FROM (transaction_date - prev_txn_date)) < 300
ORDER BY transaction_date DESC;


-- 2c. Durbin compliance check
-- Cap formula: $0.21 + 0.05% of amount + $0.01
-- Only check debit transactions from regulated issuers.
SELECT
    t.transaction_id,
    t.issuer_id,
    t.amount_usd,
    t.interchange_amount_usd,
    ROUND(0.21 + (t.amount_usd * 0.0005) + 0.01, 4) AS durbin_cap,
    CASE
        WHEN t.interchange_amount_usd > (0.21 + (t.amount_usd * 0.0005) + 0.01)
        THEN true ELSE false
    END AS exceeds_cap
FROM transactions t
JOIN issuers i ON t.issuer_id = i.issuer_id
WHERE i.is_durbin_regulated = true
  AND t.card_type IN ('consumer_debit', 'prepaid')
  AND t.interchange_amount_usd > (0.21 + (t.amount_usd * 0.0005) + 0.01)
ORDER BY t.interchange_amount_usd DESC;


-- ============================================================
-- SECTION 3: ANOMALY DETECTION
-- ============================================================

-- 3a. Issuers with interchange rate drop > 5 bps month-over-month
-- Join to issuers for name; LAG for prior month; filter delta < -5 bps.
WITH rate_changes AS (
    SELECT
        s.issuer_id,
        i.issuer_name,
        s.month_start,
        s.avg_interchange_rate,
        LAG(s.avg_interchange_rate) OVER (PARTITION BY s.issuer_id ORDER BY s.month_start) AS prev_rate
    FROM monthly_interchange_summary s
    JOIN issuers i ON s.issuer_id = i.issuer_id
)
SELECT
    issuer_id,
    issuer_name,
    month_start,
    avg_interchange_rate,
    prev_rate,
    ROUND((avg_interchange_rate - prev_rate) * 10000, 2) AS change_bps
FROM rate_changes
WHERE prev_rate IS NOT NULL
  AND (avg_interchange_rate - prev_rate) * 10000 < -5
ORDER BY change_bps;


-- 3b. MCC volume spike per acquirer — current 30d vs. prior 30d, > 30% increase
-- Two CTEs define the two periods, then compare.
WITH prior_period AS (
    SELECT
        m.acquirer_id,
        m.mcc,
        SUM(t.amount_usd) AS prior_volume
    FROM transactions t
    JOIN merchants m ON t.merchant_id = m.merchant_id
    WHERE t.transaction_date BETWEEN CURRENT_DATE - INTERVAL '60 days'
                                AND CURRENT_DATE - INTERVAL '30 days'
    GROUP BY 1, 2
),
current_period AS (
    SELECT
        m.acquirer_id,
        m.mcc,
        SUM(t.amount_usd) AS current_volume
    FROM transactions t
    JOIN merchants m ON t.merchant_id = m.merchant_id
    WHERE t.transaction_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY 1, 2
)
SELECT
    c.acquirer_id,
    c.mcc,
    ROUND(p.prior_volume, 2)   AS prior_volume,
    ROUND(c.current_volume, 2) AS current_volume,
    ROUND((c.current_volume - p.prior_volume) / NULLIF(p.prior_volume, 0) * 100, 1) AS pct_change
FROM current_period c
JOIN prior_period p ON c.acquirer_id = p.acquirer_id AND c.mcc = p.mcc
WHERE (c.current_volume - p.prior_volume) / NULLIF(p.prior_volume, 0) > 0.30
ORDER BY pct_change DESC;


-- 3c. Downgrade rate trend — rolling 4-week average per acquirer
-- First compute weekly downgrade rate, then apply window function.
WITH weekly_downgrades AS (
    SELECT
        m.acquirer_id,
        DATE_TRUNC('week', t.transaction_date) AS week_start,
        COUNT(*) AS total_txns,
        SUM(CASE WHEN t.qualification_status = 'downgraded' THEN 1 ELSE 0 END) AS downgraded_txns,
        ROUND(
            SUM(CASE WHEN t.qualification_status = 'downgraded' THEN 1.0 ELSE 0.0 END) / COUNT(*),
            4
        ) AS weekly_downgrade_rate
    FROM transactions t
    JOIN merchants m ON t.merchant_id = m.merchant_id
    GROUP BY 1, 2
)
SELECT
    acquirer_id,
    week_start,
    weekly_downgrade_rate,
    AVG(weekly_downgrade_rate) OVER (
        PARTITION BY acquirer_id
        ORDER BY week_start
        ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
    ) AS rolling_4wk_avg
FROM weekly_downgrades
ORDER BY acquirer_id, week_start;


-- ============================================================
-- SECTION 4: INCIDENT ANALYSIS
-- ============================================================

-- 4a. Open compliance cases with aging
-- CURRENT_DATE - opened_date gives days open. Filter where closed_date IS NULL.
SELECT
    case_id,
    case_type,
    severity,
    opened_date,
    CURRENT_DATE - opened_date AS days_open,
    financial_impact_usd
FROM compliance_cases
WHERE closed_date IS NULL
ORDER BY
    CASE severity
        WHEN 'critical' THEN 1
        WHEN 'high'     THEN 2
        WHEN 'medium'   THEN 3
        ELSE 4
    END,
    days_open DESC;


-- 4b. Compliance case volume and impact by type, last 12 months
-- Conditional aggregation for open count; AVG resolution days only for closed cases.
SELECT
    case_type,
    COUNT(*) AS case_count,
    SUM(financial_impact_usd) AS total_financial_impact,
    ROUND(AVG(
        CASE WHEN closed_date IS NOT NULL
             THEN closed_date - opened_date
        END
    ), 1) AS avg_resolution_days,
    SUM(CASE WHEN closed_date IS NULL THEN 1 ELSE 0 END) AS open_count
FROM compliance_cases
WHERE opened_date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY 1
ORDER BY total_financial_impact DESC;


-- 4c. Top 5 acquirers by total compliance case financial impact
-- LEFT JOIN because not every case has an acquirer. ROW_NUMBER for top 5.
WITH acquirer_impact AS (
    SELECT
        cc.affected_acquirer_id AS acquirer_id,
        a.acquirer_name,
        COUNT(cc.case_id) AS case_count,
        SUM(cc.financial_impact_usd) AS total_impact,
        ROUND(AVG(cc.financial_impact_usd), 2) AS avg_impact_per_case,
        ROW_NUMBER() OVER (ORDER BY SUM(cc.financial_impact_usd) DESC) AS rk
    FROM compliance_cases cc
    JOIN acquirers a ON cc.affected_acquirer_id = a.acquirer_id
    WHERE cc.affected_acquirer_id IS NOT NULL
    GROUP BY 1, 2
)
SELECT acquirer_id, acquirer_name, case_count, total_impact, avg_impact_per_case
FROM acquirer_impact
WHERE rk <= 5;


-- ============================================================
-- SECTION 5: TRICKY / INTERVIEW-STYLE PROBLEMS
-- ============================================================

-- 5a. Month with highest downgrade rate per issuer (window function approach)
-- RANK instead of ROW_NUMBER so tied peak months both appear.
WITH ranked_months AS (
    SELECT
        issuer_id,
        month_start,
        downgrade_rate,
        RANK() OVER (PARTITION BY issuer_id ORDER BY downgrade_rate DESC) AS rk
    FROM monthly_interchange_summary
)
SELECT issuer_id, month_start, downgrade_rate
FROM ranked_months
WHERE rk = 1;


-- 5b. Interchange variance analysis by acquirer
-- Overpayment = actual > expected; underpayment = actual < expected.
-- Pct accuracy = 1 - (abs(net_variance) / total_expected).
SELECT
    m.acquirer_id,
    COUNT(t.transaction_id) AS txn_count,
    ROUND(SUM(CASE WHEN t.interchange_amount_usd > t.expected_interchange_usd
              THEN t.interchange_amount_usd - t.expected_interchange_usd ELSE 0 END), 2) AS total_overpayment,
    ROUND(SUM(CASE WHEN t.interchange_amount_usd < t.expected_interchange_usd
              THEN t.expected_interchange_usd - t.interchange_amount_usd ELSE 0 END), 2) AS total_underpayment,
    ROUND(SUM(t.interchange_amount_usd - t.expected_interchange_usd), 2) AS net_variance,
    ROUND(
        1.0 - ABS(SUM(t.interchange_amount_usd - t.expected_interchange_usd))
            / NULLIF(SUM(t.expected_interchange_usd), 0),
        4
    ) AS pct_accuracy
FROM transactions t
JOIN merchants m ON t.merchant_id = m.merchant_id
WHERE t.expected_interchange_usd IS NOT NULL
GROUP BY 1
ORDER BY ABS(net_variance) DESC;


-- 5c. Merchant MCC consistency check — z-score on avg ticket vs. MCC group
-- Window functions compute MCC-level stats, then z-score per merchant.
WITH merchant_stats AS (
    SELECT
        m.merchant_id,
        m.merchant_name,
        m.mcc,
        m.mcc_description,
        AVG(t.amount_usd) AS avg_ticket
    FROM transactions t
    JOIN merchants m ON t.merchant_id = m.merchant_id
    WHERE t.transaction_date >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY 1, 2, 3, 4
    HAVING COUNT(*) >= 30  -- minimum sample for meaningful stats
),
mcc_stats AS (
    SELECT
        *,
        AVG(avg_ticket) OVER (PARTITION BY mcc) AS mcc_avg_ticket,
        STDDEV(avg_ticket) OVER (PARTITION BY mcc) AS mcc_std_ticket
    FROM merchant_stats
)
SELECT
    merchant_id,
    merchant_name,
    mcc,
    mcc_description,
    ROUND(avg_ticket, 2) AS avg_ticket,
    ROUND(mcc_avg_ticket, 2) AS mcc_avg_ticket,
    ROUND(mcc_std_ticket, 2) AS mcc_std_ticket,
    ROUND((avg_ticket - mcc_avg_ticket) / NULLIF(mcc_std_ticket, 0), 2) AS z_score
FROM mcc_stats
WHERE ABS((avg_ticket - mcc_avg_ticket) / NULLIF(mcc_std_ticket, 0)) > 2.0
ORDER BY ABS((avg_ticket - mcc_avg_ticket) / NULLIF(mcc_std_ticket, 0)) DESC;


-- ============================================================
-- SECTION 6: VISA-SPECIFIC SCENARIOS
-- ============================================================

-- 6a. Rate change impact analysis
-- Compare 30 days pre vs. post a rate change for each rate_id.
-- Self-join interchange_rates to find rates that changed on '2024-04-01'.
WITH rate_changes AS (
    SELECT rate_id, rate_name
    FROM interchange_rates
    WHERE effective_date = '2024-04-01'
),
pre_post AS (
    SELECT
        t.interchange_rate_id AS rate_id,
        CASE
            WHEN t.transaction_date < '2024-04-01' THEN 'pre'
            ELSE 'post'
        END AS period,
        COUNT(*) AS txn_count,
        SUM(t.interchange_amount_usd) AS total_interchange
    FROM transactions t
    WHERE t.interchange_rate_id IN (SELECT rate_id FROM rate_changes)
      AND t.transaction_date BETWEEN '2024-03-02' AND '2024-04-30'
    GROUP BY 1, 2
)
SELECT
    rc.rate_id,
    rc.rate_name,
    MAX(CASE WHEN pp.period = 'pre'  THEN pp.txn_count END)          AS pre_txn_count,
    MAX(CASE WHEN pp.period = 'post' THEN pp.txn_count END)          AS post_txn_count,
    MAX(CASE WHEN pp.period = 'pre'  THEN pp.total_interchange END)  AS pre_interchange,
    MAX(CASE WHEN pp.period = 'post' THEN pp.total_interchange END)  AS post_interchange,
    ROUND(
        MAX(CASE WHEN pp.period = 'post' THEN pp.total_interchange END)
        - MAX(CASE WHEN pp.period = 'pre' THEN pp.total_interchange END),
        2
    ) AS interchange_delta
FROM rate_changes rc
JOIN pre_post pp ON rc.rate_id = pp.rate_id
GROUP BY 1, 2
ORDER BY interchange_delta DESC;


-- 6b. Debit routing network distribution
-- Percentage of debit volume by network, split by regulated/exempt.
-- This is critical for Durbin routing compliance.
WITH debit_txns AS (
    SELECT
        t.is_regulated,
        t.network_id,
        COUNT(*) AS txn_count,
        SUM(t.amount_usd) AS total_volume
    FROM transactions t
    WHERE t.card_type IN ('consumer_debit', 'prepaid')
    GROUP BY 1, 2
),
debit_totals AS (
    SELECT
        is_regulated,
        SUM(total_volume) AS segment_volume
    FROM debit_txns
    GROUP BY 1
)
SELECT
    d.is_regulated,
    d.network_id,
    d.txn_count,
    d.total_volume,
    ROUND(d.total_volume / NULLIF(dt.segment_volume, 0), 4) AS pct_of_debit_volume
FROM debit_txns d
JOIN debit_totals dt ON d.is_regulated = dt.is_regulated
ORDER BY d.is_regulated, d.total_volume DESC;


-- 6c. Acquirer data quality scorecard
-- Multiple subqueries compute each dimension, then normalize with MIN/MAX windows.
WITH acquirer_metrics AS (
    SELECT
        m.acquirer_id,
        a.acquirer_name,
        -- Qualification rate
        AVG(CASE WHEN t.qualification_status = 'qualified' THEN 1.0 ELSE 0.0 END) AS qualification_rate,
        -- Downgrade rate
        AVG(CASE WHEN t.qualification_status = 'downgraded' THEN 1.0 ELSE 0.0 END) AS downgrade_rate,
        -- Avg settlement delay
        AVG(CASE WHEN t.settlement_date IS NOT NULL
            THEN t.settlement_date - t.transaction_date::date
        END) AS avg_settlement_delay
    FROM transactions t
    JOIN merchants m ON t.merchant_id = m.merchant_id
    JOIN acquirers a ON m.acquirer_id = a.acquirer_id
    WHERE t.transaction_date >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY 1, 2
),
dup_rates AS (
    SELECT
        m.acquirer_id,
        COUNT(*) AS total_txns,
        SUM(CASE WHEN seconds_apart < 300 THEN 1 ELSE 0 END) AS dup_count
    FROM (
        SELECT
            t.merchant_id,
            EXTRACT(EPOCH FROM (
                t.transaction_date - LAG(t.transaction_date) OVER (
                    PARTITION BY t.card_number_hash, t.merchant_id, t.amount_usd
                    ORDER BY t.transaction_date
                )
            )) AS seconds_apart
        FROM transactions t
        WHERE t.transaction_date >= CURRENT_DATE - INTERVAL '90 days'
    ) sub
    JOIN merchants m ON sub.merchant_id = m.merchant_id
    GROUP BY 1
),
combined AS (
    SELECT
        am.*,
        COALESCE(dr.dup_count * 1.0 / NULLIF(dr.total_txns, 0), 0) AS duplicate_rate
    FROM acquirer_metrics am
    LEFT JOIN dup_rates dr ON am.acquirer_id = dr.acquirer_id
),
with_bounds AS (
    SELECT
        *,
        MIN(qualification_rate)    OVER () AS min_qual,  MAX(qualification_rate)    OVER () AS max_qual,
        MIN(downgrade_rate)        OVER () AS min_down,  MAX(downgrade_rate)        OVER () AS max_down,
        MIN(avg_settlement_delay)  OVER () AS min_delay, MAX(avg_settlement_delay)  OVER () AS max_delay,
        MIN(duplicate_rate)        OVER () AS min_dup,   MAX(duplicate_rate)        OVER () AS max_dup
    FROM combined
),
normalized AS (
    SELECT
        acquirer_id,
        acquirer_name,
        ROUND(qualification_rate, 4) AS qualification_rate,
        ROUND(downgrade_rate, 4)     AS downgrade_rate,
        ROUND(avg_settlement_delay, 2) AS avg_settlement_delay,
        ROUND(duplicate_rate, 6)     AS duplicate_rate,
        (qualification_rate - min_qual) / NULLIF(max_qual - min_qual, 0) AS norm_qual,
        (downgrade_rate - min_down) / NULLIF(max_down - min_down, 0)     AS norm_down,
        (avg_settlement_delay - min_delay) / NULLIF(max_delay - min_delay, 0) AS norm_delay,
        (duplicate_rate - min_dup) / NULLIF(max_dup - min_dup, 0)        AS norm_dup
    FROM with_bounds
)
SELECT
    acquirer_id,
    acquirer_name,
    qualification_rate,
    downgrade_rate,
    avg_settlement_delay,
    duplicate_rate,
    ROUND(
        (0.30 * COALESCE(norm_qual, 0))
        + (0.25 * (1 - COALESCE(norm_down, 0)))
        + (0.25 * (1 - COALESCE(norm_delay, 0)))
        + (0.20 * (1 - COALESCE(norm_dup, 0))),
        4
    ) AS health_score
FROM normalized
ORDER BY health_score DESC;


-- 6d. Interchange revenue leakage estimation
-- For downgraded transactions, estimate what interchange would have been
-- if they had qualified. Use the rate schedule to compute the delta.
WITH downgraded AS (
    SELECT
        m.acquirer_id,
        t.card_type,
        t.transaction_id,
        t.amount_usd,
        t.interchange_amount_usd AS actual_interchange,
        -- Estimate qualified interchange using the transaction's rate
        (t.amount_usd * ir.pct_rate + ir.flat_fee_usd) AS estimated_qualified_interchange
    FROM transactions t
    JOIN merchants m ON t.merchant_id = m.merchant_id
    JOIN interchange_rates ir ON t.interchange_rate_id = ir.rate_id
    WHERE t.qualification_status = 'downgraded'
)
SELECT
    acquirer_id,
    card_type,
    COUNT(*) AS downgraded_txn_count,
    ROUND(SUM(amount_usd), 2) AS total_volume,
    ROUND(SUM(actual_interchange), 2) AS actual_interchange,
    ROUND(SUM(estimated_qualified_interchange), 2) AS estimated_qualified_interchange,
    ROUND(SUM(actual_interchange - estimated_qualified_interchange), 2) AS leakage_usd
FROM downgraded
GROUP BY 1, 2
ORDER BY leakage_usd DESC;


-- 6e. Multi-dimensional compliance alert
-- UNION ALL three separate alert queries, each with its own threshold.
WITH latest_month AS (
    SELECT MAX(month_start) AS max_month FROM monthly_interchange_summary
),

-- Alert 1: Low qualification rate
low_qual AS (
    SELECT
        s.issuer_id,
        i.issuer_name,
        'low_qualification_rate' AS alert_type,
        s.qualification_rate AS metric_value,
        0.85 AS threshold
    FROM monthly_interchange_summary s
    JOIN issuers i ON s.issuer_id = i.issuer_id
    CROSS JOIN latest_month lm
    WHERE s.month_start = lm.max_month
      AND s.qualification_rate < 0.85
),

-- Alert 2: Downgrade rate spike > 3 percentage points MoM
downgrade_spike AS (
    SELECT
        s.issuer_id,
        i.issuer_name,
        'downgrade_rate_spike' AS alert_type,
        ROUND((s.downgrade_rate - LAG(s.downgrade_rate) OVER (
            PARTITION BY s.issuer_id ORDER BY s.month_start
        )) * 100, 2) AS metric_value,
        3.0 AS threshold
    FROM monthly_interchange_summary s
    JOIN issuers i ON s.issuer_id = i.issuer_id
),

-- Alert 3: High compliance case impact in last 90 days
high_case_impact AS (
    SELECT
        cc.affected_issuer_id AS issuer_id,
        i.issuer_name,
        'high_case_impact' AS alert_type,
        SUM(cc.financial_impact_usd) AS metric_value,
        200000 AS threshold
    FROM compliance_cases cc
    JOIN issuers i ON cc.affected_issuer_id = i.issuer_id
    WHERE cc.opened_date >= CURRENT_DATE - INTERVAL '90 days'
      AND cc.affected_issuer_id IS NOT NULL
    GROUP BY 1, 2
    HAVING SUM(cc.financial_impact_usd) > 200000
)

SELECT * FROM low_qual
UNION ALL
SELECT * FROM (
    SELECT * FROM downgrade_spike
    WHERE metric_value > 3.0
) ds
UNION ALL
SELECT * FROM high_case_impact
ORDER BY issuer_id, alert_type;
