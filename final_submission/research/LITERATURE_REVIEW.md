# LITERATURE REVIEW

Scope: the techniques *actually implemented* by the project — a 1-level Haar DWT, a global DCT, SVD, additive
singular-value embedding of a logo, JPEG/noise/filter/geometric attacks, and PSNR/SSIM/NC/BER evaluation — plus
the neighbouring work needed to place the results (hybrid schemes, the false-positive problem, geometric attacks, video, learned watermarking).

**Provenance rule.** The original report cites Cox et al. [1], Liu & Tan [2], Ganic & Eskicioglu [3], Gonzalez & Woods [31] and library documentation.
It does not say that any code was derived from them. This review therefore describes them as *foundational literature identified during this review*,
not as the code's source. Papers were located by web search on 2026-10-13; their bibliographic details were checked as recorded in `REFERENCES.md`
(status V1/V2/V3). Where I could read only an abstract or a secondary description, the text below says so and no result is attributed beyond it.

## 1. Development of the techniques

**Spatial-domain beginnings.** Early digital watermarks modified pixel values directly, typically least-significant bits; van Schyndel, Tirkel and Osborne's "A digital watermark" [10]
is the usual starting reference. LSB embedding has very high capacity and negligible distortion but no robustness: in our own baseline (`benchmark_tech.py`) an LSB payload of 4095 bits reaches a PSNR of 69.5 dB
yet suffers bit-error rates of 0.43 (JPEG Q=50) and 0.50 (Gaussian noise σ²=0.02) — i.e. chance level — which is why the original report is right to move to transform domains.

**Spread-spectrum in a transform domain.** Cox, Kilian, Leighton and Shamoon [1] argued that a watermark must live in the *perceptually significant* spectral components if it is to survive processing:
a Gaussian pseudo-random sequence is added to the largest DCT coefficients and detected by correlation (abstract-level description verified on IEEE Xplore). This established the imperceptibility–robustness trade-off that the project studies through α.
Block-DCT variants that hide bits in relations between mid-frequency coefficients, such as Koch and Zhao [11], tune the embedding to the JPEG model; our own simplified block-DCT baseline in the spirit of [11] (not a re-implementation) when tuned to the project's PSNR (35.1 vs 35.9 dB) reaches chance-level BER (0.48–0.49) under 5° rotation and 0.5× scaling and 0.30 under JPEG Q=50, while tolerating a 3×3 median filter (BER 0.047).
General surveys of the field are Hartung and Kutter [17] and the textbook of Cox et al. [32].

**Wavelets.** Mallat's multiresolution theory [12] gives the DWT used in T2; watermarking in the approximation (LL) band trades visibility for robustness, in the detail bands the reverse.
The project's choice of LL with the Haar wavelet is the simplest instance of that idea.

**Singular value decomposition.** SVD-based watermarking was introduced by Liu and Tan [2], who modify the host's singular values and derive the key from the SVD of the modified matrix, claiming good resistance to common attacks (title-level and citing-paper description).
Ganic and Eskicioglu [3] combined DWT and SVD and embedded in all sub-bands ("embedding data in all frequencies"); a later comparison table describes it as a non-blind, grey-scale, hybrid DWT-SVD scheme.
Sverdlov, Dexter and Eskicioglu [6] did the same for the DCT. Lai and Tsai [7] proposed a DWT-SVD scheme in IEEE Trans. Instrum. Meas. (abstract not re-read in this session).

**Hybrid DWT-DCT-SVD.** Cascading all three transforms is common in the later literature: Bekkouch and Faraoun [8] describe a reversible, robust scheme using combined DCT-DWT-SVD transforms with two watermarks;
Begum, Ferdush and Uddin [9] describe a blind variant in which the watermark is Arnold-map scrambled and DCT is applied to the watermark and host before a DWT and SVD, reporting better robustness and imperceptibility than prior methods (as stated in the abstract/listing; not re-evaluated here).
The project's claim that hybrids "repeatedly outperform any single transform" is therefore *supported as a trend reported by authors of hybrid schemes*, not independently tested by us; in our own experiments the project's global scheme beat two simpler baselines but was itself beaten by a block-based blind hybrid library (§4).

## 2. The false-positive problem

Zhang and Li [4] published a comment on Liu and Tan [2] and Ting [5] studied *ambiguity attacks* on Ganic and Eskicioglu's DWT-SVD scheme [3]. Later literature (found only through search snippets and reference lists, not re-read) describes the common cause:
when the watermark's singular values are embedded and its singular vectors are stored as the key, the detector reconstructs the key owner's watermark irrespective of what was embedded, so an attacker can claim any logo ("false positive").
**Our experiment E4 measures exactly this** on 100 images: embedding logo B and decoding with the key of logo A gives NC(A) = 0.975 versus 0.977 for the genuine pair — a difference of 0.002 in mean NC (the two distributions overlap almost completely; Mann–Whitney AUC 0.78, where 0.5 = indistinguishable).
The literature therefore *predicts* the behaviour; the experiment *confirms* it for this implementation. Remedies proposed in the literature (embedding the whole principal component rather than singular values only, or adding independent signature checks) were not implemented; a quick test of embedding the principal-component matrix in this framework (`exp_principal_component_variant.py`, output in `results/exp_principal_component_variant.txt`) made the problem **worse** (an unwatermarked image still decoded at NC = 0.98 because the key then contains the whole logo), so it is not recommended without redesign.

## 3. Geometric attacks, blind detection and video

Pure global-SVD embedding is not geometrically invariant. Lin et al. [22] show that the problem is structural: rotation, scale and translation (RST) break correlation detectors unless the embedding/detection domain is made invariant (they use a log-polar Fourier transform and a one-dimensional signal); they also test false positives on 10 000 images.
This matches our measurements: rotation by 15° passes in 72 % of images and border cropping in 1 %.
For video, Hartung and Girod [23] address watermarking of uncompressed and compressed video; our exploratory test (per-frame embedding, 60 frames × 2 clips, H.264/MJPEG) shows that codec re-encoding is not the difficulty for this scheme (NC ≥ 0.972 for every frame) — bookkeeping of per-frame keys and temporal attacks would be.

## 4. Classical versus learned approaches

HiDDeN [29] learns an encoder/decoder pair with differentiable distortion layers; StegaStamp [30] learns watermarks that survive print-and-photograph transmission. Learned methods optimise robustness to a *training-time attack distribution* and can carry bits blindly; the project deliberately excludes machine learning for explainability, which is a legitimate scope choice, not a claim of superiority.
The relevant trade-offs for this project: classical schemes are transparent, cheap (≈ 37 ms embed on one CPU core) and need no training data, but are brittle to geometry and do not fix the false-positive problem by themselves.

## 5. Mathematical foundations (what each equation rests on)

| Component | Foundation | Reference |
|---|---|---|
| DWT / multiresolution | Mallat's wavelet representation | [12] |
| DCT | Ahmed, Natarajan & Rao; JPEG standard | [13], [14] |
| SVD, singular-value perturbation (Weyl) | Golub & Van Loan | [15] |
| Imperceptibility metrics | MSE/PSNR; SSIM | [16] |
| Spread-spectrum detection & trade-off | Cox et al. | [1] |

## 6. Paper-to-implementation mapping

| Reference | Technique | Project function / experiment | Relationship |
|---|---|---|---|
| [1] Cox et al. 1997 | embedding in perceptually significant coefficients; α trade-off | `embed_watermark` (α), E3 alpha sweep | conceptual foundation |
| [2] Liu & Tan 2002 | embedding in singular values | `embed_watermark` step 5 | closest ancestor; the project adds the logo's singular values rather than the logo matrix |
| [3] Ganic & Eskicioglu 2004 | DWT-SVD hybrid | `embed_watermark` (DWT + SVD) | conceptual foundation |
| [4], [5] | false-positive/ambiguity critique | `run_batch_experiment.py` E4 | motivates the controls |
| [7], [8], [9] | DWT(-DCT)-SVD hybrids | whole pipeline | related work |
| [10], [11] | LSB, block-DCT | `LSBScheme`, `BlockDCTScheme` in `benchmark_tech.py` | baselines |
| [12] Mallat | DWT | `pywt.dwt2` call | theory |
| [13], [14] | DCT, JPEG | `dct2`, `jpeg_compression` | theory / attack |
| [16] Wang et al. | SSIM | `metrics.ssim` | metric |
| [22] Lin et al. | RST-resilient detection | rotation/cropping/scaling attacks | explains the observed geometric fragility |
| [23] Hartung & Girod | video watermarking | `video_demo.py` | related work |
| [28] `blind-watermark` | block DWT-DCT-SVD, blind | `BlindWMScheme` | comparison |
| [29], [30] | learned watermarking | — (context only) | not implemented |

## 7. Research gaps and implementation trade-offs relevant to this project

1. **Identity binding.** The scheme does not bind the logo to the image (F1/E4). Literature remedies exist [4][5] but were not validated here.
2. **Geometry.** Global SVD is geometry-fragile; block-based or invariant-domain embedding [22] is the standard answer. Our benchmark shows a block-based blind hybrid [28] already keeps BER at 0.06 under the same border-zeroing attack (project: 0.135) but is *worse* under 5° rotation (0.214 vs 0.029) — block grids break under rotation too.
3. **Metric reliability.** NC is dominated by the logo's first singular value (a blank white image scores 0.359; a rank-1 approximation 0.868). ZNCC and BER should be reported alongside NC; thresholds (0.75) should be calibrated against controls (our wrong-image 95th percentile is NC 0.82, so 0.75 corresponds to ≈ 10–13 % false positives against unrelated images).
4. **Imperceptibility metrics.** PSNR is almost host-independent here (determined by `α·Sw`); SSIM collapses on near-constant images (0.58 on a near-black sky). Both need image-class-aware interpretation.
5. **Evaluation breadth.** Most published hybrid schemes (as listed in [7]–[9]) are evaluated on a handful of standard images; a 100-image, category-stratified evaluation is a contribution of this submission.

## 8. Which improvements are justified by the evidence

* **Justified and implemented:** seeding of stochastic attacks; rounding to 8 bit before attack; ZNCC alongside NC; control experiments; wider α sweep with harsher attacks; larger dataset.
* **Justified by measurements but *not* implemented (future work):** block-based redundant embedding with per-block keys (cropping failure, F1/F2); a signature check bound to the image (false positives); histogram-equalisation compensation by a pre-extraction normalisation step (hist-eq pass rate is 44 %).
* **Not justified by the evidence collected:** moving to deep-learning watermarking — no experiment here compares against it.
