# EXPERIMENT METHODOLOGY

All results are produced by scripts in `source_code/src` and stored in `results/`. Nothing in the report or deck is typed by hand: tables are rendered from the CSV/JSON files.

## 1. Questions
Q1 How imperceptible is the watermark (PSNR, SSIM) across many different images?
Q2 How robust is the extraction (NC, ZNCC, BER) to 14 attacks (plus an unattacked reference), and for which kinds of images does it fail?
Q3 How does the embedding strength α trade imperceptibility against robustness?
Q4 Does a high NC prove that *this* watermark is present (false-positive controls)?
Q5 How does the scheme compare with existing technology, and can it run on video?

## 2. Data
100 unique 512×512 8-bit grey images (94 real, 6 labelled synthetic) — `data/README.md`. One 64×64 binary logo ("CYBERION", `logo.py`) is the payload for every image. Hosts are **not** modified except by the watermark.

## 3. Experiments (`run_batch_experiment.py`, `config.json`)

| ID | What is done | Units | Metrics recorded |
|---|---|---|---|
| E1 | embed with α = 0.10; round to 8 bit and save PNG (`outputs/watermarked`); reopen and validate | 100 images | PSNR, SSIM (on the stored 8-bit image and on the float image), max/mean abs difference, embed time, key size, file validity |
| E2 | 15 conditions (14 attacks + unattacked reference) × 2 protocols (**uint8**: attack the 8-bit image — primary; **float**: attack the float image — the original submission's protocol); extract; compare with the logo | 100 × 15 × 2 = 3000 trials | NC, ZNCC, BER, attack time, extract time, status/error text |
| E3 | α ∈ {0.02, 0.05, 0.08, 0.10, 0.15, 0.20, 0.30, 0.40} × {no attack, JPEG Q=50, Gaussian noise σ²=0.02, Gaussian blur σ=1.5, rotation 5°} | 100 × 8 × 5 = 4000 rows | PSNR, SSIM, NC, ZNCC, BER |
| E4 | controls: (a) other host unwatermarked, key of image *i*; (b) other host watermarked with the same logo, key of image *i*; (c) same host watermarked with a different logo (two alternative logos), decoded with the key of logo A; (c-ref) same, decoded with its own key; (d) own unwatermarked host with own key; genuine reference | 1600 rows (5 random other images per image, seeded) | NC, ZNCC, BER |
| S1 | scheme comparison (`benchmark_tech.py`): project vs `blind-watermark` vs block-DCT vs LSB; 30 random real images × 9 attacks | 1080 trials | PSNR, BER, NC, times |
| S2 | component benchmark: 10 operations, 3 random images, 2 warm-ups + 9 repeats | | median/IQR time, numerical agreement |
| V1 | video (`video_demo.py`): 2 clips × first 60 frames × 6 codec settings | 720 decoded frames | PSNR, NC, BER, bit-rate, times, frames decoded |

Per-image seeds: stochastic attacks use `base_seed + 100·index (+offset)`; control images are drawn with `numpy.random.default_rng(base_seed)`. Re-running gives identical numbers (verified: two full runs produced identical aggregates).

## 4. Metrics
* **PSNR** `10·log10(255²/MSE)` (capped at 100 dB when identical); **SSIM** scikit-image defaults (7×7 uniform window, data range 255) [16].
* **NC** (the original metric), **ZNCC** (mean-centred NC; added because NC of a *blank bright image* is already 0.359 for this logo and 0.868 for its rank-1 approximation), **BER** at threshold 127.5.
* **Recognisability threshold** NC ≥ 0.75: kept for comparability with the submitted report; it is a *convention used by the project*, not a verified literature standard. Its false-positive rate is estimated by E4 (≈ 10–13 % for unrelated images).
* **Interpretation limits** (stated again in the report): higher PSNR/SSIM is better only for imperceptibility against the *original*; NC/BER are conditional on the key; edge density and similar detection metrics were not used because no edge-detection operation exists in the project.

## 5. Statistics
Means with 95 % bootstrap CIs (2000 resamples, seeded) for NC; pass rates with Wilson 95 % intervals; Spearman correlations between NC and image contrast/brightness (n = 100, p-values not corrected for 28 tests); Mann–Whitney AUC for genuine vs control NC. Images are treated as independent samples; the 94 real images are a convenience sample, so confidence intervals describe sampling variability *within this set*, not a population of all photographs.

## 6. Validity checks
* 43 unit/integration tests (`tests/`, result in `results/test_results.txt`).
* The legacy two-image script reproduces the submitted report (`results/tables/legacy_reproduction_cameraman.csv`, max |ΔNC| = 0.004).
* `run_summary.json`: 100/100 images OK, 3000/3000 attack trials OK, 100/100 output PNGs reopened with correct shape/dtype, 0 failures; 4000/4000 sweep rows OK.
* Protocol check: the uint8 and float protocols differ by at most 0.2 in NC for a single image (histogram equalisation) and by < 0.01 elsewhere (`protocol_comparison.csv`).

## 7. Hardware / software
4 vCPU Intel Xeon @ 2.1 GHz, 15 GB RAM, Linux 6.18, Python 3.13.16, NumPy 2.5.3, SciPy 1.18.1, scikit-image 0.26.0, Pillow 12.3.0, PyWavelets (module 1.8.0 / metadata 1.10.0), OpenCV 5.0.0, ImageMagick 6.9.12, FFmpeg 6.1.1. Timing: one BLAS thread per process; experiments ran in 4 parallel worker processes (so per-operation timings are single-thread but may include some cache contention). Peak resident memory of a worker: 166 MB. No GPU.

## 8. Reproduce
```
pip install -r source_code/requirements.txt
cd source_code/src
python build_dataset.py            # data/original + metadata.csv   (~1 min, needs network)
python run_batch_experiment.py     # results/*.csv, outputs/watermarked (~80 s on 4 cores)
python analysis.py                 # results/tables, results/analysis_summary.json, visualizations/
python benchmark_tech.py && python analysis_tech.py    # technology comparison (~2.5 min)
python video_demo.py --frames 60   # exploratory video test (~45 s, needs ffmpeg)
python run_experiment.py           # legacy 2-image reproduction
python exp_principal_component_variant.py   # negative-result experiment
cd ../.. && python -m pytest tests -q
```
