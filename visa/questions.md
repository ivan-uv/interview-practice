# Visa Interview Question Bank

---

## 1. Role Fit & Motivation

- Why Visa? Why interchange compliance specifically?
- Tell me about a time you identified a data anomaly that had real financial impact.
- What does "interchange compliance" mean to you, and why does it matter?
- How do you think about the relationship between compliance monitoring and business strategy?
- What's the difference between a metric that's *interesting* and one that's *actionable* in a compliance context?

**Strong answer frame**: Lead with the business/client impact, then the methodology. Reference interchange mechanics and regulatory context.

---

## 2. SQL

### Conceptual
- What's the difference between `ROW_NUMBER()`, `RANK()`, and `DENSE_RANK()`? When do you use each?
- When would you use a CTE vs. a subquery vs. a temp table? What about performance at scale?
- Explain window functions. Give a business example with transaction data.
- What's the difference between `INNER JOIN`, `LEFT JOIN`, and `FULL OUTER JOIN`? When does `LEFT JOIN` surprise you?
- How do you handle deduplication in large datasets? What's your approach when you see duplicate transaction records?
- What's a self-join and when would you use one with transaction data?

### Scenario-based
- *"We have a transactions table with transaction_id, merchant_id, card_number_hash, amount_usd, and transaction_date. Write a query to detect potential duplicate transactions — same card, same merchant, same amount, within 5 minutes."*
- *"Given transactions and interchange_rates tables, write a query to calculate the variance between actual interchange paid and expected interchange for each transaction."*
- *"Find the top 10 merchant categories (by MCC) where the downgrade rate exceeds 20%, ranked by total financial impact."*
- *"Write a query to compute month-over-month change in average interchange rate per issuer."*
- *"Given a rate change effective April 1, compare 30 days of transaction volumes before and after by card type."*

See `sql/questions.sql` for worked examples.

---

## 3. Python & Statistics

### Statistics / Analytical Thinking
- You detect that a large issuer's average interchange rate dropped by 3 basis points month-over-month. How do you determine if this is statistically significant or just noise?
- What is statistical significance? Explain it to a non-technical compliance stakeholder.
- What's the difference between correlation and causation? Give a payments example.
- How would you set up monitoring to detect when interchange anomalies exceed normal variance?
- What is a confidence interval and how would you explain it in a compliance report?
- Describe your approach to outlier detection. What methods work best for transaction data?

### Python / Coding
- Write a function to parse a CSV of transaction records, validate data types, and flag malformed rows.
- How would you build an automated data quality check that runs daily?
- Given a time series of daily interchange totals per issuer, how would you detect anomalous days?
- Write a script to compute the expected interchange for each transaction given a rate schedule.
- How would you use Python to automate a Bash-based ETL pipeline?

### Automation & Tooling
- Describe your experience with command-line automation (Bash scripting).
- How would you set up an Airflow DAG to refresh a compliance dashboard daily?
- What is a DAG and why is "acyclic" important?
- How does Airflow differ from cron?
- What is idempotency and why does it matter for data pipelines?
- How would you handle a task that frequently fails in Airflow?
- Walk me through your version control workflow — how do you use Git for analytical work?
- Why does code review matter in a compliance context? (audit trail, four-eyes principle)
- How do you ensure reproducibility in your analyses?
- What environments does code move through before production? (Dev → Test → Staging → Prod)

See `python/questions.py` for worked examples.

---

## 4. Interchange & Payments Domain

- Explain how interchange works in the four-party model. Who pays whom?
- Walk through the transaction lifecycle: authorization → clearing → settlement. What happens at each step?
- What is the Durbin Amendment? How does it affect debit interchange?
- What determines which interchange rate a transaction receives?
- What causes a transaction to be "downgraded" to a higher interchange rate?
- A merchant is classified as MCC 5411 (Grocery) but actually operates as a restaurant. What's the compliance issue?
- How does the Credit Card Competition Act differ from the Durbin Amendment?
- What happens during a Visa interchange rate update (April/October cycle)?
- Why does Visa care about interchange compliance if Visa doesn't collect interchange?
- Explain the difference between regulated and exempt debit interchange.
- What is Level II/III data and why does it matter for commercial card interchange?
- **What is CEDP and why does it matter right now?** (This is the most relevant current change — know the L2 sunset timeline, Product 3, and compliance implications)
- What is the DOJ antitrust lawsuit about? How does it affect the compliance team's work?
- What is tokenization and how does it affect interchange qualification?
- Break down the Merchant Discount Rate — what percentage goes to interchange vs. scheme fees vs. acquirer markup?
- What are the structural changes in the Nov 2025 amended merchant settlement? (10 bps reduction, 1.25% cap for 8 years)

---

## 5. Dashboards & Monitoring

- What makes a good compliance monitoring dashboard vs. a bad one?
- How do you decide what KPIs to track for interchange compliance?
- Walk me through how you'd design an alerting system for interchange anomalies.
- A stakeholder says "the dashboard shows too many false positives." How do you tune it?
- What's your process for defining metrics and thresholds before building a dashboard?
- How do you ensure dashboard data is trustworthy? What validation checks do you build in?
- How would you visualize interchange rate changes over time across multiple card types?

---

## 6. Incident Management & Case Study

- *"An issuer reports that they received $500K less interchange than expected last month. Walk me through your investigation."*
- *"You notice that downgrade rates for a specific acquirer jumped from 5% to 15% after a rate change. How do you investigate?"*
- *"A batch of 2 million debit transactions was settled at the wrong interchange rate. Walk me through incident management from detection to resolution."*
- *"Design a monitoring query that would have caught the above error before the client reported it."*

See `case_study.md` for a full worked example.

---

## 7. Cross-Functional & Behavioral

- Tell me about a time you had to explain a complex data finding to a non-technical audience.
- Describe a situation where your analysis changed a business decision.
- Tell me about a time your analysis was wrong or incomplete. What happened?
- How do you handle competing priorities from multiple stakeholders?
- Give an example of a time you proactively identified an issue before someone asked.
- Describe a project where documentation was critical to the outcome.
- Tell me about a time you automated something that used to be manual. What was the impact?
- How do you ensure accuracy and attention to detail in your work?

**STAR format**: Situation -> Task -> Action -> Result (quantify the result whenever possible)

---

## 8. Regulatory & Compliance Awareness

- What regulatory trends are you following in the payments space?
- How would you monitor compliance with the Durbin Amendment's routing requirements?
- If a new regulation caps credit card interchange (like the CCCA proposes), what analytical work would this team need to do?
- How do you balance the need for thorough compliance review with the pressure to resolve cases quickly?
- What's the difference between a compliance violation and a processing error? Why does the distinction matter?
- How would you quantify the financial risk of a compliance gap?

---

## 9. Questions to Ask Visa

These are researched and tailored — they show you know the interchange space.

1. "With interchange rate updates happening twice a year, what does the compliance validation process look like around those windows? Is it largely automated or manual?"
2. "How does the team prioritize which compliance cases to investigate first — is it purely by financial impact, or are there other factors like client tier or regulatory exposure?"
3. "What does the data infrastructure look like — is the team querying VisaNet transaction data directly, or is there an analytics/warehouse layer? What's the typical data freshness?"
4. "The Durbin cap may be lowered and the CCCA is in discussion — how is the compliance team preparing for potential regulatory changes?"
5. "How much of the team's work is proactive monitoring vs. reactive incident management? Where is the team trying to shift that balance?"
6. "What does success look like for this role in the first 6-12 months?"
