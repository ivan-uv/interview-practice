# Data Schema Reference

This schema models a payments interchange compliance environment — the kind of data you'd work with on Visa's Global Interchange Compliance team. Seven tables cover the full lifecycle from transaction authorization through interchange settlement and compliance monitoring.

---

## Entity Relationship Overview

```
issuers ─────────────────────────────────────────────────────┐
    │                                                         │
    │ (1:many)                                                │
    ▼                                                         │
transactions ──────────────────────────────────────────┐      │
    │               │                │                  │      │
    │ (many:1)      │ (many:1)       │ (many:1)         │      │
    │               ▼                ▼                  │      │
    │          merchants        acquirers               │      │
    │               │                                   │      │
    │               │ (many:1)                          │      │
    │               ▼                                   │      │
    │          interchange_rates                        │      │
    │                                                   ▼      │
    │                                          compliance_cases│
    │                                                          │
    ▼                                                          │
monthly_interchange_summary ◄──────────────────────────────────┘
```

---

## Tables

### `transactions`
One row per card transaction. The central fact table — every analysis starts here.

| Column | Type | Description |
|--------|------|-------------|
| `transaction_id` | `VARCHAR` | Primary key |
| `card_number_hash` | `VARCHAR` | Hashed PAN — used for duplicate detection, not cardholder identification |
| `issuer_id` | `VARCHAR` | FK → `issuers.issuer_id` |
| `acquirer_id` | `VARCHAR` | FK → `acquirers.acquirer_id` |
| `merchant_id` | `VARCHAR` | FK → `merchants.merchant_id` |
| `transaction_date` | `TIMESTAMP` | When the transaction was authorized |
| `settlement_date` | `DATE` | When the transaction settled (may be NULL for pending) |
| `amount_usd` | `DECIMAL(12,2)` | Transaction amount in USD |
| `card_type` | `VARCHAR` | `consumer_credit`, `consumer_debit`, `commercial_credit`, `commercial_debit`, `prepaid` |
| `entry_mode` | `VARCHAR` | `chip`, `contactless`, `swipe`, `keyed`, `ecommerce` |
| `is_regulated` | `BOOLEAN` | True if issuer is Durbin-regulated (assets > $10B) |
| `interchange_rate_id` | `VARCHAR` | FK → `interchange_rates.rate_id` (the rate that was applied) |
| `interchange_amount_usd` | `DECIMAL(10,4)` | Actual interchange paid on this transaction |
| `expected_interchange_usd` | `DECIMAL(10,4)` | What interchange should have been based on rate schedule (NULL if not yet computed) |
| `qualification_status` | `VARCHAR` | `qualified`, `downgraded`, `standard` — whether the txn met criteria for its target rate |
| `network_id` | `VARCHAR` | Routing network used: `visa`, `interlink`, `plus`, `star`, `nyce` (debit routing) |

**Derived metrics:**
- Interchange variance: `interchange_amount_usd - expected_interchange_usd`
- Qualification rate: `AVG(CASE WHEN qualification_status = 'qualified' THEN 1.0 ELSE 0.0 END)`

**Common query patterns:** aggregate by card_type/entry_mode/merchant for rate analysis, filter by is_regulated for Durbin compliance, join to merchants for MCC-level analysis, detect anomalies via interchange variance.

---

### `merchants`
One row per merchant. Merchant classification drives which interchange rate applies.

| Column | Type | Description |
|--------|------|-------------|
| `merchant_id` | `VARCHAR` | Primary key |
| `merchant_name` | `VARCHAR` | Business name (e.g., "Walmart #4532", "Shell Gas Station") |
| `mcc` | `VARCHAR(4)` | Merchant Category Code — 4-digit code determining rate category |
| `mcc_description` | `VARCHAR` | Human-readable MCC name (e.g., "Grocery Stores", "Eating Places") |
| `acquirer_id` | `VARCHAR` | FK → `acquirers.acquirer_id` |
| `country_code` | `VARCHAR(2)` | ISO country code |
| `state_code` | `VARCHAR(2)` | US state (NULL for international) |
| `registration_date` | `DATE` | When merchant was onboarded |
| `is_high_risk` | `BOOLEAN` | High-risk merchant flag (affects processing rules) |

**Common query patterns:** group by MCC for interchange analysis, join to transactions for volume/revenue by merchant category, flag merchants with suspicious MCC assignments.

---

### `issuers`
One row per card-issuing financial institution.

| Column | Type | Description |
|--------|------|-------------|
| `issuer_id` | `VARCHAR` | Primary key |
| `issuer_name` | `VARCHAR` | Bank name (e.g., "Chase", "Bank of America", "Navy Federal CU") |
| `country_code` | `VARCHAR(2)` | Issuer's country |
| `total_assets_usd` | `DECIMAL(15,2)` | Total assets — determines Durbin regulation status |
| `is_durbin_regulated` | `BOOLEAN` | True if total_assets > $10B (subject to debit interchange cap) |
| `primary_network` | `VARCHAR` | Primary debit network: `visa`, `interlink`, `star`, `nyce`, `pulse` |

**Common query patterns:** filter for regulated vs. exempt issuers, aggregate interchange received by issuer, validate Durbin cap compliance.

---

### `acquirers`
One row per acquiring bank/processor.

| Column | Type | Description |
|--------|------|-------------|
| `acquirer_id` | `VARCHAR` | Primary key |
| `acquirer_name` | `VARCHAR` | Processor name (e.g., "Worldpay", "Fiserv", "Adyen") |
| `country_code` | `VARCHAR(2)` | Acquirer's country |
| `total_merchants` | `INTEGER` | Number of merchants in their portfolio |

**Common query patterns:** aggregate interchange paid by acquirer, identify acquirers with high downgrade rates, monitor data quality by acquirer.

---

### `interchange_rates`
The rate schedule — one row per rate category. Visa publishes these rates and updates them typically in April and October.

| Column | Type | Description |
|--------|------|-------------|
| `rate_id` | `VARCHAR` | Primary key |
| `rate_name` | `VARCHAR` | Human-readable name (e.g., "CPS/Retail 2", "Regulated Debit", "Commercial Card Not Present") |
| `card_type` | `VARCHAR` | Which card types this rate applies to |
| `mcc_group` | `VARCHAR` | Merchant category group (e.g., `grocery`, `fuel`, `restaurant`, `general_retail`, `ecommerce`) |
| `entry_mode_group` | `VARCHAR` | `card_present`, `card_not_present`, `any` |
| `pct_rate` | `DECIMAL(6,4)` | Percentage component (e.g., 0.0165 for 1.65%) |
| `flat_fee_usd` | `DECIMAL(6,4)` | Fixed component (e.g., 0.10 for $0.10) |
| `effective_date` | `DATE` | When this rate took effect |
| `end_date` | `DATE` | When this rate was superseded (NULL if current) |
| `is_regulated` | `BOOLEAN` | True if this is a Durbin-regulated rate |

**Derived metric:** Expected interchange = `amount_usd * pct_rate + flat_fee_usd`

**Common query patterns:** look up current rates (WHERE end_date IS NULL), compare rate changes over time, validate that regulated rates are within the Durbin cap.

---

### `compliance_cases`
One row per compliance incident. Tracks errors, anomalies, and investigation outcomes.

| Column | Type | Description |
|--------|------|-------------|
| `case_id` | `VARCHAR` | Primary key |
| `case_type` | `VARCHAR` | `misclassification`, `rate_error`, `settlement_discrepancy`, `durbin_violation`, `downgrade_anomaly`, `routing_violation` |
| `opened_date` | `DATE` | When the case was opened |
| `closed_date` | `DATE` | When the case was resolved (NULL if open) |
| `severity` | `VARCHAR` | `low`, `medium`, `high`, `critical` |
| `affected_issuer_id` | `VARCHAR` | FK → `issuers.issuer_id` (NULL if not issuer-specific) |
| `affected_acquirer_id` | `VARCHAR` | FK → `acquirers.acquirer_id` (NULL if not acquirer-specific) |
| `affected_merchant_id` | `VARCHAR` | FK → `merchants.merchant_id` (NULL if not merchant-specific) |
| `transaction_count` | `INTEGER` | Number of transactions affected |
| `financial_impact_usd` | `DECIMAL(12,2)` | Total estimated financial impact |
| `root_cause` | `VARCHAR` | Description of what went wrong |
| `resolution` | `VARCHAR` | Description of how it was fixed |
| `analyst_id` | `VARCHAR` | Who handled the case |

**Common query patterns:** case volume by type/severity, time-to-resolution, financial impact trends, top affected clients.

---

### `monthly_interchange_summary`
Pre-aggregated monthly summary per issuer. A convenience mart for dashboards and trend analysis.

| Column | Type | Description |
|--------|------|-------------|
| `issuer_id` | `VARCHAR` | FK → `issuers.issuer_id` |
| `month_start` | `DATE` | First day of the month (grain: issuer x month) |
| `transaction_count` | `BIGINT` | Total transactions |
| `total_volume_usd` | `DECIMAL(15,2)` | Total transaction dollar volume |
| `total_interchange_usd` | `DECIMAL(12,2)` | Total interchange received |
| `avg_interchange_rate` | `DECIMAL(6,4)` | Effective interchange rate (total_interchange / total_volume) |
| `qualification_rate` | `DECIMAL(5,4)` | Fraction of transactions that qualified for their target rate |
| `downgrade_rate` | `DECIMAL(5,4)` | Fraction of transactions that were downgraded |
| `compliance_case_count` | `INTEGER` | Number of compliance cases opened this month |

**Composite PK:** `(issuer_id, month_start)`

**Common query patterns:** trend analysis, rolling averages, month-over-month comparisons, flagging issuers with deteriorating qualification rates.

---

## Key Relationships at a Glance

| Relationship | Type | Join |
|---|---|---|
| issuer → transactions | 1:many | `transactions.issuer_id = issuers.issuer_id` |
| acquirer → transactions | 1:many | `transactions.acquirer_id = acquirers.acquirer_id` |
| merchant → transactions | 1:many | `transactions.merchant_id = merchants.merchant_id` |
| interchange_rate → transactions | 1:many | `transactions.interchange_rate_id = interchange_rates.rate_id` |
| acquirer → merchants | 1:many | `merchants.acquirer_id = acquirers.acquirer_id` |
| issuer → monthly_summary | 1:many | `monthly_interchange_summary.issuer_id = issuers.issuer_id` |
| various → compliance_cases | many:1 | Cases can reference issuer, acquirer, and/or merchant |

---

## Intentional Data Quality Gaps (for practice)

- `expected_interchange_usd` can be NULL for recently processed transactions — handle in WHERE/COALESCE
- `settlement_date` is NULL for pending transactions — use for data pipeline freshness checks
- Not every transaction has a corresponding compliance case (most don't) — LEFT JOIN for enrichment
- `compliance_cases.closed_date` is NULL for open cases — use for aging analysis
- Some merchants may have incorrect MCC codes — this is a real-world compliance issue to detect
