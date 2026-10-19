# Part 6: First 90 days (Deliverable M), founder decision register (Deliverable N) and final recommendation

Evidence labels **[F] [D] [I] [H] [PK]** and source IDs (S#) are as defined in [SOURCES.md](SOURCES.md).

---

## Stage 7 summary: execution planning

- **First 90 days:** sell before building. The deliverable of weeks 1–6 is **paid evidence**: audits, letters of intent and measured gaps, not code.
- **Code work:** limited to (a) hardening PackQuote's costing engine and (b) a thin Margin Control MVP that the audits prove is needed.
- **Hardware:** one 2-week **feasibility spike** on the bench using off-the-shelf parts. No PCB design and no hardware spend beyond about ₹40,000.

---

## Deliverable M: First 90 days, week by week

**Budget for 90 days (lean):** ≈ ₹6–8 L.
- Founder draw ₹3 L.
- Engineer from week 9 ₹0.9 L.
- Travel and visits ₹0.8 L.
- Prototype design and tools ₹0.5 L.
- Hardware spike ₹0.4 L.
- Legal (NDA, MSA, privacy policy) ₹0.4 L.
- Contingency ₹1 L.

**Offset:** 5 paid audits bring in ~₹1.25 L.

| Week | Research and discovery | Factory visits | Product / engineering | Customer acquisition | Spend priority | Milestone (measurable) |
|---|---|---|---|---|---|---|
| **1** | Audit PackQuote: segments supported, customers, usage, code quality, costing accuracy on 20 known quotes. Choose a cluster using the Part 5 method | — | Engine test harness started | List 150 ICP plants; identify 10 warm referrers (existing PackQuote users, kraft dealers, CAs) | None | PackQuote audit note; cluster chosen; list built |
| **2** | Finalise interview guide (H2), audit template, NDA and pilot terms | 3 | Reference-quote tests | 20 outreach contacts; 8 meetings booked | Legal templates | 8 meetings booked |
| **3** | Interviews 1–8 | 3 | Clickable re-pricing + quote-vs-actual prototype (Figma or PackQuote UI stub) | Offer first audits | Travel | ≥ 6 interviews; 2 audit offers |
| **4** | Interviews 9–16; first synthesis | 2 | Prototype tested with 3 owners (V4) | 20 more outreach contacts | — | ≥ 2 audits **paid** |
| **5** | Interviews 17–25; plastics interviews 1–5 (for the Pulse thesis) | 2 | Audit tooling: import scripts for quotes, invoices and Tally exports | Deliver audit #1 | — | Audit #1 delivered |
| **6** | **Gate 1 review** (H7) | — | **Hardware spike:** off-the-shelf ESP32 + 2 CTs + Modbus meter on a bench motor; measure state accuracy and noise | Deliver audits #2–3; offer annual plans | Hardware spike ₹40k | **Go:** ≥ 3 audits paid, ≥ 15 interviews with concrete losses. **Pivot:** < 2 audits paid → test flexible converters with the same offer for 3 weeks |
| **7** | Synthesis: real gap distribution; pricing reaction (V8) | 2 | MVP spec frozen: price book, bulk re-price, job-close PWA, quote-vs-actual, Tally import | Close first annual plan | — | Spec signed off; 1 contract |
| **8** | Flexible-converter interviews 1–5 | 2 | MVP sprint 1: price book + re-price | Audits #4–5 | — | ≥ 5 audits completed in total |
| **9** | Plastics interviews 6–10 (Pulse) | 2 | Engineer #1 joins; sprint 2: job-close PWA (offline) | 2 more annual plans | Engineer salary | ≥ 3 contracts or LOIs with payment dates |
| **10** | — | 1 | Sprint 3: quote-vs-actual report; Tally CSV/XML import | Onboard customers 1–3 (5-step playbook) | — | 3 customers live on the price book |
| **11** | Job-close compliance measurement (V5) | 3 (onboarding) | Sprint 4: margin alerts; escalation pack PDF; audit log | Referral asks; first association contact | — | ≥ 70% job-close compliance at 2 plants |
| **12** | Retrospective; update model with real ARPA, cycle time and onboarding hours | — | Bug fixing; security basics (backups, RLS checks, MFA) | Close contracts 4–5 | — | **Gate 2** (below) |
| **13** | Write the next-quarter plan | — | Release v1.0 Margin Control | Ask for case-study consent | — | Plan approved |

### Day-90 stop / continue / pivot criteria

| Outcome at day 90 | Decision |
|---|---|
| ≥ 5 paying annual accounts (or 3 + 5 LOIs); ≥ 2 audits with gap ≥ 1% of revenue; job-close ≥ 70% at ≥ 2 plants | **Continue.** Hire customer success at month 6; plan the sales hire for month 10; keep Pulse on hold until 15 accounts |
| Audits sell, but customers will not subscribe | **Reposition.** Sell Margin Audit as a recurring quarterly service (₹15–25k/quarter) while simplifying the software; re-test pricing |
| Gap is small (< 0.5% of revenue) in most audits | **Pivot the wedge** to WIP/job control (O5) or to flexibles (O2), where costing complexity is higher |
| No one pays for anything after 10 serious offers | **Stop** the corrugated thesis. Run the same 6-week protocol on plastics energy/runtime (O3/O4) before writing any more code |

---

## Deliverable N: Founder decision register

| # | Decision | Recommendation | Evidence supporting it | Consequence of getting it wrong |
|---|---|---|---|---|
| N1 | What exactly is PackQuote today (segments, customers, revenue, code health)? | Audit in week 1 before anything else | Not available to this research; every timeline depends on it | Building Margin Control on an engine that cannot be trusted; months lost |
| N2 | First segment: corrugated vs flexible | **Corrugated first**, flexibles second | Thousands of units (S1, S2); kraft ≈ 90% of input cost, ~5% margins (S4); documented volatility (S5); simpler, standardisable costing | If wrong, slower sales. Mitigated by testing flexibles if gate 1 fails |
| N3 | Software first or hardware first? | **Software first** (Margin Control); Pulse after 15 accounts or 3 paid Pulse pilots | Monitoring is crowded (S16–S22); hardware adds certification (S42, S43), installation and working-capital burden | Hardware first risks cash burn in a crowded market without a differentiated story |
| N4 | Which cluster? | One cluster within day-trip distance of the founder, scored on density, access and association activity | Sales practicality beats cluster size (brief requirement); clusters listed in Part 5 are hypotheses | Wrong cluster means long travel and slow learning; switch after 4 weeks if meetings < 8/week |
| N5 | Price level | Starter ₹3,500, Growth ₹8,000, Multi-plant ₹25k+/month; always charge onboarding | Anchors S25 (₹5k calculators) vs S17/S18 (USD monitoring); the model shows onboarding fees materially reduce cash need | Too low: support costs swamp margin. Too high: slow adoption. Test with V8 |
| N6 | Commercial model for Pulse | **Model A:** hardware sale + annual SaaS prepaid; HaaS only for > 30 machines with deposit | Working-capital protection; Indian SMEs buy small capex [I] | HaaS without capital strands devices on churned customers |
| N7 | Build custom PCB or buy industrial ESP32/gateway hardware for pilots? | **Buy for pilots**; design own PCB only after the I/O mix is proven | Avoids EMC iteration and certification before demand exists | Early PCB spend wasted if requirements change |
| N8 | AI scope in year 1 | Limited to RFQ extraction (human-approved) and margin explanation text; **no LLM in pricing maths** | Deterministic costing is auditable; LLM errors in prices destroy trust | An AI pricing error in front of an owner can lose the account and referrals |
| N9 | Data policy | Customer owns data; no cross-tenant pooling of prices or structures; opt-in anonymised aggregates only | DPDP Act/Rules (S39); confidentiality expectations of competitors in the same cluster [I] | One leak between competing box makers in a cluster could end the business locally |
| N10 | Custom development requests | Rate card; build only reusable connectors (≥ 3 customers) | Agency drift destroys SaaS margins (brief requirement) | Founder time absorbed by bespoke work; product stalls |
| N11 | International (Latvia/EU) | **Delay** until ≥ 150 Indian accounts; software-only first; hardware only after CE/RED/CRA readiness | Small Latvian market (S49); EU regulatory load (S40, S41, [PK] RED) | Premature expansion splits a tiny team and adds compliance cost without customers |
| N12 | Funding | Bootstrap through gate 2 using audit and onboarding revenue; raise ~₹50 L only after 15–25 paying accounts | Base-case peak cash ~₹34 L (model); conservative path not worth funding | Raising too early dilutes on hypotheses; raising too late stalls hiring |
| N13 | Safety boundary | Monitoring and decision support only; never control or safety functions; licensed electricians install | EUROMAP 77 itself excludes control/safety (S32); electrical safety rules [PK] | Injury, liability, warranty disputes and loss of trust across the cluster |

---

## Final recommendation (falsifiable)

**What to build first.**
- **PackQuote Margin Control:** a kraft-price-linked bulk re-pricing and quote-vs-actual job-profitability layer on top of PackQuote.
- Includes a 30-second mobile job close, Tally import, and an audit trail.
- Software only; deterministic costing; LLM used only for explanation text and, later, RFQ extraction with human approval.

**For whom.** Indian corrugated box manufacturers with ₹5–150 cr turnover, automatic or larger semi-automatic plants, using Tally and Excel, in **one** cluster within reach of the founder. Flexible-packaging converters come next on the same engine.

**At what indicative price.**
- ₹3,500 / ₹8,000 / ₹25,000+ per month (annual prepaid, excluding GST), plus ₹15k–₹3 L onboarding.
- Entry is via a ₹25,000 **Margin Audit** credited to year one.

**How to validate it.**
- 25+ owner interviews and 10 walk-throughs.
- 5 paid Margin Audits that measure the real quote-vs-actual and re-pricing-lag gap on the customer's own records.
- ≥ 3 annual contracts by day 90.

**What must be true before scaling.**
1. Most audited plants show a recoverable gap of **≥ 1% of revenue**, which is at least 5× the subscription price.
2. **≥ 80% job-close compliance** at most live plants (without it the product is just a calculator).
3. **Logo churn < 2%/month** through month 9.
4. **Audit-to-subscription conversion ≥ 50%**, with a sales cycle under 45 days.

**What would disprove the thesis:**
- Audits find small gaps (< 0.5% of revenue).
- Owners will not pay a recurring fee once the audit is done.
- Floor staff will not record actuals even with a 30-second flow.

**What not to build now:** generic OEE dashboards, vibration predictive maintenance, camera inspection, LLM factory copilots, closed-loop control, custom ERP features, and EU expansion.

**What comes second, and when.**
- **Cyberion Pulse:** a non-invasive retrofit node (split-core CTs, isolated pulse input, Modbus to certified energy meters) on ESP32-S3 with secure boot, signed OTA and an offline buffer.
- Sold as hardware (₹11–12k per machine) plus ₹700–1,200 per machine per month, feeding machine hours, kWh and counts into job costing.
- Built after **15 paying Margin Control accounts or 3 paid Pulse pilots**, and taken into plastics clusters as the path beyond the ~₹15–20 cr ARR ceiling of corrugated costing alone.
