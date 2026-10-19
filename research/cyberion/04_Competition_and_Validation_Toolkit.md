# Part 4: Competitive landscape (Deliverable G) and customer validation toolkit (Deliverable H)

Evidence labels **[F] [D] [I] [H] [PK]** and source IDs (S#) are as defined in [SOURCES.md](SOURCES.md).

---

## Deliverable G: Competitive landscape

**Reading rule.** "Confirmed" means a third-party or documentary source describes the capability. "Claimed" means vendor marketing only. Pricing is shown only where a listing was found. Everything else is "not published".

### G1. Packaging costing, MIS and ERP

| Competitor | Segment / geography | Capabilities (confirmed vs claimed) | Business model / price | Integration / deployment | Strengths | Weaknesses / unserved | Switching cost |
|---|---|---|---|---|---|---|---|
| **Samadhan ERP** (India) | Corrugated, commercial print, flexible | Claimed: reel tracking, wastage by job/shift/machine, deckle optimisation, actual-cost quotes (S24) | Not published | Microsoft-based ERP; full implementation | Indian, domain-specific, exhibits at IndiaCorr | Full-ERP scope means a heavy rollout for small plants [I] | High once live |
| **Dataman** (India) | Corrugated | ERP covering inventory, procurement, sales (search extract) | Not published | ERP | Corrugation focus | Same as above [I] | High |
| **ParamERP / Speedpeq** (India) | Flexo, corrugators, narrow web, commercial | ~100 installations reported c. 2014 (S26) | Not published | On-prem/web | Long presence | Dated evidence; current status unknown | Med–High |
| **Rogler ERP via Shenso** (India distributor) | Cartons, corrugation | Customisation for multi-location, complex pricing (S27) | Not published | Imported ERP | Mature product | Cost; customisation dependency [I] | High |
| **SolPrint via Sergusa** | Commercial print | Estimation, job costing, purchasing, planning (search extract) | Purchase or hosted | — | Broad MIS | Commercial-print focus | Med |
| **Disha Swarajsoft** (India) | Corrugated | Box costing calculator (S25) | ~₹5,000 one-time listing | Offline | Very cheap | No actual-cost feedback, no price feeds, single-user [I] | Very low |
| **Tally + custom TDLs / Excel** | All | Accounting + spreadsheets (S28) | Tally licence; free spreadsheets | Universal in Indian SMEs [I] | Familiar, cheap | No job costing discipline | Low |
| **Label Traxx (Amtech)** | Labels, flexible (global) | MIS/ERP; scheduling (Batched), portal (Siteline) (S29) | Not published | Cloud API, data warehouse | Category leader with Cerm (S61) | Priced for Western converters; India presence unverified | High |
| **Cerm** | Labels (global) | Leading label MIS (S61) | Not published | — | Depth | Same | High |
| **ePS / Kiwiplan** (global) | Corrugated / packaging ERP & MES | Well-known in large corrugators [PK] | Enterprise | Heavy | Depth, integrations | Out of reach for most Indian SMEs [I] | Very high |
| **Generic Indian cloud ERP** (Zoho, Odoo partners, Busy, Marg) | All SMEs | Customisable (S33 shows a Zoho job-costing build) | Low per-user | Partner-led | Cheap, flexible | Domain logic must be custom-built by partners; inconsistent quality [I] | Med |

**Cyberion position:** not an ERP. A *margin layer* that sits beside Tally and any ERP: price book, re-pricing, quote-vs-actual. Win on time-to-value (days), segment depth, and price below ERP but above calculators.

**Risk:** an ERP vendor ships an equivalent "margin dashboard". Mitigation: speed, segment depth, and later the Pulse data that ERPs do not have.

### G2. Machine monitoring, MES and IIoT

| Competitor | Segment / geography | Capabilities | Price evidence | Hardware / deployment | Strengths | Weaknesses vs Cyberion's target |
|---|---|---|---|---|---|---|
| **Guidewheel (FactoryOps)** | Plastics & packaging, US | CT-clamp state learning; extruders, IMMs, blow moulders, thermoformers (S16) | "From $15,000/yr for 10 machines", removed from public page Sept 2026 (S17) | Self-install CTs | Strong plastics focus; vendor-reported case results | USD pricing; India presence not found |
| **Amper** | Discrete manufacturing, US | Self-installed sensors, trial before purchase | $75–100/machine/month (S18) | Self-install | Easy trial | USD pricing |
| **Epicor Advanced MES (Mattec)** | Plastics MES, global | Full MES | Listing "from $399/month" (S30) | Machine interfaces | Plastics depth | Complexity |
| **TIG 2go, KraussMaffei MaXecution, Syscon-PlantStar** | Moulding MES | Entry cloud MES; EUROMAP connectivity (S31) | Not published | OEM-centric | OEM integration | Newer machines; cost |
| **LEANworx** (India) | MSME machine monitoring | "Cost of a cup of coffee per day per machine" (S21) | Not published | Retrofit | India-native, low price | Generic OEE; no costing link [I] |
| **Sochiot** (India) | Tier-2/3 factories, IMMs | Self-reported per-machine monthly subscription; NCR IMM deployments (S22) | Not published | Plug-and-play | Same target as Pulse | Early stage; unverified |
| **Pearl Automation** (India) | OEE systems | Listing at ₹50,000 per "piece" (S20) | ₹50k listing | — | Local | Scope unclear |
| **EcoAxis AxisPlast** | Plastics | OEE, downtime, rejection analysis, service tickets (S53) | Not published | — | Plastics focus | Origin unverified |
| **Infinite Uptime** (India) | Large process plants, PdM | Raised ~$35M in 2025; large enterprise customers (S23) | Enterprise | Vibration sensors | Funding, scale | Not SME-focused [I] |
| **System integrators + PLC/SCADA** | All | Custom dashboards | Project pricing; e.g. ₹20k–1L PLC-based, ₹1–10L full installs (S54) | Custom | Flexible | Project-based; no product |
| **Auto-gauge OEMs** (Addex, TSM, Nordson) | Film extrusion | Gauge variation −50–70% (S36) | Capex | OEM | Closed-loop expertise | Capex too high for small lines [I] |

**Cyberion position for Pulse:**
- Do not sell "OEE"; that market is crowded.
- Sell **"actual cost per job and per kg"**, tied to Margin Control: machine hours, kWh and counts per job.
- Price in rupees at roughly ₹700–1,200 per machine per month, about 10–15% of US list prices.
- Install through trained local electricians.

### G3. Substitutes

- **Spreadsheets and WhatsApp.** The default; free. Cyberion must be *faster than Excel* at re-pricing, and job close must be *faster than writing in a register*.
- **Consultants and energy auditors.** One-off reports. They are potential **channel partners**, not just substitutes.

### G4. Partnership opportunities (to approach after the first 5–10 customers)

| Partner type | Value | Example approach |
|---|---|---|
| Kraft paper dealers / mill agents | Daily price data; trusted access to box makers | Co-branded price bulletin linked to Margin Control |
| Corrugation associations (ICCMA, regional) | Credibility, events (IndiaCorr S62) | Member-discount pilot programme |
| Tally partners | Distribution to SMEs already on Tally | Referral commission (15–20% of year-1) |
| Machine dealers / service technicians (corrugation, IMMs) | Trust inside plants; can install Pulse | Install-partner certification + fee |
| Meter brands (Selec, etc.) | Certified energy hardware | Approved-meter list; distributor pricing |
| Energy auditors / BEE-linked programmes | Energy pilots | Pulse as their measurement tool |

---

## Deliverable H: Customer validation toolkit

### H1. Buyer personas (SME corrugated or flexible plant)

| Persona | Experiences the pain | Controls budget | Evaluates | Can block | What they need to hear |
|---|---|---|---|---|---|
| Owner / MD | Margin squeeze, cash, price fights (S4) | **Yes** | Yes | Yes | "₹X lakh/year margin recovered, proven on your own data in 30 days" |
| Plant / production manager | Downtime, schedule chaos | Influences | Pulse | Yes (floor adoption) | "Fewer status calls, proof for breakdown reasons" |
| Estimator / costing staff | RFQ load, re-pricing work | No | **Yes** | Yes (fear of replacement) | "You approve every price; the tool does the arithmetic" |
| Accounts / finance | Reconciliation, Tally | Influences | Tally fit | **Yes** | "No change to Tally vouchers; import only" |
| Purchase manager | Price volatility, supplier quotes | No | Price book | Rarely | "Supplier price history in one place" |
| Maintenance manager | Breakdowns, energy | No (SMEs) | Pulse | Yes (panel access) | "Non-invasive, licensed electrician, no control wiring" |
| Quality manager | Complaints, traceability | No | WIP/traceability | Rarely | "Batch-to-job link in seconds" |
| IT (only in larger plants) | Security | No | Security review | **Yes** | "Outbound-only MQTT/TLS, VLAN, data export, DPDP compliance" |
| Machine operator / dispatch | Extra data entry | No | De facto | **Yes** (by not using it) | "One scan or 3 fields; done in 30 seconds" |

### H2. Interview guide

**Rules:**
- Ask about **past behaviour, actual numbers and documents**, never "would you use…?"
- Ask to *see* the spreadsheet, the price list and the job card.
- Record answers in a structured sheet (template in H6).
- 45 minutes per interview; do not pitch until the last 10 minutes.

**Core questions (all segments):**
1. Walk me through the last RFQ you priced, from the moment it arrived to the moment the price was sent. Who touched it and how long did it take?
2. Can you show me the sheet or tool you used? Who built it and who is allowed to change it?
3. When did your main raw-material supplier last change prices? How many of your customer prices did you revise, and how long did that take?
4. Of the revisions you asked for, how many did customers accept? What evidence did you show them?
5. For your top 10 customers, do you know the profit on each one last quarter? How do you know?
6. Tell me about the last job you found out you lost money on. How did you find out, and how much was it?
7. How do you decide the wastage % in a quote? When was it last checked against reality?
8. What happens on the floor when a job is finished? What gets written down, by whom, and where does that paper go?
9. Which software do you pay for today (Tally, ERP, others)? What did each cost, and what do you actually use?
10. Have you bought or tried any costing/ERP/monitoring tool that you stopped using? Why did it fail?
11. If you wanted to improve margins by 1%, what would you try first? Have you tried it?
12. Who in the company would have to say yes to spending ₹1 lakh a year on software? Who could stop it?
13. How did you buy your last piece of software or equipment under ₹2 lakh? How long did it take, and what did you need to see?
14. What would you need to see in a 30-day trial to keep paying after it?
15. What data would you be uncomfortable putting in the cloud? Why?

**Printing and packaging specific:**

16. (Corrugated) How do you calculate board weight per box today, including flute take-up and trim? Show me one.
17. (Corrugated) How many reels did you write off or lose track of last year? How do you know?
18. (Corrugated) How is the deckle planned on your corrugator? What trim % do you run?
19. (Flexibles) How do you cost a 3-layer laminate? Where do coat weights and solvent come from?
20. (Flexibles/labels) What is your actual makeready waste on a short run versus what you quote? Who measures it?
21. How many cylinders, plates or dies do you hold? How often does a job wait for tooling?

**Plastics and polymers specific:**

22. What were your units (kWh) and electricity bill last month? Do you know kWh per kg for any machine or product?
23. What is your standard cycle time for your top 5 moulds, and what did they actually run at last week? How do you know?
24. Tell me about your last unplanned breakdown. How long was the machine down, and what did it cost?
25. How do you dry hygroscopic materials? Have you had a moisture-related rejection or complaint this year?
26. How much regrind do you use, and how is the ratio controlled and recorded?
27. (Film) What is your target gauge and how much over target do you run on average? Have you weighed rolls against target g/m²?

**Hardware-based solutions:**

28. Who is allowed to open your machine panels? Do you have a licensed electrician on staff or on call?
29. Do any OEM warranties or AMCs on your machines restrict adding devices?
30. Is there Wi-Fi or Ethernet on the shop floor? Where do phones lose signal?
31. Have you installed any sensors or meters before? What happened to them after 6 months?
32. Would you pay for hardware upfront or prefer a monthly fee? What have you done for other equipment (UPS, compressors, RO plants)?
33. Who fixes things when a device stops reporting, and how quickly do you expect a response?

### H3. Validation experiments (recommended, not statistical rules)

| # | Experiment | Sample | Success criterion | Failure / pivot signal |
|---|---|---|---|---|
| V1 | Structured interviews (H2) | 25 corrugated + 10 flexible + 10 plastics | ≥ 60% of corrugated owners report a revision lag ≥ 2 weeks *or* unknown job profitability, with a specific example | < 30% can name a recent concrete loss |
| V2 | Factory walk-throughs | 10 plants | Map the job-card → dispatch → Tally data path in ≥ 7; identify who could close jobs | No consistent person/point for job close |
| V3 | **Paid Margin Audit (concierge MVP)**: ₹25,000, Cyberion reconstructs quoted vs actual material cost on 50–100 recent jobs using the customer's quotes, purchase invoices and dispatch records | 5 plants | ≥ 3 show gap ≥ 1% of revenue, *and* ≥ 3 agree to an annual plan | < 2 audits sold out of 10 offers → WTP problem; < 2 show a meaningful gap → pain overestimated |
| V4 | Clickable re-pricing prototype | 10 owners | ≥ 7 complete a re-price task in < 5 min; ask for a price | Confusion on core flow |
| V5 | Job-close compliance test (paper form or PWA) | 3 plants × 30 days | ≥ 80% of dispatched jobs closed | < 50% after coaching → redesign capture (e.g. weighbridge/dispatch integration) |
| V6 | Pulse bench + 1 friendly site | 4 machines | ≥ 95% agreement of run state against 8 h of manual observation | < 90% or installation > 3 h per machine |
| V7 | Pulse paid pilot | 3 plants × 4 machines | ≥ 2 convert to paid at ≥ ₹700/machine/month | Willing only if free |
| V8 | Price test | Present 3 tiers to the last 15 interviewees | ≥ 40% choose Growth at ₹8,000 | Most anchor to ₹5,000 one-time |

**Evidence thresholds before committing to a full build:**
- **Margin Control full build:** V3 success *and* ≥ 5 signed annual contracts or letters of intent with a payment date.
- **Pulse hardware design:** ≥ 15 paying Margin Control accounts **or** ≥ 3 paid Pulse pilots with conversion. V6 must pass.
- **Flexibles edition:** ≥ 3 flexible converters pay for an audit.

### H4. Pilot proposal template (one page to the customer)

> **Cyberion Margin Audit – [Company]**
> **Objective:** quantify how much margin you lost in the last 90 days from (a) delayed price revisions after kraft changes and (b) the gap between quoted and actual material use.
> **You provide:** quotes/price lists for the period; kraft purchase invoices; dispatch challans or Tally sales export; 2 hours of your estimator's time.
> **We deliver in 15 working days:** job-by-job quoted vs actual material cost; top 20 loss-making SKUs/customers; revision lag after each price change; a recommended revised price list; a 30-minute review with the owner.
> **Fee:** ₹25,000 + GST, **credited in full** against a Margin Control annual plan signed within 30 days.
> **Confidentiality:** NDA; your data is used only for this audit; deleted on request.
> **Success measure we commit to:** a margin-gap figure with every assumption shown. If we cannot reconstruct at least 50 jobs from your records, we refund 50%.

### H5. ROI worksheet (customer-facing; fill with measured values only)

| Line | Formula | Measured value |
|---|---|---|
| A. Annual material spend | from invoices | ₹ |
| B. Re-pricing lag recovery | Σ over price changes: (cost increase per kg × kg sold during lag days) × share of revisions that customers accept | ₹ |
| C. Quote-vs-actual correction | (actual – quoted material cost) on repeat SKUs × annual repeat volume × share corrected | ₹ |
| D. Waste reduction (only if measured in pilot) | Δ waste kg × ₹/kg | ₹ |
| E. Additional operating costs | subscription + onboarding (amortised) + staff time | ₹ |
| **Annual net benefit** | B + C + D − E | ₹ |
| **Payback (months)** | (onboarding + first-year prepaid) ÷ (monthly net benefit) | |

**Rules:**
- No double counting: B and C must use different jobs or periods.
- No capacity-based revenue unless the plant is demand-constrained *and* the extra output was sold.

For **Pulse**, replace B–D with: measured kWh reduction × tariff (S47); measured downtime reduction × contribution per hour **only where orders were waiting**; avoided overtime.

### H6. Interview record template (columns)

`date | plant | segment | turnover band | role | tools used | last price change date | revision lag (days) | % revisions accepted | known loss example (₹) | job-close owner | Tally/ERP | software spend/yr | failed tools | WTP signal (none/soft/hard) | next step | evidence attached (Y/N)`

### H7. Go / no-go criteria (summary)

| Gate | Go | No-go |
|---|---|---|
| Week 6 | ≥ 3 paid audits sold; ≥ 15 interviews with concrete loss examples | < 2 audits sold out of 10 serious offers |
| Week 12 | ≥ 5 paying accounts (or ≥ 3 + 5 LOIs); ≥ 2 audits with gap ≥ 1% revenue | No annual contract signed → re-segment (flexibles or plastics) or reposition to WIP/job control |
| Month 9 | ≥ 15 accounts; job-close compliance ≥ 80% in ≥ 60% of accounts; logo churn < 3%/month | Compliance < 50% → product redesign before any hardware |
