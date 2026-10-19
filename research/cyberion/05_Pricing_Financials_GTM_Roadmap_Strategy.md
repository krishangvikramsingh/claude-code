# Part 5: Pricing (§11), financial model (Deliverable I), engineering roadmap (Deliverable J), go-to-market (Deliverable K), international (§18), 3–5-year strategy (Deliverable L)

Evidence labels **[F] [D] [I] [H] [PK]** and source IDs (S#) are as defined in [SOURCES.md](SOURCES.md). All money is in INR, excluding GST.

---

## Stage 5–6 summary: business design

- **Prices are hypotheses**, anchored between local calculators (₹5,000 one-time, S25) and Western monitoring/MIS prices (S17, S18, S30).
- **The model is driven mainly by new-account velocity, onboarding fees and ARPA**, not by infrastructure cost.
- **Corrugated alone caps out** at roughly ₹15–20 cr ARR in India (bottom-up, below). Expansion into flexibles and plastics via Pulse is necessary for a larger company. That is why the second product matters, but it comes second.

---

## §11: Pricing strategy

### Pricing models evaluated

| Model | Fit | Verdict |
|---|---|---|
| Per user | SMEs resist paying for floor users; it discourages job-close adoption | **Reject** for floor users; include unlimited "capture-only" users |
| Per plant tier | Matches how owners think ("my factory") | **Primary model** for Margin Control |
| Per machine | Natural for Pulse; scales with value | **Primary model** for Pulse |
| Usage-based (AI credits) | For RFQ extraction and NL reports | Add-on, with an included monthly allowance |
| Hardware + software bundle | Pulse | Yes (Model A) |
| Enterprise licence | Multi-plant | Custom, ≥ ₹3 L/yr |
| Annual contracts | Cash and retention | **Default:** annual prepaid; monthly at +20% |
| Implementation fees | Funds onboarding; filters out tyre-kickers | **Always charge**; the sensitivity analysis shows waiving them nearly doubles peak cash need |
| Premium integrations | Tally live sync, ERP connectors | Add-on |
| Paid support / SLA | Enterprise | Add-on |

### Indicative price scenarios (hypotheses)

| Product | Entry SME | Growing mid-size | Larger industrial |
|---|---|---|---|
| **Margin Control – corrugated** | ₹3,500/mo (₹42k/yr) + ₹15k onboarding | ₹8,000/mo (₹96k/yr) + ₹40k | ₹25–50k/mo + ₹1.5–3 L |
| **Margin Control – flexibles** | ₹6,000/mo + ₹25k | ₹12,000/mo + ₹50–75k | ₹30–60k/mo + ₹2 L+ |
| **Pulse (per machine)** | ₹12k hardware + ₹700/mo (≤ 10 machines) | ₹11k + ₹900/mo with analytics and job costing | Volume pricing ₹10k + ₹600–800/mo; optional HaaS ₹1,500–1,800/mo on 24-month contracts |
| **Pulse Energy** | Meter at cost + 25%; ₹500/meter/mo | Plant bundle ₹6,000/mo up to 10 meters | Custom |
| **AI credits** | 50 RFQ extractions/mo included in Growth | ₹5–10 per extra extraction | Volume |

### Risks of pricing too low

**Bottom line: no tier below ₹3,500/month in year 1.** The reasons:
- Onboarding a non-digital SME takes 1–2 days, plus repeated phone and WhatsApp support.
- Pulse adds hardware replacement and truck-rolls.
- At ₹1,000–2,000 per month, one support visit erases a year of margin.

### How Cyberion avoids becoming a custom-development agency

1. **Published product boundary.** Costing, margin, job actuals and machine actuals. **Not** accounting, payroll, GST invoicing or a general ERP.
2. **Configuration over customisation.** Segment templates; plant tables (waste, flute factors, machine rates); report builder with fixed fields.
3. **Standard onboarding (5 steps):**
   1. Data request checklist.
   2. Import masters.
   3. Reference-quote calibration (20 quotes must match the customer's own within ±1%).
   4. Training (2 sessions).
   5. 30-day check-in.
4. **Reusable connectors only.** A customer-specific integration is built only if it becomes a product connector usable by ≥ 3 customers. Otherwise it is paid at a rate card (e.g. ₹15,000/day) with no long-term maintenance promise.
5. **Paid change requests.** Anything outside configuration goes to a public roadmap vote, or is paid work that Cyberion owns and productises.
6. **Say no** to plant-specific forks of the code.

---

## Deliverable I: Financial model

**Files:**
- [model/financial_model.py](model/financial_model.py): all assumptions in code, editable.
- [model/monthly.csv](model/monthly.csv): 36 months × 3 scenarios.
- [model/summary.md](model/summary.md): tables for all scenarios.
- [model/sensitivity.md](model/sensitivity.md).

> These are **scenarios, not predictions**. The account-acquisition curve is the least certain input and must be replaced with pilot data by month 6.

### Key assumptions

| Assumption | Conservative | Base | Optimistic | Basis |
|---|---|---|---|---|
| Starting ARPA (software) | ₹4,500/mo | ₹6,000/mo | ₹7,500/mo | Tier mix hypothesis (Starter/Growth) |
| ARPA expansion | 0.6%/mo | 1.0%/mo | 1.2%/mo | Upsell to Growth, WIP, Tally connector [H] |
| Onboarding fee | ₹20k | ₹30k | ₹40k | Tier mix |
| Monthly logo churn | 3.0% | 2.0% | 1.5% | SME SaaS typical range [I]; measure from pilots |
| New accounts, Y1 total | 15 | 29 | 45 | Founder-led selling in one cluster [H] |
| New accounts, Y2 / Y3 | 43 / 60 | 90 / 138 | 144 / 240 | Sales hire + partners [H] |
| Pulse attach (from M13) | 10% | 20% | 30% of new accounts × 4 machines | [H] |
| Pulse hardware price / cost | ₹12,000 / ₹6,500 | same | same | Part 3 BOM ranges [I] |
| Pulse SaaS | ₹900/machine/mo | same | same | [H] |
| Founder draw | ₹1.0 L/mo | same | same | Assumption |
| Engineer 1 (from M3) | ₹85k/mo loaded | same | same | Indian market [I] |
| Customer success | 1 FTE per 60 accounts at ₹45k (in COGS) | same | same | SME hand-holding [I] |
| Sales executive | from M13 | from M10 | from M8 | ₹60k + 10% of first-year contract value |
| Engineer 2 (IoT/data) | from M16 | from M13 | from M10 | ₹1.1 L/mo |
| Cost to serve per account | ₹700/mo (infra ₹250, AI ₹150, support ₹300) | same | same | [I] |
| Marketing | ₹40k/mo from M4; trade fairs ₹3–4 L in M9, M21, M33 | same | same | IndiaCorr-type events (S62) |
| Pulse development | ₹5 L across M10–M12 | same | same | Part 3 |

### Results

| Scenario | Peak cumulative cash need | Sustained operating break-even | Month-36 accounts | Month-36 MRR | Month-36 ARR |
|---|---|---|---|---|---|
| Conservative | **₹92 L** (still burning at M36) | Not within 36 months | ~84 | ₹4.9 L | ₹0.59 cr |
| Base | **₹34 L** | Month 22 | ~205 | ₹18.8 L | ₹2.26 cr |
| Optimistic | **₹21 L** | Month 13 | ~364 | ₹45 L | ₹5.4 cr |

**Base case: monthly detail for year 1, quarterly for years 2–3 (₹ lakh)**

| Period | New | Accounts | MRR | Revenue | Gross margin % | Opex | Net | Cum. cash |
|---|---|---|---|---|---|---|---|---|
| M1 | 0 | 0 | 0.00 | 0.00 | – | 1.30 | −1.30 | −1.30 |
| M2 | 0 | 0 | 0.00 | 0.00 | – | 1.30 | −1.30 | −2.60 |
| M3 | 0 | 0 | 0.00 | 0.00 | – | 2.15 | −2.15 | −4.75 |
| M4 | 1 | 1.0 | 0.06 | 0.36 | 64.9 | 2.45 | −2.22 | −6.97 |
| M5 | 2 | 3.0 | 0.19 | 0.79 | 66.8 | 2.45 | −1.92 | −8.89 |
| M6 | 2 | 4.9 | 0.31 | 0.91 | 20.4 | 2.45 | −2.26 | −11.15 |
| M7 | 3 | 7.8 | 0.50 | 1.40 | 38.2 | 2.45 | −1.92 | −13.07 |
| M8 | 3 | 10.7 | 0.69 | 1.59 | 44.2 | 2.45 | −1.75 | −14.82 |
| M9 | 4 | 14.5 | 0.94 | 2.14 | 51.8 | 5.45 | −4.34 | −19.16 |
| M10 | 4 | 18.2 | 1.19 | 2.39 | 55.8 | 5.86 | −4.53 | −23.69 |
| M11 | 5 | 22.8 | 1.51 | 3.01 | 59.8 | 4.95 | −3.15 | −26.84 |
| M12 | 5 | 27.3 | 1.83 | 3.33 | 62.7 | 4.45 | −2.36 | −29.20 |
| Q5 | 18 | 43.4 | 3.12 | 15.20 | 65.1 | 13.93 | −4.03 | −33.23 |
| Q6 | 21 | 61.4 | 4.63 | 20.70 | 67.5 | 14.22 | −0.25 | −33.48 |
| Q7 | 24 | 81.3 | 6.38 | 26.89 | 67.8 | 18.04 | +0.20 | −33.28 |
| Q8 | 27 | 103.0 | 8.36 | 33.78 | 71.2 | 14.87 | +9.20 | −24.08 |
| Q9 | 30 | 126.3 | 10.58 | 41.40 | 72.8 | 15.22 | +14.91 | −9.16 |
| Q10 | 33 | 151.3 | 13.06 | 49.78 | 73.2 | 15.59 | +20.87 | +11.70 |
| Q11 | 36 | 177.7 | 15.81 | 58.93 | 75.4 | 19.98 | +24.44 | +36.14 |
| Q12 | 39 | 205.4 | 18.82 | 68.89 | 75.2 | 16.39 | +35.41 | +71.55 |

Gross margin dips in M6–M8 because the first customer-success hire is carried as COGS before there are enough accounts to absorb it.

### Unit economics (base case, steady state)

- **ARPA:** ~₹7,500–9,000/month (incl. expansion); **gross margin:** ~73–75%.
- **Contribution per account:** ≈ ₹5,500–6,500/month.
- **CAC (blended, base, Y2):** (sales salary + commission + marketing + founder sales time) ÷ new accounts ≈ ₹25–40k [I].
  - **CAC payback:** about 4–7 months of contribution, or faster after onboarding fees.
  - Founder time is unpriced in this calculation.
- **Lifetime at 2% monthly churn:** ~50 months, so LTV/CAC is comfortably above 3 **if** churn holds. At 4% churn LTV halves (sensitivity below).

### Sensitivity: what matters most

| One change from base | Peak cash ₹L | Break-even month | M36 ARR ₹cr |
|---|---|---|---|
| Base | 33.6 | 22 | 2.26 |
| ARPA −30% | 44.2 | 22 | 1.63 |
| New accounts −30% | 46.5 | 22 | 1.59 |
| New accounts +30% | 27.3 | 16 | 2.93 |
| Churn 4%/mo | 36.1 | 22 | 1.85 |
| CS capacity 30 accounts/person | 37.3 | 22 | 2.26 |
| No ARPA expansion | 38.5 | 22 | 1.64 |
| **Onboarding fee waived** | **61.1** | 23 | 2.26 |

**Measure in the first pilots:**
1. Audit-to-subscription conversion rate.
2. Achieved ARPA and tier mix.
3. Onboarding hours per account.
4. Job-close compliance (predicts churn).
5. Support contacts per account per month.
6. Time from first meeting to payment (sales cycle).

### Bottom-up market estimate (not TAM)

| Segment | Reachable ICP plants (method) | Annual contract value | Serviceable ARR |
|---|---|---|---|
| Corrugated: automatic + upper semi-automatic | ~300–500 automatic (S1, S2) + ~15–20% of 10,000–12,000 semi-automatic ≈ **2,000–2,900** [I] | ₹72k (blended ₹6k/mo) | **₹14–21 cr** |
| Flexible converters (organised) | No reliable count found; **1,000–2,000 is a hypothesis** to verify with association directories [H] | ₹1.4 L | ₹14–28 cr |
| Plastics processors with ≥ 10 machines | 30,000–50,000 units (S6, S7) × 10–15% [H] ≈ **3,000–7,500** | Pulse: 15 machines × ₹900 × 12 ≈ ₹1.6 L + costing | ₹50–120 cr |

**Obtainable in 36 months (base):** ~205 accounts, ₹2.3 cr ARR, about 10% of corrugated SAM plus early flexibles. The arithmetic shows **plastics plus Pulse is where scale must eventually come from**, which is why it is the second product.

### Funding implication

- **Base case:** needs ~₹35 L of runway plus a 30% buffer (≈ ₹45–50 L).
- **Conservative case:** needs ~₹90 L+ and still does not break even. **Do not fund the conservative path:** if month-9 gates fail, re-segment rather than spend through it.
- **Sources:** founder capital, revenue from audits and onboarding, then angels or government programmes. The Startup India Seed Fund Scheme and state startup grants exist [PK]; verify current terms before relying on them.

---

## Deliverable J: Engineering roadmap

| Phase | Duration (lean / staffed) | Skills | Dependencies | Indicative budget (lean / staffed) | Deliverables | Key metrics | Go / no-go | Principal risks |
|---|---|---|---|---|---|---|---|---|
| **1. Research and validation** | 6–8 wk / 4–6 wk | Founder (sales and domain), 1 analyst (optional) | Cluster access; PackQuote audit | ₹1.5–3 L / ₹4–6 L (travel, audits, prototype) | 35–45 interviews; 10 walk-throughs; 5 paid audits; PackQuote technical audit; clickable prototype | Audits sold; gap measured; WTP | See H7 week 6 | Founder time split between selling and building |
| **2. MVP (Margin Control)** | 8–12 wk / 6–8 wk | Full-stack engineer, founder as product owner, part-time designer | Phase 1 go | ₹4–6 L / ₹10–15 L | Versioned costing engine; price book; bulk re-price; job-close PWA; quote-vs-actual; Tally CSV/XML import; RBAC; audit log; billing | 20 reference quotes within ±1%; job close < 30 s | 5 paying accounts | Legacy PackQuote code debt |
| **3. Paid pilots** | 8–12 wk (overlaps 2) | + CS/implementation executive | MVP | ₹3–5 L / ₹6–8 L | 5–10 live plants; baseline vs pilot reports; onboarding playbook v1 | Compliance ≥ 80%; NPS; conversion | ≥ 3 audits show ≥ 1% gap and convert | Compliance; owner attention |
| **3b. Pulse prototype** (starts only after 15 accounts or 3 pilot commitments) | 12–20 wk / 10–14 wk | Embedded engineer (ESP-IDF), hardware designer (contract), licensed electrician partner | Customer demand | ₹5–8 L / ₹10–15 L | Off-the-shelf industrial ESP32/gateway pilot → custom PCB rev A/B; firmware with OTA and secure boot; EMC pre-scan; WPC ETA; installation SOP | ≥ 95% state accuracy; < 2 h install; 0 safety incidents | 3 paid Pulse pilots, ≥ 2 convert | EMC, field failures, certification scope (MTCTE) |
| **4. Commercial product** | 3–6 mo / 2–4 mo | + 2nd engineer, + sales | Pilot conversions | ₹10–15 L / ₹25–35 L | Self-serve onboarding; billing; monitoring; documentation; security hardening (pen-test); Pulse batch 100 units with test jig; spares and RMA process | Churn < 2%/mo; onboarding < 5 days; gross margin > 65% | 50 accounts | Support load; hardware returns |
| **5. Repeatable growth** | 6–18 mo | + CS team, partner manager | — | Revenue-funded | Partner programme; Flexibles edition; Tally live connector; EUROMAP/OPC UA connector; scheduling; RFQ document AI | NRR > 100%; partner-sourced > 30% of new | 150+ accounts, positive operating cash | Spreading across too many segments |

**Notes:**
- **Hardware timelines** (EMC fixes, certification, enclosure tooling, component lead times) are longer and less predictable than web software. Do not commit Pulse delivery dates to customers before rev B passes the pre-compliance scan.
- **Lean vs staffed:** "lean" means the founder plus 1 engineer plus contractors. "Staffed" adds a product designer, an embedded engineer and a CS hire from the start. It is roughly 2× the cost for ~30% less elapsed time; the bottleneck is customer learning, not coding.

---

## Deliverable K: Go-to-market plan for India

### Cluster selection method (to finalise in weeks 1–2)

Score candidate clusters on:
- **Density** of ICP plants within 60 km;
- **Founder access** (day trips, language, network);
- **Association activity**;
- **Price pain** (recent kraft or resin shocks);
- **Fit** for later Pulse (co-located plastics processors).

**Candidates to evaluate (hypotheses to verify with association directories and GST/IndiaMART listings):**

| Cluster | Why consider | Caveat |
|---|---|---|
| Ahmedabad–Vadodara–Vapi–Daman–Silvassa belt (Gujarat/DNH) | Packaging and plastics density; DNH claims ~28% of India's plastic production (S48); integrated corrugated + plastics | Claim is promotional; verify unit counts |
| Mumbai–Thane–Bhiwandi–Vasai–Palghar | Many corrugated and flexible converters serving FMCG/pharma [I] | Expensive travel time |
| Delhi NCR (Faridabad, Noida, Sonipat, Bahadurgarh) | Northern corrugated association activity; complaints documented (S4); IMM deployments by local IoT startups (S22) | Competitive for monitoring |
| Pune–Chakan | Auto-component packaging and plastics [I] | — |
| Chennai–Hosur–Sriperumbudur | Auto/electronics packaging, moulders [I] | — |
| Baddi / Himachal | Pharma packaging; corrugators under stress (Tribune, S4 series) | Remote |

**Rule:** choose **one** cluster within day-trip distance of the founder. Do not pick it for size alone. The second cluster comes only after 10 paying customers.

### Path to 10 / 25 / 100 / 500 customers

| Milestone | Primary channel | Tactics | Proof assets | Metrics |
|---|---|---|---|---|
| **First 10** (M1–M7) | Founder-led direct | Warm intros (existing PackQuote users, kraft dealers, CA/Tally partners); paid Margin Audit; owner review meetings | Audit reports (anonymised with consent) | Audits sold/offered ≥ 30%; audit→annual ≥ 60% |
| **25** (M8–M12) | Founder + 1 sales executive; association talks | ICCMA/regional association sessions; WhatsApp price-bulletin with dealers; referral credit (1 month free per referral) | 2 named case studies with ₹ figures | Lead→audit ≥ 15%; cycle < 45 days |
| **100** (Y2) | Sales team + partners | Second cluster; IndiaCorr Expo (S62); Tally partners (15–20% commission); flexibles edition | Benchmark report (opt-in, anonymised); video testimonials | Partner-sourced ≥ 30%; CAC < ₹40k |
| **500** (Y3–Y4) | Partners + inside sales + Pulse cross-sell into plastics | Machine-dealer installation partners; energy auditors; regional resellers | ROI calculator; certified installers | NRR > 105%; churn < 1.5%/mo |

### Repeatable sales process

1. Lead (referral/association/dealer).
2. 20-minute call: qualify turnover, ICP, owner availability.
3. Factory visit (45 min interview + walk-through; H2).
4. Margin Audit proposal (H4) with payment.
5. Audit delivery and owner review.
6. Annual plan proposal: tier, onboarding, start date.
7. Onboarding (5 steps).
8. 30-day check-in with compliance report.
9. Quarterly margin review (this drives retention and upsell).
10. Renewal at month 11, with a value summary attached.

**Selling outcomes, not AI.** Every conversation centres on the customer's own rupees:
- "₹X stuck in un-revised prices since the last mill hike."
- "Y SKUs below 5% margin."

AI is mentioned only as "it reads your RFQ PDFs for you" once the core value is accepted.

### Initial outreach plan (first 6 weeks)

- Build a list of 150 ICP plants in the chosen cluster (association member lists, IndiaMART, GST search, dealer referrals).
- Send 60 personalised WhatsApp/phone approaches through a referrer.
- Target 35 meetings, 25 interviews and 10 walk-throughs.
- Make 10 audit offers and close 5 audits.
- **Track weekly:** contacts, meetings, interviews, audits offered, audits paid, and conversion at each stage.

---

## §18: International expansion

| Factor | India (beachhead) | Latvia | Larger EU option (e.g. Poland, Germany) [I] |
|---|---|---|---|
| Customer concentration | Thousands of ICP plants (S1, S6) | Small: individual plastic-packaging firms of tens of employees (S49) | Larger converter base [PK] |
| Competitor maturity | Fragmented, low-price | Mature EU MIS/MES vendors sell into the region [I] | Mature (Label Traxx, Cerm, Kiwiplan, Guidewheel-type) |
| Localisation | English/Hindi/regional, Tally | Latvian/Russian/English; EU accounting | Local language, DATEV etc. |
| Data protection | DPDP (S39) | GDPR | GDPR |
| Hardware certification | WPC ETA (S42), MTCTE to verify (S43) | CE: RED + EN 18031 [PK], CRA from Dec 2027 (S40), Data Act access-by-design (S41) | Same |
| CAC and support | Low cost, but field-heavy | High travel/support cost from India | High |
| Advantage over India | — | **None evident** unless the founder has a specific network, partner or funding there | Larger ACVs, but heavy compliance |

**Recommendation: delay international expansion** until there are ≥ 150 Indian accounts, a stable product, and documented ROI case studies.

- **Earliest sensible move:** *software-only* Margin Control for a specific EU segment, via a partner, with **no hardware**, to avoid CE/RED/CRA work.
- **Latvia** only makes sense if the founder has a concrete reason: a customer, partner, residence, grant, or an EU entity needed for funding. Even then, use it as an EU legal and sales base for software, not as a primary market.
- No public evidence found here makes Latvia's packaging or plastics sector a better market than India.

---

## Deliverable L: 3–5-year company strategy (conditional)

### Strategy options compared

| Strategy | Capital need | Gross margin | Operational complexity | Competitive advantage | Risk |
|---|---|---|---|---|---|
| A. Focused vertical SaaS (packaging costing only) | Low | 75–85% | Low | Domain depth | Capped market (~₹15–40 cr SAM) |
| B. Portfolio of specialised products (costing + Pulse + modules) | Medium | 60–75% blended (hardware dilutes) | Medium–High | Hardware–software loop; job-level actuals | Spreading thin |
| C. Integrated industrial platform | High | Variable | Very high | Data and integration network | Premature without scale |

**Recommendation:** **A → B → (conditional) C.**
- Stay A until ~50 accounts.
- Become B with Pulse once the triggers below are met.
- Consider C only beyond ~₹15–20 cr ARR, with external capital.

### Conditional stages and milestones

| Stage | Trigger (evidence required) | What gets unlocked | Organisation |
|---|---|---|---|
| 1. Focused product (Y1) | 5 paid audits converted | Margin Control MVP → commercial | Founder, 1–2 engineers, 1 CS |
| 2. Connected SaaS modules (Y1–Y2) | 25 accounts, churn < 2%, job-close ≥ 80% | WIP, Flexibles edition, Tally live | + sales, + CS |
| 3. Retrofit IIoT (Y2) | 15+ accounts asking for automatic actuals, or 3 paid Pulse pilots | Pulse hardware batch of 100; plastics beachhead | + embedded engineer, installation partners |
| 4. Analytics and AI decision support (Y2–Y3) | ≥ 100 accounts and ≥ 50k closed jobs | Learned waste curves, rate calibration, RFQ AI, scheduling | + data engineer |
| 5. Platform (Y4–Y5) | ≥ ₹15 cr ARR, NRR > 110%, partner demand for an API | Public API, partner ecosystem, opt-in benchmarks, possibly an EU software entry | Product teams per segment; partner team |

**Hardware scale-up criteria:**
- Stay with contract manufacturing until 1,000+ units a year.
- Hardware RMA rate < 2%.
- Hardware never exceeds ~30% of revenue, to protect margins and working capital.

**Build internally:**
- Costing engine and segment models.
- Data model.
- Firmware and security.
- Customer success playbooks.

**Partner for:**
- PCB assembly and enclosure manufacturing.
- Electrical installation.
- Certified meters and sensors.
- Tally/ERP distribution.
- Certification testing labs.
- Cloud infrastructure.

**Hiring triggers:**
- Each engineer added at roughly +₹10–15 L ARR.
- Customer success at 1 per 60 accounts.
- Sales hires once founder-led conversion is documented: ≥ 10 deals with a repeatable script.
