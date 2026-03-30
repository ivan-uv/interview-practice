# Visa — Senior Analyst, Global Interchange Compliance

Interview prep for the **Senior Analyst, Global Interchange Compliance** role at Visa.

---

## Role Summary

- **Team**: Global Interchange Compliance (within Global Pricing & Interchange)
- **Focus**: Ensuring proper interchange levels are paid/received, identifying anomalies, incident management, building compliance KPIs/dashboards
- **Partners**: Interchange Strategy, Legal/Compliance, Government Relations, Client Services, Product, Finance
- **Stack signals**: SQL (advanced), Python/Bash automation, Power BI/Tableau, Airflow, GitHub/version control
- **Comp range**: $129,200 - $206,700 base + bonus + equity

---

## What They're Actually Hiring For

Reading between the lines of the JD:

1. **Anomaly detection in payments processing** — Identify when interchange isn't flowing correctly between issuers and acquirers. This is the core deliverable. Errors here have direct financial impact on Visa's clients.
2. **KPI dashboards & compliance monitoring** — Build and maintain automated monitoring that catches issues before clients do. Power BI/Tableau, refreshed via Airflow.
3. **Incident management & documentation** — Full-cycle error resolution: detect, investigate, document, remediate, prevent recurrence. This is operational rigor.
4. **Interchange program expertise** — Deep knowledge of how rates are set, what qualifies a transaction for a given category, and how regulations (Durbin) constrain the system.

---

## Prep Materials

| File | What it covers |
|------|---------------|
| [`visa_deep_dive.md`](visa_deep_dive.md) | **START HERE** — Visa's business, interchange mechanics, four-party model, regulatory landscape |
| [`interview_intel.md`](interview_intel.md) | Interview process, expected questions, format tips, what to expect |
| [`schema.md`](schema.md) | Full data schema — 7 tables modeling interchange transaction data, compliance cases, rate schedules |
| [`questions.md`](questions.md) | Full question bank by category |
| [`case_study.md`](case_study.md) | Full realistic case study: investigating an interchange misclassification anomaly |
| [`study_guide.md`](study_guide.md) | Key concepts: interchange mechanics, Durbin, SQL patterns, compliance frameworks |

### SQL (`sql/`)

| File | What it covers |
|------|---------------|
| [`sql/questions.sql`](sql/questions.sql) | 20 problems — prompts only, no answers (interchange-specific scenarios) |
| [`sql/solutions.sql`](sql/solutions.sql) | Full solutions with inline explanations |

### Python (`python/`)

| File | What it covers |
|------|---------------|
| [`python/questions.py`](python/questions.py) | Function stubs + docstrings — implement these |
| [`python/solutions.py`](python/solutions.py) | Full implementations + runnable demo (`python solutions.py`) |
| [`python/sample_dag.py`](python/sample_dag.py) | Working Airflow DAG — daily compliance monitoring pipeline with sensors, branching, XCom, and interview talking points |

### Bash (`bash/`)

| File | What it covers |
|------|---------------|
| [`bash/questions.sh`](bash/questions.sh) | 30 problems — file inspection, text processing, piping, loops, cron, process management |
| [`bash/solutions.sh`](bash/solutions.sh) | Full solutions with interview context notes (`bash solutions.sh all`) |

### Behavioral

| File | What it covers |
|------|---------------|
| [`behavioral_prep.md`](behavioral_prep.md) | 10 STAR story templates mapped to Visa leadership principles + question-to-story index |

---

## Interview Structure (Likely)

1. **Recruiter screen** — Background, motivation, comp expectations
2. **Hiring manager round** — Role fit, interchange knowledge, how you approach compliance problems
3. **Technical assessment** — SQL + Python live coding or take-home; expect transaction data, anomaly detection
4. **Panel / virtual onsite** — 3-4 rounds: technical depth, business acumen, behavioral
5. **Senior leadership** — Culture fit, strategic thinking, communication skills

---

## Key Themes to Hit in Every Round

- "I think about compliance as a data problem — anomalies in interchange flow are detectable patterns, and the faster we surface them, the less financial exposure for our clients"
- Business-first: always start with the client/financial impact before describing the technical approach
- Regulatory fluency: demonstrate you understand Durbin, MCC classification, and why interchange compliance matters in the current environment
- Automation mindset: manual monitoring doesn't scale at Visa's volume — show you think in pipelines, scheduled jobs, and alerting
- Precision and documentation: in compliance, audit trails matter as much as the analysis itself
