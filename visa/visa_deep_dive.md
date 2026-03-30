# Visa — Deep Dive for Interview Prep

Know this cold. Every interviewer will expect you to understand how Visa makes money, how interchange works, and what the compliance team does.

---

## Company Overview

- **Founded**: 1958 (as BankAmericard), incorporated as Visa Inc. 2007, IPO 2008
- **Mission**: To connect the world through the most innovative, convenient, reliable, and secure payments network
- **Employees**: ~26,500 globally
- **HQ**: Foster City, CA (offices in San Francisco, Austin, Denver, Atlanta, Miami, London, Singapore, and 100+ countries)
- **Market cap**: ~$600B+ (one of the most valuable companies in the world)
- **FY2025 revenue**: ~$40B net revenue (up 11% YoY)
- **Q1 FY2026 revenue**: $10.9B (up 15%)
- **Net profit margin**: ~50%+
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
Per-transaction fees for authorization, clearing, settlement, and network access. This is the toll for using VisaNet. Largest segment.

### 3. International Transaction Revenues (~27% of net revenue)
Cross-border transaction fees when the issuer and acquirer are in different countries. 13% constant-dollar growth in FY2025.

### 4. Value-Added Services (~24% growth, $10.9B in FY2025)
Fastest-growing segment. Includes fraud prevention (Visa Advanced Authorization), risk/identity solutions, issuer processing (Pismo), consulting, analytics (Visa Consulting Analytics), and acceptance solutions.

**Note**: Client incentives (rebates to issuers and merchants) offset ~27% of gross revenue.

### Visa's Three Growth Levers
1. **Consumer Payments**: Core card business — credit, debit, prepaid across CP and CNP channels
2. **Commercial & Money Movement**: B2B payments, Visa Direct (real-time push payments — 12.5B transactions in FY2025), cross-border remittances, disbursements
3. **Value-Added Services (VAS)**: Fraud prevention, risk/identity, issuer processing, consulting, analytics

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

## Recent Strategic Moves (2024–2026)

| Date | Move | Why It Matters |
|------|------|---------------|
| Jan 2024 | **Pismo Acquisition** ($929M) | Cloud-native issuer processing platform. Visa now competes with FIS/Fiserv/TSYS in core banking infrastructure. |
| Dec 2024 | **Featurespace Acquisition** ($946M) | Real-time AI fraud prevention, strengthening Visa's risk/identity stack. |
| 2025 | **AI & GenAI investments** | Early adopter of neural networks for fraud scoring. Now investing in generative AI for agentic commerce (AI agents making purchases autonomously). |
| 2025 | **Stablecoins & Tokenization** | Piloting stablecoin settlement and expanding token-based commerce. Tokenized transactions can qualify for lower interchange. |
| 2025-2026 | **CEDP** (Commercial Enhanced Data Program) | Major overhaul of commercial interchange incentives — **directly relevant to your role**. See below. |

CEO Ryan McInerney's vision: Visa as a "payments hyperscaler" — modular services that clients plug into.

---

## CEDP — Commercial Enhanced Data Program

**This is the single most relevant current change to interchange, and it's happening RIGHT NOW.**

CEDP replaces the legacy Level 2/Level 3 interchange incentive structure for commercial cards. It fundamentally changes how commercial interchange is qualified.

| Date | Change |
|------|--------|
| April 2025 | CEDP launched. 0.05% participation fee on eligible transactions. Replaces legacy L2/L3 structure. |
| October 2025 | Only verified merchants eligible for reduced CEDP rates. New **Product 3** interchange rates introduced. Business cards now eligible for L3-level savings for first time. |
| November 2025 | Visa paused new merchant verifications to adjust methodology. Existing verified merchants unaffected. |
| January 2026 | Level 2 interchange rates for small business cards increased by 75 bps — making L2 more expensive than sending no enhanced data at all. |
| April 2026 | Level 2 interchange programs sunset entirely (except fleet fuel). **CEDP Product 3 becomes the only path to reduced commercial rates.** |

### Why This Matters for Your Role
- Your team will monitor whether merchants and acquirers are correctly submitting CEDP data
- Qualification rates for Product 3 need validation
- The L2 → Product 3 transition must proceed without errors
- Financial impacts of the transition need accurate calculation
- Expect interview questions about CEDP — it's the most relevant current change

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

### Merchant Class Action Settlement (2005–Present)

The longest-running interchange litigation: *In re Payment Card Interchange Fee and Merchant Discount Antitrust Litigation*.

- **$5.54B Monetary Settlement** (2019): Approved, claims period closed Feb 2025. Payments to merchants for alleged interchange overcharges 2004–2019.
- **Equitable Relief Settlement** (Nov 2025): Amended settlement with major structural changes:
  - Merchants gain the right to **decline high-cost premium and commercial cards**
  - Interchange rates reduced by **10 basis points** (up from 7 bps in the rejected 2024 proposal)
  - Standard consumer credit rates **capped at 1.25%** (125 bps) for eight years
  - $21 million merchant education program
  - Final approval expected late 2026/early 2027
- **Why it matters for your role**: Caps and structural changes require system updates, new monitoring logic, and compliance verification across Visa's global operations.

### DOJ Antitrust Lawsuit (Sept 2024)

Separate from the merchant litigation. The U.S. Department of Justice sued Visa for **monopolization of the debit card market** under Sections 1 and 2 of the Sherman Act.

- Visa handles **60%+ of U.S. debit transactions**, collecting $7B+ annually in processing fees
- DOJ alleges Visa uses exclusionary contracts with merchants and issuers to lock up debit volume and prevent competitors from gaining traction
- **Visa's motion to dismiss was denied** in June 2025. Case ongoing under Judge John Koeltl in SDNY.
- Trump administration continuing the Biden-era case — bipartisan concern about interchange costs
- **Why it matters**: Increased regulatory scrutiny means compliance is more important than ever. Errors or anomalies could have amplified legal/reputational consequences.

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
| FY2025 net revenue | ~$40B (up 11% YoY) |
| Q1 FY2026 net revenue | $10.9B (up 15%) |
| Transactions processed (FY2025) | ~258B (901M/day average) |
| Total payments volume | ~$14+ trillion |
| Cards in circulation | ~4.3B globally |
| Countries/territories | 200+ |
| Transactions per second (peak) | 65,000+ |
| Employees | ~26,500 |
| Net profit margin | ~50%+ |
| Value-Added Services revenue | $10.9B (up 24% YoY) |
| Visa Direct transactions (FY2025) | 12.5B |
| Cross-border volume growth | 13% constant-dollar |
| US regulated debit interchange cap | ~$0.21 + 0.05% + $0.01 |
| US credit/debit volume split | ~60/40 by txn count (debit higher volume, lower ticket) |
| Rate update cycle | April and October |
| Consumer credit interchange cap (settlement) | 1.25% for 8 years (pending approval) |

---

## "Why Visa?" Answer Framework

> "Three things drew me to this role. First, the scale — Visa processes over 250 billion transactions a year, so even small improvements in compliance monitoring have outsized financial impact. That's the kind of data problem I want to work on. Second, the interchange space is uniquely dynamic right now — the CEDP transition is fundamentally changing how commercial interchange is qualified, the DOJ antitrust suit is increasing scrutiny on debit routing, the merchant settlement is introducing rate caps, and the Durbin cap may be lowered. This team is right at the center of all of it. Third, I'm excited about building analytical infrastructure that scales — the JD mentions Airflow, version control, and dashboards, which tells me this team is moving toward automated, production-grade monitoring rather than ad-hoc analysis. That's exactly the kind of work I want to do."
