# TECHNOLOGY COMPARISON

Everything marked **measured** was executed in this submission (`source_code/src/benchmark_tech.py`; raw data in `results/tech_benchmark_*.csv`; environment in `results/tech_summary.json`).
Everything marked **documentation-based** comes from the libraries' public documentation and package metadata and was **not** benchmarked.

## 0. What is being compared, and what is not

The project is an *algorithm* (hybrid DWT–DCT–SVD watermarking) built on *libraries* (NumPy, SciPy, PyWavelets, scikit-image, Pillow, Matplotlib/Pandas).
It is not a general image-processing toolkit and is not claimed to compete with OpenCV, ImageMagick or FFmpeg as such.
Two comparisons are meaningful:

* **A. Component level** – the same low-level operation implemented by different libraries (is the project's choice of library sound?).
* **B. Scheme level** – the project's watermarking scheme against an existing open-source scheme and two classical baselines (what does the algorithm buy?).

## 1. Feature matrix (documentation-based)

| Capability used by the project | NumPy | SciPy | PyWavelets | scikit-image | Pillow | OpenCV (`cv2`) | ImageMagick | FFmpeg | `blind-watermark` |
|---|---|---|---|---|---|---|---|---|---|
| 2-D DCT | – | ✓ (`fft`, `fftpack`) | – | – | – | ✓ (`cv2.dct`) | – | – | internal |
| SVD | ✓ (`linalg`) | ✓ (`linalg`) | – | – | – | ✓ (`cv2.SVDecomp`) | – | – | internal |
| Discrete wavelet transform | – | – | ✓ | via PyWavelets only (denoising) | – | – | – | – | internal |
| JPEG encode/decode | – | – | – | via I/O plug-ins | ✓ | ✓ | ✓ | MJPEG ✓ | – |
| Median / Gaussian filters | – | ✓ (`ndimage`) | – | ✓ | ✓ | ✓ | ✓ | filters ✓ | – |
| Rotation / resize | – | ✓ (`ndimage`) | – | ✓ | ✓ | ✓ | ✓ | scale filter | – |
| Histogram equalisation | – | – | – | ✓ | ✓ (`ImageOps`) | ✓ (+CLAHE) | ✓ | – | – |
| PSNR / SSIM | – | – | – | ✓ / ✓ | – | PSNR ✓ (SSIM only in the contrib `quality` module) | `compare -metric` | – | – |
| Video decode/encode | – | – | – | – | – | ✓ (`VideoCapture/Writer`, FFmpeg back end) | – | ✓ (reference tool) | – |
| GPU | via other libs | via CuPy-type drop-ins | – | – | – | OpenCL T-API in core; CUDA needs a contrib build | OpenCL (build option) | HW encoders | – |
| Licence (package metadata) | BSD-3-Clause | BSD | MIT / BSD-3-Clause | BSD | MIT-CMU (HPND) | Apache-2.0 | ImageMagick licence (Apache-style) | LGPL/GPL depending on build | MIT |
| Role in project | arrays, SVD | DCT, filters | DWT | rotate/resize/metrics | JPEG, I/O | *not used in the algorithm* (benchmark, video only) | benchmark only | video test | benchmark only |

Reading the matrix: no single library covers DWT + DCT + SVD + JPEG + metrics; combining PyWavelets, SciPy, NumPy and Pillow is a natural, minimal choice, and OpenCV could replace SciPy/skimage/Pillow for everything except the DWT.

## 2. Component benchmark (measured)

Setup: 3.13.16-based, NumPy 2.5.3, SciPy 1.18.1, scikit-image 0.26.0, OpenCV 5.0.0, Pillow 12.3.0, PyWavelets (module 1.8.0; distribution metadata 1.10.0), Version: ImageMagick 6.9.12-98 Q16 x86_64 18038 https://legacy.imagemagick.org, ffmpeg version 6.1.1-3ubuntu5; 4-core Intel Xeon @ 2.1 GHz; **one thread** (BLAS/OpenCV threads fixed to 1), in-memory, file I/O excluded, 2 warm-up calls + 9 timed repeats, median of 3 randomly chosen real test images (seed 20260713: image_021, image_020, image_055); input 512×512 (256×256 LL for DCT/SVD).
† = includes process start-up and file I/O (ImageMagick is a command-line tool) – not comparable with the in-memory rows.
"Speed vs project" > 1 means faster than the implementation the project uses.

| Operation | Implementation | Median ms (IQR) | Speed vs project | Agreement with project's output |
|---|---|---|---|---|
| 2-D DCT-II 256x256 | scipy.fftpack.dct (project) | 0.430 (0.401–0.445) | 1.00 (reference) | max rel. diff 0.0e+00 |
| 2-D DCT-II 256x256 | scipy.fft.dctn | 0.437 (0.432–0.450) | 0.98× | max rel. diff 2.7e-16 |
| 2-D DCT-II 256x256 | cv2.dct | 0.651 (0.630–0.663) | 0.66× | max rel. diff 8.5e-16 |
| 2-D DCT-II 256x256 | NumPy matrix C.A.C^T | 1.276 (1.206–1.515) | 0.34× | max rel. diff 4.6e-15 |
| SVD 256x256 | numpy.linalg.svd (project) | 11.634 (11.534–11.701) | 1.00 (reference) | max rel. diff 0.0e+00 |
| SVD 256x256 | scipy.linalg.svd (gesdd) | 9.769 (9.667–9.827) | 1.19× | max rel. diff 1.5e-18 |
| SVD 256x256 | scipy.linalg.svd (gesvd) | 62.947 (62.674–63.392) | 0.18× | max rel. diff 1.5e-16 |
| SVD 256x256 | cv2.SVDecomp | 15.299 (15.250–15.548) | 0.76× | max rel. diff 1.5e-16 |
| Haar DWT level-1 (LL) 512x512 | PyWavelets dwt2 (project) | 3.655 (3.553–3.711) | 1.00 (reference) | max abs diff 0.0e+00 |
| Haar DWT level-1 (LL) 512x512 | NumPy slicing | 0.327 (0.324–0.367) | 11.19× | max abs diff 1.1e-13 |
| JPEG round-trip Q=50, 512x512 | Pillow (project) | 1.245 (1.201–1.277) | 1.00 (reference) | identical |
| JPEG round-trip Q=50, 512x512 | OpenCV imencode/imdecode | 0.974 (0.959–1.007) | 1.28× | identical |
| JPEG round-trip Q=50, 512x512 | ImageMagick convert (process + file I/O) † | 48.641 (46.208–51.257) | 0.03× | PSNR 48.8 dB |
| Median filter 3x3 | scipy.ndimage (project) | 20.883 (20.567–21.663) | 1.00 (reference) | identical |
| Median filter 3x3 | cv2.medianBlur (uint8) | 0.062 (0.061–0.064) | 339.16× | identical |
| Median filter 3x3 | skimage.filters.median (uint8) | 27.018 (24.217–27.369) | 0.77× | identical |
| Gaussian blur sigma=1.5 | scipy.ndimage (project) | 4.531 (4.471–4.945) | 1.00 (reference) | identical |
| Gaussian blur sigma=1.5 | cv2.GaussianBlur | 1.041 (0.981–1.120) | 4.35× | PSNR 320.0 dB |
| Gaussian blur sigma=1.5 | skimage.filters.gaussian | 4.609 (4.575–4.877) | 0.98× | PSNR 78.8 dB |
| Rotation 15 deg (bilinear) | skimage.transform.rotate (project) | 6.126 (6.059–6.267) | 1.00 (reference) | PSNR 168.1 dB (interior) |
| Rotation 15 deg (bilinear) | cv2.warpAffine | 1.208 (1.164–1.271) | 5.07× | PSNR 64.2 dB (interior) |
| Rotation 15 deg (bilinear) | Pillow Image.rotate | 3.196 (3.087–3.243) | 1.92× | PSNR 53.4 dB (interior) |
| Down/up-scale 0.5x | skimage.transform.resize (project) | 11.060 (10.727–12.105) | 1.00 (reference) | identical |
| Down/up-scale 0.5x | cv2.resize (AREA down, LINEAR up) | 0.291 (0.286–0.302) | 37.97× | PSNR 52.4 dB |
| Down/up-scale 0.5x | Pillow resize (BILINEAR) | 1.784 (1.762–1.849) | 6.20× | PSNR 48.6 dB |
| Histogram equalisation | skimage.exposure.equalize_hist (project) | 7.863 (7.791–8.134) | 1.00 (reference) | identical |
| Histogram equalisation | cv2.equalizeHist (uint8) | 0.417 (0.403–0.421) | 18.87× | PSNR 53.3 dB |
| PSNR 512x512 | skimage.metrics (project) | 0.717 (0.700–0.726) | 1.00 (reference) | 48.1308 vs 48.1308 |
| PSNR 512x512 | cv2.PSNR | 0.302 (0.300–0.319) | 2.38× | 48.1308 vs 48.1308 |
| PSNR 512x512 | NumPy formula | 0.674 (0.670–0.706) | 1.06× | 48.1308 vs 48.1308 |

**Observations (measured, not extrapolated)**
* The numerical results of equivalent implementations agree: DCT/SVD to ≤ 1.5e-16 relative, Haar DWT to 1e-13, Pillow and OpenCV JPEG bit-identical, 3×3 median identical, Gaussian blur between 78.8 dB and 320 dB PSNR (border handling).
  Rotation, scaling and histogram equalisation are *different algorithms* behind the same name (interpolation, area averaging, discrete vs continuous CDF), so they agree only to 48–64 dB PSNR.
* The project's embedding is dominated by two SVDs (≈ 23 of ≈ 37 ms). `scipy.linalg.svd` (gesdd) was 1.19× faster than `numpy.linalg.svd`; `gesvd` was 5.4× *slower*; `cv2.SVDecomp` 0.76×. DCT: SciPy's two APIs are equal; `cv2.dct` 0.66×.
* OpenCV is much faster for 3×3 median (≈ 340×, SIMD on `uint8` versus SciPy's generic float64 filter), Gaussian blur (4.4×), rotation (5.1×), rescaling (38×) and equalisation (19×). These affect only the *attack simulator*, not the watermark algorithm, and total experiment run time was about 80 s (78–85 s over runs) for 100 images × 2 protocols × 15 conditions plus sweeps and controls — so speed was not a limiting factor and no change of library is justified on performance grounds. Caveat: some of these speed-ups partly reflect `uint8` versus `float64` input, not only library quality.
* PyWavelets' `dwt2` took 3.7 ms for a Haar level-1 LL band while four lines of NumPy slicing took 0.33 ms (11×); PyWavelets is nevertheless the right choice for generality (other wavelets, more levels, validated boundary modes).
* ImageMagick via the command line cost ≈ 49 ms per JPEG round-trip, dominated by process start-up and disk I/O; it is a poor fit for in-loop experiments but a good fit for batch conversion.

## 3. Scheme benchmark (measured)

Setup: the same 64×64 logo payload, **4095 bits** (the last bit is dropped because `blind-watermark` requires strictly fewer bits than its 4096 blocks); 30 real images chosen at random (seed 20260713); 9 attacks; 8-bit rounding before attack; BER of the recovered logo averaged over images.
The 8×8 block-DCT baseline's strength (Δ = 48) was tuned on 5 other images so that its PSNR matches the project's (35.4 vs 35.6 dB) – equal imperceptibility, then compare robustness.
`blind-watermark` embeds in the YUV channels of a 3-channel image; we fed it the grey image replicated to three channels, attacked each channel independently with the same grey-scale attack, and measured PSNR on luminance. JPEG was therefore applied per channel (no chroma sub-sampling), which may favour that library.
The project's extraction uses its key (non-blind); the three other schemes are blind.

| Attack | Project (global DWT-DCT-SVD) | blind-watermark 0.4.4 | Baseline: 8x8 block DCT | Baseline: spatial LSB |
|---|---|---|---|---|
| No Attack | 0.010 | 0.004 | 0.000 | 0.000 |
| JPEG Q=50 | 0.010 | 0.004 | 0.296 | 0.426 |
| JPEG Q=20 | 0.010 | 0.074 | 0.469 | 0.531 |
| Gaussian Noise (var=0.02) | 0.038 | 0.005 | 0.182 | 0.500 |
| Median Filter 3x3 | 0.004 | 0.004 | 0.047 | 0.081 |
| Gaussian Blur (sigma=1.5) | 0.022 | 0.004 | 0.106 | 0.456 |
| Rotation 5 deg | 0.029 | 0.214 | 0.493 | 0.504 |
| Cropping 25% | 0.135 | 0.060 | 0.124 | 0.128 |
| Scaling 0.5x | 0.015 | 0.004 | 0.483 | 0.455 |
| **PSNR (dB)** | 35.9 | 42.4 | 35.1 | 69.5 |
| **embed ms / image** | 32 | 420 | 26 | 2 |
| **extract ms / image** | 17 | 315 | 12 | 1 |

(Lower BER is better; 0.5 = random guessing. The project's own clean-image BER of ≈ 0.01 arises from the 64→256→64 logo resampling, not from an attack.)

**Observations**
* The **LSB** baseline is imperceptible (69.5 dB) and fragile: chance-level BER under JPEG, noise and rescaling.
* The **8×8 block-DCT** baseline, matched in PSNR, is poor under JPEG (0.30–0.47) and geometric attacks (≈ 0.48–0.49).
* **`blind-watermark`** is *better than the project* under JPEG Q=50, noise, blur, rescaling and cropping, at a *higher* PSNR (42.4 dB); but it is **13× slower to embed** (420 vs 32 ms) and **18× slower to extract** (315 vs 17.5 ms), **worse under rotation** (BER 0.214 vs 0.029) and **under JPEG Q=20** (0.074 vs 0.010), and it is a different design (blind, block-based, two integer passwords instead of a 2.1 MB key; clean-image BER 0.004 vs the project's 0.010).
* The project therefore sits **between** the classical baselines and a mature block-based blind hybrid: it is clearly more robust than LSB/block-DCT at equal PSNR, but it is **not superior to existing technology** — it is a simple, explainable, key-based alternative with a different robustness profile and a measured false-positive weakness.
* Not measured: `invisible-watermark`, learned watermarkers, commercial tools, GPU variants (no GPU in the environment).

## 4. Strengths and weaknesses

| Technology | Strengths (evidence) | Weaknesses (evidence) |
|---|---|---|
| Project scheme | closed-form and explainable; 32–37 ms embed / 18–20 ms extract per 512² image (scheme benchmark vs 4-worker experiment); survives JPEG Q ≥ 20, median, blur, 0.5× scaling (≥ 96 % of 100 images); better under rotation than block-based schemes | non-blind (2.1 MB key per image); false-positive problem (wrong logo → NC 0.975); cropping 1 % pass; hist-eq 44 %; 0.9 % BER even without attack |
| `blind-watermark` | lowest BER in most attacks; blind; 42 dB PSNR | slow (0.42 s embed), rotation-fragile (0.214), 4096-bit capacity ceiling for 512² host (observed), YUV/colour design |
| Block-DCT baseline | blind, fast (26 ms) | fails under JPEG/geometry at project-level PSNR |
| LSB baseline | 70 dB PSNR, 1.7 ms | useless under any lossy processing |
| OpenCV | fastest filters/geometry (up to 340×); video I/O | no DWT; SSIM only in contrib; heavier dependency |
| Pillow | simple JPEG/PNG I/O, bit-identical JPEG to OpenCV | no transforms for watermarking |
| scikit-image | clear API, metrics, `equalize_hist`, `rotate` | slower than OpenCV for the same task |
| SciPy/NumPy | accurate DCT/SVD, SciPy gesdd 1.19× NumPy | none relevant |
| PyWavelets | general DWT | 11× slower than 4 lines of NumPy for Haar level 1 |
| ImageMagick | many formats, scriptable | 49 ms/call through a process; no transforms needed here |
| FFmpeg | the reference for codecs; used for the video test | per-frame algorithms must be piped in/out |

## 5. What the current project contributes

1. A **compact, fully documented, reproducible reference implementation** of DWT–DCT–SVD singular-value watermarking (≈ 150 lines), whose every step can be verified by hand — an *educational* contribution.
2. A **100-image, category-stratified, seeded evaluation** with controls for false positives and a metric-reliability analysis; published evaluations of such hybrids usually use few images (see `research/LITERATURE_REVIEW.md` §7).
3. Evidence about where the approach works (compression, filtering, scaling, mild noise) and where it does not (cropping, rotation > 5°, equalisation, false-positive resistance).

## 6. Technical justification for the selected implementation

* **PyWavelets + SciPy + NumPy + Pillow + scikit-image** cover every operation with correct, mutually-agreeing numerics (§2).
* Library choice is not performance-critical (whole experiment: about 80 s on 4 cores).
* Pillow is retained for the JPEG attack because its output matched OpenCV's bit-for-bit and it is a lightweight dependency.

## 7. Recommendations

1. **Swap implementation, not algorithm, if speed ever matters:** `scipy.linalg.svd` for the SVDs (1.19×) and a NumPy Haar for level-1 (11×); OpenCV for attack simulation.
2. **Algorithmic improvements justified by the benchmark:** block-based redundant embedding (cropping), an image-bound signature (false positives), and a comparison against the `blind-watermark` design as the new baseline.
3. **Report NC together with ZNCC and BER, and calibrate thresholds on controls.**
4. **If colour/video are required:** embed in luminance per frame with a keyed, index-aware scheme; do not rely on the 60-frame per-frame demo as evidence for temporal robustness.
