# CHANGELOG

Originals are preserved unchanged in `source_code/original_backup/`, `report/Original_Report.docx` and `presentation/Original_Presentation.pptx`.
IDs `F1…F14` refer to `PROJECT_AUDIT.md`.

## Modified files (`source_code/src`)

| File | Change | Why | Effect on results |
|---|---|---|---|
| `watermark_core.py` | input validation (2-D, numeric, finite, size, α>0, sub-band name); `resize` import moved to module top; docstring corrected ("global DCT", "non-blind", false-positive limitation) — **numerical code unchanged** | F5, F6, F13 | none (verified: legacy re-run reproduces the report) |
| `metrics.py` | shape checks; `mse()`; PSNR capped at 100 dB for identical images; new `zero_normalized_correlation()` (ZNCC); docs | F13, NC reliability | none for existing metrics; ZNCC added |
| `attacks.py` | `make_attack_suite(seed)` (seeded noise); `ATTACK_NAMES`, `ATTACK_FAMILY`; JPEG attack **rounds** instead of truncating and validates quality; cropping documented as 43.75 % area | F7, F8, F9 | NC changes ≤ 0.003 at α = 0.10 (JPEG rows) |
| `run_experiment.py` | now the *legacy* 2-image script: logo moved to `logo.py`, results → `results/legacy_two_image/` | traceability | reproduces Table 5.1 within 0.004 NC |
| `make_diagram.py` | wording ("2-D DCT (global)", "non-blind", key contents), output → `visualizations/` | F5, F6 | — |

## New files

| File | Purpose |
|---|---|
| `logo.py` | procedural logo (bit-identical to the original; verified) |
| `image_io.py` | safe loading/standardisation (alpha, 16-bit, palette, bilevel, crop, Lanczos), corrupt/empty/unsupported-file errors, PNG verification |
| `dataset_manifest.py`, `build_dataset.py` | 100-image dataset: sources, licences, hashing, near-duplicate rejection, synthetic controls, `metadata.csv` |
| `run_batch_experiment.py` + `config.json` | E1–E4, multiprocessing, per-operation status/timing, output validation, seeded |
| `analysis.py`, `analysis_tech.py` | statistics, tables, figures from recorded CSVs only |
| `benchmark_tech.py` | component and scheme benchmarks vs OpenCV, Pillow, scikit-image, SciPy, NumPy, ImageMagick, `blind-watermark`, LSB, block-DCT |
| `video_demo.py` | exploratory per-frame video test (FFV1, H.264, MJPEG) |
| `exp_principal_component_variant.py` | documented negative result (does not fix false positives) |
| `exp_jpeg_truncation.py` | re-creates the first report's α-sweep conditions: truncation vs rounding before JPEG explains the NC dip at α = 0.02 |
| `tests/` (5 test modules + `conftest.py`, 43 tests) | functions, edge cases, loaders, batch completeness |
| `requirements.txt` | versions used |

## Bug fixed during development (for transparency)
`run_batch_experiment.py --limit N` initially overwrote `data/metadata.csv` with only N rows when writing back processing status. Fixed (merge, never drop rows); dataset rebuilt and the full experiment re-run; `tests/test_dataset_and_results.py::test_exactly_100_unique_images` guards against a recurrence.

## Behavioural differences a reader may notice
* **Protocol:** the primary robustness protocol attacks the 8-bit rounded watermarked image (as it would exist on disk); the original attacked the float image. Both are reported; results differ by < 0.01 NC except histogram equalisation (≤ 0.2 for single images; mean 0.644 vs 0.638).
* **α sweep:** the original sweep used one attack (JPEG Q=50) and a dual axis; now four attacks, 100 images, separate panels (F3).
* **Metrics:** NC kept; ZNCC and BER reported next to it.

## Known limitations
1. **False-positive problem** — the extractor returns the key owner's logo; NC does not prove the logo was embedded (E4). Not fixed.
2. **Non-blind** — requires a 2.1 MB key per image holding the original singular values.
3. **Geometry** — cropping (1 % pass) and rotation > 5° (72 % pass at 15°) fail; no re-synchronisation.
4. **Histogram equalisation** — 44 % pass; no compensation.
5. **Grey-scale only**; colour needs a luminance wrapper.
6. **Clean extraction not lossless** — BER ≈ 0.9 % because of logo resampling.
7. **PSNR is nearly host-independent; SSIM unstable on near-constant images** (0.58 on a near-black image).
8. **Dataset** — 94 real + 6 synthetic images from GitHub-hosted sample sets; rights not individually documented upstream; not a recognised benchmark.
9. **Video** — exploratory only (60 frames × 2 clips); per-frame keys; no temporal attacks; frame dropping requires frame-index bookkeeping (naive index alignment still gave NC 0.969–0.977 versus 0.979–0.981 when aligned — presumably because neighbouring frames are almost identical; not tested further).
10. **Technology comparison** — one existing watermark library (`blind-watermark`) was measured; others (e.g. `invisible-watermark`, learned methods) were not. Its colour/YUV design and channel-wise attacks may favour it.
11. **Timing** — 4 processes on 4 vCPUs; single-thread BLAS; no GPU; run-to-run variation of ≈ 5–10 % (e.g. 78 vs 85 s wall time).
12. **PyWavelets version string** inconsistency in the environment (module 1.8.0 vs distribution 1.10.0) — noted, no effect observed.
