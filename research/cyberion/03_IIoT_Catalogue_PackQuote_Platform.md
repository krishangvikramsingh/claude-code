# Part 3: ESP32 / IIoT product catalogue (Deliverable E), PackQuote expansion (Deliverable F), shared platform, data strategy, security and regulation

Evidence labels **[F] [D] [I] [H] [PK]** and source IDs (S#) are as defined in [SOURCES.md](SOURCES.md).

> **Cost disclaimer.** All BOM figures are **indicative ranges as of October 2026**, from marketplace listings and typical distributor pricing for similar parts. Component availability and prices were **not verified with suppliers** in this research. The only listed price actually retrieved is the Selec MFM383A meter (S45). Re-quote from LCSC/Mouser/DigiKey India/Robu/Element14 India before any build decision.

---

## Stage 4: Technical evaluation summary

- **Is ESP32 appropriate?** Yes, for **low-rate, non-invasive telemetry nodes**: run state from CT clamps, pulse counting, Modbus RTU polling of certified meters, local buffering, then MQTT over Wi-Fi or Ethernet.
  - **Strengths:** cost, a mature SDK (ESP-IDF), and security features (Secure Boot V2, flash encryption) [PK]. WPC ETA certificates exist for Espressif modules (S42).
  - **Not appropriate for:**
    - High-speed vibration analysis requiring kHz sampling with precision ADCs, where a dedicated vibration sensor or DSP is better.
    - Revenue-grade energy metering. Use certified meters.
    - Anything in a control or safety loop.
    - Hazardous areas, such as solvent-laden zones in gravure plants. These need certified Ex equipment [PK]; Cyberion should not enter them.
- **Variant choice [PK]:**
  - **Classic ESP32 (ESP32-WROOM-32E)** has an Ethernet MAC (RMII) for wired plants.
  - **ESP32-S3** has more RAM and USB but needs SPI Ethernet (W5500).
  - **ESP32-C6** adds Wi-Fi 6.
  - **Recommendation:** ESP32-S3-WROOM-1 (N8, no PSRAM) + W5500 for a single SKU supporting both Wi-Fi and Ethernet.
  - Confirm the module's ambient temperature grade in the datasheet (S46). Panel interiors near heaters can exceed 50 °C. Some PSRAM variants have lower temperature limits [PK].
- **Buy before build:** for pilots, consider certified industrial ESP32 controllers (DIN-rail units with isolated I/O are sold by several vendors) or a commercial Modbus/MQTT gateway. Design a custom PCB only after ≥ 3 paid pilots confirm the I/O mix [I].

---

## Deliverable E: IIoT product catalogue

### E1. Pulse Node (machine run-state, cycle and count). Priority: HIGH (second product)

| # | Item | Specification |
|---|---|---|
| 1 | Problem | Unrecorded downtime, cycle drift, machine hours per job (PK4, IM1, IM2, CB7) |
| 2 | Target machine | IMMs, extruders, corrugators, printer-slotters, presses, folder-gluers |
| 3 | Buyer | Owner (SME); plant head evaluates |
| 4 | Sensors | **Split-core CTs** around the main motor/heater feeder conductors, inside the machine's panel or at the feeder: 0–100 A or 0–200 A, **333 mV or 1 V voltage-output type** (built-in burden, safe if disconnected). **Optional isolated pulse input:** 24 V machine signal such as mould-open or a counter output, via a dedicated relay contact or a proximity/photo sensor that Cyberion installs, never by tapping control wiring without approval |
| 5 | Sampling and accuracy | CT RMS computed over ~200 ms windows; reported at 1–10 s. Accuracy ±2–5% is sufficient for **state classification** (not billing). Pulse input up to ~50 Hz; debounced |
| 6 | Controller | ESP32-S3-WROOM-1 (or ESP32-WROOM-32E for native Ethernet) |
| 7 | Signal conditioning | External ADC (e.g. ADS1115, 16-bit) or ESP32 ADC with calibration. Op-amp buffer, RC filtering, TVS on every input. Pulse inputs via optocoupler (e.g. PC817 class) or digital isolator, rated ≥ 2.5 kV |
| 8 | Interfaces | 3× CT analogue, 2× isolated DI, 1× isolated RS-485 (Modbus RTU master for meters), 1× I²C for an optional temperature sensor |
| 9 | Communications | MQTT over TLS on Wi-Fi 2.4 GHz **or** Ethernet (W5500). **Optional gateway mode:** one node acts as Modbus master or Ethernet uplink for the others. BLE only for commissioning |
| 10 | Gateway need | Not required for ≤ 20 nodes on good Wi-Fi. Use an Ethernet-uplinked node or an industrial router where Wi-Fi is poor (metal sheds, interference) |
| 11 | Offline buffering | ≥ 7 days of aggregated data in flash (LittleFS ring buffer) or FRAM/microSD; store-and-forward with sequence numbers and idempotent ingestion |
| 12 | Power and protection | 24 VDC from a certified DIN-rail PSU (e.g. 230 VAC → 24 V, 15 W, IEC/EN 62368-1 listed). Reverse-polarity and TVS protection, polyfuse. **The node itself never touches mains**; mains wiring is only the certified PSU's input, installed by a licensed electrician |
| 13 | Enclosure | DIN-rail inside the existing panel, or separate IP65 polycarbonate box (IEC 60529 [PK]); cable glands; ambient 0–55 °C design target; conformal coating against dust and humidity |
| 14 | Calibration | CT ratio set in software; one-shift auto-learning of run/idle/stop thresholds (as in S16); annual verification visit |
| 15 | Indicative BOM (Oct 2026, unverified) | Module ₹300–450; W5500 ₹200–350; isolated RS-485 ₹300–800; ADC ₹150–300; optocouplers and protection ₹150–300; PCB 4-layer + SMT assembly at 100 pcs ₹700–1,400; enclosure + glands + terminals ₹600–1,200; 24 V PSU ₹700–1,100; **3 industrial split-core CTs ₹1,500–4,500**. **Total ₹4,600–10,400** per machine node |
| 16 | Other costs | Assembly and test fixture ₹300/unit at small volume; EMC pre-compliance scan ₹40k–1L per design iteration [I]; WPC ETA self-declaration for the end product (S42); MTCTE applicability to be confirmed (S43); installation 1–2 h per machine by an electrician + engineer ≈ ₹1,500–3,000 |
| 17 | Service life | 5–7-year design target; electrolytic capacitors rated 105 °C; replace by swap; keep 5% spares |
| 18 | Firmware and fleet | ESP-IDF; **dual OTA partitions with rollback**; signed images; staged rollout (1% → 10% → 100%); remote logs; watchdog; device health telemetry (RSSI, heap, uptime, buffer depth) |
| 19 | Security | Secure Boot V2 + flash encryption enabled in production [PK]. Unique per-device X.509 certificate provisioned at factory test; mTLS to the broker; no default passwords; BLE commissioning only within a time window after a button press; topic ACLs per device. Aligned with ETSI EN 303 645 / IEC 62443-4-2 principles (voluntary) [PK]. Design for CRA if the EU is ever targeted (S40) |
| 20 | Software integration | Device registry → MQTT ingest → time-series → state engine → job-context join → Margin Control actuals |
| 21 | Limitations and alternatives | CT state detection cannot tell "running good parts" from "running scrap" (needs a count or quality input). Multi-motor machines need CT placement engineering. **Alternatives:** EUROMAP 63/77 or OPC UA on newer IMMs (S32); commercial monitoring kits; PLC tags via Modbus TCP |

### E2. Pulse Energy Gateway (certified meters over Modbus). Priority: HIGH (bundled with E1)

| Item | Specification |
|---|---|
| Problem | kWh per machine, job and kg; idle energy; demand/PF penalties (IM3, EX3, UT1, UT2) |
| Hardware | Same node as E1 acting as Modbus RTU master on isolated RS-485; up to 8–16 certified panel meters (e.g. Selec MFM383A-C-CE, listed ₹2,000–3,400: S45; or Schneider/L&T equivalents). Meters use their own certified CTs and voltage taps, **installed by a licensed electrician** |
| Sampling | Poll 1–15 s; 1-min aggregates; energy registers read as cumulative counters (robust to gaps) |
| Accuracy | Meter class (typically Class 1 or 0.5S, check the datasheet) |
| BOM | Node ₹4,600–7,000 (fewer CTs) + meters ₹2,000–3,400 each + meter CTs ₹600–1,500 each (unverified) |
| Safety | **Mains measurement only through certified meters**; node remains on 24 V SELV |
| Recurring revenue | ₹500/meter/month or plant bundle |

### E3. Utility channel add-ons. Priority: MEDIUM (after E1/E2 pilots)

| Device | Sensor | Interface | Purpose | Note |
|---|---|---|---|---|
| Compressed-air monitor | Pressure transmitter 0–16 bar, 4–20 mA; compressor kW from E2 | 4–20 mA input board (precision shunt + ADC, isolated) | Leak load at no-production times (S15) | Optional thermal-mass flow meter is costly (₹40k+ [I]) |
| Chiller / cooling-water monitor | PT100/PT1000 RTDs (supply/return), pulse-output flow meter | RTD front-end (MAX31865 class), DI | ΔT and flow → cooling adequacy (IM9) | — |
| Dryer condition logger | Temperature at hopper inlet; dew-point sensor | 4–20 mA / Modbus | Drying compliance for hygroscopic resins (IM4, S37) | Industrial dew-point sensors are expensive (often ₹30k+ [I]); validate WTP first |
| Storage condition monitor | Temperature/RH sensor (SHT4x class) | I²C | Kraft reel moisture conditioning (CB9) | Low value alone; add-on only |

### E4. Rejected device concepts (for now)

| Concept | Reason |
|---|---|
| Vibration predictive-maintenance node | Needs high-rate, accurate accelerometers and analytics. Well-funded competitors (S23); SME ROI unproven |
| Inline film-thickness gauge | Specialist nuclear/IR/capacitive gauges from OEMs (S36); safety and regulatory issues for radiation sources |
| Camera-based defect inspection | See ranking O14 |
| Any device that switches machine power or writes setpoints | Safety-critical; outside scope |

### Electrical and industrial safety rules (non-negotiable)

1. **No hobby boards in customer panels.** Production uses Cyberion's own PCB, or certified industrial controllers, built to a documented design with creepage/clearance, isolation and protection.
2. **ESP32 circuits never connect directly to mains or to machine control circuits.** Mains only enters through certified PSUs and certified meters. CT secondaries must be voltage-output types or properly burdened; never leave a current-output CT open-circuit.
3. **Installation by licensed electricians** under the applicable Indian electrical safety regulations (CEA Safety Regulations 2023 [PK]), with machine isolation (lock-out/tag-out) during installation. Get written customer permission; photograph installation records.
4. **Warranty:** prefer installing at the feeder or distribution board rather than inside OEM control cabinets. Where an OEM cabinet must be opened, get the customer's written acceptance and, ideally, OEM/dealer consent.
5. **EMC and noise:** VFDs and heater SSRs are severe noise sources. Use shielded cables, ferrites, isolated inputs and TVS; route signal cables away from power; run a pre-compliance EMC scan (IEC 61326-1 is the relevant family for measurement/control equipment [PK]).
6. **Standards that actually apply (India, v1):**

   | Requirement | Status | What to do |
   |---|---|---|
   | WPC ETA (radio) | **Mandatory** | Self-declaration for the end product's radio (S42) |
   | MTCTE | **Status to verify** | Applicability to Cyberion's device class; IoT gateways and monitoring endpoints appear in published scope lists (S43) |
   | Electrical safety of the PSU | **Mandatory** | Use certified parts |
   | Product safety of the node | **Recommended practice** | Design to IEC 61010-1 principles [PK] |
   | BIS CRS | **Check** | Verify whether the final product falls in a notified category [PK] |

7. **Hazardous areas:** do not deploy in solvent zones (gravure ink rooms, solvent stores) without Ex-certified equipment. Exclude these areas from scope.

### Device economics (Pulse, per machine)

| Item | Conservative | Base | Optimistic |
|---|---|---|---|
| Hardware cost (BOM + assembly + test) | ₹9,500 | ₹7,000 | ₹5,500 |
| Installation cost (Cyberion's cost) | ₹3,000 | ₹2,000 | ₹1,500 |
| Hardware selling price | ₹12,000 | ₹12,000 | ₹15,000 |
| Hardware gross margin | 21% | 42% | 63% |
| Installation charged | ₹2,000 | ₹2,500 | ₹3,000 |
| SaaS per machine per month | ₹700 | ₹900 | ₹1,200 |
| Cost to serve per machine per month (cloud ₹20–40 + support + field visits) | ₹300 | ₹200 | ₹150 |
| Warranty provision (12 months, % of hardware price) | 8% | 5% | 3% |
| Customer upfront investment, 10 machines | ₹1.4 L | ₹1.45 L | ₹1.8 L |
| Customer payback | Needs measured benefit ≥ ₹25–30k/month for a 10-machine plant to pay back in < 12 months [H] | | |

**Commercial model comparison:**

| Model | For the customer | For Cyberion | Verdict |
|---|---|---|---|
| A. Hardware sale + annual subscription | Capex small, familiar; renewal risk | Cash upfront covers BOM, so working capital is protected | **Recommended for SMEs.** Prepay 12 months of SaaS; paid pilot credited |
| B. Hardware-as-a-service (monthly) | No capex, easy yes | Cyberion funds hardware; churn strands devices; needs debt or equity | Only for larger customers (> 30 machines) with 24-month contracts and a deposit |
| C. One-time install + optional analytics | Cheapest | No recurring revenue; drifts into project/agency work | **Avoid** |

---

## Deliverable F: PackQuote expansion strategy

### F1. What PackQuote is today (and what is unknown)

PackQuote is described as packaging costing, quotation generation and workflow automation. This research **could not inspect** its codebase, customer list, segments covered, pricing or usage. Founder decision N1 (Part 6) is to audit these first.

Nothing below assumes PackQuote should be discarded. Every stage builds on its costing engine.

### F2. Staged roadmap

| Stage | Timing | Capabilities | Packaging | Gate to next stage |
|---|---|---|---|---|
| **0. Audit and harden** | Weeks 1–4 | Costing engine extracted as a versioned, unit-tested library; tenant isolation verified; audit log | Existing plans | Engine test coverage on 100 real reference quotes from customers |
| **1. Margin Control** | Months 2–4 | Kraft/resin price book; bulk re-price; margin-impact report; escalation pack; job close PWA; quote-vs-actual; Tally CSV/XML import | New Growth tier; Starter keeps quoting only | ≥ 5 paying accounts; ≥ 80% job-close compliance in ≥ 3 |
| **2. Flexibles + WIP** | Months 4–8 | Laminate structure costing; waste curves; QR job cards; stage tracking; customer status link | Flexibles edition; WIP included in Growth | ≥ 15 accounts; < 3% monthly logo churn |
| **3. Actuals automation (Pulse)** | Months 9–15 | Device registry; MQTT ingest; machine hours, kWh and counts joined to jobs; cost-per-hour learned from actuals | Pulse add-on (hardware + per-machine SaaS) | ≥ 3 paid Pulse pilots converted; measured ≥ 95% state accuracy |
| **4. Intelligence** | Months 15–30 | Learned waste curves; machine-rate calibration; scheduling assistant; RFQ document AI; NL margin explanations; tenant-private benchmarks | AI credits; Enterprise tier | Positive gross margin per AI feature; usage by > 30% of accounts |
| **5. Platform** | Months 30+ | Public API, partner connectors (ERPs, OEM interfaces), opt-in anonymised benchmarking | Platform/partner pricing | ≥ 150 accounts, NRR > 100% |

**What is paid for separately and what is bundled:**

| Paid separately | Bundled in a tier | Wait for adoption |
|---|---|---|
| Pulse hardware + per-machine SaaS; Tally live connector; multi-plant; custom reports; onboarding; RFQ document AI (credits) | Price book, re-pricing, quote-vs-actual, WIP (Growth) | Scheduling, benchmarking, customer/supplier portals, predictive alerts |

### F3. Telemetry → costing workflow

```
Machine (CT / pulse / meter) → Pulse node (state, counts, kWh; buffer) → MQTT/TLS → Ingest (validate, dedupe by device+seq)
  → Time-series store (raw 1–10 s, 1-min rollups) → State engine (run/idle/stop, cycles)
  → JOB CONTEXT JOIN ← (QR scan "job 4512 started on M7" | planner schedule | dispatch close-out)
  → Job actuals (machine h, kWh, counts, downtime by reason) + manual actuals (kg issued, kg rejected)
  → Costing engine (actual cost per job, versioned rates) → Quote-vs-actual variance → Rate-table recalibration proposal
  → Human approval (estimator/owner) → updated cost tables for future quotes
```

**The job-identification problem.** Telemetry knows *a machine ran*, not *which job*. Three ways to link them, in order of reliability:
1. **Operator scan** of the QR job card at job start and end. It is cheap, but compliance must be measured.
2. **Schedule inference:** the planner's sequence plus state changes. Error-prone when sequences change.
3. **Machine interface:** job/recipe IDs from EUROMAP 77 or OPC UA on newer machines (S32).

Cyberion should use (1) with (2) as a fallback, flag unassigned runtime as "unallocated", and never silently guess.

**How actuals improve future quotes:**
- Machine-hour rates are re-derived from *actual* hours per job; plant-specific waste curves come from measured kg in and out.
- Energy per kg is measured instead of estimated.
- Changes are always **proposed** to the estimator with before/after impact on reference quotes, never auto-applied. That keeps pricing explainable.

### F4. AI architecture (inside the modular platform)

| Component | Role | Determinism |
|---|---|---|
| Costing engine | All money calculations | **Deterministic**, versioned, unit-tested, reproducible ("quote 123 was computed with engine v1.8, rate table r42") |
| Structured industrial data model | Jobs, SKUs, specs, materials, machines, events | Deterministic |
| API gateway | Auth, rate limits, versioning (/v1) | — |
| Tenant-isolated storage | Postgres with `tenant_id` + row-level security (RLS); per-tenant encryption keys for documents | — |
| Knowledge base and RAG | Per-tenant document index; shared public technical corpus (non-confidential) | Probabilistic, cited answers only |
| Model router and usage limits | Small/cheap model for extraction; larger for explanations; per-tenant monthly caps | — |
| AI credits billing | Usage-metered features (RFQ extraction, NL reports) | — |
| Device registry | Identity, certificates, firmware version, location, machine mapping | — |
| Event ingestion and alerting | MQTT → queue → rules → notifications (WhatsApp/email) | Rules deterministic |
| Analytics and reporting | SQL rollups; scheduled PDFs | Deterministic |
| RBAC and audit trail | Owner/Estimator/Dispatch/Maintenance/Viewer; every price change logged | — |
| Private/edge option | Later, for Enterprise only: on-prem gateway with cloud sync | — |

LLMs never set prices, approve discounts, change process limits, or decide authorisation.

---

## §15: Shared technology platform (recommended stack for a small team)

**Principle: a modular monolith.** One deployable backend with clear modules, one Postgres database, one MQTT broker. Avoid microservices until there are more than 3 teams.

| Concern | Recommendation | Why |
|---|---|---|
| Backend | Keep **PackQuote's existing language and framework**. If greenfield: TypeScript (NestJS) or Python (FastAPI) | Avoids a rewrite; productivity |
| Database | **PostgreSQL** with RLS for tenant isolation; **TimescaleDB extension** for telemetry (or Postgres partitioned tables to start) | One database to operate; time-series without a second system |
| Messaging | **MQTT broker:** EMQX or Mosquitto (self-hosted), or AWS IoT Core (managed). Mumbai region (ap-south-1) | Standard; mTLS; ACLs |
| Background jobs | Postgres-backed queue (e.g. pg-boss / Celery + Redis) | Simple |
| Frontend | Existing PackQuote web + **PWA** for shop-floor job close (offline-first, IndexedDB queue) | Phones on the floor, poor connectivity |
| Files | S3-compatible object storage, versioned; server-side encryption | — |
| Auth | Existing auth; add org-level RBAC; OTP/WhatsApp login for floor users; SSO only for Enterprise | — |
| Observability | OpenTelemetry → Grafana/Loki/Tempo or a SaaS equivalent; device-fleet dashboard | — |
| Backups and DR | Daily snapshots + WAL archiving (PITR), cross-region copy, quarterly restore drill; RPO 15 min / RTO 4 h target | — |
| Encryption and keys | TLS 1.2+ everywhere; KMS-managed keys; device private keys generated on-device, never exported | — |
| OTA | Signed firmware in object storage; device pulls on a schedule or command; staged rollout with automatic halt on error-rate spike | — |
| Rate limiting | Per tenant and per device at gateway and broker | — |
| Data retention | Raw telemetry 90 days; 1-min rollups 3 years; business records per contract; customer-configurable | — |
| Customer data export | CSV/JSON export of all tenant data plus API; documented in contract | — |
| AI ops | Prompt and model versions stored with each AI output; evaluation sets per use case run in CI; usage and cost dashboards | — |
| Cloud vs private | Cloud-first (Mumbai). Private deployment only for Enterprise at a premium; avoid until > ₹50 L ARR | — |

**Shared across all products:** tenant/auth/RBAC, audit log, costing engine library, job/SKU/material data model, device registry and ingest, notifications, reporting, billing/credits, the Tally connector.
**Independent modules:** segment costing templates (corrugated, flexibles, labels, moulding), Pulse firmware, scheduling, AI features.

---

## §16: Data strategy and defensibility

| Asset | How it is built | Real defensibility? |
|---|---|---|
| **Costing models per segment** (corrugated, flexibles, moulding) | Encoded expertise, validated against hundreds of real quotes | Moderate: copyable in principle, but accuracy comes from field calibration |
| **Industrial data model / ontology** (job → route → machine → material lot → actuals) | Product design | Low–moderate |
| **Customer-specific calibrated tables** (waste curves, machine rates) | Each customer's actuals | **High switching cost**: leaving means losing calibrated costing |
| **Integration library** (Tally, common Indian ERPs, meters, EUROMAP) | Every deployment | Moderate: saves time; compounding |
| **Device fleet and installation playbooks** | Field experience | Moderate: operational moat |
| **Domain evaluation datasets** (RFQ extraction, costing reference sets) | With explicit consent, or synthetic | Moderate |
| **Opt-in anonymised benchmarks** (e.g. kWh/kg distribution for IMMs by tonnage) | Aggregated across consenting tenants, k-anonymity (≥ 10 contributors per cell) | Network effect **only if** enough customers opt in; speculative until ~100+ plants |

**Legal basis and confidentiality:**
- Machine and production data is mostly not personal data. Operator names, phone numbers and attendance-like data *are* personal data under the DPDP Act and Rules: notified 13 Nov 2025, phased to ~May 2027 (S39). Collect only what is needed; give notice; enable deletion.
- **Contract terms:** the customer owns its data. Cyberion may use **de-identified, aggregated** metrics to improve products only where the contract says so, with opt-out. **No cross-tenant pooling of prices, structures or customer lists, ever.** Supplier prices entered by one customer are never shown to another.
- Improvement without exposure comes from:
  - better *code and templates* (product learning);
  - *public or consented* price indices;
  - *aggregate* statistics with minimum cohort sizes.
- **Real moats, honestly ranked:** (1) calibrated customer-specific costing plus workflow habit; (2) integration and installation know-how; (3) segment depth. "Data network effects" are a later, conditional bonus.

---

## §17: Security, reliability and regulatory register

| Area | India (now) | EU (only if expanding) | Mandatory vs recommended |
|---|---|---|---|
| Personal data | DPDP Act 2023 + Rules 2025, phased; consent/notice, security safeguards, breach intimation (S39) | GDPR | Mandatory |
| Cyber incident reporting | CERT-In Directions 2022 (6-hour reporting, log retention) [PK] | NIS2 (customer-side), CRA reporting from 11 Sep 2026 for products with digital elements (S40) | Mandatory where applicable |
| Device cybersecurity | Recommended: IEC 62443-4-2 / ETSI EN 303 645 principles | **RED delegated act (EU) 2022/30 + EN 18031-x applicable from Aug 2025 for radio products** [PK]; **CRA full application 11 Dec 2027** (S40) | EU: mandatory for radio products placed on the market |
| Data access by design | — | **EU Data Act**: connected products placed on the market after 12 Sep 2026 must make user data accessible (S41) | Mandatory in the EU |
| Radio approval | WPC ETA self-declaration (S42) | RED conformity, CE marking | Mandatory |
| Telecom equipment | MTCTE: verify scope for gateways/IoT endpoints (S43) | — | Possibly mandatory |
| Electrical safety and EMC | Certified PSUs; design to IEC 61010-1 / IEC 61326-1 [PK]; installation by licensed electricians [PK] | LVD/EMC via CE (RED covers both for radio products) [PK] | Mandatory (EU); strongly recommended (India) |
| Machinery | Not a machine or safety component if strictly monitoring-only | Machinery Regulation (EU) 2023/1230 from 20 Jan 2027 [PK]: not applicable to monitoring-only devices, but keep out of safety functions | — |
| Enclosure | IP54/IP65 as per environment (IEC 60529) [PK] | Same | Recommended |
| Calibration | Certified meters carry the meter's class; CT-based state detection is not metrology | Same | Recommended |
| Network segmentation | Devices on a separate VLAN/SSID; outbound-only MQTT/TLS; no inbound ports | Same | Recommended |
| Cloud security | Mumbai region; encryption at rest; MFA for admins; least-privilege IAM; annual penetration test once revenue allows | ISO 27001 often demanded by larger EU customers (voluntary) | Recommended |
| Product liability | Written scope ("monitoring only"); limitation-of-liability clauses; product liability insurance once hardware ships | Product Liability Directive (revised) [PK] | Recommended (contractual) |
