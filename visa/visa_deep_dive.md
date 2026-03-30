# Visa — Deep Dive for Interview Prep

Know this cold. Every interviewer will expect you to understand how Visa makes money, how interchange works, and what the compliance team does.

---

## Company Overview

- **Founded**: 1958 (as BankAmericard), incorporated as Visa Inc. 2007, IPO 2008
- **Mission**: To connect the world through the most innovative, convenient, reliable, and secure payments network
- **Employees**: ~26,500 globally
- **HQ**: Foster City, CA (offices in San Francisco, Austin, Denver, Atlanta, Miami, London, Singapore, and 100+ countries)
- **Market cap**: ~$600B+ (one of the most valuable companies in the world)
- **FY2024 revenue**: ~$35.9B net revenue
- **CEO**: Ryan McInerney (since Feb 2023; previously President of Visa)
- **Chairman**: Alfred F. Kelly Jr. (former CEO)

### Key Leadership
- **Ryan McInerney** — CEO. Former President, deep payments background, JPMorgan Chase before Visa
- **Chris Suh** — CFO. Former Microsoft finance leadership
- **Paul Fabara** — Chief Risk & Client Services Officer. Responsible for compliance functions
- **Antony Cahill** — President, Global Markets. Oversees regional strategy including North America

**Why this matters in your interview**: Visa is not a bank. Visa is a technology company that operates a payments network. It does not issue cards, extend credit, or set interest rates. Understanding this distinction is fundamental.

---

## How Visa Makes Money

Visa earns revenue from **three primary sources** — none of which are interchange:

### 1. Service Revenues (~44% of net revenue)
Fees charged to financial institutions based on their payment volume on Visa's network.

### 2. Data Processing Revenues (~38% of net revenue)
Per-transaction fees for authorization, clearing, settlement, and network access. This is the toll for using VisaNet.

### 3. International Transaction Revenues (~27% of net revenue)
Cross-border transaction fees when the issuer and acquirer are in different countries.

### 4. Other Revenues (~5%)
Consulting, analytics (Visa Consulting Analytics), licensing, and value-added services.

**Note**: Client incentives (rebates to issuers and merchants) offset ~27% of gross revenue.

---

## The Four-Party Model

```
Cardholder                                      Merchant
    │                                               │
    │  Uses card                          Accepts card
    │                                               │
    ▼                                               ▼
 Issuer ◄──── Interchange Fee ────────── Acquirer
(cardholder's bank)                    (merchant's bank)
    │                                               │
    └────────────── VisaNet ──────────────────────────┘
                 (Visa's network)
```

### Transaction Flow
1. **Authorization**: Cardholder taps/swipes/enters card → merchant's terminal sends request to acquirer → acquirer routes through VisaNet → issuer approves/declines in ~1 second
2. **Clearing**: End of day, Visa aggregates all transactions and calculates net positions
3. **Settlement**: Visa facilitates the transfer of funds — acquirer pays issuer the interchange fee, merchant receives sale amount minus merchant discount rate

### What Is Interchange?
- A **transfer fee** paid by the acquirer to the issuer for each card transaction
- Compensates the issuer for: credit risk, fraud prevention, rewards programs, transaction processing
- **Visa sets the rates but does NOT collect interchange** — it flows between banks
- Interchange is the largest component of the merchant discount rate (what merchants pay to accept cards)

### The Strategic Balancing Act
- **Higher interchange** → More attractive for issuers to issue Visa cards → More cards in market → More volume
- **Higher interchange** → More expensive for merchants → Risk of surcharging, steering to competitors, or declining to accept Visa
- Visa must optimize this two-sided market: keep issuers motivated AND merchants accepting

---

## Interchange Rate Structure

Visa publishes **hundreds** of interchange rate categories. Rates vary by:

| Factor | Examples |
|--------|----------|
| **Card type** | Consumer credit, consumer debit, commercial/corporate, prepaid, rewards vs. basic |
| **Merchant category** | Grocery (lower), restaurant, fuel, e-commerce, general retail |
| **Transaction type** | Card-present (CP) vs. card-not-present (CNP), contactless, chip, e-commerce with 3D Secure |
| **Transaction size** | Some rates have fixed + percentage (e.g., 1.65% + $0.10) |
| **Qualification criteria** | Must meet specific data requirements for preferred rates (Level II/III for commercial) |

### Typical US Interchange Ranges
| Card Type | Typical Range |
|-----------|--------------|
| Consumer credit | 1.15% - 2.40% + $0.05-$0.10 |
| Regulated debit (Durbin) | ~0.05% + $0.22 (capped) |
| Exempt debit (non-Durbin) | 0.50% - 0.80% |
| Commercial/corporate | 2.00% - 2.65% + $0.10 |
| Prepaid | 1.15% - 1.65% |

### Qualification & Downgrades
- Transactions must meet specific criteria to qualify for their target interchange rate
- Missing data elements (e.g., no AVS for e-commerce, missing Level II data for commercial) causes a **downgrade** — the transaction falls to a higher, default rate
- Downgrades cost merchants more money and are a major compliance focus
- The compliance team monitors whether transactions are correctly classified and qualified

---

## Regulatory Landscape

### The Durbin Amendment (2010, effective 2011)

The single most important regulation for your role:

- Part of the **Dodd-Frank Wall Street Reform Act**
- **Caps debit interchange fees** for issuers with assets > $10 billion ("regulated issuers")
- **Current cap**: ~$0.21 + 0.05% of transaction value + $0.01 fraud adjustment = ~$0.22 on a typical transaction
- **Exempt issuers**: Banks/credit unions with < $10B in assets are NOT capped
- **Network routing**: Merchants must be able to route debit transactions over at least two unaffiliated networks (e.g., Visa debit card must also carry Interlink, Star, NYCE, or Pulse)
- **Does NOT apply to credit cards** — only debit (signature and PIN)

**Recent developments**:
- Federal Reserve proposed **lowering the cap** from ~$0.21 to ~$0.14.4 in late 2023 — would be a major revenue hit to large issuers
- Visa/bank lobbyists have pushed back vigorously
- The final rule implementation timeline remains in flux — check for latest updates

### Merchant Class Action Settlement (2024)
- Visa and Mastercard reached a **$30 billion settlement** with merchants (March 2024) — largest antitrust settlement in US history
- Included provisions to reduce interchange rates by at least 4 basis points for 3 years and cap rates for 5 years
- **Federal judge rejected the settlement** in June 2024, calling relief "insufficient"
- Case remains active — a major overhang on interchange strategy

### Credit Card Competition Act (CCCA)
- Proposed legislation (Senators Durbin & Marshall) that would extend routing competition to **credit cards**
- Would require large issuers to enable a second network on credit cards (like Durbin did for debit)
- **Existential threat** to Visa's credit card interchange economics if passed
- Has not passed as of early 2025 but keeps being reintroduced

### Other Regulatory Considerations
| Regulation | What It Covers |
|-----------|---------------|
| **Reg E** | Electronic fund transfer rules affecting debit |
| **PCI DSS** | Data security standards for cardholder data |
| **EU IFR** | European interchange caps: 0.20% debit, 0.30% credit (useful for global comparisons) |
| **RBA (Australia)** | Australia has had interchange caps since 2003 — longest-running case study |
| **State surcharging laws** | Vary by state, affect merchant behavior |

---

## What the Global Interchange Compliance Team Does

Based on the JD and industry context:

### Core Activities
1. **Transaction monitoring**: Validate that interchange is correctly calculated and settled for every transaction
2. **Anomaly detection**: Identify patterns where interchange isn't flowing correctly — overpayments, underpayments, misclassifications
3. **MCC validation**: Ensure merchants are assigned correct Merchant Category Codes (affects which interchange rate applies)
4. **Durbin compliance**: Track that regulated debit transactions are capped correctly and routing requirements are met
5. **Rate qualification monitoring**: Detect transactions that should qualify for preferred rates but are being downgraded (or vice versa)
6. **Incident management**: When errors are found — investigate root cause, quantify financial impact, coordinate remediation, document resolution
7. **KPI dashboards**: Build and maintain monitoring infrastructure that surfaces compliance issues proactively
8. **Program change support**: When Visa updates interchange rates or programs (typically April and October), validate that changes are implemented correctly across the network

### Why This Matters
- Visa processes **212+ billion transactions/year** at 65,000+ TPS
- Even a tiny error rate at this scale = massive financial impact
- Clients (issuers and acquirers) trust Visa to get interchange right — compliance errors erode that trust
- Regulatory scrutiny means documentation and audit trails are critical

---

## VisaNet & Data Infrastructure

### VisaNet
- One of the world's largest electronic payment networks
- Processes **65,000+ transactions per second** at peak
- **~1.8 second** average end-to-end authorization time
- Handles authorization, clearing, settlement, and risk scoring
- **Visa Advanced Authorization (VAA)**: Real-time fraud scoring using 500+ risk attributes per transaction

### Analytics Stack (from job postings)
| Tool | Usage |
|------|-------|
| **SQL** | Primary analysis tool — querying massive transaction databases (petabytes) |
| **Python** | Automation, statistical analysis, data processing |
| **Bash** | CLI automation, scripting scheduled jobs |
| **Power BI / Tableau** | Dashboards, executive reporting, compliance monitoring |
| **Airflow** | Pipeline orchestration, scheduled data refreshes |
| **GitHub / Bitbucket** | Version control, code review, CI/CD |
| **Teradata / Oracle** | Legacy data warehouse platforms |
| **GCP (BigQuery)** | Cloud analytics (Visa-Google partnership since 2020) |
| **Hadoop / Spark** | Large-scale batch processing |

---

## Competitive Landscape

### Network Competitors
| Network | Key Differentiator |
|---------|-------------------|
| **Mastercard** | #2 global network; similar four-party model; strong in Europe and emerging markets |
| **American Express** | Three-party model (issuer AND network); higher interchange but also higher merchant fees |
| **Discover** | Smaller US network; recently acquired by Capital One (pending regulatory approval) |
| **UnionPay** | Dominant in China; growing international presence |

### Alternative Payment Threats
- **Real-time payment rails**: FedNow, RTP (The Clearing House) — bypass card networks entirely
- **Buy Now Pay Later**: Affirm, Klarna, Afterpay — redirect transaction economics
- **Digital wallets**: Apple Pay, Google Pay — currently ride on Visa rails but could disintermediate
- **Cryptocurrency**: Visa has embraced (Visa offers crypto-linked cards) rather than fought this trend

### Visa's Moat
1. **Network effects**: 4.3B+ cards × 100M+ merchant locations × universal acceptance
2. **Processing infrastructure**: VisaNet's reliability (99.999%+ uptime) and speed
3. **Brand trust**: Consumers and merchants trust the Visa brand globally
4. **Data assets**: Transaction data powering fraud prevention, analytics, and consulting services

---

## Key Numbers to Memorize

| Metric | Number |
|--------|--------|
| FY2024 net revenue | ~$35.9B |
| Transactions processed (FY2024) | ~212.6B |
| Total payments volume (FY2024) | ~$14.8T |
| Cards in circulation | ~4.3B globally |
| Countries/territories | 200+ |
| Transactions per second (peak) | 65,000+ |
| Employees | ~26,500 |
| US regulated debit interchange cap | ~$0.21 + 0.05% + $0.01 |
| US credit/debit volume split | ~60/40 by transaction count (debit higher volume, lower ticket) |
| Debit vs credit average ticket | Debit ~$40, Credit ~$90 |

---

## "Why Visa?" Answer Framework

> "Three things drew me to this role. First, the scale — Visa processes over 200 billion transactions a year, so even small improvements in compliance monitoring have outsized financial impact. That's the kind of data problem I want to work on. Second, the interchange space is uniquely interesting right now — with the Durbin cap potentially being lowered, the merchant settlement still unresolved, and the Credit Card Competition Act in discussion, the regulatory environment is evolving fast, and this team is right at the center of it. Third, I'm excited about building analytical infrastructure that scales — the JD mentions Airflow, version control, and dashboards, which tells me this team is moving toward automated, production-grade monitoring rather than ad-hoc analysis. That's exactly the kind of work I want to do."
