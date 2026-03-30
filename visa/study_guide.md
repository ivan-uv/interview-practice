# Study Guide: Visa Senior Analyst, Global Interchange Compliance

Quick-reference notes on the highest-priority concepts for this role.

---

## Interchange Mechanics

### The Four-Party Model
| Party | Role | Interchange Flow |
|-------|------|-----------------|
| **Cardholder** | Uses the card | Pays nothing directly (interchange is invisible) |
| **Issuer** | Issues the card to cardholder | Receives interchange from acquirer |
| **Acquirer** | Processes transactions for merchant | Pays interchange to issuer |
| **Merchant** | Accepts the card | Pays merchant discount rate (includes interchange + acquirer markup + network fees) |
| **Visa** | Operates the network | Sets interchange rates but does NOT collect interchange; earns network fees |

### Rate Determination
A transaction's interchange rate depends on:
1. **Card type**: Consumer credit > commercial > consumer debit > prepaid (generally)
2. **Merchant category (MCC)**: Grocery/fuel get lower rates; general retail/e-commerce get higher
3. **Entry mode**: Card-present (chip/contactless) gets better rates than card-not-present
4. **Data qualification**: Meeting Level II/III requirements for commercial cards lowers the rate
5. **Regulation**: Durbin-regulated debit is capped regardless of other factors

### Qualification & Downgrades
| Status | Meaning |
|--------|---------|
| **Qualified** | Transaction meets all criteria for its target interchange rate |
| **Downgraded** | Missing data elements or criteria → falls to a higher default rate |
| **Standard** | Default rate when no preferred qualification is met |

Common downgrade causes:
- Missing AVS (Address Verification) for e-commerce
- Settlement delay > 2 days after authorization
- Missing Level II data (tax amount, customer code) for commercial cards
- Incorrect or missing MCC information

---

## The Durbin Amendment

### Key Facts
| Item | Detail |
|------|--------|
| **Law** | Part of Dodd-Frank (2010), effective 2011 |
| **What it caps** | Debit interchange for issuers with > $10B in assets |
| **Cap formula** | $0.21 + 0.05% of transaction + $0.01 fraud adjustment |
| **On a $50 transaction** | $0.21 + $0.025 + $0.01 = ~$0.245 |
| **Who's exempt** | Banks/credit unions with < $10B in assets |
| **Credit cards** | NOT covered by Durbin |
| **Routing requirement** | Merchants must have access to at least 2 unaffiliated debit networks |

### Compliance Implications
- Must verify that regulated transactions aren't exceeding the cap
- Must monitor that routing options are properly available
- Must distinguish regulated vs. exempt issuers correctly
- Proposed reduction to ~$0.144 base (late 2023) — check for latest

---

## SQL Quick Reference

### Window Functions
```sql
-- Rank within partition
ROW_NUMBER() OVER (PARTITION BY issuer_id ORDER BY total_volume DESC)
RANK()        -- ties get same rank, next rank skips
DENSE_RANK()  -- ties get same rank, next rank does NOT skip

-- Running totals
SUM(interchange_amount_usd) OVER (
    PARTITION BY issuer_id ORDER BY transaction_date
)

-- Rolling average (last 4 weeks)
AVG(avg_interchange_rate) OVER (
    PARTITION BY issuer_id
    ORDER BY month_start
    ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
)

-- Lag/Lead for period-over-period
LAG(total_interchange_usd, 1) OVER (PARTITION BY issuer_id ORDER BY month_start)
```

### Common Patterns
- **Anomaly detection**: Compare current period to baseline using z-score: `(current - avg) / stddev`
- **Duplicate detection**: `ROW_NUMBER() OVER (PARTITION BY card_hash, merchant_id, amount ORDER BY txn_date)` — rn > 1 = potential duplicate
- **Pre/post comparison**: `CASE WHEN date < cutoff THEN 'pre' ELSE 'post' END`, then aggregate
- **MCC migration**: Self-join on merchant_id with different time windows to detect MCC changes
- **Qualification rate**: `AVG(CASE WHEN qualification_status = 'qualified' THEN 1.0 ELSE 0.0 END)`

### Performance at Scale
- Visa tables can have billions of rows — always think about query efficiency
- Filter early (WHERE before JOIN when possible)
- Use date partitions aggressively
- Prefer `EXISTS` over `IN` for correlated subqueries on large tables
- CTEs can materialize — if reused, consider temp tables for performance

---

## Python Quick Reference

### EDA Checklist
```python
df.shape, df.dtypes, df.isnull().sum()
df.describe(include='all')
df["col"].value_counts(normalize=True)
df["numeric"].hist(bins=30)
df.corr()  # pearson by default
```

### Key scipy.stats functions
```python
stats.ttest_ind(a, b, equal_var=False)      # Welch's t-test
stats.mannwhitneyu(a, b, alternative='two-sided')  # non-parametric
stats.chi2_contingency(contingency_table)    # chi-square
stats.zscore(series)                          # z-scores for outlier detection
stats.norm.ppf(0.975)                        # z-score for 95% CI = 1.96
```

### Anomaly Detection Patterns
```python
# Z-score based anomaly detection
def detect_anomalies(series, threshold=2.5):
    z_scores = stats.zscore(series)
    return abs(z_scores) > threshold

# IQR-based (robust to outliers)
def iqr_anomalies(series, multiplier=1.5):
    q1, q3 = series.quantile([0.25, 0.75])
    iqr = q3 - q1
    return (series < q1 - multiplier * iqr) | (series > q3 + multiplier * iqr)

# Rolling baseline comparison
df["rolling_mean"] = df.groupby("issuer_id")["interchange"].transform(
    lambda x: x.rolling(30, min_periods=7).mean()
)
df["rolling_std"] = df.groupby("issuer_id")["interchange"].transform(
    lambda x: x.rolling(30, min_periods=7).std()
)
df["z_score"] = (df["interchange"] - df["rolling_mean"]) / df["rolling_std"]
df["is_anomaly"] = df["z_score"].abs() > 3.0
```

### Bash Automation Basics
```bash
# Cron job to run a daily data quality check
0 6 * * * /usr/bin/python3 /opt/compliance/daily_check.py >> /var/log/compliance.log 2>&1

# Parse a large CSV and extract specific columns
cut -d',' -f1,5,7 transactions.csv | head -100

# Count lines matching a pattern
grep -c "DOWNGRADE" settlement_report.csv

# Loop through files
for f in /data/daily/*.csv; do
    python3 validate.py "$f"
done
```

---

## Compliance & Incident Management

### Incident Lifecycle
1. **Detection**: Automated alert or client report identifies anomaly
2. **Triage**: Assess severity, scope, and financial impact
3. **Investigation**: Query data, identify root cause, quantify impact
4. **Remediation**: Coordinate with affected parties (issuer, acquirer, merchant)
5. **Resolution**: Confirm fix is in place, validate with data
6. **Documentation**: Record case details, root cause, resolution, prevention steps
7. **Prevention**: Update monitoring rules to catch similar issues earlier

### Severity Classification
| Severity | Criteria | Response Time |
|----------|----------|---------------|
| **Critical** | > $1M impact or regulatory violation | Same day |
| **High** | $100K-$1M impact or major client affected | 1-2 business days |
| **Medium** | $10K-$100K impact | 3-5 business days |
| **Low** | < $10K impact or informational | Next sprint/cycle |

### Root Cause Categories
| Category | Example |
|----------|---------|
| **Misclassification** | Merchant assigned wrong MCC |
| **Rate error** | Incorrect interchange rate applied to transaction |
| **Settlement discrepancy** | Mismatch between authorized and settled amounts |
| **Durbin violation** | Regulated debit exceeding cap |
| **Downgrade anomaly** | Unexpected spike in downgrade rates |
| **Routing violation** | Debit transaction routed without proper network options |
| **Platform/system error** | Bug in processing logic after update |

---

## Dashboarding Principles

### Metric Selection for Compliance
- Every metric should answer: "Is interchange flowing correctly?"
- Lead with financial impact, not just counts
- Max ~5-7 KPIs per dashboard view
- Always show trend direction, not just current state

### Key KPIs for Interchange Compliance
| KPI | What It Measures | Alert Threshold |
|-----|-----------------|----------------|
| **Qualification rate** | % of txns qualifying for target rate | < 85% (investigate) |
| **Downgrade rate** | % of txns downgraded to higher rate | > 15% (flag) |
| **Interchange variance** | Gap between actual and expected IC | > 2 std dev from baseline |
| **MCC migration rate** | Merchants changing MCC codes | > 5% of portfolio/month |
| **Case resolution time** | Avg days to close compliance cases | > 10 business days |
| **Financial exposure** | Open case $ impact | > $500K aggregate |
| **Durbin cap compliance** | % of regulated debit within cap | Must be 100% |

### Dashboard Design Tips
- Title = the question being answered, not the metric name
- Use sparklines/trend lines to show direction
- Red/yellow/green only when thresholds are agreed upon and well-calibrated
- Always show sample size (n=) alongside rates and averages
- Include data freshness indicator (when was this last refreshed?)

---

## Communication Templates

### Explaining an interchange anomaly to a non-technical stakeholder
> "We detected that a group of merchants processed under the grocery interchange rate actually have transaction patterns inconsistent with grocery stores — their average ticket is $85 and 60% of transactions are e-commerce. This means issuers received about $1.8M less interchange than they should have over the past month. We've documented the affected merchants and are working with the acquirer to correct the classifications."

### Explaining statistical significance in a compliance report
> "The 3 basis point drop in average interchange rate is statistically significant — it's well outside the normal month-to-month variance we've observed historically. This isn't random fluctuation; something changed in the transaction mix or rate qualification that we need to investigate."

### When the analysis is inconclusive
> "The data shows a shift in the MCC distribution, but we can't definitively attribute it to misclassification vs. legitimate merchant onboarding without reviewing the specific merchants. I've flagged the top 50 merchants by volume delta for manual review and recommend we prioritize the 15 with transaction patterns inconsistent with their assigned MCC."

---

## Key Numbers to Memorize

| Metric | Number |
|--------|--------|
| Visa FY2024 net revenue | ~$35.9B |
| Transactions processed annually | ~212.6B |
| Total payments volume | ~$14.8T |
| Cards in circulation | ~4.3B globally |
| Transactions per second (peak) | 65,000+ |
| US Durbin debit cap | ~$0.21 + 0.05% + $0.01 |
| Typical US credit interchange | 1.15% - 2.40% |
| Typical exempt debit interchange | 0.50% - 0.80% |
| Rate update cycle | April and October |
| EU interchange cap | 0.20% debit, 0.30% credit |

---

## Visa-Specific Talking Points

### For "Why Visa?"
1. Scale of impact — 212B+ transactions, so small compliance improvements prevent millions in misallocated interchange
2. Regulatory complexity is increasing (Durbin changes, CCCA, merchant settlement) — this team is at the intersection of data and policy
3. The role blends analytics with operational rigor — building automated monitoring, not just ad-hoc reports

### For "Tell me about your analytical approach"
Always frame around the compliance value chain:
1. **Detection** → Does the data show an anomaly? (Statistical monitoring, threshold alerts)
2. **Investigation** → What's the root cause? (SQL deep-dives, transaction pattern analysis)
3. **Quantification** → What's the financial impact? (Interchange variance × volume × time)
4. **Remediation** → How do we fix it and prevent recurrence? (Documentation, acquirer outreach, enhanced monitoring)

### For "How do you work at scale?"
- Reference **automation**: Airflow DAGs, scheduled SQL, Python scripts — not manual spreadsheets
- Reference **version control**: All queries and scripts in Git, peer-reviewed
- Reference **monitoring infrastructure**: Dashboards with alerting thresholds, not one-off queries
- Reference **documentation**: Every case documented, every resolution recorded, every prevention step added to the monitoring playbook
