# Part 1: Executive decision brief (Deliverable A) and pain-point database (Deliverable B)

**Evidence labels used throughout:**
- **[F]** Verified fact from a cited source.
- **[D]** Documented customer problem: case study, association statement, operator forum or vendor-documented demand.
- **[I]** Commercial or engineering inference, reasoned from evidence.
- **[H]** Unvalidated hypothesis that needs interviews or a pilot.
- **[PK]** Prior knowledge not re-verified in this session.

Source IDs (S1…S62) resolve in [SOURCES.md](SOURCES.md).

---

## Deliverable A: Executive decision brief

### The decision in one paragraph

Cyberion's first commercial product should be **PackQuote Margin Control**, a software-only upgrade of PackQuote. It does two jobs:
1. It **re-prices every open quote and price list automatically when kraft-paper prices move.**
2. It **compares quoted against actual material cost and job profit**, using reel issues, dispatch weights and a 30-second mobile job-close entry.

The first customers should be **Indian corrugated-box manufacturers**: automatic plants and the larger semi-automatic plants, roughly ₹5–150 crore turnover. **Flexible-packaging converters** come second, on the same engine.

The indicative price is **₹3,500 / ₹8,000 / ₹25,000+ per month** (Starter / Growth / Multi-plant, excluding GST), plus a paid onboarding fee.

Hardware waits. A retrofit monitoring device, **Cyberion Pulse**, is the second product. It is built only after about 15 paying Margin Control accounts exist, and only if those customers ask for automatic runtime and energy actuals. Its first use is to feed real machine hours and kWh into job costing, not to compete head-on in generic OEE dashboards.

### Most attractive market opportunity

**Corrugated packaging.** Margin is decided at the quoting desk, and the industry is fragmented, price-squeezed and under-digitised.

- **Many reachable buyers [F].** ICCMA's 2026 statement counts about 300 automatic and 12,000+ semi-automatic units. They produce ~5.2 Mt/yr and employ more than 6 lakh workers (S1). Earlier ICCMA figures said ~500 automatic and ~10,000 semi-automatic plants (S2).
- **Market-size figures conflict.** They range from ₹18,000 cr (S1) to ₹50,000 cr (S3). This report does not rely on any of them; Part 5 sizes the market bottom-up.
- **Margin is extremely sensitive to the dominant input [D].**
  - Kraft paper is reported at about 90% of input cost, with margins around 5% (S4).
  - Mills announce price rises at the last moment, while box makers have already committed prices to buyers (S4).
  - In 2017, four kraft price revisions raised prices 22–29% in under three months (S5).
  - In July 2026 the association again describes the industry as in distress over kraft prices and supply (S1).

### Strongest customer pain point

**Quotes and price lists go stale faster than SMEs can re-cost them, and nobody knows which jobs lost money until the year-end books.**

The mechanism [I]:
- A box price is driven almost entirely by **board weight per box**: sheet area × the GSM of each liner and flute × flute take-up factor, plus wastage.
- That weight is then multiplied by **kraft ₹/kg for each BF/GSM grade**.
- Costing usually lives in an owner's or estimator's spreadsheet (S52, S33). Re-pricing 200–2,000 active SKUs after a mill revision is slow, so it is done late or partially.
- Meanwhile, actual consumption differs from the quoted assumptions: deckle trim, board rejection, extra wastage on short runs. Without job-level actuals, the error is never fed back into the next quote.

How big is it? [I] Take a ₹20 cr plant with material at ~70% of revenue. A **1 percentage-point** systematic under-estimate of material cost equals about **₹14 lakh a year**. At ~5% margin (S4) that is **~14% of annual profit**. This is a worked example built on stated assumptions, not a measured result. Validating its real size is the first job of customer discovery.

### Why customers should buy

**What the customer gets:**
- **Recovered margin.** Faster re-pricing after kraft revisions; fewer loss-making repeat jobs. This is the primary value.
- **Fewer quoting errors and faster quotes.** A vendor case study reports 54% fewer job-costing errors after moving off handwritten job sheets and Excel. It is directional evidence only (S33).
- **Lower dependence on one estimator.** Costing rules live in a system rather than in one person's head (S52).

**Why Cyberion can win this:**
- **Software only.** No machine access, no electrical work, no warranty risk. It can be live in days and sold to the owner, who is both the person feeling the pain and the budget holder.
- **Competitors exist, but they are either too heavy or too thin.**
  - Corrugation ERPs such as Samadhan (S24) and Dataman, and imported ERPs such as Rogler (S27), are full ERPs that need heavy implementation.
  - Offline calculators such as Disha Swarajsoft (~₹5,000, S25) and Excel do no actual-cost feedback and no supplier-price linkage.
- **The wedge** is the middle ground: a focused margin tool that integrates with Tally rather than replacing the ERP [I].

### Expected development difficulty

- **Low to medium technically:** a deterministic costing engine, a price-index service, mobile job-close, Tally import/export, and reports.
- **Hard on the shop floor:** getting actual data captured consistently. Job close-out must take less than 30 seconds per job and be done by someone who already handles dispatch.
- **Estimated MVP:** 8–12 weeks for a founder plus one engineer on top of the existing PackQuote code base [I]. This must be confirmed against the actual PackQuote architecture, which this research could not inspect.

### Proposed business model

- **Annual SaaS subscription** in three tiers, billed annually in advance.
- **Paid onboarding:** ₹15k / ₹40k / ₹1.5L+.
- **Paid "Margin Audit" pilot** at ₹25,000, credited against the first year.
- **Optional add-ons later:** Tally/ERP connectors, multi-plant, and the Pulse hardware plus monitoring subscription.
- **No free custom development.** Custom work is priced from a published rate card.

### Main commercial risks

1. **Willingness to pay.** Price-squeezed SMEs that already have a ₹5,000 calculator or Excel (S25) may not pay ₹40k–1L a year.
2. **Data discipline.** If actuals are not recorded, the product degrades into "just another calculator" and churns.

Both are testable within 90 days with paid audits; see Part 6.

### The next action

Within 6 weeks, in **one cluster** reachable for day trips from the founder's base:
- Run **25 structured interviews and 10 factory walk-throughs** with corrugated plant owners.
- Sell **5 paid Margin Audits** (₹25,000 each). Each audit reconstructs quoted vs actual material cost for 50–100 recent jobs from the customer's own quotes, kraft purchase invoices and dispatch records.
- **Go** if at least 3 audits show a material-cost gap of ≥1% of revenue *and* at least 3 customers commit to an annual subscription.
- **Stop or pivot** if fewer than 2 audits show a gap worth ≥5× the subscription price.

### What NOT to build now

- **Generic OEE dashboards:** crowded with Guidewheel, Amper, LEANworx, Sochiot and many integrators (S16–S22).
- **Camera-based defect inspection:** capital- and integration-heavy, with OEM competition.
- **Vibration-based predictive maintenance:** well-funded incumbents such as Infinite Uptime (S23); hard to prove ROI on SME machines.
- **LLM "factory copilots":** no defined buyer or measurable outcome yet.
- **Closed-loop control of any kind.**
- **EU/Latvia expansion:** before domestic product–market fit.

---

## Stage 1 summary: industry research findings, evidence gaps, decisions

**Findings**

1. **Corrugated:** the most quantified pain is input-price volatility against thin margins (S1, S4, S5). Indian vendors already sell corrugation ERPs with reel tracking, deckle optimisation and actual-cost quoting (S24). That shows the problem is real *and* that buyers pay for it at some price point.
2. **Flexible packaging and labels:** costing is more complex (multi-layer laminates, cylinders and plates, makeready waste) and makeready waste is strongly run-length dependent (S35, S56, S59). Specialist MIS exists internationally, such as Label Traxx and Cerm (S29, S61), and in India (Samadhan, ParamERP: S24, S26). Evidence of Indian SME adoption is thin.
3. **Plastics:** energy is a material cost line. It is reported at 6–8% of turnover, "in the same order as profit" (S13), with ~30% discretionary in unmanaged plants (S12). Machine type drives specific energy: all-electric machines use 0.16 vs hydraulic 0.61 kWh/kg in one field study (S11); 12.6 vs 19.0 MJ/kg in another (S10). Treat single benchmark numbers with caution (S14).
4. **Monitoring market:** retrofit current-sensing monitoring works technically and is commercialised. Western pricing is $75–125/machine/month (S16–S19). Indian players are present at much lower price points (S20–S22). The market is crowded and price-competitive.
5. **Market-size data is unreliable:** published flexible-packaging market sizes differ 4–5× (S8 vs S9), and corrugated ₹18,000–50,000 cr (S1, S3). Sizing must be bottom-up.

**Evidence gaps that only fieldwork can close**
- Actual quote-vs-actual material variance in Indian corrugated plants.
- Current subscription prices of Samadhan, Dataman and other Indian ERPs.
- Share of plants using Tally plus Excel versus an ERP.
- Willingness to pay for a margin tool.
- How PackQuote is used today, by whom, and at what price. This is not available to this research and is the single biggest unknown.

**Decisions that follow**
- Focus the first product on software and on the quote desk.
- Use hardware as a later accelerator for actual costs.
- Run paid audits to quantify the gap before building.

---

## Deliverable B: Industry pain-point database (47 distinct entries; FX8 is a cross-reference)

The database is split into two linked tables (B1 problem and B2 solution) so it stays readable. Rows join on the ID.

- **Frequency/Severity:** Hi / Med / Lo.
- **Difficulty:** implementation difficulty for Cyberion: L / M / H.
- **Evidence strength:** strong (independent and corroborated) / moderate (single credible source or vendor-documented demand) / weak (inference from mechanism).

**Segment codes:**
- **CB:** corrugated boxes
- **FX:** flexible packaging
- **LB:** labels
- **CP:** commercial and folding-carton print
- **PK:** cross-packaging
- **IM:** injection moulding
- **EX:** extrusion (film/sheet/pipe)
- **BM:** blow moulding
- **TF:** thermoforming
- **UT:** utilities
- **BX:** business/compliance

**Honesty note.** Rows with evidence "weak" are included because the manufacturing mechanism is well understood. Their *economic size* in Indian SMEs is unverified. Rows that research could not support (for example vision-based colour control for SMEs) were folded into broader rows rather than padded.

### B1: Problem side

| ID | Segment / workflow | Root cause (mechanism) | Typical workaround | Financial / operational impact | Freq / Sev | Affected stakeholders → buyer (budget owner) |
|---|---|---|---|---|---|---|
| CB1 | CB / quotation re-pricing after kraft revisions | Kraft ≈ 90% of input cost; mills revise prices abruptly; box prices already committed (S4, S5, S1) | Owner re-prices top customers by hand in Excel; others lag | Margin erosion on every order until re-priced; at ~5% margin a few % kraft move wipes profit [D] | Hi / Hi | Owner, sales, estimator → **Owner/MD** |
| CB2 | CB / box costing from spec (ply, GSM, BF, flute, deckle) | Many parameters; flute take-up and wastage assumptions vary by estimator (S52) | Personal spreadsheets; rule-of-thumb wastage % | Inconsistent prices; loss on complex boxes; slow RFQ turnaround [D] | Hi / Med | Estimator, sales → Owner |
| CB3 | CB / quote-vs-actual job profitability | No job-level capture of board actually consumed, rejects and extra trim (S33) | Year-end P&L only; gut feel | Loss-making repeat jobs go unnoticed [D] | Hi / Hi | Owner, accounts → Owner |
| CB4 | CB / corrugator deckle and trim planning | Reel widths don't match combined order widths; manual combination (S24 offers deckle optimisation) | Planner experience | Trim waste on every run; directly material cost [D] | Hi / Med | Planner, production manager → Owner |
| CB5 | CB / reel inventory and consumption | Reels issued without weight/ID tracking; partial reels lost (S24 sells reel-tracking) | Stock register | Stock-outs, double buying, untraceable waste [D] | Hi / Med | Stores, purchase → Owner |
| CB6 | CB / price escalation with buyers | Price lists to FMCG and industrial buyers are fixed for periods; no index clause (S4) | Ad-hoc negotiation after cost shock | Absorbed losses during volatile months [D] | Med / Hi | Owner, sales → Owner |
| CB7 | CB / automatic-plant corrugator downtime and changeover | Order changes, splice, glue and steam issues; small orders increase changes [I] | Shift log on paper | Lost capacity in plants that are capacity-constrained [I] | Hi / Med | Production manager → Plant head/Owner |
| CB8 | CB / semi-automatic plant labour productivity and counting | Manual feeding, stitching, counting; piece-rate disputes [I] | Supervisor tallies | Overtime, miscounts, dispatch shortages [H] | Hi / Med | Supervisor → Owner |
| CB9 | CB / board quality (moisture, warp, BCT/ECT failures) | Paper moisture variation, starch and steam conditions [I] | Lab tests on complaint | Rejections, customer claims [H] | Med / Med | QC, sales → Owner |
| CB10 | CB / boiler fuel and steam cost | Steam needed at corrugator; fuel-price exposure; poor condensate return [I] | Monthly bill review | Energy cost per tonne unknown by job [H] | Med / Med | Maintenance → Owner |
| FX1 | FX / laminate structure costing | Multiple layers (film GSM, ink coverage, adhesive coat weight, solvent), cylinder or plate charges [I]; vendor MIS models these (S24, S29) | Expert estimator's spreadsheet | Mis-pricing of complex structures; slow quotes [D] | Hi / Hi | Estimator, sales → Owner/MD |
| FX2 | FX / rotogravure and flexo makeready waste | Registration and colour approval on every changeover; waste high relative to short runs (S35, S59) | Fixed waste % in quote | Material waste and press time; under-quoted short runs [D] | Hi / Hi | Press manager → Plant head |
| FX3 | FX / solvent consumption and recovery | Solvent-based inks and adhesives; evaporation, retention, recovery-plant efficiency [I] | Monthly purchase vs output | Cost and compliance exposure [H] | Hi / Med | Production, EHS → Plant head |
| FX4 | FX / lamination defects and curing WIP | Adhesive mixing ratio, coat weight, curing time; tunnelling and bond failures [I] | Re-lamination, hold stock | Rework, delayed dispatch [H] | Med / Med | QC → Plant head |
| FX5 | FX / colour matching and reprints | Ink mixing, substrate variation, viewing conditions [I] | Operator judgement, re-runs | Reprints; customer disputes [H] | Med / Med | Press, QC → Plant head |
| FX6 | FX / cylinder and plate inventory | Hundreds of cylinders; location, condition, re-chroming due [I] | Register, memory | Delays finding tooling; duplicate engraving cost [H] | Med / Lo | Pre-press → Plant head |
| FX7 | FX / slitting and roll-yield tracking | Edge trim, joins, roll weight not reconciled to order [I] | Dispatch weight only | Hidden yield loss [H] | Hi / Med | Production → Owner |
| FX8 | FX / film extrusion in-house (integrated converters) | See EX1–EX3 | — | — | — | — |
| LB1 | LB / short-run estimating and makeready share | Makeready dominates short runs; waste % non-linear with quantity (S35, S56) | Flat waste % | Under-priced short jobs [D] | Hi / Med | Estimator → Owner |
| LB2 | LB / digital-press click-charge averaging | Averaged click costs mis-price coverage-heavy jobs (S51) | Average rate card | Some jobs overcharged, others lose money [D] | Med / Med | Owner |
| LB3 | LB / die and tooling inventory | Many shapes; die wear [I] | Shelves and memory | Delays, duplicate dies [H] | Med / Lo | Pre-press → Owner |
| CP1 | CP / estimate inconsistency | Costing logic lives in estimators' heads and spreadsheets (S52) | Senior estimator reviews | Inconsistent pricing; dependency on one person [D] | Hi / Med | Owner |
| CP2 | CP / offset and carton makeready time | Plate change, ink presetting, die-cut makeready (S57, S58, S59) | Experienced operators; new presses | 45 min to 3 h per makeready reported (S59) [D] | Hi / Hi | Press manager → Owner |
| PK1 | PK / production scheduling across shared machines | Many small orders, sequence-dependent setups; MIS vendors sell scheduling add-ons (S29) | Whiteboard, WhatsApp | Late deliveries, excess changeovers [D] | Hi / Med | Planner → Plant head |
| PK2 | PK / WIP and order-status visibility | Paper job cards; status known only on the floor (S28) | Phone calls to supervisor | Sales time lost; missed delivery dates [D] | Hi / Med | Sales, customer → Owner |
| PK3 | PK / Tally + Excel fragmentation | Accounting in Tally; costing, production and stock in separate sheets (S28) | Manual re-keying | Errors, delays, no single truth [D] | Hi / Med | Accounts, owner → Owner |
| PK4 | PK / unknown machine utilisation and OEE | No automatic data capture on legacy machines (S16, S22) | Shift reports | Capacity decisions made blind; secondary reports say OEE is often 45–50% (unverified) [I] | Hi / Med | Plant head → Owner |
| PK5 | PK / customer complaints and batch traceability | No link between dispatch batch, material lot and machine/shift [I] | Search paper records | Slow complaint resolution; liability exposure for food/pharma packs [H] | Med / Med | QC → Owner |
| PK6 | PK / RFQ and spec intake | RFQs arrive by email/WhatsApp/PDF drawings; manual transcription [I] | Retyping | Slow quotes; transcription errors [H] | Hi / Lo | Sales/estimator → Owner |
| IM1 | IM / cycle-time drift vs standard | Cooling dominates cycle; operators lengthen cycles to avoid defects; nobody compares actual to quoted cycle [I] | None; output shortfall noticed late | Hidden capacity loss and under-costed parts [I] | Hi / Hi | Production manager → Owner |
| IM2 | IM / unrecorded downtime and micro-stops | Mould problems, material starvation, operator absence; no automatic logging (S16, S22, S53) | Shift log | Lost hours never analysed [D] | Hi / Hi | Production, maintenance → Owner |
| IM3 | IM / energy per kg on hydraulic machines | Fixed-pump hydraulics draw power when idle; heater losses (S10, S11, S12) | Monthly utility bill | Energy ~6–8% of turnover (S13); ~30% discretionary (S12) [F/D] | Hi / Hi | Owner, maintenance → Owner |
| IM4 | IM / moisture and drying defects | Hygroscopic resins hydrolyse in the melt if wet; under- and over-drying both harm parts (S37, S55) | Fixed drying time; operator checks | Splay, brittleness, latent field failures [F] | Med / Hi | QC, production → Plant head |
| IM5 | IM / mould maintenance timing | PM by calendar or failure, not shot count [I] | Reactive repair | Unplanned mould breakdowns, flash, damage [H] | Med / Hi | Tool room → Plant head |
| IM6 | IM / process-setting knowledge loss | Proven settings live with experienced setters; older machines lack recipe export [I]; EUROMAP 77 targets this on new machines (S32) | Notebook of settings | Long re-setups, inconsistent quality [I] | Hi / Med | Setter, QC → Plant head |
| IM7 | IM / colour and material changeover purge | Purging between colours/resins; scheduling ignores sequence [I] | Purge compound, experience | Material and time waste [H] | Med / Med | Production → Plant head |
| IM8 | IM / regrind ratio and recycled content control | Regrind ratio affects properties; ratio not recorded [I] | Fixed mixing by eye | Quality variation; EPR claims unprovable [H] | Med / Med | QC → Owner |
| IM9 | IM / cooling water and chiller faults | Scale, low flow, chiller undersizing raise cycle time [I] | React when parts fail | Longer cycles, defects [H] | Med / Med | Maintenance → Plant head |
| EX1 | EX / blown-film thickness variation and giveaway | Die gap, melt temperature, air ring; lines run heavy to meet minimum gauge; auto-gauge control cuts variation 50–70% (S36) | Manual bolt adjustment; run heavier | Resin giveaway on every kg produced [D] | Hi / Hi | Production → Owner |
| EX2 | EX / start-up and changeover scrap | Temperature stabilisation, gauge and colour settling [I] | Experience | Scrap per changeover [H] | Hi / Med | Production → Plant head |
| EX3 | EX / extrusion energy and output tracking | Motor and heater load vs kg output not measured per job (S13) | Monthly bill / total output | Unknown cost per kg by product [I] | Hi / Med | Owner |
| BM1 | BM / wall thickness and weight variation | Parison programming, temperature; containers run heavy [I] | Weight checks | Resin giveaway [H] | Med / Med | Production → Owner |
| TF1 | TF / skeleton and trim waste | Sheet utilisation geometry; regrind loop [I] | Regrind | Material and energy loss [H] | Hi / Med | Production → Owner |
| UT1 | UT / compressed-air leaks and pressure | Leaks can waste 20–30% of compressor output in poorly maintained systems (S15) | Occasional leak walk | Electricity waste [F (DOE via secondary)] | Hi / Med | Maintenance → Owner |
| UT2 | UT / power factor, maximum demand and tariff penalties | Industrial tariffs vary by state, ~₹3.35–10/kWh, with demand charges (S47) | Capacitor bank, bill review | Avoidable penalties and demand charges [I] | Med / Med | Maintenance → Owner |
| BX1 | BX / resin and kraft price volatility in quotes | Commodity inputs; quotes not indexed (S4, S5, S50) | Periodic manual revision | Margin swings [D] | Hi / Hi | Owner |
| BX2 | BX / EPR and recycled-content compliance records | PWM rule amendments set recycled-content targets, certificates and reporting (S38) | Consultants and spreadsheets | Compliance cost; customer audits [F] | Med / Med | Owner, compliance → Owner (often brand-owner driven) |
| BX3 | BX / operator turnover and knowledge loss | Migrant and contract workforce; skills held by few [I] | Training on the job | Quality variation, slower changeovers [H] | Hi / Med | Plant head → Owner |

### B2: Solution side

| ID | Existing competing solutions | Why they may be inadequate (evidence-based where possible) | Proposed Cyberion solution | Data, sensors, integrations | Difficulty | Evidence strength (sources) | Most important assumption to validate |
|---|---|---|---|---|---|---|---|
| CB1 | Excel; corrugation ERPs (Samadhan S24, Dataman); ₹5k calculators (S25) | ERPs need full implementation; calculators lack price feeds and bulk re-pricing [I] | **Margin Control: kraft price book + bulk re-price + margin alerts** | Supplier price lists/invoices; customer price lists; SKU specs | L | Moderate (S1, S4, S5) | Owners will re-price faster if shown margin impact per customer |
| CB2 | Same as CB1 | Logic not standardised across estimators (S52) | Deterministic box-costing engine with plant-specific take-up and waste tables | Plant flute factors, waste tables | L | Moderate (S52, S33) | PackQuote engine already covers ply, flute and BF math |
| CB3 | ERP job costing (S24); Zoho custom (S33) | Heavy setup; SMEs lack data discipline [I] | **Quote-vs-actual: reel issue + dispatch weight + mobile job close** | Reel issue slips, dispatch challans, Tally sales | M | Moderate (S33) | Someone already recording dispatch can close jobs in <30 s |
| CB4 | ERP deckle optimisers (S24); planners | Built into heavy ERPs [I] | Deckle-combination suggestion (heuristic/ILP), later | Order widths, reel stock | M | Moderate (S24) | Trim waste is significant in semi-auto plants |
| CB5 | ERP stores modules | Same | Reel register with QR labels, inside Margin Control | QR labels, weighing scale entry | L | Moderate (S24) | Stores staff will scan reels |
| CB6 | Contracts negotiated by owners | No data to justify revisions [I] | Price-escalation report per customer (cost index vs price) | Kraft index, customer price list | L | Moderate (S4) | Buyers accept index-linked revisions with evidence |
| CB7 | OEM controls, MES, monitoring vendors (S16–S22) | Cost and setup; generic dashboards [I] | Pulse node on corrugator (later) | CT clamps, run signal | M | Weak | Automatic plants want job-linked downtime |
| CB8 | Manual | — | Count capture via Pulse digital input (later) | Photo-eye / count pulse | M | Weak | Counting accuracy matters enough to pay |
| CB9 | Lab testers | — | Out of scope (lab equipment market) | — | — | Weak | — |
| CB10 | Energy auditors | — | Pulse energy channel for boiler auxiliaries (later) | Modbus meter | M | Weak | — |
| FX1 | Samadhan, ParamERP (S24, S26), Label Traxx (S29) | Imported MIS expensive; Indian ERPs heavy [I] | **Margin Control – Flexibles: laminate structure costing** | Layer library, coat weights, cylinder costs | M | Moderate (S24, S29) | Converters will share real coat weights and waste tables |
| FX2 | OEM automation (S57, S58); MIS waste tables (S56) | Doesn't feed actual waste back into quotes [I] | Actual makeready-waste capture per job → waste curve by run length | Job close: input/output kg, metres | M | Moderate (S35, S59) | Operators record input and output weights |
| FX3 | Solvent recovery OEMs | — | Solvent-per-job tracking in Margin Control (later) | Solvent issue log | L | Weak | Solvent is a top-3 cost converters care about |
| FX4 | QC registers | — | Hold/curing WIP board in WIP tracker | Job status | L | Weak | — |
| FX5 | Spectrophotometer and ink-kitchen vendors | Specialised hardware market [I] | Out of scope; partner | — | — | Weak | — |
| FX6 | Spreadsheets | — | Tooling register (QR) in WIP module | QR labels | L | Weak | — |
| FX7 | ERP | — | Roll-yield reconciliation in quote-vs-actual | Slitting output weights | L | Weak | — |
| LB1 | Label Traxx, Cerm (S29, S61) | Priced for Western converters [I] | Run-length-aware waste curves in costing | Job actuals | L | Moderate (S35, S56) | Indian label converters use structured costing |
| LB2 | Vendor calculators (S51) | Generic [I] | Coverage-aware digital costing | Artwork coverage % | M | Moderate (S51) | — |
| LB3 | Spreadsheets | — | Tooling register | QR | L | Weak | — |
| CP1 | Print MIS (SolPrint, Rogler, Speedpeq: S26, S27) | Heavy, generic [I] | Same engine as CB2/FX1 (not a priority segment) | — | L | Moderate (S52) | — |
| CP2 | OEM press automation | Capex [I] | Makeready time capture (Pulse) | Run signal | M | Moderate (S57, S59) | — |
| PK1 | MIS schedulers (S29) | Complex; data-hungry [I] | Simple visual scheduler after WIP tracking exists | Job routes, machine calendar | M–H | Moderate (S29) | Plants will keep the schedule up to date |
| PK2 | ERP; WhatsApp | ERP heavy; WhatsApp unstructured [I] | **Mobile job-ticket / WIP tracker** (QR job cards) | QR job cards, phone | L | Moderate (S28) | Supervisors scan at stage changes |
| PK3 | Tally add-ons, ERPs | — | Tally connector (import masters and sales vouchers; export) | Tally XML/ODBC [PK] | M | Moderate (S28) | Customers allow Tally access |
| PK4 | Guidewheel, Amper, LEANworx, Sochiot, Pearl (S16–S22) | Crowded; Western pricing too high for SMEs; Indian offers fragmented [I] | **Cyberion Pulse** (second product), positioned on job costing | CT clamps, DI, Modbus | M | Moderate (S16–S22) | Job-linked runtime is valued above OEE dashboards |
| PK5 | ERP batch modules | — | Batch ↔ job ↔ material-lot link in WIP tracker | QR, lot numbers | M | Weak | Food/pharma packaging buyers demand traceability |
| PK6 | Generic OCR | — | Document AI for RFQ/spec extraction into quote draft (human approves) | Email/PDF/WhatsApp images | M | Weak | Intake volume justifies it |
| IM1 | MES (Mattec $399/mo listing S30; TIG S31), monitoring vendors | Cost and complexity for small moulders [I] | Pulse cycle counting + standard-cycle comparison → cost per part | Cycle pulse (mould-open signal) or CT signature | M | Moderate (S16, S30) | Clean cycle signal obtainable without opening the control panel |
| IM2 | Same | Same | Pulse runtime + operator reason codes (tablet/phone) | CT clamp; reason-code UI | M | Moderate (S16, S22) | Operators enter reason codes |
| IM3 | Energy meters + consultants; BEE-style audits | One-off audits do not sustain savings [I] | Pulse energy channel → kWh/kg by machine and job | Modbus meter (e.g. Selec MFM383A-C, S45) | M | Strong-moderate (S10–S14) | Monthly kWh/kg reporting changes behaviour or capex decisions |
| IM4 | Dryer OEM controls | Older dryers lack logging [I] | Dryer-condition logger (dew point/temperature) – later | Dew-point sensor (expensive), temperature | M–H | Moderate (S37, S55) | Moulders of hygroscopic resins will pay for logging |
| IM5 | CMMS tools | Not fed by shot counts [I] | Shot-count-driven PM tickets from Pulse | Cycle count | L | Weak | — |
| IM6 | EUROMAP 63/77 on newer machines (S32) | Legacy machines lack interfaces [I] | Setting-sheet library (photo + structured fields) | Operator entry; later EUROMAP | L–M | Weak | Plants value a settings library |
| IM7 | Purge compounds | — | Sequence-aware scheduling (later) | Job colours | M | Weak | — |
| IM8 | Manual | — | Regrind ratio entry in job close | Operator entry | L | Weak | — |
| IM9 | Chiller OEM controls | — | Water temperature/flow channel on Pulse (later) | RTD/flow sensor | M | Weak | — |
| EX1 | Auto-gauge OEMs: Addex, TSM, Nordson (S36) | Capex-heavy for small lines [I] | Roll-weight-based giveaway report (target vs actual g/m²) | Roll weights, metres, width | L | Moderate (S36) | Lines run measurably heavy and owners know it |
| EX2 | Experience | — | Start-up scrap capture in job close | Scrap weight | L | Weak | — |
| EX3 | Energy meters | — | Pulse kWh/kg per line | Modbus meter, output kg | M | Moderate (S13) | — |
| BM1 | Parison controllers | — | Weight-giveaway report | Weigh-scale entry | L | Weak | — |
| TF1 | — | — | Sheet-utilisation analytics (later) | — | M | Weak | — |
| UT1 | Ultrasonic leak surveys | Periodic, not continuous [I] | Pulse pressure + compressor kW channel (later) | Pressure transmitter 4–20 mA, CT | M | Moderate (S15) | Savings visible within 60 days |
| UT2 | Capacitor vendors, meters | — | Demand/PF alerting via Modbus meter | Modbus meter | L | Weak | — |
| BX1 | Market price newsletters | Not linked to quotes [I] | Price index service inside Margin Control | Supplier quotes, invoices | L | Moderate (S4, S5, S50) | Price data can be maintained per region |
| BX2 | EPR consultants | Fragmented [I] | Recycled-content and batch records export (later) | Material lots | M | Moderate (S38) | Brand owners push converters for proof |
| BX3 | — | — | Settings library + SOP knowledge base (RAG) much later | Documents | M | Weak | — |

**Database limitation.** Only about 20 of the 47 rows have moderate or better *external* evidence. The rest rest on established manufacturing mechanisms but have no Indian cost data. That imbalance is itself a finding: the costing-and-margin rows are where public evidence is densest, which is one reason they rank first.
