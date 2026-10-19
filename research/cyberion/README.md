# Cyberion Tech Innovations: master research report

**Industrial AI, B2B SaaS, automation and IoT for printing, packaging, plastics and polymers (India-first)**
Research date: 19 October 2026. Prepared as a decision document; no implementation code is included except the transparent financial and scoring models.

## The answer in five lines

1. **Build first:** *PackQuote Margin Control*. It re-prices every quote and price list when kraft prices move, and compares quoted against actual job profit using a 30-second mobile job close. It is software only.
2. **Sell first to:** Indian corrugated box makers (₹5–150 cr turnover) in one cluster. Kraft is ~90% of input cost against ~5% margins, and mills revise prices abruptly (S1, S4, S5).
3. **Price:** ₹3,500 / ₹8,000 / ₹25,000+ per month plus onboarding. The entry point is a paid ₹25,000 **Margin Audit** that measures the customer's own margin leak.
4. **Second product:** *Cyberion Pulse*, a non-invasive ESP32-S3 retrofit node (CT clamps, isolated pulse input, Modbus to certified meters). It feeds machine hours, kWh and counts into job costing. Build it after 15 paying accounts or 3 paid Pulse pilots, and use it to enter plastics.
5. **Do not build now:** generic OEE dashboards, vibration predictive maintenance, vision inspection, LLM copilots, any control functions, or EU/Latvia expansion.

## Document map

| Part | Contents | Deliverables |
|---|---|---|
| [01 Decision brief and pain points](01_Decision_Brief_and_Pain_Points.md) | Executive brief; Stage 1 findings; 47-row source-linked pain-point database | A, B |
| [02 Opportunities, ranking, business cases](02_Opportunities_Ranking_Business_Cases.md) | Technology-to-problem matrix; AI use-case specifications; automation levels; weighted top-15; top-5 business cases | C, D |
| [03 IIoT catalogue, PackQuote, platform](03_IIoT_Catalogue_PackQuote_Platform.md) | ESP32/IIoT device specs, BOM ranges, safety rules, device economics; PackQuote staged roadmap; telemetry-to-costing workflow; architecture; data strategy; security and regulatory register | E, F, §15–17 |
| [04 Competition and validation](04_Competition_and_Validation_Toolkit.md) | Competitor tables; personas; 33 interview questions; experiments; pilot proposal; ROI worksheet; go/no-go gates | G, H |
| [05 Pricing, financials, GTM, roadmap, strategy](05_Pricing_Financials_GTM_Roadmap_Strategy.md) | Pricing; 36-month three-scenario model; sensitivity; bottom-up market estimate; engineering phases; route to 10/25/100/500 customers; international; 3–5-year plan | I, J, K, L, §11, §18 |
| [06 First 90 days and decisions](06_First_90_Days_and_Decision_Register.md) | Week-by-week plan; stop/continue/pivot criteria; founder decision register; final falsifiable recommendation | M, N |
| [SOURCES.md](SOURCES.md) | 62 numbered sources with type and reliability | — |
| [model/](model/) | `financial_model.py`, `monthly.csv`, `summary.md`, `sensitivity.md`, `scoring.py`, `scoring_output.md` | — |

## How to read the evidence

- **[F]** verified fact from a cited source.
- **[D]** documented customer problem.
- **[I]** commercial or engineering inference.
- **[H]** unvalidated hypothesis.
- **[PK]** prior knowledge not re-verified in this session.

Sources marked "(extract)" in SOURCES.md were read through search extracts because the page could not be opened from the research environment. Verify them before quoting externally.

## Known limitations of this research

- **PackQuote:** its code, customers and pricing were not available, so roadmap timings assume a reusable costing engine (decision N1).
- **No interviews were conducted.** No customer quotes, pilots or partnerships are claimed anywhere in this report.
- **Published market sizes conflict by up to 5×** (corrugated ₹18,000–50,000 cr; flexible packaging USD 4.6–20 bn). The report therefore uses bottom-up estimates.
- **No Indian competitor subscription prices were found** for packaging ERPs or monitoring. All Cyberion prices are hypotheses to test.
- **Hardware BOM figures are indicative October 2026 ranges.** Only one component price (Selec meter) was retrieved from listings.
- **Regulatory points marked [PK] need primary-text verification:** EU RED delegated act dates, CERT-In directions, CEA safety regulations, BIS CRS scope and MTCTE scope for the specific device.

## Re-running the models

```bash
cd research/cyberion/model
python3 financial_model.py   # edit ASSUMPTIONS / NEW_ACCTS / COMMON first
python3 scoring.py           # edit WEIGHTS / SCORES first
```
