# TRANSFORMATIONS REFERENCE

Only operations that exist in the project's code are listed (verified by reading `source_code/src/*.py`).
Generic examples from the task brief (Sobel/Canny, CLAHE, morphology, affine/perspective warps, colour-space
conversions other than RGB→grey, etc.) are **not implemented** in this project and are therefore not documented as if they were.
Notation: image `f(x,y)`, 8-bit range [0,255]; `N` = number of pixels; the host is 512×512 so N = 262 144, and its LL sub-band is 256×256.
Reference numbers `[n]` refer to `research/REFERENCES.md`.

## Summary table

| # | Transformation | Role in project | Function (file) | Library |
|---|---|---|---|---|
| T1 | Greyscale conversion, centre-crop, Lanczos resize | dataset standardisation | `load_gray_square` (`image_io.py`) | Pillow |
| T2 | 1-level 2-D Haar DWT / inverse | embedding domain | `embed_watermark`, `extract_watermark` (`watermark_core.py`) | PyWavelets |
| T3 | 2-D DCT-II / inverse | embedding domain | `dct2`, `idct2` | SciPy `fftpack` |
| T4 | SVD of host sub-band and of the logo | embedding domain | `embed_watermark` | NumPy |
| T5 | Singular-value embedding `S' = S + α·Sw` and extraction | the watermarking rule | `embed_watermark`, `extract_watermark` | NumPy |
| T6 | Anti-aliased resize of logo / sub-band | shape matching | inside T5 | scikit-image |
| T7 | Procedural binary logo | watermark payload | `make_watermark_logo` (`logo.py`) | Pillow, NumPy |
| T8 | JPEG compression (attack) | attack | `jpeg_compression` | Pillow |
| T9 | Additive Gaussian noise (attack) | attack | `gaussian_noise` | scikit-image |
| T10 | Salt-and-pepper noise (attack) | attack | `salt_pepper_noise` | scikit-image |
| T11 | 3×3 median filter (attack) | attack | `median_filter` | SciPy `ndimage` |
| T12 | Gaussian blur (attack) | attack | `gaussian_blur` | SciPy `ndimage` |
| T13 | Rotation (attack) | attack | `rotation_attack` | scikit-image |
| T14 | Border cropping/zeroing (attack) | attack | `cropping_attack` | NumPy |
| T15 | Down- then up-scaling (attack) | attack | `scaling_attack` | scikit-image |
| T16 | Histogram equalisation (attack) | attack | `histogram_equalization` | scikit-image |
| T17 | Unsharp-mask sharpening (attack) | attack | `sharpening_attack` | SciPy |
| T18 | Quality metrics PSNR, SSIM, MSE | evaluation | `metrics.py` | scikit-image |
| T19 | Robustness metrics NC, ZNCC (new), BER | evaluation | `metrics.py` | NumPy |
| T20 | Frame extraction, per-frame embedding, video encode/decode (exploratory, new) | video test | `video_demo.py` | OpenCV, FFmpeg |

Pipeline order matters: `T1 → T2 → T3 → T4 → T5 (embed) → 8-bit quantisation → attack (T8–T17) → T2 → T3 → T4 → T5 (extract)`.
DCT must follow DWT (the DCT is applied to LL, not to the pixels) and the SVD must follow the DCT (it factorises the DCT coefficient matrix);
swapping any two stages changes the embedding domain and invalidates the key.
Rounding to 8 bit **before** attacking is what a saved image experiences; the original code attacked the float image (both are reported).

---

## T1 — Standardisation (grey, crop, resize)
* **Purpose** one comparable 512×512 8-bit host for every source file. **Maths** grey: `L = 0.299R + 0.587G + 0.114B` (ITU-R BT.601, Pillow's `convert("L")`); alpha is composited over white; 16-bit data is rescaled linearly `255·(f−min)/(max−min)`; crop to the largest centred square; Lanczos-3 resampling `f'(x)=Σ f(i)·L(x−i)` with `L(t)=sinc(t)sinc(t/3)`, |t|<3.
* **Parameters** `size=512`. **Output** `uint8`→`float64` array. **Advantages** no aspect distortion, deterministic. **Limits** crop discards image borders; colour information is lost (the scheme is grey-only); Lanczos can ring at sharp edges.
* **Complexity** O(N). **Use** pre-processing for any single-channel algorithm. **Evaluated** by unit tests (`tests/test_image_io.py`) and the per-image validation in `metadata.csv`. **Refs** Pillow documentation [24].

## T2 — Haar DWT (1 level, 2-D)
* **Purpose** split the image into an approximation LL (energy-rich, robust) and details LH/HL/HH. **Maths** with the Haar filters `h=(1,1)/√2`, `g=(1,−1)/√2` applied separably to rows and columns and sub-sampled by 2: for each 2×2 block `(a,b;c,d)`, `LL = (a+b+c+d)/2`; the three detail bands are the sums/differences `(a−b+c−d)/2`, `(a+b−c−d)/2`, `(a−b−c+d)/2` up to PyWavelets' sign/naming convention (the LL formula was verified against a NumPy slicing implementation to 1e-13, `tech_benchmark_components.csv`). The inverse reconstructs perfectly.
* **Parameters** wavelet `"haar"`, sub-band `"LL"`. **Advantages** orthonormal, perfect reconstruction, cheapest wavelet. **Limits** blocky basis, not shift-invariant, poor frequency localisation compared with longer wavelets; the LL band of a 512×512 image is 256×256, so the SVD in T4 is large. **Complexity** O(N). **Use** compression (JPEG 2000 uses DWT), denoising, watermarking. **Evaluated** perfect-reconstruction check inside tests (`test_clean_roundtrip_recovers_logo`) and timing (3.7 ms with PyWavelets, 0.33 ms with plain NumPy). **Refs** [12] Mallat, [18] PyWavelets.

## T3 — 2-D DCT-II (global, orthonormal)
* **Purpose** move LL to a frequency domain aligned with JPEG's. **Maths** `F(u,v)=α(u)α(v)ΣΣ f(x,y)cos[(2x+1)uπ/2M]cos[(2y+1)vπ/2N]`, `α(0)=√(1/M)`, `α(u>0)=√(2/M)`; implemented as two 1-D `scipy.fftpack.dct(norm="ortho")` passes. It is applied to the **whole 256×256 sub-band, not to 8×8 blocks** (the earlier "block DCT" wording was wrong).
* **Advantages** orthonormal (energy preserving), fast. **Limits** a global DCT is not aligned with JPEG's 8×8 blocks, so the "JPEG-aligned robustness" argument of the original report does not strictly apply; the measured JPEG robustness (NC ≥ 0.75 in 100 % of Q=50 trials) comes from the SVD stage, not from DCT alignment. **Complexity** O(N log N). **Use** compression, spectral analysis. **Evaluated** round-trip test; agreement with `scipy.fft.dctn`, `cv2.dct` and a matrix implementation to ≤ 9e-16 relative. **Refs** [13] Ahmed et al., [14] Wallace.

## T4 — Singular value decomposition
* **Purpose** factor the DCT matrix `A = U·diag(S)·Vᵀ`; singular values change little under small perturbations, which makes them a stable carrier. Same for the logo `Wm = Uw·diag(Sw)·Vwᵀ`.
* **Implementation** `np.linalg.svd(…, full_matrices=False)` (LAPACK gesdd). **Advantages** optimal low-rank structure, stability (Weyl: `|σᵢ(A+E)−σᵢ(A)| ≤ ‖E‖₂`). **Limits** O(n³): 11.6 ms for a 256×256 matrix; the two SVDs of the embedding (host sub-band and logo) take ≈ 23 of the ≈ 37 ms; the singular *vectors* are not stable under geometric change. **Complexity** O(n³). **Evaluated** agreement with SciPy/OpenCV (≤ 1.5e-16 relative), timing in `tech_benchmark_components.csv`. **Refs** [15] Golub & Van Loan.

## T5 — Embedding and extraction rule
* **Embedding** `S' = S + α·Sw`; `A' = U·diag(S')·Vᵀ`; inverse DCT → inverse DWT → clip. `α = 0.10` (config). Added energy: `α·‖Sw‖₂`. **Extraction** `Sw' = (S_att − S_orig)/α`, `W' = Uw·diag(Sw')·Vwᵀ`, then resize to 64×64 and clip.
* **Parameters** `alpha` (> 0), `wavelet`, `subband`. Effect of α (measured, 100 images): PSNR 49.1 dB (α=0.02) → 36.0 dB (0.10) → 24.2 dB (0.40); robustness grows with α for noise/blur/rotation but not for JPEG (`alpha_sweep_summary.csv`).
* **Advantages** closed form, one tunable parameter, survives JPEG, filtering, scaling. **Limits** non-blind; false-positive problem (identity in the key; NC 0.975 for a wrong logo); fragile to cropping (NC 0.02) and histogram equalisation (pass rate 44 %); clean extraction is not lossless (BER ≈ 0.9 %) because the logo is resampled 64→256→64. **Complexity** dominated by two SVDs (≈ 37 ms embed, ≈ 20 ms extract single-threaded). **Use** ownership/copyright watermarking [2][3]. **Refs** [2] Liu & Tan, [3] Ganic & Eskicioglu, [4][5] false-positive critiques.

## T6 — Anti-aliased resize (logo ↔ sub-band)
`skimage.transform.resize(anti_aliasing=True, preserve_range=True)`: Gaussian pre-smoothing (σ = (scale−1)/2) followed by bilinear interpolation when shrinking. Needed because the watermark must have the host sub-band's shape. **Limit** the round trip is lossy (source of the 0.9 % clean BER).

## T7 — Procedural logo
A 256×64 black canvas, 3-px white frame, text "CYBERION" in Pillow's default bitmap font, resized to 64×64 and thresholded at 100 → binary {0,255}; 12.9 % of pixels are white. No external asset. **Limit** the text is only a few pixels high after down-sizing, so the logo is largely a frame; this is a weak identity carrier and a reason NC is dominated by the first singular value (σ₁ holds 74.7 % of its energy; a blank white image already scores NC = 0.359, a rank-1 approximation 0.868).

## T8 — JPEG compression (attack)
* **Maths** 8×8 block DCT, quantisation `Q_q` scaled by quality, entropy coding [14]. Used at quality 90/50/20 via Pillow (baseline, 4:4:4 for grey). **Change** floats are now rounded before encoding (originally truncated). **Limits** results depend on the libjpeg version (Pillow vs OpenCV outputs were bit-identical here; ImageMagick differed by 48.8 dB PSNR). **Complexity** O(N). **Evaluated** NC/BER after attack; the scheme passes 100 % (Q 90, 50) and 97 % (Q 20) of the 100 images.

## T9/T10 — Gaussian and salt-and-pepper noise
Gaussian: `g = f + n`, `n ~ N(0, σ²)`, σ² = 0.005 and 0.02 on the [0,1] scale (σ ≈ 18 and 36 grey levels), clipped. Salt-and-pepper: 2 % of pixels set to 0 or 255 with equal probability. **Seeded** (new). Robustness decreases with image contrast (Spearman ρ = −0.65 vs contrast for σ²=0.02; ρ = −0.68 for s&p).

## T11/T12/T17 — Median, Gaussian blur, unsharp mask
Median 3×3: `g(x)=median{f(x+k)}`, non-linear, removes impulses, preserves edges. Gaussian blur: `g = f * G_σ`, σ=1.5 (separable, kernel radius 4σ). Sharpening: `g = f + a(f − G_1*f)`, a=1. All O(N·k). Pass rates 100 %, 96 %, 99 %.

## T13 — Rotation
`skimage.transform.rotate` bilinear, about the image centre, size kept, edge replication; 5° and 15°. Geometric: the DCT/SVD structure is not rotation-invariant and no re-registration is attempted. Pass rates 92 % and 72 %.

## T14 — Border cropping/zeroing
A frame of `frac/2` of each dimension is set to 0 (64 px each side for frac = 0.25): 43.75 % of the area is removed, geometry kept. Pass rate 1 % (mean NC 0.022): all singular values change.

## T15 — Down/up scaling (0.5×)
Bilinear/anti-aliased reduction to 256×256 and enlargement back. Pass rate 98 %.

## T16 — Histogram equalisation
`skimage.exposure.equalize_hist` — maps intensities through the empirical CDF. Strong, global, non-linear. Pass rate 44 % (mean NC 0.644); the ρ with mean brightness is −0.31 (p = 0.002), with contrast 0.06 (n.s.).

## T18/T19 — Metrics
* `MSE = (1/N)Σ(x−y)²`; `PSNR = 10·log₁₀(255²/MSE)` (capped at 100 dB for identical images). Mean PSNR 35.99 dB (35.92 real images only).
* `SSIM` = mean of local `(2μxμy+c₁)(2σxy+c₂)/((μx²+μy²+c₁)(σx²+σy²+c₂))` over 7×7 windows [16]; mean 0.992; three images < 0.98 (the near-black `image_055` reaches only 0.58).
* `NC = ΣW·W'/(‖W‖‖W'‖)`; `ZNCC` = NC after subtracting each image's mean (new, because plain NC rewards any bright image); `BER` = mismatching fraction after thresholding at 127.5.
* **Caveat** a higher value is not always "better": PSNR/SSIM compare against the *unwatermarked original* (appropriate), but NC/BER are conditional on the key (see T5).

## T20 — Video (exploratory)
`cv2.VideoCapture` frame reading → T1 per frame → T2–T5 per frame with its own key → FFmpeg encode (FFV1 lossless, H.264 CRF 18/23/28, MJPEG q 5/15) → decode → extract. 60 frames × 2 clips × 6 settings: NC ≥ 0.972 in all 720 frames. This tests feasibility only (no temporal attacks, no colour, no frame-rate change).
