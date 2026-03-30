# Case Study: Investigating an Interchange Misclassification Anomaly

**Scenario**: Your automated monitoring flags that a major acquirer (Worldpay) has seen a 40% spike in "Grocery" (MCC 5411) interchange volume over the past 30 days, while their overall transaction count is flat. The Interchange Strategy team asks you to investigate — this could mean merchants are being misclassified to receive lower grocery interchange rates, costing issuers millions in lost interchange revenue.

---

## Step 1: Clarify the Business Question

Before touching data, ask:
- What is the normal variance in MCC-level volume for this acquirer? Is 40% outside the expected range?
- Did any rate changes go into effect recently that might incentivize reclassification?
- Is this concentrated in a specific geography, merchant size, or card type?
- What's the financial exposure? Grocery interchange is typically 20-40 bps lower than general retail — if $500M in non-grocery transactions are being classified as grocery, that's $1-2M in lost interchange per month.

**Primary concern**: Merchants reclassified from higher-rate MCCs (e.g., 5999 General Retail, 5812 Eating Places) to lower-rate MCCs (5411 Grocery) to reduce their interchange cost.

**Secondary concerns**:
- Legitimate business changes (new grocery merchants onboarded by Worldpay)
- MCC assignment errors during merchant boarding
- Systemic mapping issue after a platform migration

---

## Step 2: Design the Investigation

### Phase 1: Scope the anomaly

```sql
-- Compare MCC 5411 volume for Worldpay: last 30 days vs. prior 30 days
WITH periods AS (
    SELECT
        CASE
            WHEN transaction_date >= CURRENT_DATE - INTERVAL '30 days' THEN 'current'
            ELSE 'prior'
        END AS period,
        COUNT(*) AS txn_count,
        SUM(amount_usd) AS total_volume,
        SUM(interchange_amount_usd) AS total_interchange
    FROM transactions t
    JOIN merchants m ON t.merchant_id = m.merchant_id
    WHERE m.acquirer_id = 'acq_worldpay'
      AND m.mcc = '5411'
      AND transaction_date >= CURRENT_DATE - INTERVAL '60 days'
    GROUP BY 1
)
SELECT
    period,
    txn_count,
    total_volume,
    total_interchange,
    total_interchange / NULLIF(total_volume, 0) AS effective_rate
FROM periods
ORDER BY period;
```

### Phase 2: Identify which merchants are driving the spike

```sql
-- Merchants classified as MCC 5411 with the largest volume increase
WITH merchant_volume AS (
    SELECT
        m.merchant_id,
        m.merchant_name,
        m.registration_date,
        SUM(CASE WHEN t.transaction_date >= CURRENT_DATE - INTERVAL '30 days'
            THEN t.amount_usd ELSE 0 END) AS current_volume,
        SUM(CASE WHEN t.transaction_date < CURRENT_DATE - INTERVAL '30 days'
            THEN t.amount_usd ELSE 0 END) AS prior_volume
    FROM transactions t
    JOIN merchants m ON t.merchant_id = m.merchant_id
    WHERE m.acquirer_id = 'acq_worldpay'
      AND m.mcc = '5411'
      AND t.transaction_date >= CURRENT_DATE - INTERVAL '60 days'
    GROUP BY 1, 2, 3
)
SELECT
    merchant_id,
    merchant_name,
    registration_date,
    prior_volume,
    current_volume,
    current_volume - prior_volume AS volume_delta,
    CASE WHEN prior_volume = 0 THEN 'NEW' ELSE
        ROUND((current_volume - prior_volume) / prior_volume * 100, 1) || '%'
    END AS pct_change
FROM merchant_volume
WHERE current_volume > prior_volume
ORDER BY volume_delta DESC
LIMIT 50;
```

### Phase 3: Cross-reference with merchant characteristics

```sql
-- Do these merchants look like groceries? Check avg transaction amount.
-- Groceries: avg ticket ~$35-50. Restaurants: ~$25-40. General retail: $50-150.
-- If "grocery" merchants have avg tickets of $80+, that's a red flag.
SELECT
    m.merchant_id,
    m.merchant_name,
    m.mcc,
    COUNT(t.transaction_id) AS txn_count,
    AVG(t.amount_usd) AS avg_ticket,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY t.amount_usd) AS median_ticket,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY t.amount_usd) AS p95_ticket,
    AVG(CASE WHEN t.entry_mode = 'ecommerce' THEN 1.0 ELSE 0.0 END) AS ecommerce_pct
FROM transactions t
JOIN merchants m ON t.merchant_id = m.merchant_id
WHERE m.acquirer_id = 'acq_worldpay'
  AND m.mcc = '5411'
  AND t.transaction_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY 1, 2, 3
HAVING AVG(t.amount_usd) > 70  -- flag merchants with non-grocery transaction patterns
ORDER BY txn_count DESC;
```

---

## Step 3: Quantify the Financial Impact

```python
import pandas as pd
import numpy as np

# Load the suspect merchants identified in Phase 2/3
suspect_merchants = pd.read_csv("suspect_grocery_merchants.csv")
transactions = pd.read_csv("suspect_transactions.csv")

# Calculate interchange difference: what they paid (grocery rate) vs. what
# they should have paid (their likely true MCC rate)
GROCERY_RATE = 0.0122 + 0.05     # 1.22% + $0.05 (CPS/Supermarket)
RETAIL_RATE  = 0.0165 + 0.10     # 1.65% + $0.10 (CPS/Retail 2)

transactions["paid_interchange"] = (
    transactions["amount_usd"] * GROCERY_RATE
)
transactions["correct_interchange"] = (
    transactions["amount_usd"] * RETAIL_RATE
)
transactions["interchange_gap"] = (
    transactions["correct_interchange"] - transactions["paid_interchange"]
)

# Aggregate impact
impact = transactions.groupby("merchant_id").agg(
    txn_count=("transaction_id", "count"),
    total_volume=("amount_usd", "sum"),
    total_gap=("interchange_gap", "sum"),
).reset_index()

total_impact = impact["total_gap"].sum()
print(f"Total estimated interchange shortfall: ${total_impact:,.2f}")
print(f"Affected merchants: {len(impact)}")
print(f"Affected transactions: {impact['txn_count'].sum():,}")
```

---

## Step 4: Classify Root Cause

After investigation, categorize findings:

| Category | Count | Financial Impact | Action |
|----------|-------|-----------------|--------|
| **Misclassified merchants** (non-grocery operating as MCC 5411) | 47 merchants | $1.8M/month | Escalate to acquirer for MCC correction |
| **Newly onboarded legitimate groceries** | 12 merchants | N/A — correct classification | No action needed |
| **Platform migration mapping error** | 83 merchants | $340K/month | Work with acquirer tech team to fix mapping |
| **Intentional gaming** (suspect) | 3 merchants | $220K/month | Escalate to compliance/legal |

---

## Step 5: Build the Incident Report

### Documentation Structure
1. **Executive Summary** (1 paragraph): What happened, financial impact, recommended actions
2. **Detection**: How the anomaly was identified (automated monitoring, KPI dashboard)
3. **Investigation Timeline**: Steps taken, data examined, parties consulted
4. **Root Cause Analysis**: Clear categorization of why the anomaly occurred
5. **Financial Impact**: Total, by category, projected annualized exposure
6. **Remediation Plan**: Specific actions, owners, timelines
7. **Prevention**: What monitoring should be added to catch this earlier next time

### Executive Summary Example

> Between March 1-29, 2026, automated monitoring detected a 40% increase in MCC 5411 (Grocery) interchange volume for Worldpay without a corresponding increase in overall transaction count. Investigation identified 130 merchants misclassified under MCC 5411, resulting in an estimated $2.36M/month ($28.3M annualized) in interchange shortfall to issuers. Root causes include 47 merchants with incorrect MCC assignments, 83 merchants affected by a platform migration mapping error, and 3 merchants flagged for potential intentional misclassification. Recommended actions: (1) Worldpay to correct all MCC assignments within 15 business days, (2) retroactive interchange adjustment for the affected 30-day period, (3) enhanced automated monitoring for MCC migration patterns.

---

## Step 6: Design Prevention

### Automated Monitoring Query

```sql
-- Alert: MCC-level volume spike detection
-- Run daily, flag any acquirer x MCC combo where current 7-day volume
-- exceeds prior 30-day weekly average by more than 2 standard deviations
WITH weekly_baseline AS (
    SELECT
        m.acquirer_id,
        m.mcc,
        DATE_TRUNC('week', t.transaction_date) AS week_start,
        COUNT(*) AS weekly_txn_count,
        SUM(t.amount_usd) AS weekly_volume
    FROM transactions t
    JOIN merchants m ON t.merchant_id = m.merchant_id
    WHERE t.transaction_date BETWEEN CURRENT_DATE - INTERVAL '37 days'
                                AND CURRENT_DATE - INTERVAL '7 days'
    GROUP BY 1, 2, 3
),
baseline_stats AS (
    SELECT
        acquirer_id,
        mcc,
        AVG(weekly_txn_count) AS avg_weekly_count,
        STDDEV(weekly_txn_count) AS std_weekly_count,
        AVG(weekly_volume) AS avg_weekly_volume
    FROM weekly_baseline
    GROUP BY 1, 2
),
current_week AS (
    SELECT
        m.acquirer_id,
        m.mcc,
        COUNT(*) AS current_count,
        SUM(t.amount_usd) AS current_volume
    FROM transactions t
    JOIN merchants m ON t.merchant_id = m.merchant_id
    WHERE t.transaction_date >= CURRENT_DATE - INTERVAL '7 days'
    GROUP BY 1, 2
)
SELECT
    c.acquirer_id,
    c.mcc,
    b.avg_weekly_count,
    c.current_count,
    ROUND((c.current_count - b.avg_weekly_count) / NULLIF(b.std_weekly_count, 0), 2) AS z_score,
    c.current_volume - b.avg_weekly_volume AS volume_delta_usd
FROM current_week c
JOIN baseline_stats b
    ON c.acquirer_id = b.acquirer_id AND c.mcc = b.mcc
WHERE (c.current_count - b.avg_weekly_count) / NULLIF(b.std_weekly_count, 0) > 2.0
ORDER BY volume_delta_usd DESC;
```

---

## Potential Interview Objections & Responses

**"How do you know the MCC is wrong? Maybe these really are grocery stores."**
Check the transaction pattern. Grocery stores have consistent avg ticket sizes ($35-50), high card-present rates, and regular weekday patterns. If a "grocery" merchant has $80+ avg tickets, 60% e-commerce, and no weekend volume, it's likely misclassified.

**"Isn't this the acquirer's problem, not ours?"**
Visa sets the interchange rates and has a responsibility to ensure its network operates fairly. If issuers are systematically receiving less interchange due to misclassification, it undermines trust in the network. Additionally, Visa's own compliance programs require MCC accuracy.

**"How do you scale this? You can't manually review every merchant."**
Exactly — that's why automated monitoring matters. Build statistical baselines per acquirer x MCC, alert on deviations, and focus manual investigation on the flagged cases. The SQL above runs daily in an Airflow DAG and feeds a Power BI dashboard.

**"What if the acquirer pushes back on the corrections?"**
Document the evidence, quantify the financial impact, and escalate through Visa's compliance framework. Ultimately, Visa has contractual authority over MCC accuracy as part of its network rules.

---

## What a Strong Answer Looks Like in an Interview

> "I'd start by scoping the anomaly — is this a spike in specific merchants or a broad pattern? I'd compare the current 30-day volume against a baseline at the acquirer x MCC level and identify which merchants are driving the delta. Then I'd cross-reference with transaction characteristics: average ticket size, entry mode distribution, and time patterns to determine whether these merchants actually look like groceries. For the ones that don't, I'd quantify the interchange shortfall — what they're paying at the grocery rate vs. what they should pay at their true MCC rate — and categorize the root cause: boarding error, platform migration issue, or intentional gaming. I'd package this as an incident report with a clear financial impact number, specific merchants for the acquirer to remediate, and a recommendation for enhanced automated monitoring to prevent recurrence. The key is having the data ready so we can escalate with evidence, not just suspicion."
