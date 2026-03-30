-- ============================================================
-- Visa SQL Practice — Questions
-- Senior Analyst, Global Interchange Compliance
-- See schema.md for full table reference
-- Solutions in solutions.sql
-- ============================================================


-- ============================================================
-- SAMPLE DATA (for reference while solving)
-- ============================================================

-- issuers
-- issuer_id   | issuer_name          | country_code | total_assets_usd   | is_durbin_regulated | primary_network
-- iss_001     | Chase                | US           | 3900000000000      | true                | visa
-- iss_002     | Bank of America      | US           | 3100000000000      | true                | visa
-- iss_003     | Navy Federal CU      | US           | 170000000000       | true                | interlink
-- iss_004     | First Community Bank | US           | 8500000000         | false               | star

-- acquirers
-- acquirer_id | acquirer_name | country_code | total_merchants
-- acq_001     | Worldpay      | US           | 45000
-- acq_002     | Fiserv        | US           | 38000
-- acq_003     | Adyen         | NL           | 12000

-- merchants
-- merchant_id  | merchant_name         | mcc  | mcc_description    | acquirer_id | country_code | state_code | registration_date | is_high_risk
-- mch_001      | Walmart #4532         | 5411 | Grocery Stores     | acq_001     | US           | TX         | 2018-03-15        | false
-- mch_002      | Shell Station #891    | 5541 | Service Stations   | acq_001     | US           | CA         | 2019-07-22        | false
-- mch_003      | Joe's Pizza           | 5812 | Eating Places      | acq_002     | US           | NY         | 2021-01-10        | false
-- mch_004      | TechGadgets.com       | 5999 | Misc Retail        | acq_003     | US           | NULL       | 2022-06-01        | false

-- interchange_rates
-- rate_id   | rate_name              | card_type       | mcc_group      | entry_mode_group  | pct_rate | flat_fee_usd | effective_date | end_date   | is_regulated
-- rt_001    | CPS/Supermarket        | consumer_credit | grocery        | card_present      | 0.0122   | 0.05         | 2024-04-01     | NULL       | false
-- rt_002    | CPS/Retail 2           | consumer_credit | general_retail | card_present      | 0.0165   | 0.10         | 2024-04-01     | NULL       | false
-- rt_003    | Regulated Debit        | consumer_debit  | all            | any               | 0.0005   | 0.22         | 2024-04-01     | NULL       | true
-- rt_004    | CPS/E-Commerce Basic   | consumer_credit | ecommerce      | card_not_present  | 0.0195   | 0.10         | 2024-04-01     | NULL       | false

-- transactions (sample)
-- transaction_id | card_number_hash | issuer_id | acquirer_id | merchant_id | transaction_date        | settlement_date | amount_usd | card_type       | entry_mode   | is_regulated | interchange_rate_id | interchange_amount_usd | expected_interchange_usd | qualification_status | network_id
-- txn_000001     | hash_aaa         | iss_001   | acq_001     | mch_001     | 2024-06-15 14:23:11     | 2024-06-16      | 47.50      | consumer_credit | chip         | false        | rt_001              | 0.6295                 | 0.6295                   | qualified            | visa
-- txn_000002     | hash_bbb         | iss_004   | acq_002     | mch_003     | 2024-06-15 18:05:33     | 2024-06-16      | 32.00      | consumer_debit  | contactless  | false        | rt_003              | 0.2360                 | 0.1280                   | qualified            | star
--   → iss_004 is exempt (assets < $10B), so Durbin cap should NOT apply, but is_regulated = false and rate_id = rt_003 (regulated rate) — data quality issue
-- txn_000003     | hash_ccc         | iss_001   | acq_003     | mch_004     | 2024-06-15 22:10:00     | NULL            | 89.99      | consumer_credit | ecommerce    | false        | rt_004              | 1.8548                 | 1.8548                   | downgraded           | visa
-- txn_000004     | hash_aaa         | iss_001   | acq_001     | mch_001     | 2024-06-15 14:25:30     | 2024-06-16      | 47.50      | consumer_credit | chip         | false        | rt_001              | 0.6295                 | 0.6295                   | qualified            | visa
--   → txn_000004 is a potential duplicate of txn_000001 (same card, merchant, amount, 2 min apart)

-- compliance_cases
-- case_id  | case_type           | opened_date | closed_date | severity | affected_issuer_id | affected_acquirer_id | affected_merchant_id | transaction_count | financial_impact_usd | root_cause               | resolution              | analyst_id
-- cc_001   | misclassification   | 2024-05-10  | 2024-05-22  | high     | NULL               | acq_001              | mch_003              | 15000             | 180000               | Wrong MCC assigned       | MCC corrected to 5812   | analyst_a
-- cc_002   | durbin_violation    | 2024-06-01  | NULL        | critical | iss_001            | NULL                 | NULL                 | 230000            | 450000               | Cap exceeded on batch    | Under investigation     | analyst_b
-- cc_003   | downgrade_anomaly   | 2024-06-05  | 2024-06-08  | medium   | NULL               | acq_003              | NULL                 | 8000              | 45000                | Missing AVS data         | Acquirer fixed gateway   | analyst_a

-- monthly_interchange_summary
-- issuer_id | month_start | transaction_count | total_volume_usd | total_interchange_usd | avg_interchange_rate | qualification_rate | downgrade_rate | compliance_case_count
-- iss_001   | 2024-04-01  | 45000000          | 4050000000       | 72900000              | 0.0180               | 0.91               | 0.07           | 2
-- iss_001   | 2024-05-01  | 47000000          | 4230000000       | 74070000              | 0.0175               | 0.89               | 0.09           | 3
-- iss_002   | 2024-04-01  | 38000000          | 3420000000       | 58140000              | 0.0170               | 0.93               | 0.05           | 1
-- iss_003   | 2024-04-01  | 12000000          | 480000000        | 2880000               | 0.0060               | 0.95               | 0.03           | 0
--   → iss_001 qualification rate trending down (0.91 → 0.89), downgrade rate trending up (0.07 → 0.09)


-- ============================================================
-- SECTION 1: WARM-UP — Core Interchange Metrics
-- ============================================================

-- 1a. Total interchange by card type and entry mode
-- Expected output: card_type | entry_mode | txn_count | total_volume | total_interchange | effective_rate


-- YOUR QUERY HERE


-- ---------------------------------------------------------------

-- 1b. Top 5 merchant categories (MCC) by total interchange volume, last 90 days
-- Expected output: mcc | mcc_description | txn_count | total_volume | total_interchange
-- Hint: join transactions to merchants


-- YOUR QUERY HERE


-- ---------------------------------------------------------------

-- 1c. Month-over-month change in average interchange rate per issuer
-- Expected output: issuer_id | month_start | avg_interchange_rate | prev_month_rate | rate_change_bps
-- Hint: use LAG and multiply by 10000 to convert to basis points


-- YOUR QUERY HERE


-- ============================================================
-- SECTION 2: COMPLIANCE MONITORING
-- ============================================================

-- 2a. Qualification rate by acquirer — flag acquirers where qualification < 85%
-- Expected output: acquirer_id | acquirer_name | txn_count | qualification_rate | is_flagged


-- YOUR QUERY HERE


-- ---------------------------------------------------------------

-- 2b. Detect potential duplicate transactions
-- Duplicates = same card_number_hash, same merchant_id, same amount_usd, within 5 minutes
-- Expected output: transaction_id | card_number_hash | merchant_id | amount_usd | transaction_date | prev_txn_date | seconds_apart


-- YOUR QUERY HERE


-- ---------------------------------------------------------------

-- 2c. Durbin compliance check
-- For regulated issuers (is_durbin_regulated = true), verify that debit interchange
-- does not exceed the cap: $0.21 + 0.05% of amount + $0.01
-- Expected output: transaction_id | issuer_id | amount_usd | interchange_amount_usd | durbin_cap | exceeds_cap


-- YOUR QUERY HERE


-- ============================================================
-- SECTION 3: ANOMALY DETECTION
-- ============================================================

-- 3a. Issuers with interchange rate drop > 5 basis points month-over-month
-- These need investigation — could indicate misclassification or system error
-- Expected output: issuer_id | issuer_name | month_start | avg_interchange_rate | prev_rate | change_bps


-- YOUR QUERY HERE


-- ---------------------------------------------------------------

-- 3b. MCC volume spike detection per acquirer
-- Compare current 30-day volume by MCC to prior 30-day volume
-- Flag any acquirer x MCC combo where volume increased > 30%
-- Expected output: acquirer_id | mcc | prior_volume | current_volume | pct_change


-- YOUR QUERY HERE


-- ---------------------------------------------------------------

-- 3c. Downgrade rate trend — rolling 4-week average per acquirer
-- Expected output: acquirer_id | week_start | weekly_downgrade_rate | rolling_4wk_avg


-- YOUR QUERY HERE


-- ============================================================
-- SECTION 4: INCIDENT ANALYSIS
-- ============================================================

-- 4a. Open compliance cases by severity with aging
-- Days open = CURRENT_DATE - opened_date for open cases
-- Expected output: case_id | case_type | severity | opened_date | days_open | financial_impact_usd


-- YOUR QUERY HERE


-- ---------------------------------------------------------------

-- 4b. Compliance case volume and impact by type, last 12 months
-- Expected output: case_type | case_count | total_financial_impact | avg_resolution_days | open_count


-- YOUR QUERY HERE


-- ---------------------------------------------------------------

-- 4c. Top 5 acquirers by total compliance case financial impact
-- Include both open and closed cases
-- Expected output: acquirer_id | acquirer_name | case_count | total_impact | avg_impact_per_case


-- YOUR QUERY HERE


-- ============================================================
-- SECTION 5: TRICKY / INTERVIEW-STYLE PROBLEMS
-- ============================================================

-- 5a. For each issuer, find the month with the highest downgrade rate
-- Constraint: use window functions, not GROUP BY + MAX subquery


-- YOUR QUERY HERE


-- ---------------------------------------------------------------

-- 5b. Interchange variance analysis
-- For each transaction where expected_interchange_usd is not null,
-- compute the variance (actual - expected). Aggregate by acquirer:
-- total_overpayment, total_underpayment, net_variance, pct_accuracy
-- Expected output: acquirer_id | txn_count | total_overpayment | total_underpayment | net_variance | pct_accuracy


-- YOUR QUERY HERE


-- ---------------------------------------------------------------

-- 5c. Merchant MCC consistency check
-- Find merchants whose average transaction amount is more than 2 standard
-- deviations from the mean for their MCC group.
-- These are candidates for MCC misclassification review.
-- Expected output: merchant_id | merchant_name | mcc | mcc_description | avg_ticket | mcc_avg_ticket | mcc_std_ticket | z_score


-- YOUR QUERY HERE


-- ============================================================
-- SECTION 6: VISA-SPECIFIC SCENARIOS
-- ============================================================

-- 6a. Rate change impact analysis
-- Given a rate effective_date of '2024-04-01', compare 30 days before vs. 30 days after
-- for each rate_id that changed. Show volume shift and interchange impact.
-- Expected output: rate_id | rate_name | pre_txn_count | post_txn_count | pre_interchange | post_interchange | interchange_delta


-- YOUR QUERY HERE


-- ---------------------------------------------------------------

-- 6b. Debit routing network distribution
-- For debit transactions, show the distribution across routing networks
-- (visa, interlink, star, nyce, etc.) by regulated vs. exempt
-- This relates to Durbin routing requirements
-- Expected output: is_regulated | network_id | txn_count | total_volume | pct_of_debit_volume


-- YOUR QUERY HERE


-- ---------------------------------------------------------------

-- 6c. Acquirer data quality scorecard
-- Score each acquirer on multiple compliance dimensions:
--   qualification_rate (higher = better)
--   downgrade_rate (lower = better)
--   avg_settlement_delay_days (lower = better)
--   duplicate_rate (lower = better — use the duplicate logic from 2b)
-- Normalize each to 0-1 using MIN/MAX, compute composite:
--   health_score = (0.30 * norm_qual) + (0.25 * (1 - norm_downgrade)) + (0.25 * (1 - norm_delay)) + (0.20 * (1 - norm_dup))
-- Expected output: acquirer_id | acquirer_name | qualification_rate | downgrade_rate | avg_settlement_delay | duplicate_rate | health_score


-- YOUR QUERY HERE


-- ---------------------------------------------------------------

-- 6d. Interchange revenue leakage estimation
-- For transactions that were downgraded, estimate how much interchange was
-- "leaked" — the difference between what the transaction would have earned
-- at its qualified rate vs. what was actually paid.
-- Group by acquirer and card_type.
-- Expected output: acquirer_id | card_type | downgraded_txn_count | total_volume | actual_interchange | estimated_qualified_interchange | leakage_usd


-- YOUR QUERY HERE


-- ---------------------------------------------------------------

-- 6e. Multi-dimensional compliance alert
-- Build a single query that flags issuers meeting ANY of these conditions:
--   1. Qualification rate < 85% in the most recent month
--   2. Downgrade rate increased > 3 percentage points month-over-month
--   3. Total compliance case financial impact > $200K in the last 90 days
-- Expected output: issuer_id | issuer_name | alert_type | metric_value | threshold


-- YOUR QUERY HERE
