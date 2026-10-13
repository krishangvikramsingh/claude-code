"""
build_report.py
===============
Builds report/Final_Project_Report.docx from the recorded results (results/*.csv|json)
and the generated figures (visualizations/*.png).  Two passes: the first collects the
heading/figure/table registry, the second writes the front matter with page numbers
taken from a PDF render of the previous build.

    python build_report.py          # writes the .docx, converts to PDF with LibreOffice, fills page numbers
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

import pandas as pd

from docx_helpers import Report

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
RES, VIS, TAB = (os.path.join(ROOT, "results"), os.path.join(ROOT, "visualizations"), os.path.join(ROOT, "results", "tables"))
OUT = os.path.join(ROOT, "report")
os.makedirs(OUT, exist_ok=True)
V = lambda n: os.path.join(VIS, n)

AS = json.load(open(os.path.join(RES, "analysis_summary.json")))
RS = json.load(open(os.path.join(RES, "run_summary.json")))
TS = json.load(open(os.path.join(RES, "tech_summary.json")))
VM = json.load(open(os.path.join(RES, "video_demo_meta.json")))
ROB = pd.read_csv(os.path.join(TAB, "robustness_by_attack.csv"))
FAM = pd.read_csv(os.path.join(TAB, "robustness_by_family.csv"))
SWP = pd.read_csv(os.path.join(TAB, "alpha_sweep_summary.csv"))
CTL = pd.read_csv(os.path.join(TAB, "controls_summary.csv"))
COR = pd.read_csv(os.path.join(TAB, "nc_vs_image_statistics.csv"))
CATF = pd.read_csv(os.path.join(TAB, "nc_by_category_family.csv"))
PRO = pd.read_csv(os.path.join(TAB, "protocol_comparison.csv"))
LEG = pd.read_csv(os.path.join(TAB, "legacy_reproduction_cameraman.csv"))
TCOMP = pd.read_csv(os.path.join(RES, "tech_benchmark_components.csv"))
TSCH = pd.read_csv(os.path.join(RES, "tech_benchmark_schemes.csv"))
VID = pd.read_csv(os.path.join(RES, "video_demo_results.csv"))
META = pd.read_csv(os.path.join(ROOT, "data", "metadata.csv"))
IMG = pd.read_csv(os.path.join(RES, "results_images.csv"))
E1, E2, E4 = AS["E1"], AS["E2"], AS["E4"]
BASE = AS["metric_baselines"]
rob = ROB.set_index("attack")
ctl = CTL.set_index("control")


def f3(x): return f"{x:.3f}"
def pc(x, d=0): return f"{100 * x:.{d}f} %"


def genuine(): return CTL.iloc[0]
def ctl_row(prefix): return CTL[CTL.control.str.startswith(prefix)].iloc[0]


G, CA, CB, CC, CCR, CD = (genuine(), ctl_row("a:"), ctl_row("b:"), ctl_row("c: "), ctl_row("c-ref"), ctl_row("d:"))
sw = SWP.set_index(["attack", "alpha"])


def sweep(attack, alpha, col): return float(sw.loc[(attack, alpha), col])


NREAL = int((META.is_synthetic == 0).sum())
NSYN = int((META.is_synthetic == 1).sum())
vsch = TSCH.set_index(["scheme", "attack"])
PROJ, BWM, BDCT, LSB = ("Project: global DWT-DCT-SVD", "blind-watermark 0.4.4 (block DWT-DCT-SVD)",
                        "Baseline: 8x8 block DCT", "Baseline: spatial LSB")


def ber(s, a): return float(vsch.loc[(s, a), "mean_ber"])
def psnr_s(s): return float(TSCH[TSCH.scheme == s].psnr_db.mean())
def tms(s, col): return float(TSCH[TSCH.scheme == s][col].median())


# ===================================================================== CONTENT
def content(r: Report):
    # ------------------------------------------------------------- 1 INTRO
    r.h1("Introduction")
    r.h2("Background and motivation")
    r.para("Digital images and videos are trivially copied, redistributed and repurposed. Photographers, medical institutions, publishers and manufacturers therefore need a way of embedding an invisible, verifiable ownership signature in their visual content without degrading it. Digital watermarking hides auxiliary information directly in the pixel or transform-domain data of the host media [17][32].")
    r.para("Two broad families exist. Spatial-domain methods, such as least-significant-bit (LSB) substitution [10], are simple but fragile. Transform-domain methods (DCT, DWT, SVD and their hybrids) spread the watermark over frequency components and are considerably more robust to compression and everyday signal processing [1][2][3]. This project implements a hybrid DWT–DCT–SVD scheme and evaluates it; the present report extends the first submission (two test images) with a 100-image evaluation, controlled experiments, a comparison with existing technology and a verified literature review.")
    r.h2("Problem statement")
    r.para("Design an invisible digital image watermarking system that (a) introduces minimal, imperceptible distortion, (b) survives common real-world distortions such as compression, noise, filtering and geometric change, and (c) is fully explainable through closed-form linear-algebraic operations, with no learned component — and **establish, with measurements, how far each of these properties actually holds**.")
    r.h2("Objectives")
    r.numbered([
        "Implement a hybrid DWT–DCT–SVD embedding and extraction pipeline from first principles (original objective).",
        "Quantify imperceptibility (PSNR, SSIM) and robustness (NC, BER, and the added ZNCC) under a suite of 14 attacks (plus an unattacked reference) on **100 unique images** (extended objective).",
        "Characterise the imperceptibility–robustness trade-off as a function of the embedding strength α.",
        "Identify and explain failure modes, including whether a high NC really proves that *this* watermark is present (control experiments).",
        "Compare the implementation with established libraries and with an existing open-source watermarking package, using controlled benchmarks.",
        "Test, as an exploratory extension, whether the scheme can be applied frame by frame to real video that is re-encoded with lossy codecs.",
    ])
    r.h2("Scope and boundaries")
    r.bullets([
        "8-bit **grey-scale** images; colour is handled only by converting to luminance (ITU-R BT.601) during dataset preparation.",
        "No machine learning or deep learning at any stage (design constraint of the project); learned watermarking is discussed only as context.",
        "The scheme is **non-blind**: extraction needs a key that contains the original singular values.",
        "Video is an **exploratory** test (60 frames from each of two clips); temporal attacks, colour video and hardware codecs are out of scope.",
        "Only operations present in the project's code are documented as transformations; edge detection, CLAHE, morphology, perspective warps etc. are not part of this project.",
    ])
    r.h2("Applications")
    r.para("Ownership marking of photographs, medical-image provenance, tracing of unauthorised redistribution of publications, and certification of technical imagery. The measurements in Chapter 8 show which of these uses the scheme can support (robust against re-compression and filtering) and which it cannot (geometric cropping; proof of ownership without additional safeguards).")
    r.h2("Expected outcomes and main contributions")
    r.bullets([
        "A reproducible, tested implementation (43 unit/integration tests, seeded experiments, config-driven batch runner).",
        f"A category-stratified evaluation set of {len(META)} unique images ({NREAL} real, {NSYN} clearly labelled synthetic) and 3000 attack trials (+4000 sweep and 1600 control rows) with full status logging.",
        "**A measured false-positive problem:** a different logo decoded with the owner's key still yields NC "
        f"{f3(CC.mean_nc)} (genuine {f3(G.mean_nc)}), so NC alone cannot prove ownership.",
        "Corrections to the first submission (global rather than block DCT, non-blind rather than semi-blind, an α-trade-off figure that exaggerated a 0.05 change, unreproducible noise attacks) — Appendix F.",
        "A controlled comparison with PyWavelets/SciPy/NumPy/OpenCV/Pillow/scikit-image/ImageMagick implementations and with the `blind-watermark` package, showing where the project is and is not competitive.",
    ])

    # ------------------------------------------------------------- 2 LITERATURE
    r.h1("Literature Review")
    r.para("This chapter summarises the literature relevant to the techniques the project actually uses. The first submission cited Cox et al. [1], Liu and Tan [2], Ganic and Eskicioglu [3], Gonzalez and Woods [31] and library documentation; it did not state that code was derived from them, so they are treated here as *foundational literature identified during this review*. Bibliographic details were checked as recorded in the reference list (status flags in `research/REFERENCES.md`).")
    r.h2("Development of the techniques")
    r.para("**Spatial domain.** Van Schyndel, Tirkel and Osborne [10] are the usual starting point for digital image watermarking in the spatial domain. LSB embedding offers high capacity and almost no distortion but no robustness; in our own baseline (Chapter 8) a 4095-bit LSB payload reaches "
           f"{psnr_s(LSB):.1f} dB PSNR yet has a bit-error rate of {ber(LSB, 'JPEG Q=50'):.2f} after JPEG Q=50 and {ber(LSB, 'Gaussian Noise (var=0.02)'):.2f} after Gaussian noise (chance level is 0.5).")
    r.para("**Spread spectrum in a transform domain.** Cox, Kilian, Leighton and Shamoon [1] argued that a watermark must be placed in the perceptually significant spectral components if it is to survive processing; a pseudo-random Gaussian sequence is inserted into the most significant spectral components and detected by correlation. This established the imperceptibility–robustness trade-off studied here through α. Block-DCT methods such as Koch and Zhao [11] tie the embedding to the JPEG model; surveys are given by Hartung and Kutter [17] and Cox *et al.* [32].")
    r.para("**Wavelets.** Mallat's multiresolution theory [12] gives the DWT used here. Embedding in the approximation (LL) band trades visibility for robustness; embedding in detail bands does the opposite.")
    r.para("**Singular value decomposition.** Liu and Tan [2] introduced SVD-based ownership watermarking; Ganic and Eskicioglu [3] combined DWT and SVD and embedded in all sub-bands; Sverdlov, Dexter and Eskicioglu [6] did the same with the DCT; Lai and Tsai [7] proposed a DWT-SVD scheme. Hybrids that cascade DWT, DCT and SVD appear in later work, for example Bekkouch and Faraoun [8] (reversible, two watermarks) and Begum, Ferdush and Uddin [9] (blind, Arnold-map scrambling). These authors report better robustness or imperceptibility than earlier schemes; **we did not re-evaluate those claims**.")
    r.h2("The false-positive problem")
    r.para("Zhang and Li [4] published a comment on Liu and Tan [2], and Ting [5] studied ambiguity attacks on the Ganic–Eskicioglu scheme [3]. Review literature found during the search describes the common cause: if the watermark's singular values are embedded and its singular vectors are kept as the key, the detector reconstructs the key owner's watermark regardless of what was embedded. This report contributes a direct measurement of the effect for this implementation (Section 8.6).")
    r.h2("Geometric attacks, video and learned approaches")
    r.para("Lin *et al.* [22] explain that rotation, scale and translation defeat correlation detectors unless the detection domain is made invariant (log-polar Fourier representation); our rotation and cropping results are consistent with that. Hartung and Girod [23] treat watermarking of uncompressed and compressed video. Learned watermarking (HiDDeN [29], StegaStamp [30]) trains encoder/decoder networks against a distribution of distortions; the project excludes it by design, and no experiment here compares against it.")
    r.h2("Paper-to-implementation mapping")
    r.table(["Ref.", "Technique", "Project function / experiment", "Relationship"], [
        ["[1] Cox et al.", "embedding in significant coefficients; α trade-off", "`embed_watermark` (α); E3", "conceptual foundation"],
        ["[2] Liu & Tan", "singular-value embedding", "`embed_watermark` step 5", "closest ancestor (the project adds the logo's singular values)"],
        ["[3] Ganic & Eskicioglu", "DWT-SVD hybrid", "`embed_watermark` (DWT + SVD)", "conceptual foundation"],
        ["[4][5]", "false-positive / ambiguity critique", "experiment E4", "motivates the controls"],
        ["[10][11]", "LSB; block-DCT", "baselines in `benchmark_tech.py`", "comparison"],
        ["[12] Mallat", "DWT theory", "`pywt.dwt2`", "theory"],
        ["[13][14]", "DCT; JPEG", "`dct2`; `jpeg_compression`", "theory / attack"],
        ["[16] Wang et al.", "SSIM", "`metrics.ssim`", "metric"],
        ["[22] Lin et al.", "RST-resilient detection", "rotation, cropping, scaling attacks", "explains geometric fragility"],
        ["[23] Hartung & Girod", "video watermarking", "`video_demo.py`", "related work"],
        ["[28] blind-watermark", "block DWT-DCT-SVD, blind", "`BlindWMScheme`", "measured comparison"],
    ], "Mapping of literature to the implementation.", widths=[3.0, 4.6, 4.6, 4.4], size=8.5)
    r.h2("Research gaps and trade-offs relevant to this project")
    r.numbered([
        "**Identity binding:** the scheme does not bind the logo to the image (Section 8.6).",
        "**Geometry:** global SVD embedding is geometry-fragile; block-based or invariant-domain embedding [22] is the standard remedy.",
        f"**Metric reliability:** plain NC is dominated by the logo's first singular value — a blank white image already scores NC = {BASE['nc_constant_white_image']:.3f} and a rank-1 approximation {BASE['nc_rank1_approximation']:.3f} for this logo.",
        "**Evaluation breadth:** hybrid schemes in [7]–[9] are, to our reading of their abstracts, evaluated on small standard-image sets; a 100-image stratified evaluation is a contribution of this work.",
    ])
    r.para("The text of this chapter was written from verified titles, abstracts and reference-list entries; where only secondary descriptions were available this is stated.", italic=True, size=9.5)

    # ------------------------------------------------------------- 3 EXISTING TECH
    r.h1("Existing Technology and Problem Analysis")
    r.h2("Existing tools and approaches")
    r.para("The project is an algorithm built on libraries; it is not a general-purpose imaging toolkit. Relevant technologies are NumPy/SciPy (SVD, DCT, filters), PyWavelets (DWT), scikit-image (geometry, metrics), Pillow (JPEG), OpenCV (DCT, SVD, filters, video I/O), ImageMagick (command-line conversion), FFmpeg (video codecs), and at scheme level the `blind-watermark` package [28]. Machine-learning watermarkers [29][30] are out of scope.")
    r.h2("Feature comparison")
    r.table(["Capability", "NumPy", "SciPy", "PyWavelets", "scikit-image", "Pillow", "OpenCV", "ImageMagick", "FFmpeg"], [
        ["2-D DCT", "–", "✓", "–", "–", "–", "✓", "–", "–"],
        ["SVD", "✓", "✓", "–", "–", "–", "✓", "–", "–"],
        ["DWT", "–", "–", "✓", "(via PyWavelets)", "–", "–", "–", "–"],
        ["JPEG codec", "–", "–", "–", "(I/O plug-ins)", "✓", "✓", "✓", "MJPEG"],
        ["filters, rotate, resize", "–", "✓", "–", "✓", "✓", "✓", "✓", "✓"],
        ["PSNR / SSIM", "–", "–", "–", "✓ / ✓", "–", "PSNR (SSIM: contrib)", "`compare`", "–"],
        ["video decode/encode", "–", "–", "–", "–", "–", "✓", "–", "✓"],
        ["licence (metadata)", "BSD-3", "BSD", "MIT/BSD-3", "BSD", "MIT-CMU", "Apache-2.0", "IM licence", "LGPL/GPL"],
    ], "Capability matrix (documentation-based; not benchmarked).", widths=[3.0, 1.4, 1.4, 1.9, 2.0, 1.4, 2.2, 1.9, 1.5], size=8)
    r.h2("Limitations relevant to the project")
    r.para("No single library covers DWT + DCT + SVD + JPEG + metrics, so a combination is necessary; PyWavelets supplies the DWT that OpenCV lacks. An existing blind watermarking package exists [28] and outperforms the project in several attacks (Chapter 8), so novelty cannot be claimed on robustness. The first submission's central design argument — hybrids beat single transforms — was taken from the literature and is not independently tested here.")
    r.h2("Justification for the chosen methods")
    r.bullets([
        "The singular-value scheme is closed-form and explainable, in line with the project's constraint of no learned components.",
        "PyWavelets + SciPy + NumPy + Pillow + scikit-image give numerically agreeing results (≤ 1.5e-16 relative for DCT/SVD; Section 8.8) and the whole 100-image experiment runs in about 80 s on four cores, so a change of library is not justified on performance grounds.",
        "The Haar wavelet and global DCT were retained from the first submission to preserve its functionality and allow direct comparison.",
    ])

    # ------------------------------------------------------------- 4 ARCHITECTURE
    r.h1("System Requirements and Architecture")
    r.h2("Functional requirements")
    r.table(["ID", "Requirement", "Where satisfied"], [
        ["FR1", "Load any common image file safely (colour, alpha, 16-bit, odd sizes) and standardise it", "`image_io.load_gray_square`"],
        ["FR2", "Embed a binary logo into a grey image with a single strength parameter α", "`embed_watermark`"],
        ["FR3", "Extract the logo from a possibly attacked image using the key", "`extract_watermark`"],
        ["FR4", "Apply a reproducible suite of 14 attacks plus an unattacked reference", "`attacks.make_attack_suite`"],
        ["FR5", "Compute PSNR, SSIM, NC, ZNCC, BER", "`metrics.py`"],
        ["FR6", "Process 100 images in batch, record status, time and parameters per operation, validate outputs", "`run_batch_experiment.py`"],
        ["FR7", "Produce tables and figures from recorded results only", "`analysis.py`"],
        ["FR8", "Apply the scheme to video frames (exploratory)", "`video_demo.py`"],
    ], "Functional requirements.", widths=[1.2, 10.0, 5.4], size=9)
    r.h2("Non-functional requirements")
    r.bullets([
        "**Reproducibility:** all stochastic steps seeded; two complete runs gave identical metrics (maximum absolute difference 0.0).",
        "**Robustness of the tooling:** a failing image or attack is recorded, not fatal; corrupt, empty and unsupported files raise `ImageLoadError`.",
        "**Performance:** a 512×512 image is embedded in about 37 ms and extracted in about 20 ms on one CPU core; peak resident memory of a worker is "
        f"{RS['peak_rss_mb_max_over_workers']:.0f} MB.",
        "**Portability:** pure Python with NumPy/SciPy stack; no GPU required.",
    ])
    r.h2("Hardware and software requirements")
    r.para(f"Tested on a 4-vCPU Intel Xeon @ 2.1 GHz with 15 GB RAM, Linux, Python {RS['environment']['python']}, NumPy {RS['environment']['numpy']}, SciPy {RS['environment']['scipy']}, scikit-image {RS['environment']['scikit-image']}, Pillow {RS['environment']['Pillow']}, Pandas {RS['environment']['pandas']}. Optional: OpenCV 5.0.0 and FFmpeg 6.1.1 (video test), ImageMagick 6.9.12 (one benchmark row), `blind-watermark` 0.4.4 (comparison).")
    r.h2("System architecture and data flow")
    r.para("Two pipelines share one key: an embedding pipeline run once by the owner and an extraction pipeline run whenever ownership is to be verified (Figures 4.1 and 4.2). In the batch experiment the watermarked image is rounded to 8 bit, attacked, and then passed to the extractor.")
    r.figure(V("diagram_embedding.png"), "Watermark embedding pipeline (global 2-D DCT of the LL sub-band; the first submission's \"block DCT\" label was wrong).", 15.5)
    r.figure(V("diagram_extraction.png"), "Watermark extraction pipeline (non-blind, key-based).", 15.5)
    r.h2("Module description")
    r.table(["Module", "Responsibility"], [
        ["`watermark_core.py`", "DWT + DCT + SVD embedding / extraction (numerics unchanged from the first submission, validation added)"],
        ["`metrics.py`", "MSE, PSNR, SSIM, NC, ZNCC, BER with shape checks"],
        ["`attacks.py`", "14 attacks + reference; `make_attack_suite(seed)`"],
        ["`logo.py`", "procedural 64×64 binary logo"],
        ["`image_io.py`", "safe decoding, standardisation, PNG verification"],
        ["`dataset_manifest.py`, `build_dataset.py`", "sources, licences, near-duplicate rejection, synthetic controls, `metadata.csv`"],
        ["`run_batch_experiment.py`", "E1–E4 with multiprocessing, per-operation status"],
        ["`analysis.py`, `analysis_tech.py`", "statistics, tables, figures"],
        ["`benchmark_tech.py`", "component and scheme benchmarks"],
        ["`video_demo.py`", "exploratory video test"],
        ["`run_experiment.py`, `make_diagram.py`", "legacy two-image experiment, architecture diagrams"],
    ], "Software modules (`source_code/src`).", widths=[5.4, 11.2], size=9)
    r.h2("Input and output specification")
    r.bullets([
        "**Input:** any decodable image (PNG/JPEG/…); standardised to a 512×512 8-bit grey array. Watermark: 2-D array, any size (64×64 binary logo used).",
        "**Output of embedding:** watermarked 512×512 float array in [0,255] (stored as 8-bit PNG) and a key holding the original singular values (≈ 2.1 MB per image including the unused `U`, `Vᵗ`).",
        "**Output of extraction:** a 64×64 grey image; NC/ZNCC/BER against the logo.",
    ])

    # ------------------------------------------------------------- 5 METHODOLOGY
    r.h1("Methodology and Algorithms")
    r.h2("Dataset preparation and preprocessing")
    r.para("Every source image is decoded with Pillow, alpha is composited over white, 16-bit data is rescaled linearly, colour is converted to grey with the BT.601 luma `L = 0.299R + 0.587G + 0.114B`, the largest centred square is cropped (no aspect distortion), and the result is resampled to 512×512 with Lanczos. The 100-image set and its provenance are described in Chapter 7.")
    r.h2("Mathematical formulation of the scheme")
    r.para("**Haar DWT.** A one-level 2-D Haar transform splits the host H into four sub-bands; for each 2×2 block (a, b; c, d) the approximation is")
    r.equation("LL = (a + b + c + d) / 2", "1")
    r.para("and the three detail bands are the corresponding sums and differences. The watermark is embedded in LL (256×256).")
    r.para("**2-D DCT (global).** The orthonormal DCT-II is applied to the **whole** LL band:")
    r.equation("F(u,v) = α(u) α(v) Σₓ Σᵧ f(x,y) cos[(2x+1)uπ / 2M] cos[(2y+1)vπ / 2N]", "2")
    r.para("with α(0) = √(1/M) and α(u>0) = √(2/M). **SVD.** The DCT matrix and the (resized) logo are factorised:")
    r.equation("A = U · diag(S) · Vᵀ ,        W = U_w · diag(S_w) · V_wᵀ", "3")
    r.para("**Embedding rule.** With embedding strength α (0.10 in the main experiment):")
    r.equation("S′ = S + α · S_w ,        A′ = U · diag(S′) · Vᵀ", "4")
    r.para("followed by the inverse DCT, the inverse DWT and clipping to [0,255]. **Extraction rule.** From the received image the same DWT–DCT–SVD gives S_att, and")
    r.equation("S_w′ = (S_att − S_orig) / α ,        W′ = U_w · diag(S_w′) · V_wᵀ", "5")
    r.para("The key therefore contains S_orig, U_w, V_wᵀ, α and the shapes; U and Vᵀ of the host are stored but not used by the extractor. Because S_orig is derived from the unmarked host the scheme is **non-blind**, and because the logo's singular vectors are in the key the extractor outputs the key owner's logo whatever singular values it finds (Section 8.6).")
    r.h2("Pseudocode")
    r.code("""EMBED(host, logo, alpha):
    LL, details = haar_dwt2(host)
    A  = dct2(LL)                       # global 256x256
    U, S, Vt   = svd(A)
    Wr = resize(logo, shape(LL))
    Uw, Sw, Vwt = svd(Wr)
    S' = S + alpha * Sw
    LL' = idct2(U @ diag(S') @ Vt)
    out = clip(inverse_haar(LL', details), 0, 255)
    key = {S, Uw, Vwt, alpha, shapes}
    return out, key

EXTRACT(image, key):
    LL, _ = haar_dwt2(image);  if shape(LL) != key.shape: LL = resize(LL, key.shape)
    S_att = svd_values(dct2(LL))
    Sw'   = (S_att - key.S) / key.alpha
    W'    = key.Uw @ diag(Sw') @ key.Vwt
    return clip(resize(W', logo_shape), 0, 255)""")
    r.h2("Attack suite")
    r.table(["Family", "Attack (parameters)", "Implementation"], [
        ["compression", "JPEG quality 90, 50, 20", "Pillow, baseline JPEG, floats rounded to 8 bit first"],
        ["noise", "Gaussian σ²=0.005 and 0.02 (on [0,1]; σ≈18, 36 grey levels); salt-and-pepper 2 %", "scikit-image `random_noise`, seeded"],
        ["filtering", "median 3×3; Gaussian blur σ=1.5; unsharp mask (σ=1, amount 1)", "SciPy `ndimage`"],
        ["geometric", "rotation 5° and 15° (centre, bilinear, edge replicate); border zeroing with 25 % of each dimension removed (**43.75 % of the area**); down/up-scaling 0.5×", "scikit-image `rotate`, `resize`; NumPy"],
        ["global intensity", "histogram equalisation", "scikit-image `equalize_hist`"],
    ], "The attack suite: 14 attacks plus the unattacked reference \"No Attack\" (15 conditions; identical to the first submission, now seeded). The first report called all 15 \"attacks\".", widths=[2.6, 8.4, 5.6], size=9)
    r.h2("Evaluation metrics")
    r.equation("PSNR = 10 log₁₀ (255² / MSE) ,     NC = Σ W·W′ / (‖W‖ ‖W′‖) ,     ZNCC = NC of the mean-centred images", "6")
    r.para("SSIM [16] is used with scikit-image's defaults (7×7 window). BER is the fraction of logo pixels that differ after thresholding at 127.5. **ZNCC is new:** plain NC is not mean-centred, so any bright image already scores NC = "
           f"{BASE['nc_constant_white_image']:.3f} against this logo (the square root of its {pc(BASE['logo_fill_ratio'], 1)} white fraction); ZNCC removes that offset. The 0.75 recognisability threshold is a convention of the project that we keep for comparability; we could not trace it to a verified literature source.")
    r.h2("Video workflow (exploratory)")
    r.para("Frames are read with OpenCV, standardised like still images, watermarked individually (each frame has its own key because the scheme is non-blind), encoded by FFmpeg (FFV1 lossless, H.264 at CRF 18/23/28, MJPEG at q 5/15), decoded, and extracted frame by frame. Temporal redundancy is not exploited.")
    r.h2("Parameter selection and implementation decisions")
    r.bullets([
        "**α = 0.10** is kept from the first submission. It gives about 36 dB PSNR and, at that value, 100 % pass rate under JPEG Q=50; Section 8.5 shows how the pass rate under other attacks changes with α.",
        "**Protocol:** the watermarked image is rounded to 8 bit before attacking (primary), because that is what a saved file contains; the first submission's float protocol is reported as a check.",
        "**Seeds:** attacks use `20260713 + 100·index (+ offset)`; control images are drawn with the same base seed.",
    ])
    r.h2("Summary of implemented transformations")
    r.table(["#", "Transformation", "Function", "Library"], [
        ["T1", "grey conversion, crop, Lanczos resize", "`load_gray_square`", "Pillow"],
        ["T2", "1-level Haar DWT and inverse", "`embed/extract_watermark`", "PyWavelets"],
        ["T3", "2-D DCT-II and inverse (global)", "`dct2`, `idct2`", "SciPy fftpack"],
        ["T4", "SVD of host sub-band and logo", "`embed_watermark`", "NumPy"],
        ["T5", "singular-value embedding / extraction", "`embed/extract_watermark`", "NumPy"],
        ["T6", "anti-aliased resize (logo ↔ sub-band)", "inside T5", "scikit-image"],
        ["T7", "procedural binary logo", "`make_watermark_logo`", "Pillow"],
        ["T8–T17", "JPEG, Gaussian & salt-and-pepper noise, median, blur, rotation, border cropping, scaling, histogram equalisation, sharpening", "`attacks.py`", "Pillow, scikit-image, SciPy"],
        ["T18–T19", "PSNR, SSIM, MSE, NC, ZNCC, BER", "`metrics.py`", "scikit-image, NumPy"],
        ["T20", "frame extraction, per-frame embedding, codec round-trip", "`video_demo.py`", "OpenCV, FFmpeg"],
    ], "Transformation summary (details, parameters, limitations and complexity: `documentation/TRANSFORMATIONS_REFERENCE.md`).", widths=[1.6, 7.6, 4.2, 3.2], size=9)

    # ------------------------------------------------------------- 6 IMPLEMENTATION
    r.h1("Implementation")
    r.h2("Software structure")
    r.para("The repository keeps the first submission's four modules and adds loaders, a dataset builder, a batch runner, analysis and benchmark scripts (Table 4.2). Original files are preserved in `source_code/original_backup/`; every change is listed in `documentation/CHANGELOG.md`.")
    r.h2("Key functions and code excerpt")
    r.para("The embedding core is unchanged from the first submission (excerpt of `watermark_core.py`):")
    r.code("""LL, (LH, HL, HH) = pywt.dwt2(host, wavelet)
wm_resized = resize(watermark, target.shape, anti_aliasing=True, preserve_range=True)
target_dct = dct2(target)
U, S, Vt   = np.linalg.svd(target_dct, full_matrices=False)
Uw, Sw, Vtw = np.linalg.svd(wm_resized, full_matrices=False)
S_mod = S + alpha * Sw
target_mod = idct2((U * S_mod) @ Vt)""")
    r.h2("Library usage")
    r.para("NumPy (SVD, array algebra), SciPy (`fftpack.dct`, `ndimage` filters), PyWavelets (`dwt2`/`idwt2`), scikit-image (resize, rotate, noise, equalisation, PSNR/SSIM), Pillow (decoding, JPEG), Pandas/Matplotlib (tables, figures), OpenCV and FFmpeg (video test), python-docx/python-pptx (report and deck builders).")
    r.h2("Execution workflow and error handling")
    r.para("`build_dataset.py` → `run_batch_experiment.py` → `analysis.py` (→ `benchmark_tech.py`, `video_demo.py`). Each attack/extraction is wrapped so that an exception is stored as `status = error` with text; image-level failures are logged and the run continues. Outputs are re-opened and verified (shape, dtype, finiteness). The run summary records "
           f"{RS['images_ok']}/{RS['images_requested']} images, {RS['attack_trials_ok']}/{RS['attack_trials_total']} attack trials and {RS['alpha_sweep_rows_ok']}/{RS['alpha_sweep_rows_total']} sweep rows without failure.")
    r.h2("Design decisions")
    r.bullets([
        "Numerical behaviour of the original embed/extract code was **not** modified, so the first submission's numbers remain reproducible (Appendix E).",
        "Input validation rejects non-2-D, tiny, NaN/Inf or non-numeric input and α ≤ 0.",
        "A variant that embeds the logo's principal component was tried and **rejected**: because the key then contains the whole logo, an unwatermarked image still decodes at NC = 0.98 (`results/exp_principal_component_variant.txt`).",
        "Per-image parallelism with one BLAS thread per process keeps timings comparable.",
    ])
    r.h2("Tests")
    r.para("43 tests (pytest) cover DCT round trips, embedding shape/range/key, clean recovery, monotone PSNR in α, odd sizes, resized input, invalid inputs, metric definitions and boundary values, attack seeding and the cropped area, image loading of RGB/RGBA/16-bit/bilevel/palette/corrupt/empty/unsupported files, and completeness of the dataset and results. All 43 pass (`results/test_results.txt`).")

    # ------------------------------------------------------------- 7 SETUP
    r.h1("Experimental Setup and Evaluation")
    r.h2("The 100-image dataset")
    cat = META.groupby("category").size().sort_values(ascending=False)
    r.para(f"The set contains {len(META)} unique 512×512 grey images: {NREAL} real images from open GitHub-hosted sample collections and {NSYN} synthetic control images (gradient, radial gradient, grating, white noise, low-contrast noise, checkerboard) that are labelled as synthetic everywhere. Brightness classes: " +
           ", ".join(f"{k} {v}" for k, v in META.brightness_class.value_counts().items()) +
           "; contrast classes: " + ", ".join(f"{k} {v}" for k, v in META.contrast_class.value_counts().items()) +
           ". Near-duplicates were rejected by a 64-bit difference hash and uniqueness is asserted by a test. Sources, licences and exclusions are documented in `data/README.md`; per-image provenance is in `data/metadata.csv`.")
    r.figure(V("dataset_contact_sheet.png"), "All 100 images (standardised grey, 512×512), labelled with their IDs and source keys.", 15.5)
    half = (len(cat) + 1) // 2
    rows = [[k, int(v)] for k, v in cat.items()]
    rows2 = [[rows[i][0], rows[i][1], rows[i + half][0] if i + half < len(rows) else "", rows[i + half][1] if i + half < len(rows) else ""] for i in range(half)]
    r.table(["category", "images", "category", "images"], rows2, "Composition of the dataset by category.", widths=[5.0, 2.0, 5.0, 2.0], size=9)
    r.para("**Provenance and rights.** Hosting-repository licences (Apache-2.0, BSD, MIT, HPND, \"YOLO\") are recorded per image, but the repository licence is not a statement about each photograph. Where the upstream project states a licence for an image (CC0 images from scikit-image, NASA public domain, CC BY 2.0 images from scikit-learn) it is quoted in the metadata; for most others nothing is documented upstream, which is stated. The images are used only for non-commercial academic evaluation. Only `raw.githubusercontent.com` and PyPI were reachable when the set was built, which limits the choice of sources.")
    r.h2("Hardware and software environment")
    r.para(f"4-vCPU Intel Xeon @ 2.1 GHz, 15 GB RAM, Linux 6.18, Python {RS['environment']['python']}; NumPy {RS['environment']['numpy']}, SciPy {RS['environment']['scipy']}, scikit-image {RS['environment']['scikit-image']}, Pillow {RS['environment']['Pillow']}, PyWavelets (module attribute 1.8.0, distribution metadata 1.10.0), OpenCV {TS['opencv']}, FFmpeg {TS['ffmpeg'].split('version ')[1].split(' Copyright')[0].split('-')[0]}, ImageMagick {TS['ImageMagick'].split('ImageMagick ')[1].split(' ')[0]}. No GPU.")
    r.h2("Experimental procedure")
    r.table(["ID", "Experiment", "Size", "Recorded"], [
        ["E1", "embed at α = 0.10, save 8-bit PNG, re-open and verify", "100 images", "PSNR, SSIM, differences, time, key size"],
        ["E2", "15 conditions (14 attacks + reference) × 2 protocols (uint8 primary, float check)", "3000 trials", "NC, ZNCC, BER, times, status"],
        ["E3", "α sweep (8 values) × {no attack, JPEG Q=50, Gaussian noise 0.02, blur 1.5, rotation 5°}", "4000 rows", "PSNR, SSIM, NC, ZNCC, BER"],
        ["E4", "false-positive controls (a–d, genuine reference)", "1600 rows", "NC, ZNCC, BER"],
        ["S1", "scheme comparison: project vs `blind-watermark` vs block-DCT vs LSB", "30 images × 9 attacks × 4", "PSNR, BER, NC, time"],
        ["S2", "component benchmark (10 operations, several libraries)", "3 images, 9 repeats", "median time, agreement"],
        ["V1", "video: 2 clips × 60 frames × 6 codec settings", "720 decoded frames", "PSNR, NC, BER, bit-rate, time"],
    ], "Experiments.", widths=[1.1, 8.0, 3.2, 4.3], size=9)
    r.h2("Evaluation metrics and their limits")
    r.para("PSNR and SSIM compare the watermarked image with the *unwatermarked original* and are appropriate for imperceptibility. NC, ZNCC and BER compare the extracted logo with the original logo and are **conditional on the key**; they do not show that the logo was embedded (Section 8.6). A higher metric is not automatically better: PSNR is nearly host-independent here, SSIM can collapse on near-constant images, and edge-detection style metrics do not apply because the project has no edge-detection operation.")
    r.h2("Statistical methods")
    r.para("Means with 95 % bootstrap confidence intervals (2000 resamples), pass rates with Wilson 95 % intervals, Spearman rank correlations (28 p-values, not corrected for multiplicity), and Mann–Whitney AUC for genuine versus control NC. The 94 real images are a convenience sample, so intervals describe sampling variability within this set, not all photographs.")
    r.h2("Benchmarking methodology")
    r.para("Component benchmark: same 512×512 (or 256×256) input, one thread, in-memory (file I/O excluded), two warm-up calls, nine repeats, median over three randomly chosen real images; process-based tools (ImageMagick) are flagged. Scheme benchmark: identical 4095-bit payload (the last of the 4096 logo bits is dropped because `blind-watermark` needs strictly fewer bits than its 4096 blocks), identical attacks, 8-bit rounding, 30 random real images; the block-DCT baseline's strength "
           f"(Δ = {TS['blockdct_delta']}) was tuned on five other images so that its PSNR ({TS['blockdct_psnr']:.1f} dB) matches the project's ({TS['project_psnr_tune']:.1f} dB).")
    r.h2("Reproducibility")
    r.para("Everything is seeded; two complete executions of the batch experiment produced identical metrics (maximum absolute difference 0.0 over 3000 + 4000 + 1600 + 100 rows; timings vary by 5–10 %). Commands are in Appendix A.")

    # ------------------------------------------------------------- 8 RESULTS
    r.h1("Results and Discussion")
    r.h2("Imperceptibility (E1)")
    r.para(f"Across the {E1['n_images']} images at α = 0.10 the mean PSNR of the stored 8-bit watermarked image is **{E1['psnr_all']['mean']:.2f} dB** (median {E1['psnr_all']['median']:.2f}, minimum {E1['psnr_all']['min']:.2f}, maximum {E1['psnr_all']['max']:.2f}; real images only: {E1['psnr_real']['mean']:.2f} dB) and the mean SSIM is **{E1['ssim_all']['mean']:.4f}** (real only: {E1['ssim_real']['mean']:.4f}). No image falls below 30 dB; {E1['n_ssim_below_0.98']} images have SSIM < 0.98 ({', '.join(E1['ssim_below_0.98_ids'])}). The mean absolute pixel change is {E1['mean_abs_diff_mean']:.2f} grey levels, and PSNR is almost independent of the host (82 of 100 images lie within 35.5–35.75 dB) because the added energy is set by the logo's singular values, not by the host.")
    r.figure(V("fig_imperceptibility_hist.png"), "Distribution of PSNR and SSIM of the watermarked images (blue: real, orange: synthetic).", 14.5)
    r.figure(V("fig_representative_comparison.png"), "Original, watermarked and amplified (×10) absolute difference for four typical images (image_066, image_064, image_001, image_051) and two failure cases (image_055: near-black sky; image_100: checkerboard).", 10.3)
    r.para(f"**Failure case.** The near-black astronomy image `image_055` has PSNR 35.9 dB but SSIM {float(IMG.set_index('image_id').loc['image_055','ssim']):.2f}: with almost no signal, the added structure and clipping at 0 dominate the local statistics (difference of up to {E1['max_abs_diff_max']:.0f} grey levels). PSNR alone would have hidden this.")
    r.h2("Robustness under attack (E2)")
    rows = []
    for a in ROB.attack:
        x = rob.loc[a]
        rows.append([a, f"{x.mean_nc:.3f} [{x.ci_lo:.3f}, {x.ci_hi:.3f}]", f"{x.median_nc:.3f}", f"{100*x.pass_rate:.0f} % [{100*x.pass_lo:.0f}, {100*x.pass_hi:.0f}]", f"{x.mean_zncc:.3f}", f"{x.mean_ber:.3f}"])
    r.table(["Attack", "mean NC [95 % CI]", "median NC", "NC ≥ 0.75 [Wilson 95 %]", "mean ZNCC", "mean BER"], rows,
            f"Robustness over {E1['n_images']} images per attack (uint8 protocol). Total: {E2['n_pass']} of {E2['n_trials']} trials ≥ 0.75 ({pc(E2['pass_rate'], 1)}); mean NC {E2['mean_nc']:.3f}.", widths=[4.4, 3.6, 1.8, 3.4, 1.7, 1.7], size=8.5)
    r.para(f"**Overall,** {E2['n_pass']} of {E2['n_trials']} trials ({pc(E2['pass_rate'], 1)}) reach NC ≥ 0.75 when the 100 unattacked reference trials are counted, as the first submission did (25 of 30, 83 %); counting only the 14 attacks it is {E2['n_pass_attacks_only']} of {E2['n_trials_attacks_only']} ({pc(E2['pass_rate_attacks_only'], 1)}, mean NC {E2['mean_nc_attacks_only']:.3f}). With the reference included the mean NC is {E2['mean_nc']:.3f} (real images only {E2['mean_nc_real_only']:.3f}, pass rate {pc(E2['pass_rate_real_only'], 1)}). Clean extraction gives a mean NC of {E2['clean_nc_mean']:.3f} (minimum {E2['clean_nc_min']:.3f}, on the checkerboard). By attack family, mean NC / pass rate are: " +
           "; ".join(f"{row.family} {row.mean_nc:.3f} / {pc(row.pass_rate)}" for row in FAM.itertuples()) + ".")
    r.figure(V("fig_nc_boxplot.png"), "NC per attack over 100 images (box = interquartile range, line = median) and the share of images with NC ≥ 0.75.", 14.5)
    r.figure(V("fig_pass_rate.png"), "Detection pass rate per attack with 95 % Wilson intervals.", 13.0)
    r.figure(V("fig_extraction_gallery.png"), "Extracted logo under every attack for one image (image_066, the cameraman).", 15.5)
    r.para("**Discussion.** The scheme is very robust to JPEG compression (100 % at Q = 90 and 50, 97 % at Q = 20), median filtering (100 %), sharpening (99 %), scaling (98 %), salt-and-pepper noise (97 %), blur (96 %) and mild Gaussian noise (95 %). It is moderately robust to rotation (92 % at 5°, 72 % at 15°) and strong Gaussian noise (86 %), and it fails under histogram equalisation (44 %) and border cropping (1 %). The first submission's statement that \"moderate rotation/scaling were recovered with NC > 0.93 on average\" holds for scaling (0.938) but **not** for 5° rotation (0.880) when 100 images are used.")
    r.h2("Protocol check")
    mx = PRO.drop(PRO[PRO.attack == "Histogram Equalization"].index).max_abs_diff_per_image.max()
    r.para(f"Attacking the 8-bit image (primary) instead of the float image (first submission) changes the mean NC by less than 0.001 for every attack except histogram equalisation (0.644 vs 0.638; up to 0.21 for a single image); the largest per-image change for the other attacks is {mx:.3f}. Mean NC over all trials: {E2['mean_nc']:.4f} (uint8) versus {E2['mean_nc_float_protocol']:.4f} (float).")
    r.h2("Which images fail?")
    sig = COR[COR.p_contrast < 0.01].sort_values("rho_contrast")
    r.para("Robustness depends on the image. Across the 100 images, NC after most attacks is **negatively** correlated with image contrast (Spearman ρ): " +
           "; ".join(f"{x.attack} {x.rho_contrast:.2f}" for x in sig.itertuples()) +
           ". Histogram equalisation correlates with mean brightness instead (ρ = " + f"{float(COR[COR.attack=='Histogram Equalization'].rho_mean_intensity.iloc[0]):.2f}). These are associations (n = 100, uncorrected p-values), not demonstrated causes.")
    r.figure(V("fig_nc_vs_contrast.png"), "NC after three attacks against image contrast (blue: real, orange: synthetic).", 15.0)
    cf = CATF.set_index("category")
    worst = cf.loc[cf.index != "synthetic_control"].sort_values("noise").head(2)
    r.para(f"By category (Appendix C; several categories have only 1–4 images, so these are descriptive): the two document-text images are the least robust to noise (mean NC {cf.loc['document_text','noise']:.2f}) and filtering ({cf.loc['document_text','filtering']:.2f}), and portraits and documents are the least robust to histogram equalisation ({cf.loc['person_portrait','global intensity']:.2f} and {cf.loc['document_text','global intensity']:.2f}), while natural textures and animals are among the most robust.")
    r.figure(V("fig_category_heatmap.png"), "Mean NC by image category and attack family (real images; number of images per category in brackets).", 13.5)
    r.h2("Embedding strength α (E3)")
    j = "JPEG Q=50"; g = "Gaussian Noise (var=0.02)"
    r.para(f"Mean PSNR falls from {sweep('No Attack',0.02,'psnr'):.1f} dB (α = 0.02) to {sweep('No Attack',0.10,'psnr'):.1f} dB (0.10) and {sweep('No Attack',0.40,'psnr'):.1f} dB (0.40). The effect on robustness depends on the attack. **After JPEG Q=50 the mean NC is essentially flat** ({sweep(j,0.02,'nc_mean'):.3f} at α = 0.02, {sweep(j,0.10,'nc_mean'):.3f} at 0.10, {sweep(j,0.40,'nc_mean'):.3f} at 0.40), so the rise shown in the first submission's trade-off figure was an artefact: its NC axis spanned only 0.93–0.99 on a second y-axis, and its JPEG simulation truncated floating-point pixels to 8 bit (a −0.5 grey-level bias), which lowered NC after JPEG at α = 0.02 from 0.981 to 0.929 and had no effect for α ≥ 0.05 (re-creation of the original conditions: `results/exp_jpeg_truncation.txt`). A real trade-off appears under harsher attacks: under Gaussian noise (σ² = 0.02) the pass rate rises from {pc(sweep(g,0.02,'pass_rate'))} at α = 0.02 to {pc(sweep(g,0.05,'pass_rate'))} at 0.05, {pc(sweep(g,0.10,'pass_rate'))} at 0.10, {pc(sweep(g,0.20,'pass_rate'))} at 0.20 and {pc(sweep(g,0.40,'pass_rate'))} at 0.40, while PSNR drops below 30 dB for α ≥ 0.20 ({sweep('No Attack',0.20,'psnr'):.1f} dB). The first submission suggested α ≈ 0.15–0.20 \"at a small, still-imperceptible PSNR cost\"; the measured cost is {sweep('No Attack',0.15,'psnr'):.1f} dB and {sweep('No Attack',0.20,'psnr'):.1f} dB, i.e. at or just above the conventional 30 dB rule of thumb.")
    r.figure(V("fig_alpha_tradeoff.png"), "α sweep over 100 images: PSNR (left), mean NC (middle) and pass rate (right) after four attacks; the dashed line in the middle panel marks NC = 0.75.", 16.0)
    r.h2("False-positive controls (E4)")
    r.para(f"E4 asks whether a high NC proves the watermark is present. (a) An *unwatermarked other* image decoded with the key of image *i* gives a mean NC of {CA.mean_nc:.3f} (95th percentile {CA.p95:.3f}, maximum {CA['max']:.3f}); (b) a *watermarked other* image (same logo, wrong key) gives {CB.mean_nc:.3f} (95th percentile {CB.p95:.3f}); {pc(CA.frac_ge_0_75, 1)} and {pc(CB.frac_ge_0_75, 1)} of these controls exceed the 0.75 threshold, but only {pc(CA.frac_ge_0_90, 1)} and {pc(CB.frac_ge_0_90, 1)} exceed 0.90. (c) The **same host watermarked with a different logo and decoded with the key of logo A** gives NC(A) = **{CC.mean_nc:.3f}**, against {G.mean_nc:.3f} for the genuine pair and {CCR.mean_nc:.3f} for the different logo with its own key: the extractor returns the key owner's logo, whatever was embedded (200 trials; ZNCC {CC.mean_zncc:.3f}). (d) Decoding the image's own *unwatermarked* host with its own key gives NC = 0 by construction, since S_att = S_orig — a degenerate case that must not be read as a positive result.")
    r.figure(V("fig_false_positive.png"), "Mean NC for the genuine pair, for a different logo decoded with the owner's key (orange), and for unrelated images.", 11.0)
    r.figure(V("fig_controls_hist.png"), "Distribution of NC for genuine extraction and for unrelated-image controls.", 13.0)
    r.para(f"**Interpretation.** NC measures the fidelity of the recovered singular values *given the key*; it does not prove that a particular logo is embedded. Control (c) is the false-positive problem described for SVD schemes in [4][5] (Section 2.2), now measured for this implementation. Wrong-image controls overlap the 0.75 threshold: the 95th percentile of NC for unrelated images is {E4['wrong_image_p95']:.2f}, and a detector calibrated to a 5 % false-alarm rate would reject {pc(E4['attacked_genuine_below_wrong_p95'])} of the attacked genuine trials. A claim of ownership would need an additional safeguard (for example an image-bound signature); that was not implemented here.")
    r.figure(V("fig_nc_vs_zncc.png"), "Mean NC and mean ZNCC per attack.", 13.0)
    r.para(f"**NC versus ZNCC.** ZNCC is about 0.02 lower than NC for the clean case ({E2['zncc_clean_mean']:.3f} vs {E2['clean_nc_mean']:.3f}); over all trials the mean ZNCC is {E2['mean_zncc']:.3f} and {pc(E2['zncc_pass_rate'], 1)} of trials reach 0.75, so the conclusions based on NC are not an artefact of the brightness offset for this logo.")
    r.h2("Failure cases")
    r.bullets([
        f"**Border cropping:** mean NC {rob.loc['Cropping 25%'].mean_nc:.3f}; with 43.75 % of the image area zeroed, every singular value changes. The extracted logo is essentially black (BER {rob.loc['Cropping 25%'].mean_ber:.3f} ≈ the white fraction of the logo).",
        f"**Histogram equalisation:** pass rate {pc(rob.loc['Histogram Equalization'].pass_rate)}; it remaps the whole intensity distribution, and the effect varies strongly between images (first submission: 0.10 for the cameraman, 0.66 for the astronaut).",
        "**Near-constant images:** SSIM collapses (0.58) though PSNR is 35.9 dB; the checkerboard has the lowest clean NC (0.79).",
        "**Rotation > 5°:** 72 % pass at 15°; no re-registration is attempted.",
    ])
    r.h2("Comparison with existing technologies (S1, S2)")
    r.para("**Component level.** Equivalent operations agree numerically (DCT and SVD to ≤ 1.5e-16 relative; Haar DWT to 1e-13; Pillow and OpenCV JPEG bit-identical; 3×3 median identical). OpenCV is much faster for the attack operations (3×3 median ≈ 340×, Gaussian blur 4.4×, rotation 5.1×, down/up-scaling 38×, histogram equalisation 19×; part of this reflects `uint8` versus `float64` input), whereas `scipy.linalg.svd` is only 1.19× faster than NumPy's for the SVD that dominates embedding. Because the whole experiment takes about 80 s, none of this justifies changing libraries.")
    r.figure(V("fig_tech_component_speed.png"), "Median time per call for equivalent operations in different libraries (log scale; blue = implementation used by the project; orange includes process start-up and file I/O).", 15.0)
    rows = []
    for a in ["No Attack", "JPEG Q=50", "JPEG Q=20", "Gaussian Noise (var=0.02)", "Median Filter 3x3", "Gaussian Blur (sigma=1.5)", "Rotation 5 deg", "Cropping 25%", "Scaling 0.5x"]:
        rows.append([a] + [f"{ber(s, a):.3f}" for s in (PROJ, BWM, BDCT, LSB)])
    rows.append(["**PSNR (dB)**"] + [f"{psnr_s(s):.1f}" for s in (PROJ, BWM, BDCT, LSB)])
    rows.append(["**embed / extract (ms)**"] + [f"{tms(s,'t_embed_ms'):.0f} / {tms(s,'t_extract_ms'):.0f}" for s in (PROJ, BWM, BDCT, LSB)])
    r.table(["Attack (mean BER, lower is better)", "Project", "blind-watermark 0.4.4", "8×8 block DCT", "LSB"], rows,
            "Scheme comparison on 30 real images with the same 4095-bit payload (BER 0.5 = chance).", widths=[5.2, 2.6, 3.4, 2.8, 2.4], size=9)
    r.figure(V("fig_tech_scheme_ber.png"), "Mean BER of four schemes under nine attacks (PSNR in the legend).", 15.0)
    r.para(f"**Scheme level.** At equal PSNR the project is far more robust than LSB and 8×8 block-DCT embedding, which fall to chance level under JPEG, rescaling and rotation. It is **not superior to the existing blind block-based hybrid** `blind-watermark`: that package achieves a lower BER under JPEG Q=50 ({ber(BWM,'JPEG Q=50'):.3f} vs {ber(PROJ,'JPEG Q=50'):.3f}), noise ({ber(BWM,'Gaussian Noise (var=0.02)'):.3f} vs {ber(PROJ,'Gaussian Noise (var=0.02)'):.3f}), blur, rescaling and cropping ({ber(BWM,'Cropping 25%'):.3f} vs {ber(PROJ,'Cropping 25%'):.3f}), at a higher PSNR ({psnr_s(BWM):.1f} vs {psnr_s(PROJ):.1f} dB) and without a key; but it is {tms(BWM,'t_embed_ms')/tms(PROJ,'t_embed_ms'):.0f}× slower to embed and {tms(BWM,'t_extract_ms')/tms(PROJ,'t_extract_ms'):.0f}× slower to extract, and it is worse under rotation ({ber(BWM,'Rotation 5 deg'):.3f} vs {ber(PROJ,'Rotation 5 deg'):.3f}) and JPEG Q=20 ({ber(BWM,'JPEG Q=20'):.3f} vs {ber(PROJ,'JPEG Q=20'):.3f}). Its colour/YUV design and our channel-wise attacks may favour it. What the project contributes is a short, explainable, key-based reference implementation and the evaluation of its weaknesses, not a better algorithm.")
    r.h2("Exploratory video test (V1)")
    v = VID.groupby("codec", sort=False).agg(nc=("nc_mean", "mean"), ncmin=("nc_min", "min"), psnr=("psnr_wm_vs_orig_db", "mean"), psnr_c=("psnr_codec_only_db", "mean"), n=("frames_decoded", "sum"), kb=("size_wm_kb", "mean")).reset_index()
    rows = [[x.codec, int(x.n), f"{x.psnr:.1f}", f"{x.psnr_c:.1f}" if x.psnr_c < 99 else "∞ (lossless)", f"{x.nc:.3f}", f"{x.ncmin:.3f}", f"{x.kb:.0f}"] for x in v.itertuples()]
    r.table(["Codec setting", "frames decoded", "PSNR vs original (dB)", "PSNR of codec alone (dB)", "mean NC", "min NC", "file size (kB)"], rows,
            "Per-frame embedding on 60 frames of each of two clips (vtest.avi, Megamind.avi), re-encoded with FFmpeg; means over the two clips.", widths=[3.3, 1.9, 2.5, 2.6, 1.7, 1.6, 2.1], size=8.5)
    r.para(f"All 720 decoded frames (2 clips × 60 frames × 6 settings) yielded NC ≥ {VID.nc_min.min():.3f}, so lossy video codecs are not the difficulty for this scheme; embedding takes {VM['vtest.avi']['embed_ms_per_frame']:.0f} ms per frame (≈ {VM['vtest.avi']['embed_fps_single_thread']:.0f} frames per second on one core, 512×512). **Caveats:** this is a feasibility test, not a video-watermarking benchmark — each frame needs its own key (about 2 MB), temporal attacks (frame dropping, re-ordering, frame-rate change) and colour video were not tested, and 60 frames per clip is small. A naive frame-drop test (every tenth frame removed, keys aligned by position) still gave NC {VID.framedrop_nc_naive_index.dropna().mean():.3f} against {VID.framedrop_nc_with_frame_ids.dropna().mean():.3f} when aligned by frame ID, presumably because neighbouring frames are almost identical — another symptom of the key-dependence discussed in Section 8.6.")
    r.h2("Comparison with the claims of the first submission")
    r.table(["First submission", "This evaluation (100 images)", "Verdict"], [
        ["mean PSNR 35.6 dB / SSIM 0.996 (2 images)", f"{E1['psnr_all']['mean']:.1f} dB / {E1['ssim_all']['mean']:.3f}; {E1['n_ssim_below_0.98']} images below SSIM 0.98", "confirmed, with exceptions"],
        ["25/30 trials ≥ 0.75 (83 %)", f"{E2['n_pass']}/{E2['n_trials']} ({pc(E2['pass_rate'], 1)})", "confirmed"],
        ["JPEG: NC > 0.97", f"mean NC {rob.loc['JPEG Q=90'].mean_nc:.3f} / {rob.loc['JPEG Q=50'].mean_nc:.3f} / {rob.loc['JPEG Q=20'].mean_nc:.3f} (Q 90/50/20); pass {pc(rob.loc['JPEG Q=90'].pass_rate)}/{pc(rob.loc['JPEG Q=50'].pass_rate)}/{pc(rob.loc['JPEG Q=20'].pass_rate)}", "holds for Q ≥ 50; Q=20 slightly lower"],
        ["moderate rotation/scaling NC > 0.93", f"scaling {rob.loc['Scaling 0.5x'].mean_nc:.3f}; rotation 5°/15° {rob.loc['Rotation 5 deg'].mean_nc:.3f}/{rob.loc['Rotation 15 deg'].mean_nc:.3f}", "scaling yes, rotation no"],
        ["cropping NC 0.00; histogram eq. 0.10 / 0.66", f"cropping {rob.loc['Cropping 25%'].mean_nc:.3f} (pass {pc(rob.loc['Cropping 25%'].pass_rate)}); hist-eq mean {rob.loc['Histogram Equalization'].mean_nc:.3f} (pass {pc(rob.loc['Histogram Equalization'].pass_rate)})", "confirmed; hist-eq varies widely by image"],
        ["robustness rises with α (JPEG Q=50)", f"flat: {sweep(j,0.02,'nc_mean'):.3f} → {sweep(j,0.40,'nc_mean'):.3f}", "not supported (axis + truncation artefact); true for noise/blur/rotation"],
        ["α ≈ 0.15–0.20 at \"small\" PSNR cost", f"{sweep('No Attack',0.15,'psnr'):.1f} / {sweep('No Attack',0.20,'psnr'):.1f} dB", "borderline"],
        ["\"block DCT\", \"semi-blind\"", "global DCT; non-blind", "corrected"],
        ["extraction proves ownership (implied)", f"wrong logo decoded at NC {CC.mean_nc:.3f}", "**not supported**"],
        ["hybrids beat single transforms (literature)", "not tested; project beats LSB/block-DCT, `blind-watermark` beats project", "unverified claim"],
    ], "Claims of the first submission against the 100-image evaluation.", widths=[4.7, 7.6, 4.3], size=8.5)

    # ------------------------------------------------------------- 9 LIMITS
    r.h1("Limitations and Future Scope")
    r.h2("Current limitations")
    r.bullets([
        "**False-positive problem** (Section 8.6): the extractor returns the key owner's logo; not fixed.",
        "**Non-blind**: needs a ≈ 2.1 MB key per image holding the original singular values.",
        "**Geometry:** border cropping and rotation beyond 5° defeat the scheme; no re-synchronisation.",
        "**Histogram equalisation** and strong noise reduce the pass rate to 44 % and 86 %.",
        "**Grey-scale only**; clean extraction is not lossless (BER ≈ 0.9 % from logo resampling).",
        f"**Imperceptibility metrics:** PSNR is almost host-independent; SSIM collapses on near-constant images.",
    ])
    r.h2("Dataset limitations")
    r.para("A convenience sample of 94 real images from GitHub-hosted sample sets (plus six synthetic controls); several categories contain 1–4 images; image rights are mostly not documented upstream; standardisation to grey, centred square crops and 512×512 resampling remove colour, borders and fine detail of the originals. The images are not a recognised benchmark.")
    r.h2("Performance, quality and comparison limits")
    r.para("Timings were taken on four shared vCPUs (5–10 % run-to-run variation, no GPU). Only one existing watermarking package was measured, with channel-wise attacks that may favour it. The video test covers 120 distinct frames from two clips.")
    r.h2("Future scope")
    r.bullets([
        "**Bind the logo to the image** (for example a signature of image features stored in the key) to remove the false-positive problem; verify with the E4 controls.",
        "**Block-based redundant embedding** with per-block keys to address cropping, and a comparison against the `blind-watermark` design as the new baseline.",
        "**Geometric re-synchronisation** (log-polar or template-based registration, cf. [22]).",
        "**Colour:** embed in the luminance channel of a YCbCr image.",
        "**Video:** shared or index-aware keys, temporal redundancy, tests with frame dropping and re-timing; **real-time or embedded** implementations (≈ 37 ms per 512² frame on one CPU core suggests ≈ 27 frames per second without optimisation).",
        "**Learned or hybrid approaches** [29][30] as a comparison, if the no-ML constraint is relaxed.",
    ])

    # ------------------------------------------------------------- 10 CONCLUSION
    r.h1("Conclusion")
    r.para(f"The project implemented a closed-form hybrid DWT–DCT–SVD watermarking scheme and, in this extended evaluation, tested it on {len(META)} unique images with 14 attacks and an unattacked reference, controls, an α sweep, a technology comparison and a short video test. **Objectives achieved:** the pipeline is implemented, tested (43 tests) and reproducible; imperceptibility is good (mean PSNR {E1['psnr_all']['mean']:.1f} dB, SSIM {E1['ssim_all']['mean']:.3f}); {pc(E2['pass_rate'], 1)} of attack trials recover a logo with NC ≥ 0.75, with very high robustness to JPEG, median filtering, sharpening and rescaling.")
    r.para("**Main findings:** (1) the first submission's headline numbers are reproducible and largely hold at scale, but moderate rotation and histogram equalisation are weaker than it suggested; (2) the imperceptibility–robustness trade-off in α exists for noise, blur and rotation but not for JPEG, and the earlier figure exaggerated it (zoomed axis, truncation bias); (3) **NC is not proof of ownership** — a different logo decoded with the owner's key is reported at NC "
           f"{CC.mean_nc:.2f} — and unrelated images exceed the 0.75 threshold in 10–13 % of controls; (4) the scheme is more robust than LSB and block-DCT at equal PSNR but is not better than an existing blind block-based package, which has lower error rates under most attacks but is 13× slower to embed and weaker under rotation; (5) per-frame application to re-encoded video works technically, with per-frame keys.")
    r.para("**Practical significance and lessons.** The scheme is a clear, explainable teaching implementation and a usable robust mark against re-compression and filtering, provided its key is protected and ownership claims are not based on NC alone. The most valuable lesson of the extension is methodological: more images, seeded attacks, controls and honest axes change the conclusions of a two-image study.")

    # ------------------------------------------------------------- REFERENCES
    r.h1("References", numbered=False)
    refs = open(os.path.join(ROOT, "research", "REFERENCES.md"), encoding="utf-8").read()
    items = []
    for line in refs.splitlines():
        m = re.match(r"\| (\[\d+\]) \| (.*?) \| (.*?) \|\s*$", line)
        if m:
            items.append((int(m.group(1)[1:-1]), m.group(1), re.sub(r"\*([^*]+)\*", r"\1", m.group(2))))
    for _, tag, txt in sorted(items):
        p = r.para(f"{tag}  {txt}", size=9.5, space_after=3)
    r.para("Verification status of each reference (V1 confirmed against the publisher record, V2 confirmed through secondary listings, V3 not independently verified) is given in `research/REFERENCES.md`; references that could not be verified were not cited.", size=9, italic=True)

    # ------------------------------------------------------------- APPENDICES
    r.h1("Installation and execution", appendix="A")
    r.code("""pip install -r source_code/requirements.txt
cd source_code/src
python build_dataset.py            # data/original + metadata.csv (needs network)
python run_batch_experiment.py     # results/*.csv, outputs/watermarked  (~80 s, 4 cores)
python analysis.py                 # tables, summary, figures
python benchmark_tech.py && python analysis_tech.py   # technology comparison (~2.5 min)
python video_demo.py --frames 60   # exploratory video test (ffmpeg required)
python run_experiment.py           # legacy two-image experiment
cd ../.. && python -m pytest tests -q     # 43 tests""", size=8.5)
    r.h1("Dataset sources and attribution", appendix="B")
    g = META[META.is_synthetic == 0].groupby(["source_group", "repository_license"]).size().reset_index(name="n").sort_values("n", ascending=False)
    r.table(["Source group", "Hosting-repository licence", "images"], [[x.source_group, x.repository_license, x.n] for x in g.itertuples()],
            "Real-image sources (the repository licence is not a statement about each photograph).", widths=[7.6, 6.4, 2.0], size=9)
    r.para("Upstream-stated licences used in the metadata: CC0 (scikit-image: brick, camera, chelsea, coffee, grass, gravel, retina), NASA public domain (astronaut, Hubble field), CC BY 2.0 (scikit-learn `china.jpg` by *danielbuechele* and `flower.jpg` by *vultilion*; COCO image `hf_cats`, attribution to the Flickr author per COCO terms — not individually verified), Oxford affine-regions images (K. Mikolajczyk *et al.*, research use), Middlebury stereo/flow images (research use). Synthetic controls are generated by `build_dataset.py`. Full per-image attribution: `data/metadata.csv`, `data/README.md`.", size=10)
    r.h1("Supplementary results", appendix="C")
    cols = ["compression", "filtering", "geometric", "global intensity", "noise", "none"]
    rows = [[x.category, int(x.n_images)] + [f"{getattr(x, c.replace(' ', '_')):.2f}" for c in cols] for x in CATF.rename(columns=lambda c: c.replace(" ", "_")).itertuples()]
    r.table(["category", "n", "compr.", "filter.", "geom.", "glob.int.", "noise", "clean"], rows, "Mean NC by category and attack family (all 100 images, uint8 protocol).", widths=[4.2, 1.0, 1.9, 1.9, 1.9, 1.9, 1.9, 1.9], size=8.5)
    rows = []
    for a in ["Gaussian Noise (var=0.02)", "Gaussian Blur (sigma=1.5)", "Rotation 5 deg", "JPEG Q=50"]:
        for al in (0.02, 0.05, 0.10, 0.20, 0.40):
            rows.append([a, al, f"{sweep(a, al, 'psnr'):.1f}", f"{sweep(a, al, 'nc_mean'):.3f}", f"{sweep(a, al, 'zncc_mean'):.3f}", f"{sweep(a, al, 'ber_mean'):.3f}", pc(sweep(a, al, 'pass_rate'))])
    r.table(["attack", "α", "PSNR", "mean NC", "mean ZNCC", "mean BER", "NC ≥ 0.75"], rows, "α sweep (excerpt of `results/tables/alpha_sweep_summary.csv`).", widths=[4.8, 1.2, 1.7, 2.0, 2.2, 2.2, 2.4], size=8.5)
    rows = [[x.control[:70], int(x.n), f"{x.mean_nc:.3f}", f"{x.p95:.3f}", f"{x.max:.3f}", pc(x.frac_ge_0_75, 1), f"{x.mean_zncc:.3f}"] for x in CTL.itertuples()]
    r.table(["control", "n", "mean NC", "p95", "max", "≥ 0.75", "mean ZNCC"], rows, "False-positive controls (E4).", widths=[6.6, 1.0, 1.7, 1.4, 1.4, 1.7, 1.9], size=8)
    r.figure(V("fig_timing.png"), "Timing of embedding and extraction (single thread, 4 parallel workers).", 11.0)
    r.figure(V("contact_sheet_watermarked.png"), "Watermarked outputs of all 100 images (same order as Figure 7.1).", 13.0)
    r.h1("Test results and configuration", appendix="D")
    r.para("`python -m pytest tests -q`: **43 passed**. Configuration (`source_code/config.json`):")
    r.code(json.dumps(RS["config"], indent=1), size=8)
    r.h1("Reproduction of the first submission", appendix="E")
    rows = [[a, f"{x.orig_nc:.4f}", f"{x.rerun_nc:.4f}", f"{x.d_nc:+.4f}"] for a, x in LEG.set_index(LEG.columns[0]).iterrows()]
    r.table(["attack (cameraman)", "NC (first report)", "NC (re-run)", "difference"], rows, "Re-execution of the original two-image experiment against Table 5.1 of the first report. Differences are due to seeded noise and JPEG rounding.", widths=[5.6, 3.6, 3.4, 3.0], size=9)
    r.h1("Corrections to the first report and presentation", appendix="F")
    r.numbered([
        "\"Block DCT\" → **global** 2-D DCT of the LL band (text, diagrams, deck).",
        "\"Semi-blind\" → **non-blind** (needs S_orig of the unmarked host).",
        "Trade-off figure: dual axis with the NC axis zoomed to 0.93–0.99 replaced by separate panels, four attacks and 100 images; the single low point at α = 0.02 was caused by truncating floats before JPEG encoding (`results/exp_jpeg_truncation.txt`).",
        "\"Cropping 25%\" explained as 43.75 % of the image area.",
        "\"Fifteen attacks\": the suite has 14 attacks plus the unattacked reference \"No Attack\"; pass rates are given with and without the reference.",
        "The 0.75 NC threshold, 30 dB and 0.98 SSIM rules of thumb are conventions; no verified literature source was found.",
        "\"Hybrids repeatedly outperform any single transform\" is a reported trend in the literature, not a result of this project.",
        "Claim that JPEG alignment of the DCT explains the JPEG robustness: not supported (global DCT, SVD dominates).",
        "Reference list rebuilt with verified entries; textbook and documentation entries completed.",
        "Added: 100-image evaluation, ZNCC, false-positive controls, technology comparison, video test, unit tests.",
    ])
    r.h1("Known limitations of this submission", appendix="G")
    r.para("See Chapter 9 and `documentation/CHANGELOG.md`. Items not completed: no Canva design was edited (no link or connection was provided); no university report template was available; the false-positive problem is measured but not fixed.", size=10.5)


def front_matter(r: Report, pages, regs):
    d = r.doc
    # ------------------------------------------------ title page
    for _ in range(3):
        d.add_paragraph()
    r.para("NMIMS MPSTME", align="center", size=12, color=None)
    r.para("B.Tech Computer Engineering", align="center", size=10.5)
    d.add_paragraph()
    p = r.para("**DIGITAL IMAGE WATERMARKING**", align="center", size=26)
    r.para("A Hybrid DWT–DCT–SVD Approach for Robust, Imperceptible Copyright Protection", align="center", size=14, italic=True)
    r.para("Extended evaluation on 100 images, technology comparison, literature review and exploratory video test", align="center", size=11)
    r.para("(Classical signal-processing method — no machine learning / deep learning)", align="center", size=10, italic=True)
    for _ in range(2):
        d.add_paragraph()
    r.para("Subject: Image and Video Processing (IVP)", align="center", size=11.5)
    d.add_paragraph()
    r.para("Submitted by", align="center", size=10)
    r.para("**Krishang Vikram Singh**", align="center", size=13)
    r.para("Roll No. B106  |  Batch C1", align="center", size=10.5)
    d.add_paragraph()
    r.para("First submission: July 2026  ·  Revised and extended edition: October 2026", align="center", size=10)
    # ------------------------------------------------ abstract
    r.doc.add_page_break()
    r.h1("Abstract", numbered=False)
    r.para(f"This report presents the design, implementation and evaluation of a digital image watermarking system built entirely from classical signal-processing techniques — the Discrete Wavelet Transform (DWT), Discrete Cosine Transform (DCT) and Singular Value Decomposition (SVD). A 64×64 binary logo is embedded into the singular values of the DCT of the LL sub-band of a grey-scale host image. The first submission evaluated two images; this extended edition evaluates **{len(META)} unique images ({NREAL} real, {NSYN} labelled synthetic)** under fourteen attacks plus an unattacked reference (JPEG at three qualities, Gaussian noise at two levels, salt-and-pepper noise, median, blur, sharpening, rotation at two angles, cropping, scaling, histogram equalisation), with fully seeded, logged and validated batch processing ({RS['attack_trials_total']} attack trials, {RS['alpha_sweep_rows_total']} α-sweep rows, {RS['control_rows']} control rows, 0 failures).")
    r.para(f"Imperceptibility is good (mean PSNR {E1['psnr_all']['mean']:.1f} dB, mean SSIM {E1['ssim_all']['mean']:.3f}); the normalised correlation of the extracted logo reaches 0.75 in {pc(E2['pass_rate'], 1)} of the attack trials, with ≥ 95 % pass rates for JPEG (Q ≥ 20), median filtering, sharpening, scaling, blur and mild noise, 72 % for 15° rotation, 44 % for histogram equalisation and 1 % for border cropping. Three findings qualify the first submission: the α trade-off in the earlier figure was an artefact for JPEG — a zoomed NC axis (0.93–0.99) plus a truncation bias in the JPEG simulation that lowered NC only at α = 0.02 (the trade-off is real for noise, blur and rotation); the \"block DCT\" and \"semi-blind\" descriptions were wrong (global DCT; non-blind); and **a high normalised correlation does not prove ownership** — a different logo decoded with the owner's key scores NC {CC.mean_nc:.3f}, and unrelated images exceed 0.75 in 10–13 % of controls (the false-positive problem of SVD watermarking).")
    r.para(f"Against existing technology, the scheme is far more robust than LSB and 8×8 block-DCT embedding at equal PSNR but is not better than the open-source `blind-watermark` package, which has lower bit-error rates under most attacks at higher PSNR, is {tms(BWM,'t_embed_ms')/tms(PROJ,'t_embed_ms'):.0f}× slower to embed and is weaker under rotation. An exploratory per-frame test on two real video clips re-encoded with H.264 and MJPEG recovered the logo in all 720 decoded frames (NC ≥ {VID.nc_min.min():.2f}). Every number in this report is generated from the recorded experiment outputs; limitations and unverified items are stated explicitly.")
    r.para("**Keywords:** digital watermarking, DWT, DCT, SVD, robustness, false-positive problem, PSNR, SSIM, normalised correlation.", size=10)
    # ------------------------------------------------ TOC
    entries = []
    for lvl, num, text, label in regs["headings"]:
        if lvl <= 2:
            entries.append((lvl - 1, label, label))
    r.toc_entries([("Abstract" and (0, "Abstract", "Abstract"))] + entries, "Table of Contents")
    r.toc_entries([(0, f"{l}: {c}".replace("`", ""), l) for l, c in regs["figures"]], "List of Figures")
    r.toc_entries([(0, f"{l}: {c}".replace("`", ""), l) for l, c in regs["tables"]], "List of Tables")
    r.doc.add_heading("Abbreviations and symbols", level=1).paragraph_format.page_break_before = True
    r.table(["Symbol", "Meaning"], [
        ["DWT / DCT / SVD", "discrete wavelet transform / discrete cosine transform / singular value decomposition"],
        ["LL", "approximation (low-pass) sub-band of the DWT"],
        ["α", "embedding strength (0.10 unless stated)"],
        ["S, S_w, S_orig, S_att", "singular values of the host sub-band, of the logo, of the original host, of the attacked image"],
        ["U, V, U_w, V_w", "singular-vector matrices of host and logo"],
        ["PSNR / SSIM", "peak signal-to-noise ratio / structural similarity index"],
        ["NC / ZNCC / BER", "normalised correlation / zero-mean NC / bit error rate"],
        ["LSB", "least significant bit"],
        ["CRF / MJPEG / FFV1", "constant-rate-factor of x264 / motion JPEG / lossless codec"],
        ["FPP", "false-positive problem"],
    ], "Abbreviations and symbols.", widths=[4.4, 12.2], size=9)


def build(pages, path):
    # pass 0: registry
    r0 = Report()
    content(r0)
    regs = dict(headings=r0.headings, figures=r0.figures, tables=r0.tables)
    r = Report(pages)
    front_matter(r, pages, regs)
    # content starts on a new page
    r.h1_no = r.h2_no = r.h3_no = r.fig_no = r.tab_no = 0
    r.headings, r.figures, r.tables = [], [], []
    # the first content heading must start a new page
    r.doc.add_page_break()
    content(r)
    r.save(path)
    return regs


def page_map(pdf, regs):
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
    texts = []
    for i in range(1, n + 1):
        t = subprocess.run(["pdftotext", "-layout", "-f", str(i), "-l", str(i), pdf, "-"], capture_output=True, text=True).stdout
        texts.append(t)
    # first page after the abbreviations list (front matter ends there)
    start = next(i for i, t in enumerate(texts) if "Abbreviations and symbols" in t and "Meaning" in t) + 1
    pages = {"Abstract": 2}

    def find(label, prefix_len=38, from_page=start):
        key = label[:prefix_len]
        for i in range(from_page, n):
            for line in texts[i].splitlines():
                s = line.strip()
                if s.startswith(key) and "...." not in s:
                    return i + 1
        return None
    for lvl, num, text, label in regs["headings"]:
        pages[label] = find(label) or 0
    for l, c in regs["figures"]:
        pages[l] = find(l + ":", 12) or 0
    for l, c in regs["tables"]:
        pages[l] = find(l + ":", 12) or 0
    return pages, n


if __name__ == "__main__":
    docx_path = os.path.join(OUT, "Final_Project_Report.docx")
    regs = build({}, docx_path)
    for it in range(2):
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", OUT, docx_path], capture_output=True, timeout=300)
        pdf = os.path.join(OUT, "Final_Project_Report.pdf")
        pages, n = page_map(pdf, regs)
        missing = [k for k, v in pages.items() if not v]
        print(f"pass {it + 1}: {n} pages; unresolved registry entries: {len(missing)} {missing[:6]}")
        regs = build(pages, docx_path)
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", OUT, docx_path], capture_output=True, timeout=300)
    print("done")
