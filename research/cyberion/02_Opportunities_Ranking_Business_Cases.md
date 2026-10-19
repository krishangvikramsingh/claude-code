# Part 2: Opportunity mapping, ranking (Deliverable C) and top-five business cases (Deliverable D)

Evidence labels **[F] [D] [I] [H] [PK]** and source IDs (S#) are as defined in [SOURCES.md](SOURCES.md).

---

## Stage 2: Technology-to-problem matrix

**Key:**
- ● best primary technology
- ◐ useful supporting role
- ○ adds complexity without clear value now
- blank = not relevant

| Problem cluster (pain-point IDs) | Deterministic software / workflow | Rules + statistics | Classical ML | LLM / RAG / document AI | Non-invasive IoT (CT, pulse, Modbus) | PLC/OEM interface (EUROMAP, OPC UA) | Machine vision | Benefit | Build cost | Integration difficulty | Time to pilot | Commercial potential |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Quote costing and re-pricing (CB1, CB2, CB6, FX1, LB1, LB2, CP1, BX1) | ● | ◐ alerts | ○ | ◐ explain margins, draft emails | | | | High | Low | Low | 2–6 wk | **High** |
| Quote-vs-actual job profitability (CB3, CB5, FX2, FX7, EX1, EX2) | ● | ◐ variance thresholds | ◐ later: waste-curve fitting | ○ | ◐ auto actuals (Pulse) | ◐ | | High | Low–Med | Med (shop-floor capture) | 6–10 wk | **High** |
| WIP, job tickets, dispatch (PK2, PK5, FX4, FX6) | ● | ◐ delay alerts | | ◐ natural-language status query, later | ◐ | | | Med | Low | Low | 4–8 wk | Med |
| Scheduling (PK1, CB4, IM7) | ● heuristics / ILP | ◐ | ○ | ○ | ◐ | | | Med–High | Med–High | Med | 3–6 mo | Med |
| Runtime, downtime, cycle (PK4, IM1, IM2, CB7, CP2) | ◐ reason codes | ● state detection by thresholds | ◐ anomaly detection, later | ○ | ● | ◐ newer machines | | Med–High | Med | Med (electrical access) | 2–4 mo | Med (crowded) |
| Energy per kg, utilities (IM3, EX3, UT1, UT2, CB10) | ◐ | ● normalisation, baselines | ◐ forecasting, later | ○ | ● certified meters over Modbus | | | Med–High | Med | Med | 2–4 mo | Med |
| Process parameters and quality (IM4, IM6, IM8, IM9, CB9) | ◐ settings library | ◐ SPC | ◐ | ◐ SOP search (RAG) | ◐ | ● | | Med | Med–High | High | 4–9 mo | Low–Med |
| Print defect inspection (FX5, CP) | | | ● | | | | ● | High for large plants | High | High | 6–12 mo | Low for Cyberion |
| RFQ/PO/spec intake (PK6) | ◐ | | | ● extraction with human approval | | | | Low–Med | Low–Med | Low | 4–6 wk | Low–Med |
| Compliance records (BX2) | ● | ◐ | | ◐ document parsing | | | | Low–Med | Low | Low | 4–8 wk | Low–Med |

**Where to combine technologies, and where not to:**

- **Combine:** quote-vs-actual with Pulse runtime and kWh. Machine hours and energy are the two actual-cost inputs SMEs cannot capture by hand. Here hardware *creates* data that makes the software more valuable, which is the defensible hardware–software loop. It needs a job context: the active job is set by a QR scan at the machine or by the planner's schedule.
- **Do not combine (yet):**
  - LLMs with costing arithmetic. Costs must be deterministic and auditable.
  - ML anomaly detection with first-generation monitoring. Simple thresholds on current draw detect run, idle and stop reliably (S16); ML can come after a fleet of labelled data exists.
  - Vision with anything, until the core business pays its way.

### Where plain software beats AI

| Task | Use | Why not AI |
|---|---|---|
| Box/laminate costing | Formula engine + plant tables | Exact, auditable, explainable; customers must trust every rupee |
| Re-pricing after price change | Bulk recalculation + rules | Deterministic; an LLM adds risk without benefit |
| Margin alerts | Threshold rules | Owners understand "margin < 8%" |
| Run/idle/stop detection | Current thresholds with hysteresis, learned per machine from one shift (S16) | Works with no training data |
| Approval workflows | Workflow engine | — |
| Tally integration | Connector | — |

### AI use-case specifications (only where AI earns its place)

| Use case | Input data | Output / decision supported | Model | Better alternative? | Training data / quality | Inference cost / latency | Failure modes, confidence | Human approval | Expected value | Deployment |
|---|---|---|---|---|---|---|---|---|---|---|
| **RFQ / spec extraction** (PK6) | PDF drawings, emails, WhatsApp photos of specs | Pre-filled quote draft: dimensions, ply, print colours, quantity | Vision-capable LLM or OCR + LLM structured extraction to a JSON schema | Rules fail on unstructured text; this is a genuine LLM fit | Zero-shot first; build an evaluation set of 200 real RFQs per segment (with consent) | ~₹1–5 per document at current API prices [I]; seconds | Wrong dimension or unit (mm vs inch) → wrong price. Show the source snippet next to each field; confidence per field | **Always**: the estimator confirms every field | Minutes saved per RFQ; faster turnaround | Cloud API; redact customer names if required |
| **Margin explanation and negotiation brief** (CB1, CB6) | Deterministic costing outputs, price history | Plain-language "why this SKU's margin fell and what price restores 12%", plus a draft revision email | LLM with numbers passed in, never computed by it | A template works for v1; use LLM for v2 polish | None; prompt plus evaluation set | Low | Hallucinated numbers. **Mitigation:** the LLM may only reference numbers supplied in a structured context; output is checked by regex against the source values | Owner sends | Faster, better-argued price revisions | Cloud |
| **Waste-curve learning** (FX2, LB1, CB3) | Job actuals: run length, colours, substrate, waste kg | Predicted makeready and run waste per job for quoting | Regularised regression / gradient boosting per plant; start with a parametric curve (fixed + variable waste) | A parametric fit is enough until roughly 300+ jobs | Plant's own job history; needs ~100–300 closed jobs | Negligible | Overfitting on small samples. Show the confidence band; fall back to the plant default | Estimator accepts suggested waste % | Better short-run pricing | Cloud |
| **Runtime anomaly and maintenance hints** (IM2, IM9, UT1) | Current waveforms, cycle times, energy | "Cycle time up 12% since Tuesday on M7"; "compressor loading at night = leaks" | Statistical baselines first (EWMA, control charts); ML later | **Statistics first** | Fleet data with labels from maintenance tickets | Edge or cloud, low | False alarms erode trust. Rate-limit alerts; require 2 confirmations | Maintenance acknowledges | Earlier fault detection | Cloud; edge for buffering |
| **Knowledge assistant over SOPs and settings** (BX3, IM6) | Customer's SOPs, setting sheets, troubleshooting logs | Answers with citations to the customer's own documents | RAG with per-tenant index | Search may suffice | Customer documents only, never pooled | Low | Unsafe advice on process limits. Answers are restricted to cited text; no process-limit recommendations | Yes | Training time; less dependency on experts | Cloud or private |
| **Demand / price forecasting** (BX1) | Kraft/resin price history, orders | Buy-ahead suggestions | Time-series models | Usually poor signal; **not recommended** at first | Long, clean history needed | — | Forecast error mistaken for fact | Yes | Unproven | — |

### Automation: monitoring vs decision support vs control

| Level | Definition | Cyberion position |
|---|---|---|
| 1. Monitoring | Read-only sensing, outside the machine's control circuit (CT clamps on insulated conductors, separate meters, isolated pulse pick-up) | **Yes, from Pulse v1** |
| 2. Decision support | Alerts, reports, recommendations a human acts on | **Yes** |
| 3. Supervisory integration | Reading recipes and setpoints through OEM interfaces (EUROMAP 63/77, OPC UA, Modbus TCP); EUROMAP 77 itself excludes control and safety functions (S32) | Later, read-only, with OEM/customer agreement |
| 4. Supervisory control | Writing setpoints or schedules to machines | **Not without** qualified controls engineering, OEM agreement and a documented risk assessment |
| 5. Safety functions | E-stops, interlocks, guarding | **Never** in Cyberion devices. These belong to certified safety controllers and PLCs |

---

## Stage 3: Commercial evaluation summary

- **Evidence of willingness to pay.** Indian vendors sell corrugation and flexible MIS/ERP with costing, wastage and deckle modules (S24, S26, S27). Even ₹5,000 offline costing software sells (S25). Machine monitoring has paying customers globally (S16–S19) and many Indian sellers (S20–S22).
  - **Gap:** no public evidence of what Indian SMEs pay *per month* for software of this type. This is the top validation item.
- **Buyer.** In SMEs, the **owner/MD** both feels the margin pain and holds the budget. Plant heads and production managers evaluate monitoring; accounts staff can block if Tally workflows change.
- **Competition.**
  - Costing and ERP: medium intensity, with strong incumbents for full ERP but a gap for a focused margin tool [I].
  - Monitoring: high intensity [F].
  - Vision inspection: OEM-dominated [I].

---

## Deliverable C: Opportunity ranking (top 15, transparent weighted scoring)

### Weighting rationale

| Criterion | Weight | Why |
|---|---|---|
| Evidence of willingness to pay | 10 | The scarcest thing for a founder-led company is paying customers, not ideas |
| Severity | 9 | Pain must be large enough to overcome inertia |
| Customer ROI | 9 | SMEs buy on payback, not features |
| Recurring revenue potential | 8 | Determines whether the business compounds |
| Frequency | 7 | Frequent pain means frequent use and retention |
| Time to first pilot | 7 | Cash runway is short; learning speed matters |
| Fit with PackQuote and existing capabilities | 7 | Reuses product, customers and domain knowledge |
| Dev ease, low capital, install ease, data availability, short sales cycle | 6 each | Execution feasibility for a small team |
| Market reach | 5 | Matters, but a deep niche can beat a wide shallow market |
| Low competitive intensity, defensibility | 4 each | Important long term; hard to assess before fieldwork |

Scores are 1–10, where **10 always means better for Cyberion**: easier, cheaper, shorter cycle, *less* competition. The script and data are in [model/scoring.py](model/scoring.py).

| Rank | Opportunity | Sev | Freq | WTP | ROI | Dev ease | Pilot speed | Low capex | Install | Data | Sales cycle | Recurring | Reach | Low comp. | Defens. | Fit | **Score / 100** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| | *Weight* | 9 | 7 | 10 | 9 | 6 | 7 | 6 | 6 | 6 | 6 | 8 | 5 | 4 | 4 | 7 | 100 |
| 1 | **O1 PackQuote Margin Control – corrugated** | 8 | 9 | 6 | 8 | 7 | 9 | 9 | 9 | 8 | 7 | 8 | 7 | 6 | 6 | 10 | **78.7** |
| 2 | **O2 Margin Control – flexible packaging** | 8 | 9 | 6 | 8 | 5 | 8 | 9 | 9 | 7 | 6 | 8 | 6 | 6 | 7 | 9 | **74.8** |
| 3 | **O3 Retrofit runtime/downtime/count monitor (Pulse)** | 7 | 9 | 7 | 7 | 6 | 6 | 6 | 7 | 8 | 6 | 8 | 8 | 3 | 4 | 5 | **66.6** |
| 4 | **O5 Mobile job-ticket, WIP and dispatch tracking** | 6 | 9 | 4 | 6 | 7 | 7 | 9 | 7 | 6 | 6 | 7 | 7 | 5 | 5 | 8 | **65.7** |
| 5 | **O4 Energy-per-kg and utility metering (plastics)** | 7 | 8 | 6 | 7 | 6 | 6 | 6 | 7 | 9 | 6 | 7 | 7 | 5 | 5 | 5 | **65.4** |
| 6 | O11 Kraft/resin price intelligence + supplier quote comparison | 7 | 7 | 5 | 5 | 6 | 7 | 9 | 9 | 6 | 7 | 6 | 7 | 5 | 4 | 8 | 65.3 |
| 7 | O6 Production scheduling | 7 | 9 | 4 | 6 | 4 | 5 | 8 | 7 | 5 | 5 | 7 | 6 | 5 | 6 | 7 | 60.8 |
| 8 | O12 Document AI for RFQ/PO/spec intake | 5 | 7 | 4 | 5 | 6 | 7 | 9 | 9 | 6 | 7 | 5 | 6 | 4 | 3 | 6 | 59.0 |
| 9 | O10 Blown-film giveaway analytics | 7 | 8 | 5 | 7 | 5 | 5 | 7 | 6 | 6 | 5 | 6 | 3 | 5 | 6 | 5 | 58.3 |
| 10 | O7 Compressed-air monitoring | 6 | 7 | 5 | 7 | 6 | 6 | 6 | 6 | 8 | 6 | 5 | 6 | 6 | 3 | 3 | 57.7 |
| 11 | O13 EPR / recycled-content records | 6 | 4 | 6 | 4 | 6 | 6 | 9 | 9 | 6 | 5 | 5 | 5 | 5 | 4 | 5 | 56.6 |
| 12 | O15 Mould shot-counter + PM workflow | 6 | 6 | 4 | 6 | 6 | 6 | 7 | 7 | 7 | 6 | 5 | 5 | 5 | 4 | 4 | 55.9 |
| 13 | O8 Resin-dryer condition monitoring | 7 | 6 | 3 | 6 | 5 | 5 | 6 | 6 | 7 | 5 | 5 | 4 | 6 | 4 | 3 | 51.9 |
| 14 | O9 IMM process-parameter logger (EUROMAP/Modbus) | 6 | 8 | 4 | 5 | 4 | 4 | 6 | 5 | 5 | 5 | 6 | 4 | 5 | 6 | 4 | 51.3 |
| 15 | O14 Camera-based print defect inspection | 8 | 7 | 6 | 6 | 2 | 3 | 3 | 4 | 5 | 3 | 5 | 5 | 3 | 6 | 3 | 48.0 |

### Challenging the ranking

- **Is O1 winning only because of "fit"?** No. Removing the fit criterion still leaves O1 ahead: about 71.7 against 63.1 for O3. O1 wins on time-to-pilot, capital and install ease.
- **O3 has the strongest WTP evidence** (an established global category) **but the weakest competitive position.** Its rank would rise if fieldwork found a sub-segment the incumbents ignore. Plastics moulders with 10–40 hydraulic machines in Tier-2 clusters are the candidate [H].
- **O11 (price intelligence) is absorbed into O1** as a feature rather than sold separately. Price data alone has low defensibility, and free sources exist.
- **O14 (vision) is rejected for now** despite high severity. Build cost, integration, false-reject risk and OEM competition make it a poor first bet for a small team.
- **Sensitivity:** if fieldwork shows **WTP for O1 below ₹2,500/month**, O1's ROI and recurring scores fall to ~5. It would then rank roughly level with O3/O5. In that case the strategy shifts to selling O1 + O5 as a bundled "job control" product (see the decision register).

### Final selection

| Role | Choice | Reason |
|---|---|---|
| **Best initial product** | **O1 PackQuote Margin Control (corrugated)**, with O5 WIP job-close as its data-capture feature | Fastest to revenue; software-only; owner is the buyer; reuses PackQuote |
| **Second product** | **Cyberion Pulse (O3 + O4 in one device)**, first sold to Margin Control customers' bottleneck machines and to injection moulders/extruders | Adds automatic actuals (hours, kWh, counts) that make costing defensible; bridges into plastics |
| **Longer-term platform** | **Job-level cost and performance intelligence** across packaging and plastics: quote → schedule → machine actuals → profitability → re-quote | Compounds data and switching costs; integrates O2, O6, O10, O15 as modules |

**Why the rest wait:**
- **O6 scheduling** needs reliable WIP data first.
- **O12 document AI** has small value per document until quote volume is proven.
- **O13 EPR** is driven by brand owners, with an uncertain final rule text (S38).
- **O7, O8, O9, O15** are channels or features of Pulse, not products.
- **O10** is a narrow segment best served as a Margin Control–Flexibles report.
- **O14** is capital-heavy.

---

## Deliverable D: Top-five business cases

**Pricing note:** prices exclude GST. All prices are **hypotheses** unless a competitor price is cited.

### D1. O1 PackQuote Margin Control – corrugated (FIRST PRODUCT)

1. **Ideal customer profile.**
   - Indian corrugated box manufacturer, ₹5–150 cr turnover.
   - Either one automatic line or a large semi-automatic plant (≥ 15 t/day [H]).
   - 100+ active SKUs and 20+ B2B customers; FMCG, pharma, auto-component or e-commerce buyers.
   - Uses Tally and Excel; has no full ERP, or an ERP whose costing module is unused.
   - Owner involved in pricing.
2. **Problem and current workaround.** CB1–CB6. Owners re-price in Excel after kraft revisions and see job profitability only at year end (S4, S5, S33).
3. **Proposed solution.**
   - **Kraft price book:** supplier, grade, BF and GSM, with an effective date.
   - **Bulk re-price:** every SKU and customer price list is re-costed when a price changes, with a margin-impact report by customer.
   - **Escalation pack:** a cost-index justification PDF to send to buyers.
   - **Job close-out:** from dispatch, capture boxes dispatched, board issued (kg) and rejects (kg). Results go to a quote-vs-actual report with variance alerts.
   - **Monthly "margin leak" report:** the top 20 loss-making SKUs and customers.
4. **Product scope (MVP):** the five features above, plus:
   - PackQuote's existing costing and quotation.
   - Tally master and sales import (CSV/XML first, live connector later).
   - Roles: Owner, Estimator, Dispatch.
   - WhatsApp/PDF sharing.
   - Audit trail on every price change.
   - **Explicitly out of scope:** inventory accounting, GST invoicing, payroll, scheduling.
5. **Technical architecture.**
   - Existing PackQuote web app.
   - Postgres tenant-scoped tables for price books, SKUs, jobs and actuals.
   - Deterministic costing service (pure functions, versioned).
   - Job-close Progressive Web App (PWA) for phones, working offline-first.
   - Background re-pricing jobs.
   - Report generator.
   - Optional LLM for the explanation text only. See Part 3 §15.
6. **Differentiation.** A focused margin outcome rather than a full ERP. Deployable in under a week, no data migration, Tally-friendly. Proof is delivered in the first month through the Margin Audit [I].
7. **Pricing hypothesis.**

   | Tier | Fit | Monthly (annual billing) | Onboarding |
   |---|---|---|---|
   | Starter | Semi-automatic, ≤ ₹10 cr, ≤ 3 users | ₹3,500 | ₹15,000 |
   | Growth | ₹10–75 cr, automatic line, ≤ 10 users, quote-vs-actual, Tally import | ₹8,000 | ₹40,000 |
   | Multi-plant | > ₹75 cr or multiple plants, API, SSO, custom reports | ₹25,000–50,000 | ₹1.5–3 L |

   **Anchors:** offline calculator ₹5,000 one-time (S25). Western machine monitoring sells at $75–125 per machine per month (S17, S18), so per-plant software at ₹8,000/month is far below Western price points but above local calculators. **Validate in interviews.**
8. **Estimated cost to develop and deploy.**
   - MVP increment on PackQuote: 8–12 weeks × (founder + 1 engineer) ≈ ₹4–6 L cash [I].
   - Per-customer onboarding cost ≈ ₹12,000: travel plus 1–2 days of setup.
   - Ongoing cost to serve ≈ ₹700/account/month (infrastructure, AI and support) plus customer success at 1 FTE per ~60 accounts (model assumptions, Part 5).
9. **Customer ROI (worked example; assumptions stated).**
   - Plant: ₹20 cr turnover, material 70% → ₹14 cr material.
   - **Conservative:** 0.25% of material cost recovered (faster re-pricing on a fraction of SKUs) ≈ ₹3.5 L/yr vs Growth cost ₹0.96 L + ₹0.4 L onboarding → **payback ≈ 4.7 months**.
   - **Base:** 0.75% ≈ ₹10.5 L/yr → payback ≈ 1.6 months.
   - **Optimistic:** 1.5% ≈ ₹21 L/yr.
   - Benefits counted only from measured price revisions accepted by buyers or from waste reduction recorded in actuals. Capacity effects are not counted.
10. **Sales strategy.**
    - Founder-led, one cluster.
    - Lead with the **paid Margin Audit** (₹25,000, credited against year one).
    - Present audit results to the owner with their own numbers; convert to an annual plan.
    - Channels after 10 customers: ICCMA and regional associations, kraft paper dealers, Tally partners, IndiaCorr Expo (S62).
11. **Pilot design.**
    - 60 days, 1 plant.
    - **Baseline:** last 90 days of quotes, invoices and dispatch, reconstructed in the audit.
    - **Pilot:** live price book, two re-pricing cycles, and job close for ≥ 80% of dispatched jobs.
    - **Success metric:** price revisions issued within 7 days of each mill revision, plus a measured margin-variance report.
    - **Exit:** annual contract.
12. **Risks and dependencies.**
    - Job close-out compliance.
    - Owner time.
    - Buyers refusing revisions, so value depends on negotiating power.
    - The existing PackQuote code may need refactoring.
    - Cheap local competitors.
13. **Evidence supporting.** S1, S4, S5 (pain), S24–S27 (paid market exists), S33 (vendor case), S52.
14. **Unresolved questions.**
    - Real quote-vs-actual variance.
    - Price sensitivity.
    - Whether buyers accept index-based revisions.
    - Share of plants already on ERP.
    - Current PackQuote customers and usage.

### D2. O2 Margin Control – flexible packaging

1. **ICP.** Gravure and flexo flexible-packaging converters, ₹20–300 cr, printing and laminating for FMCG/food; some with in-house film extrusion.
2. **Problem.** FX1, FX2, FX7: multi-layer structures with coat weights, cylinders, solvent and run-length-dependent waste (S35, S56, S59). Expert estimators are a bottleneck.
3. **Solution.**
   - Layer library with ₹/kg and GSM.
   - Structure builder computing the GSM and ₹/m² of the laminate.
   - Waste curves by run length and colours.
   - Cylinder/plate amortisation.
   - Quote-vs-actual from job close (input kg, output kg/m, solvent issued).
4. **Scope.** The engine extension, plus segment templates and a cylinder register.
5. **Architecture.** The same platform as D1, with segment-specific costing modules.
6. **Differentiation.** Imported MIS (Label Traxx S29) is built for Western converters. Indian ERPs (S24, S26) are broader and heavier [I].
7. **Pricing hypothesis.** Growth ₹12,000/month; Enterprise ₹30,000–60,000/month. Onboarding ₹50k–2L, because setting up structure libraries is work.
8. **Cost.** 6–10 additional weeks after D1 [I].
9. **ROI.** For a ₹60 cr converter, a 0.5% material/waste improvement ≈ ₹30 L/yr [I].
10. **Sales.** Same cluster approach; packaging consultants; converter associations.
11. **Pilot.** 60 days; 30 structures; actual waste curve fitted on ≥ 100 jobs.
12. **Risks.** Longer sales cycle; more customisation pressure; data sensitivity of structures.
13. **Evidence.** S24, S26, S29, S35, S56.
14. **Unresolved questions.** Does PackQuote already handle laminates? Do converters already own an MIS?

### D3. O3 Cyberion Pulse – retrofit runtime, downtime and count monitor (SECOND PRODUCT)

1. **ICP.**
   - (a) Margin Control customers with automatic corrugators, printer-slotters or presses.
   - (b) Injection moulders and film extruders with 10–60 machines, mostly hydraulic and older, with no MES.
2. **Problem.** PK4, IM1, IM2, CB7: unrecorded downtime, cycle drift and unknown machine hours per job (S16, S22).
3. **Solution.**
   - One node per machine. Split-core CTs on the motor or main feeder determine run, idle and stop (S16-style method).
   - Optional isolated pulse input for cycle or count.
   - A QR-scan job context.
   - A downtime-reason prompt on a shared tablet.
   - Output feeds Margin Control actuals: machine hours per job, parts per hour.
4. **Scope v1.** Run state, cycles, job context, reason codes, daily WhatsApp/email summary, and feeds to job costing. No OEE consulting and no predictive maintenance.
5. **Architecture.** See Part 3, Deliverable E (device) and §15 (platform).
6. **Differentiation.** Job-linked costing rather than OEE dashboards. Indian pricing, and installation by trained local electricians [I].
7. **Pricing hypothesis.**
   - Hardware ₹9,000–15,000 per machine.
   - Subscription ₹700–1,200 per machine per month.
   - Paid pilot: 4 machines × 60 days for ₹30,000, credited.
   - For reference: the global category charges $75–125/machine/month (S17, S18). Indian listings include a ₹50,000 "OEE system" (S20).
8. **Cost.**
   - Hardware development: ₹5–8 L, covering prototypes, EMC pre-scan and a 20-unit pilot batch [I].
   - Installation: ~₹1,500–3,000 per machine.
9. **ROI.** A moulder with 20 machines recovering 30 min/machine/day of unexplained downtime adds capacity. **Count it as value only if demand exists** (per the brief's rule). The more conservative benefit is costing accuracy plus avoided overtime. Must be measured in the pilot.
10. **Sales.** Upsell to Margin Control accounts first; then moulding clusters via machine dealers and service technicians.
11. **Pilot.** 4 machines, 2 weeks of baseline (manual log) against 6 weeks of monitoring. Success = ≥ 95% run-state agreement with observation and ≥ 1 actionable finding accepted by the plant head.
12. **Risks.**
    - Crowded market (S16–S22).
    - Electrical installation liability.
    - Field support.
    - Hardware working capital.
    - Certification (WPC/ETA; MTCTE scope to verify: S42, S43).
13. **Evidence.** S16–S22, S30, S31.
14. **Unresolved questions.** Will SMEs pay a recurring per-machine fee in India? Which is preferred: Wi-Fi, Ethernet or RS-485 to a gateway?

### D4. O5 Mobile job-ticket, WIP and dispatch tracking (feature inside D1, sold as an add-on tier)

1. **ICP.** Same as D1 and D2.
2. **Problem.** PK2, PK5: status unknown; customer calls; no traceability (S28).
3. **Solution.** QR job card printed with the quote or order. Scan at each stage (corrugation, printing, die-cut, stitching, dispatch). Delay alerts; dispatch close-out feeds actuals.
4. **Scope.** PWA with offline-first operation, scan-to-advance, status board and customer status link.
5. **Architecture.** Shared platform; event table of job-stage transitions.
6. **Differentiation.** Built into the quoting–costing chain. Data capture is a side effect of logistics people already do.
7. **Pricing.** Included in Growth tier; ₹2,000/month add-on for Starter.
8. **Cost.** 4–6 weeks [I].
9. **ROI.** Mostly indirect: fewer status calls, on-time delivery, *and the actual data that makes D1 work*. That last point is why it ships with D1.
10. **Sales.** Never sold alone; bundled.
11. **Pilot.** ≥ 80% of jobs scanned at dispatch for 30 days.
12. **Risks.** Floor compliance; phone availability.
13. **Evidence.** S28 (moderate).
14. **Unresolved.** Which stages plants are willing to scan.

### D5. O4 Energy-per-kg and utility metering (Pulse energy channel)

1. **ICP.** Plastics processors (injection, extrusion, blow) where energy is significant: 6–8% of turnover (S13), with ~30% discretionary (S12).
2. **Problem.** IM3, EX3, UT1, UT2: only the monthly bill is known; no kWh per machine, job or kg.
3. **Solution.** Certified panel energy meters with Modbus RTU (e.g. Selec MFM383A-C-CE, ~₹2,000–3,400 listed: S45) read by the Pulse gateway. Gives kWh/kg per machine and job, idle-energy alerts (hydraulic pumps idling), and compressor night-load analysis (S15).
4. **Scope.** Up to 8 meters per gateway on one RS-485 bus; reports; alerts.
5. **Architecture.** Same Pulse firmware, Modbus master role. **Cyberion never builds its own mains voltage measurement front-end;** it uses certified meters.
6. **Differentiation.** Energy tied to jobs and costs, not just a utility dashboard.
7. **Pricing.** Meter + installation at cost + 25%. Subscription ₹500/meter/month or ₹6,000/month per plant up to 10 meters [H].
8. **Cost.** Incremental to Pulse: 3–4 weeks of firmware and reports.
9. **ROI.** For a plant spending ₹10 L/month on power, a 5% sustained saving = ₹6 L/yr vs ~₹1 L/yr subscription [I]. The savings percentage is a hypothesis to measure.
10. **Sales.** Plastics clusters; energy auditors; possibly BEE/state energy-efficiency programmes (verify current schemes).
11. **Pilot.** 30-day baseline then 60 days; savings verified against production-normalised kWh/kg.
12. **Risks.** Savings depend on customer action; tariff and production mix confound measurement (S14 warns about naive kWh/kg).
13. **Evidence.** S10–S15, S45, S47.
14. **Unresolved.** Do moulders act on the data? Is the plant-head or owner the buyer?
