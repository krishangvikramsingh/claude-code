# PROJECT AUDIT — Digital Image Watermarking (hybrid DWT–DCT–SVD)

Author of the original project: Krishang Vikram Singh (NMIMS MPSTME, Image and Video Processing).
Audit performed on the files supplied with the request. Every statement below was checked by
reading the source or by executing it; evidence files are named.

## 1. What was supplied

| File | Type | Purpose | Status |
|---|---|---|---|
| `watermark_core.py` (uploaded twice, identical) | Python | `embed_watermark()` / `extract_watermark()` – DWT (Haar) → DCT → SVD, `S' = S + α·Sw` | Working. Docstring/diagram say "block DCT" – code is a **global** DCT of the whole LL sub-band. Called "semi-blind" – it is **non-blind** (needs the host's original singular values). |
| `metrics.py` | Python | PSNR, SSIM, NC, BER | Working; no shape checks; PSNR returned `inf` for identical images. |
| `attacks.py` | Python | 15-condition suite (`ATTACK_SUITE`: 14 attacks **plus "No Attack"**) | Working. The report/deck call it "fifteen attacks" although one entry is the unattacked reference. Noise attacks **not seeded** (results differ run to run). JPEG attack **truncates** floats to `uint8` (biases the image by −0.5 grey level). "Cropping 25%" removes **43.75 % of the area** (25 % of each dimension). |
| `run_experiment.py` (uploaded twice, identical) | Python | End-to-end pipeline on 2 images (`cameraman`, grey `astronaut`), figures, CSV/JSON | Working (6 s). Writes to `../results/`. |
| `make_diagram.py` | Python | Architecture diagrams for report/deck | Working; text said "Block DCT" and "semi-blind". |
| `Digital_Image_Watermarking_Report.docx` | Word | 12-page report | Complete; 2 images only; 5 references (1 textbook, 1 documentation entry). |
| `Digital_Image_Watermarking_Presentation.pptx` | PowerPoint | 15 slides (navy/teal design) | Complete; no speaker notes. |

No notebooks, datasets, videos, requirements file, tests, Canva link or university template were supplied.
(The master prompt mentions optional Canva links and templates; none were provided, so none were used.)

## 2. Architecture (verified from code)

```
host (512x512 grey)           logo (64x64 binary, procedurally drawn)
   │ pywt.dwt2 (Haar, 1 level)        │ skimage.resize -> 256x256
   ▼                                  ▼
 LL (256x256) ─ dct2 (global) ─ SVD   SVD
   │   A = U·S·Vt                     Wm = Uw·Sw·Vtw
   └──── S' = S + α·Sw  (α = 0.10) ───┘
   ▼  A' = U·S'·Vt → idct2 → idwt2 → clip[0,255] → watermarked image  (+ key)
```
Extraction: DWT → global DCT → SVD of the received image → `Sw' = (S_att − S_orig)/α` → `Uw·diag(Sw')·Vtw`.
Key contents actually used by the extractor: `S_original`, `Uw`, `Vtw`, `alpha`, shapes. (`U`, `Vt` are stored but unused.)

## 3. Baseline execution

`python run_experiment.py` ran without errors (Python 3.13, NumPy 2.5, SciPy 1.18, scikit-image 0.26, PyWavelets 1.8).

| Quantity | Original report | Re-run (this audit) | Evidence |
|---|---|---|---|
| mean PSNR / SSIM (2 hosts) | 35.637 dB / 0.9956 | 35.637 dB / 0.9956 | `results/legacy_two_image/summary.json` |
| trials with NC ≥ 0.75 | 25 / 30 | 25 / 30 | same |
| mean NC over 30 trials | 0.832 | 0.8316 | same |
| cameraman NC per attack (15) | Table 5.1 | max |ΔNC| = 0.004 | `results/tables/legacy_reproduction_cameraman.csv` |

The differences (≤ 0.004) come from (i) the seeded noise attacks and (ii) the JPEG attack now rounding instead of truncating.
**All headline numbers of the submitted report are reproducible.**

## 4. Findings (problems and improvement opportunities)

| # | Finding | Evidence | Severity | Action |
|---|---|---|---|---|
| F1 | **False-positive problem.** The logo's identity lives in the key (`Uw`,`Vtw`). Embedding a *different* logo and decoding with the owner's key still yields NC = 0.975 (vs 0.977 genuine, n = 200). NC therefore does not prove ownership. | `results/tables/controls_summary.csv`, `fig_false_positive.png` | High (scientific validity of the "ownership" claim) | Reported as a measured limitation; mitigations discussed (Ch. 9). Algorithm **not** changed. |
| F2 | Wrong-image/wrong-key controls give NC up to 0.945; 9.8 % (unwatermarked) and 12.6 % (watermarked) of such controls exceed the 0.75 "recognisable" threshold. | same | High | Threshold interpretation corrected in report. |
| F3 | The α-trade-off figure used a **dual axis with the NC axis zoomed to 0.93–0.99**, making a 0.05 difference look dramatic; its single low point (α = 0.02, NC 0.929) was caused by the JPEG simulation truncating floats (F8), shown by re-creating the original conditions (`results/exp_jpeg_truncation.txt`: 0.929 truncated vs 0.981 rounded). NC after JPEG Q=50 is essentially flat in α (0.960 → 0.976). The genuine trade-off appears only under harsher attacks (Gaussian noise: pass rate 9 % at α=0.02 → 85 % at α=0.10 → 95 % at α=0.30). | original `Imperceptibility vs. Robustness Trade-off` figure; `fig_alpha_tradeoff.png` | Medium | Figure redone (3 panels, honest axes, 4 attacks, 100 images). |
| F4 | Only 2 images; one is a down-sampled astronaut photo. Conclusions about "most real-world handling" rest on n = 2. | report §4.2 | High | 100-image dataset built (94 real + 6 labelled synthetic). |
| F5 | "Block DCT" in docstring, diagrams, deck and report is wrong: DCT is global. | `watermark_core.py` L39–44 | Low (documentation) | Corrected everywhere. |
| F6 | "Semi-blind" is wrong terminology: extraction needs the original singular values ⇒ non-blind. | `extract_watermark` | Low | Corrected. |
| F7 | Noise attacks unseeded ⇒ not reproducible. | `attacks.py` | Medium | `make_attack_suite(seed)`; per-image seeds. |
| F8 | JPEG attack truncates instead of rounding (−0.5 grey-level bias). Changes NC by ≤ 0.003 at α = 0.1 but by 0.05 at α = 0.02. | experiment in `analysis` log | Low–Medium | Rounding; both protocols reported (`protocol_comparison.csv`). |
| F9 | "Cropping 25%" label: 25 % of each dimension = 43.75 % of the area. | `cropping_attack` | Low | Docstring + report state the area. |
| F10 | PSNR/SSIM/NC thresholds (30 dB, 0.98, 0.75) are presented as "standard in the literature" without a primary source. | report §3.4, §5.1 | Medium | Re-worded as conventions; not attributed to a source I could verify. |
| F11 | PSNR is almost independent of the host (82 of 100 images lie in 35.5–35.75 dB, 91 in 35.5–36 dB; the highest values, up to 43.8 dB, occur on the bright document/object images and the black/white checkerboard — plausibly because clipping to [0,255] removes part of the added signal there; this explanation was not tested) because the added energy is `α·Sw`, set by the logo, not the host. SSIM can collapse on near-constant images (0.58 for the near-black `image_055` while PSNR is 35.9 dB). | `results_images.csv` | Medium | Reported as a limitation / failure case. |
| F12 | Reference list: one entry is a textbook without year/page, one is "library documentation"; Ganic & Eskicioglu venue unspecified. No source for the NC threshold. | report References | Medium | New verified bibliography (`research/REFERENCES.md`). |
| F13 | No input validation, no tests, no requirements file, results written outside the package. | all files | Medium | Validation, 43 unit tests, `requirements.txt`, config-driven runner. |
| F15 | "Fifteen attacks": the suite has **14 attacks + the unattacked reference** (the first report's own list names 14). Headline pass rates of the first report (25/30) include the reference trials. | `attacks.py` ATTACK_NAMES; report §3.3 | Low–Medium | Stated as 14 + reference everywhere; pass rates reported with and without the reference. |
| F14 | Report/deck mention video only as future work; no video code exists. | deck slide 13 | Info | Exploratory per-frame video test added and labelled as such. |

## 5. Existing functionality that was preserved
`embed_watermark`, `extract_watermark` (numerically identical, verified by re-running the original experiment),
the 15-condition suite and its names, the four metrics, the procedural logo (bit-identical: `np.array_equal` verified),
the original two-image pipeline (`run_experiment.py`, now a legacy script) and the original deck design language.

## 6. Missing inputs / assumptions
* No university report template was supplied: a conventional academic structure was used.
* No supervisor/guide name was given: none is invented in the report.
* No Canva link/connection was provided: see `presentation/CANVA_NOTES.md`.
* Only `raw.githubusercontent.com` and PyPI were reachable from the build environment, so the dataset is limited to images hosted there (§ `data/README.md`).
