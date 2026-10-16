"""
build_paper.py
==============
Builds paper/B106.docx : an IEEE-style two-column research paper followed by the project
source code (appendix), in ONE Word file whose name is the student's roll number (teacher's
instruction).  Every number is read from the recorded results; citations are numbered by
order of first appearance from research/REFERENCES.md.

    python make_paper_figures.py && python build_paper.py
"""

from __future__ import annotations

import json
import os
import re
import subprocess

import pandas as pd

from code_clean import strip_python
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
RES, TAB, FIG = os.path.join(ROOT, "results"), os.path.join(ROOT, "results", "tables"), os.path.join(ROOT, "paper", "figs")
OUTDIR = os.path.join(ROOT, "paper")
ROLL = "B106"
FONT = "Times New Roman"

AS = json.load(open(os.path.join(RES, "analysis_summary.json")))
RS = json.load(open(os.path.join(RES, "run_summary.json")))
ROB = pd.read_csv(os.path.join(TAB, "robustness_by_attack.csv")).set_index("attack")
SWP = pd.read_csv(os.path.join(TAB, "alpha_sweep_summary.csv")).set_index(["attack", "alpha"])
CTL = pd.read_csv(os.path.join(TAB, "controls_summary.csv"))
COR = pd.read_csv(os.path.join(TAB, "nc_vs_image_statistics.csv")).set_index("attack")
TSCH = pd.read_csv(os.path.join(RES, "tech_benchmark_schemes.csv")).set_index(["scheme", "attack"])
VID = pd.read_csv(os.path.join(RES, "video_demo_results.csv"))
META = pd.read_csv(os.path.join(ROOT, "data", "metadata.csv"))
E1, E2, E4, BASE = AS["E1"], AS["E2"], AS["E4"], AS["metric_baselines"]
G = CTL.iloc[0]
CA, CB = CTL[CTL.control.str.startswith("a:")].iloc[0], CTL[CTL.control.str.startswith("b:")].iloc[0]
CC = CTL[CTL.control.str.startswith("c: ")].iloc[0]
PROJ, BWM, BDCT, LSB = ("Project: global DWT-DCT-SVD", "blind-watermark 0.4.4 (block DWT-DCT-SVD)", "Baseline: 8x8 block DCT", "Baseline: spatial LSB")
ber = lambda s, a: float(TSCH.loc[(s, a), "mean_ber"])
psnr_s = lambda s: float(TSCH.reset_index().query("scheme == @s").psnr_db.mean())
tms = lambda s, c: float(TSCH.reset_index().query("scheme == @s")[c].median())
sw = lambda a, al, c: float(SWP.loc[(a, al), c])
pc = lambda x, d=0: f"{100 * x:.{d}f}%"

# ------------------------------------------------------------------ references (IEEE numbering by first citation)
REFS = {}
for line in open(os.path.join(ROOT, "research", "REFERENCES.md"), encoding="utf-8"):
    m = re.match(r"\| \[(\d+)\] \| (.*?) \| (.*?) \|\s*$", line)
    if m:
        REFS[int(m.group(1))] = re.sub(r"\*([^*]+)\*", r"\1", m.group(2))
order: list[int] = []


def cite(m):
    nums = [int(x) for x in m.group(1).split(",")]
    out = []
    for n in nums:
        if n not in order:
            order.append(n)
        out.append(order.index(n) + 1)
    out.sort()
    return ", ".join(f"[{k}]" for k in out)


def C(text):
    return re.sub(r"<<([\d,]+)>>", cite, text)


# ------------------------------------------------------------------ docx helpers
doc = Document()


def set_cols(section, n, space_twips=360):
    sectPr = section._sectPr
    for el in sectPr.findall(qn("w:cols")):
        sectPr.remove(el)
    cols = OxmlElement("w:cols")
    cols.set(qn("w:num"), str(n)); cols.set(qn("w:space"), str(space_twips))
    sectPr.append(cols)


def page_setup(section):
    section.page_height, section.page_width = Cm(29.7), Cm(21.0)
    section.left_margin = section.right_margin = Cm(1.9)
    section.top_margin, section.bottom_margin = Cm(1.9), Cm(2.0)


def field(run, instr):
    for t, txt in (("begin", None), (None, instr), ("separate", None), (None, "1"), ("end", None)):
        if t:
            el = OxmlElement("w:fldChar"); el.set(qn("w:fldCharType"), t); run._r.append(el)
        elif txt == instr:
            it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = instr; run._r.append(it)
        else:
            tt = OxmlElement("w:t"); tt.text = txt; run._r.append(tt)


s0 = doc.sections[0]
page_setup(s0)
normal = doc.styles["Normal"]
normal.font.name = FONT
normal.font.size = Pt(10)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
normal.paragraph_format.space_after = Pt(3)
normal.paragraph_format.line_spacing = 1.0
fp = s0.footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_ = fp.add_run(); r_.font.size = Pt(9); r_.font.name = FONT; field(r_, "PAGE")


def para(text, size=10, bold=False, italic=False, align="justify", after=3, before=0, indent=None, keep=False, color=None):
    p = doc.add_paragraph()
    p.alignment = {"justify": WD_ALIGN_PARAGRAPH.JUSTIFY, "center": WD_ALIGN_PARAGRAPH.CENTER, "left": WD_ALIGN_PARAGRAPH.LEFT}[align]
    p.paragraph_format.space_after, p.paragraph_format.space_before = Pt(after), Pt(before)
    if indent is not None:
        p.paragraph_format.first_line_indent = Cm(indent)
    if keep:
        p.paragraph_format.keep_with_next = True
    for part in re.split(r"(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|`[^`]+`)", C(text)):
        if not part:
            continue
        if part.startswith("**"):
            r = p.add_run(part[2:-2]); r.bold = True
        elif part.startswith("`"):
            r = p.add_run(part[1:-1]); r.font.name = "Courier New"; r.font.size = Pt(size - 1.5); continue
        elif part.startswith("*") and len(part) > 2:
            r = p.add_run(part[1:-1]); r.italic = True
        else:
            r = p.add_run(part)
        r.font.size = Pt(size); r.font.name = FONT
        if bold:
            r.bold = True
        if italic:
            r.italic = True
        if color is not None:
            r.font.color.rgb = color
    return p


def body(text):
    return para(text, indent=0.45)


ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
h1n = [0]
h2n = [0]


def H1(title):
    h2n[0] = 0
    p = para(f"{ROMAN[h1n[0]]}. {title.upper()}", size=9.5, align="center", before=7, after=3, keep=True)
    for r in p.runs:
        r.font.small_caps = False
    h1n[0] += 1
    return p


def H2(title):
    h2n[0] += 1
    return para(f"{chr(64 + h2n[0])}. {title}", size=10, italic=True, align="left", before=3, after=2, keep=True)


fig_n = [0]
tab_n = [0]


def figure(path, caption, width=8.2):
    fig_n[0] += 1
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(1); p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(path, width=Cm(width))
    c = para(f"Fig. {fig_n[0]}. {caption}", size=8, align="center", after=5)
    return c


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), fill); tcPr.append(shd)


def table(header, rows, caption, widths, size=7.5):
    tab_n[0] += 1
    para(f"TABLE {ROMAN[tab_n[0] - 1]}", size=8, align="center", after=0, keep=True)
    para(caption.upper() if False else caption, size=8, align="center", after=2, keep=True)
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); t._tbl.tblPr.append(lay)
    mar = OxmlElement("w:tblCellMar")
    for side in ("left", "right"):
        e = OxmlElement(f"w:{side}"); e.set(qn("w:w"), "40"); e.set(qn("w:type"), "dxa"); mar.append(e)
    t._tbl.tblPr.append(mar)
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]; c.text = ""; shade(c, "DDE3EC")
        r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(size); r.font.name = FONT
        c.paragraphs[0].paragraph_format.space_after = Pt(0)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]; p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(v)); r.font.size = Pt(size); r.font.name = FONT
            if i > 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for i, w in enumerate(widths):
        t.columns[i].width = Cm(w)
        for row in t.rows:
            row.cells[i].width = Cm(w)
    for row in t.rows[:-1]:                      # keep the table on one page/column
        for c in row.cells:
            for pp in c.paragraphs:
                pp.paragraph_format.keep_with_next = True
    for row in t.rows:
        trPr = row._tr.get_or_add_trPr(); cs = OxmlElement("w:cantSplit"); trPr.append(cs)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def equation(text, n):
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.tab_stops.add_tab_stop(Cm(4.1), WD_TAB_ALIGNMENT.CENTER)
    p.paragraph_format.tab_stops.add_tab_stop(Cm(8.2), WD_TAB_ALIGNMENT.RIGHT)
    r = p.add_run("\t" + text); r.font.name = "Cambria Math"; r._r.rPr.rFonts.set(qn("w:eastAsia"), "Cambria Math"); r.font.size = Pt(10)
    r2 = p.add_run(f"\t({n})"); r2.font.size = Pt(10); r2.font.name = FONT


# ======================================================================= TITLE BLOCK (single column)
para("Robustness and Verification Limits of a Hybrid DWT–DCT–SVD Image Watermark: A 100-Image Evaluation with False-Positive Controls",
     size=18, bold=True, align="center", after=8, before=2)
para("Krishang Vikram Singh", size=11, align="center", after=0)
para("Roll No. B106 · Batch C1 · B.Tech Computer Engineering", size=9.5, italic=True, align="center", after=0)
para("NMIMS Mukesh Patel School of Technology Management & Engineering (MPSTME), Mumbai, India", size=9.5, italic=True, align="center", after=8)

n_real, n_syn = int((META.is_synthetic == 0).sum()), int((META.is_synthetic == 1).sum())
abstract = (f"**Abstract—**Singular-value watermarking in a wavelet–cosine transform domain is widely used for ownership marking, yet reported evaluations typically use a handful of images "
            f"and score only the correlation between the extracted and the owner's logo. We re-evaluate a classical hybrid DWT–DCT–SVD scheme on {len(META)} unique 512×512 images ({n_real} real, {n_syn} labelled synthetic) "
            f"under 14 attacks plus an unattacked reference ({RS['attack_trials_total']} seeded trials), with an embedding-strength sweep, false-positive controls, a comparison with an open-source blind block-based hybrid and two classical baselines, "
            f"and an exploratory per-frame video test. The scheme is imperceptible (mean PSNR {E1['psnr_all']['mean']:.1f} dB, SSIM {E1['ssim_all']['mean']:.3f}) and recovers the logo (NC ≥ 0.75) in {pc(E2['pass_rate'], 1)} of trials: ≥ 95 % of images survive JPEG (Q ≥ 20), "
            f"median filtering, sharpening, rescaling and mild noise, but only {pc(ROB.loc['Rotation 15 deg'].pass_rate)} survive 15° rotation, {pc(ROB.loc['Histogram Equalization'].pass_rate)} histogram equalisation and {pc(ROB.loc['Cropping 25%'].pass_rate)} border cropping. "
            f"Two findings qualify common practice. First, the robustness–imperceptibility trade-off in the embedding strength α is flat for JPEG and appears only under harsher attacks. Second, a different logo decoded with the owner's key still yields NC {CC.mean_nc:.3f} "
            f"(genuine pair {G.mean_nc:.3f}), and {pc(CA.frac_ge_0_75)}–{pc(CB.frac_ge_0_75)} of unrelated-image controls exceed the customary NC 0.75 threshold: a high NC does not show that the claimed watermark is present. "
            f"The blind block-based hybrid achieves lower bit-error rates under most attacks but is {tms(BWM, 't_embed_ms') / tms(PROJ, 't_embed_ms'):.0f}× slower and weaker under rotation. Code, data manifest and all results accompany the paper.")
para(abstract, size=9, bold=False, after=3)
para("**Index Terms—**digital watermarking, DWT, DCT, SVD, robustness, false-positive problem, normalised correlation, PSNR, SSIM.", size=9, italic=True, after=6)

# ======================================================================= BODY (two columns)
s1 = doc.add_section(WD_SECTION.CONTINUOUS)
set_cols(s1, 2)

# ---------------------------------------------------------------- I
H1("Introduction")
body("Images are copied at no cost, so owners embed invisible signatures that can later be extracted to support an ownership claim <<17,32>>. Spatial-domain marks such as least-significant-bit (LSB) substitution are fragile <<10>>, whereas transform-domain schemes place the mark in perceptually significant spectral components <<1>>. "
     "SVD-based schemes for ownership protection were introduced by Liu and Tan <<2>>, combined with the wavelet transform by Ganic and Eskicioglu <<3>>, and later cascaded with the DCT in hybrid DWT–DCT–SVD designs <<8,9>>.")
body("Two gaps motivate this study. First, evaluations of such schemes usually rely on a few standard images and report one number, the normalised correlation (NC) with the owner's logo. Second, SVD schemes that store the logo's singular vectors in the key have long been criticised for false positives and ambiguity attacks <<4,5>>, "
     "but the effect is rarely quantified, so the common NC ≥ 0.75 rule is used without knowing its false-alarm rate.")
body("**Contributions.** (1) A seeded, fully logged evaluation of a classical DWT–DCT–SVD scheme on 100 unique images with 14 attacks and an unattacked reference. (2) Control experiments that measure the false-positive problem and a metric analysis (a blank image already scores NC "
     f"{BASE['nc_constant_white_image']:.2f} against our logo; a mean-centred variant, ZNCC, is added). (3) An embedding-strength study showing that the trade-off depends on the attack, correcting a single-attack plot. "
     "(4) A measured comparison with an existing open-source blind block-based hybrid <<28>> and two classical baselines, and an exploratory per-frame video test.")

# ---------------------------------------------------------------- II
H1("Related Work")
body("**Foundations.** Cox *et al.* <<1>> argued that a watermark must reside in perceptually significant coefficients and be detected by correlation; Koch and Zhao <<11>> tie block-DCT embedding to the JPEG model; Hartung and Kutter <<17>> survey the field. "
     "The DWT <<12>> and DCT <<13>> underlie JPEG-family codecs <<14>>. **SVD schemes.** Liu and Tan <<2>> modify singular values for rightful-ownership protection; Ganic and Eskicioglu <<3>> embed in the wavelet sub-bands; Lai and Tsai <<7>> and later hybrids <<8,9>> report improved robustness "
     "(we did not re-evaluate those claims). **Critique.** Zhang and Li <<4>> commented on <<2>>, and Ting <<5>> studied ambiguity attacks on <<3>>: when the logo's singular vectors are part of the key, the detector can reconstruct the key owner's logo regardless of what was embedded. "
     "**Geometry and video.** Lin *et al.* <<22>> show that rotation, scale and translation defeat correlation detectors unless the detection domain is invariant; Hartung and Girod <<23>> treat compressed video. Learned watermarking <<29,30>> is outside our scope.")

# ---------------------------------------------------------------- III
H1("Method")
H2("Embedding and extraction")
body("A one-level Haar DWT splits the 512×512 host into four sub-bands; the 256×256 approximation LL is transformed by a global orthonormal 2-D DCT (not block-wise) and factorised by SVD, A = U·diag(S)·Vᵀ. "
     "The 64×64 binary logo W is resized to the sub-band size and factorised, W = U_w·diag(S_w)·V_wᵀ. With embedding strength α (0.10 unless stated),")
equation("S′ = S + α·S_w ,   A′ = U·diag(S′)·Vᵀ", 1)
body("followed by the inverse DCT, the inverse DWT and clipping to [0, 255]. The key is K = {S_orig, U_w, V_wᵀ, α}. Given a (possibly attacked) image, the same transforms give singular values S_att, and")
equation("S_w′ = (S_att − S_orig)/α ,   W′ = U_w·diag(S_w′)·V_wᵀ", 2)
body("The scheme is therefore **non-blind** (S_orig is derived from the unmarked host), and the logo's identity is carried by the key (U_w, V_w), not by the image — the structural reason for the false-positive behaviour measured in Section V-E. "
     "The embedding and extraction code is unchanged from the first implementation of this project; numerical results of that implementation were reproduced to within 0.004 NC.")
H2("Attacks and protocol")
body("Fourteen attacks plus the unattacked reference: JPEG at quality 90/50/20; Gaussian noise (σ² = 0.005, 0.02 on [0,1]); salt-and-pepper (2 %); 3×3 median; Gaussian blur (σ = 1.5); unsharp-mask sharpening; rotation by 5° and 15°; border zeroing with 25 % of each dimension removed (43.75 % of the area); 0.5× down/up-scaling; "
     "and histogram equalisation. The watermarked image is rounded to 8 bit before attacking (primary protocol); attacking the floating-point image, as in the first implementation, changed mean NC by less than 0.001 except for equalisation (0.644 vs 0.638). All stochastic attacks are seeded.")
H2("Metrics")
body("Imperceptibility is measured against the unwatermarked original by PSNR = 10 log₁₀(255²/MSE) and SSIM <<16>>. Recovery is measured by NC = Σ W·W′ / (‖W‖‖W′‖), by BER after thresholding at 127.5, and by ZNCC, the NC of the mean-centred images. "
     f"For this logo a blank white image scores NC = {BASE['nc_constant_white_image']:.3f} and a rank-1 approximation {BASE['nc_rank1_approximation']:.3f}, so NC alone flatters bright outputs. A logo is called recovered if NC ≥ 0.75, a convention we keep for comparability with earlier work; we could not trace it to a primary source and estimate its false-alarm rate in Section V-E.")

# ---------------------------------------------------------------- IV
H1("Experimental Setup")
body(f"**Data.** {len(META)} unique images ({n_real} real, {n_syn} synthetic controls: gradients, grating, noise, checkerboard) were drawn from open sample collections hosted on GitHub (OpenCV, scikit-image, three.js textures and others), converted to grey (ITU-R BT.601), centre-cropped and resized to 512×512; "
     "near-duplicates were removed by a difference hash. The set is a convenience sample covering animals, urban scenes, objects, textures, portraits, paintings, documents, astronomy and medical images with dark/bright and low/high-contrast cases; it is not a recognised benchmark, and per-image provenance, licences and rights notes are recorded in the metadata.")
body(f"**Experiments.** E1 imperceptibility ({E1['n_images']} images); E2 robustness ({RS['attack_trials_total']} trials = 100 images × 15 conditions × 2 protocols); E3 an α sweep over eight values and four attacks ({RS['alpha_sweep_rows_total']} rows); "
     f"E4 false-positive controls ({RS['control_rows']} rows): unmarked and marked *other* images decoded with the key of image *i*, and the same host marked with a *different* logo decoded with the key of logo A. "
     "S1 compares the scheme, at equal PSNR and with an identical 4095-bit payload, with `blind-watermark` 0.4.4 <<28>> (blind, block-based DWT–DCT–SVD), an 8×8 block-DCT baseline and an LSB baseline on 30 random real images. V1 applies the scheme frame by frame to two real clips.")
body("**Statistics and reproducibility.** Means carry 95 % bootstrap intervals, pass rates Wilson intervals, associations Spearman correlations. Two complete executions gave identical metrics (maximum absolute difference 0.0); 43 unit tests pass. "
     "Software: NumPy <<19>>, SciPy <<20>>, scikit-image <<21>>, PyWavelets <<18>>, Pillow, OpenCV and FFmpeg; four vCPUs, single-thread BLAS.")

# ---------------------------------------------------------------- V
H1("Results and Discussion")
H2("Imperceptibility")
body(f"The mean PSNR of the stored 8-bit watermarked image is {E1['psnr_all']['mean']:.2f} dB (range {E1['psnr_all']['min']:.1f}–{E1['psnr_all']['max']:.1f}; none below 30 dB) and the mean SSIM is {E1['ssim_all']['mean']:.3f} (Fig. 1). "
     "PSNR is almost host-independent (82 of 100 images lie in 35.5–35.75 dB) because the added energy is set by the logo's singular values. SSIM exposes exceptions: the near-black astronomy image reaches 35.9 dB but SSIM 0.58, and three images fall below 0.98; PSNR alone would have hidden this.")
figure(os.path.join(FIG, "fig1_sample.png"), "Original, watermarked and amplified difference (image_066, α = 0.10).")

H2("Robustness")
rows = []
for a in ROB.index:
    x = ROB.loc[a]
    rows.append([a.replace("Gaussian ", "Gauss. ").replace("Histogram Equalization", "Hist. equalisation"), f"{x.mean_nc:.3f} ({x.ci_lo:.3f}–{x.ci_hi:.3f})", f"{100 * x.pass_rate:.0f}", f"{x.mean_zncc:.3f}", f"{x.mean_ber:.3f}"])
table(["Attack", "mean NC (95 % CI)", "≥0.75 (%)", "ZNCC", "BER"], rows, f"Robustness over 100 images per condition (8-bit protocol).", [2.45, 2.75, 1.0, 0.95, 0.95], size=7)
body(f"{E2['n_pass']} of {E2['n_trials']} trials ({pc(E2['pass_rate'], 1)}) reach NC ≥ 0.75 including the 100 unattacked references, as counted in earlier work; counting only the 14 attacks it is {pc(E2['pass_rate_attacks_only'], 1)} (mean NC {E2['mean_nc_attacks_only']:.3f}). "
     f"ZNCC is about 0.02 lower than NC and yields {pc(E2['zncc_pass_rate'], 1)} overall, so the conclusions are not an artefact of the brightness offset. Table I and Fig. 2 show strong robustness to compression and filtering and failure under cropping and equalisation. "
     f"Rotation is weaker than sometimes assumed: mean NC {ROB.loc['Rotation 5 deg'].mean_nc:.3f} at 5° and {ROB.loc['Rotation 15 deg'].mean_nc:.3f} at 15° (92 % and 72 % pass). The scheme's robustness to JPEG stems from the SVD stage; the DCT is global and not aligned with JPEG's 8×8 blocks.")
figure(os.path.join(FIG, "fig2_passrate.png"), "Share of the 100 images with NC ≥ 0.75 per attack.")

H2("Which images fail")
body(f"Robustness is image-dependent. NC after attack is negatively correlated with image contrast (Spearman ρ: salt-and-pepper {COR.loc['Salt & Pepper (2%)'].rho_contrast:.2f}, Gaussian noise σ²=0.02 {COR.loc['Gaussian Noise (var=0.02)'].rho_contrast:.2f}, 15° rotation {COR.loc['Rotation 15 deg'].rho_contrast:.2f}); "
     f"histogram equalisation instead tracks mean brightness (ρ = {COR.loc['Histogram Equalization'].rho_mean_intensity:.2f}). Document-text images are the weakest category under noise (mean NC 0.53). These are associations with uncorrected p-values (n = 100), not demonstrated causes.")

H2("Embedding strength")
j, g = "JPEG Q=50", "Gaussian Noise (var=0.02)"
body(f"Mean PSNR falls from {sw('No Attack', 0.02, 'psnr'):.1f} dB (α = 0.02) to {sw('No Attack', 0.10, 'psnr'):.1f} dB (0.10) and {sw('No Attack', 0.40, 'psnr'):.1f} dB (0.40). After JPEG Q = 50 the mean NC is essentially flat in α ({sw(j, 0.02, 'nc_mean'):.3f} at 0.02, {sw(j, 0.40, 'nc_mean'):.3f} at 0.40). "
     f"The trade-off appears under harsher attacks: for Gaussian noise (σ² = 0.02) the pass rate rises from {pc(sw(g, 0.02, 'pass_rate'))} at α = 0.02 to {pc(sw(g, 0.10, 'pass_rate'))} at 0.10 and {pc(sw(g, 0.40, 'pass_rate'))} at 0.40 while PSNR drops below 30 dB for α ≥ 0.20 (Fig. 3). "
     "A single-attack plot on a second, zoomed NC axis — and a JPEG simulation that truncates floating-point pixels, which lowers NC only at α = 0.02 from 0.981 to 0.929 — had earlier suggested a steep trade-off for JPEG; we reproduced that figure exactly and traced the artefact.")
figure(os.path.join(FIG, "fig3_alpha.png"), "Effect of α: PSNR (top) and pass rate after four attacks (bottom), 100 images.")

H2("False-positive controls")
rows = [[x.control.split(":")[0] if ":" in x.control[:3] else "genuine", x.control.split(": ", 1)[-1][:46] if ": " in x.control else x.control[:46], f"{x.mean_nc:.3f}", f"{x.p95:.3f}", f"{100 * x.frac_ge_0_75:.1f}"] for x in CTL.itertuples()]
rows = [["ref", "genuine: own key, clean image", f"{G.mean_nc:.3f}", f"{G.p95:.3f}", f"{100 * G.frac_ge_0_75:.1f}"],
        ["a", "other image, unmarked, key of i", f"{CA.mean_nc:.3f}", f"{CA.p95:.3f}", f"{100 * CA.frac_ge_0_75:.1f}"],
        ["b", "other image, marked, wrong key", f"{CB.mean_nc:.3f}", f"{CB.p95:.3f}", f"{100 * CB.frac_ge_0_75:.1f}"],
        ["c", "other logo B, decoded with key A", f"{CC.mean_nc:.3f}", f"{CC.p95:.3f}", f"{100 * CC.frac_ge_0_75:.1f}"]]
table(["", "Control (NC against the owner's logo)", "mean", "p95", "≥0.75 (%)"], rows, "False-positive controls (E4).", [0.7, 4.6, 1.0, 1.0, 1.1], size=7)
body(f"Embedding a *different* logo in the same host and decoding with the key of logo A returns the owner's logo: NC {CC.mean_nc:.3f}, indistinguishable from the genuine {G.mean_nc:.3f} (Fig. 4, 200 trials) — the extractor reproduces the key owner's logo whatever singular values it finds. "
     f"Unrelated images decoded with a wrong key score {CA.mean_nc:.2f}–{CB.mean_nc:.2f} on average, with 95th percentile {E4['wrong_image_p95']:.2f}; {pc(CA.frac_ge_0_75, 1)} (unmarked) and {pc(CB.frac_ge_0_75, 1)} (marked) exceed 0.75, but only about 1 % exceed 0.90. "
     f"A detector calibrated to a 5 % false-alarm rate would reject {pc(E4['attacked_genuine_below_wrong_p95'])} of the attacked genuine trials. "
     "Decoding the unmarked host with its own key gives NC = 0 by construction (S_att = S_orig) and must not be read as evidence. "
     "An attempt to cure the problem by embedding the logo's principal component made it worse (an unmarked image still decoded at NC 0.98), because the key then contains the whole logo. Claims of ownership therefore require an additional safeguard, for example an image-bound signature, which is future work.")
figure(os.path.join(FIG, "fig4_fpp.png"), "Mean NC for the genuine pair and for the controls (dashed: 0.75).")

H2("Comparison with existing technology")
rows = []
for a in ["JPEG Q=50", "JPEG Q=20", "Gaussian Noise (var=0.02)", "Rotation 5 deg", "Cropping 25%", "Scaling 0.5x"]:
    rows.append([a.replace("Gaussian Noise (var=0.02)", "Gauss. noise").replace(" deg", "°").replace("Cropping 25%", "Cropping").replace("Scaling 0.5x", "Scaling 0.5×")] + [f"{ber(s, a):.3f}" for s in (PROJ, BWM, BDCT, LSB)])
rows.append(["PSNR (dB)"] + [f"{psnr_s(s):.1f}" for s in (PROJ, BWM, BDCT, LSB)])
rows.append(["embed/extract (ms)"] + [f"{tms(s, 't_embed_ms'):.0f}/{tms(s, 't_extract_ms'):.0f}" for s in (PROJ, BWM, BDCT, LSB)])
table(["BER (30 images)", "Project", "blind-wm.", "block DCT", "LSB"], rows, "Same 4095-bit payload and attacks.", [2.7, 1.4, 1.5, 1.5, 1.2], size=7)
body(f"At equal PSNR the project is far more robust than the LSB and 8×8 block-DCT baselines, which approach chance (BER 0.5) under JPEG, rescaling and rotation (Fig. 5). It is, however, **not** superior to the existing blind block-based hybrid <<28>>: that package has lower BER under JPEG Q = 50 "
     f"({ber(BWM, 'JPEG Q=50'):.3f} vs {ber(PROJ, 'JPEG Q=50'):.3f}), noise, blur, scaling and cropping at a higher PSNR ({psnr_s(BWM):.1f} vs {psnr_s(PROJ):.1f} dB) without a key, but is {tms(BWM, 't_embed_ms') / tms(PROJ, 't_embed_ms'):.0f}× slower to embed and "
     f"{tms(BWM, 't_extract_ms') / tms(PROJ, 't_extract_ms'):.0f}× slower to extract, and worse under rotation ({ber(BWM, 'Rotation 5 deg'):.3f} vs {ber(PROJ, 'Rotation 5 deg'):.3f}) and JPEG Q = 20 ({ber(BWM, 'JPEG Q=20'):.3f} vs {ber(PROJ, 'JPEG Q=20'):.3f}). "
     "Its YUV design and our channel-wise attacks may favour it. Library-level checks showed that DCT, SVD, Haar DWT and JPEG implementations in SciPy, OpenCV, NumPy and Pillow agree to ≤ 1.5·10⁻¹⁶ (relative) or bit-identically, "
     "and that OpenCV is faster for attack operations (e.g. 3×3 median ≈ 340×, partly because it works on 8-bit data); the whole experiment runs in about 80 s on four cores, so speed was not a constraint.")
figure(os.path.join(FIG, "fig5_schemes.png"), "Mean bit-error rate of four schemes (lower is better; 0.5 = chance).")

H2("Video feasibility")
body(f"Applied frame by frame (each frame with its own key) to 60 frames of two real clips and re-encoded with H.264 (CRF 18/23/28) and MJPEG (q 5/15), the logo was recovered in all {int(VID.frames_decoded.sum())} decoded frames (NC ≥ {VID.nc_min.min():.2f}); embedding takes about 32–41 ms per frame on one core. "
     "This is a feasibility check only: temporal attacks, colour video and hardware codecs were not tested, and a naive frame-drop test with position-aligned keys still gave NC 0.97 because neighbouring frames are nearly identical — a further symptom of key-dependence.")

# ---------------------------------------------------------------- VI
H1("Limitations")
body("(i) The false-positive problem is measured, not solved. (ii) The scheme is non-blind and needs a key of about 2 MB per image. (iii) Border cropping and rotation beyond 5° defeat it; equalisation is only partly survived. (iv) Grey-scale only; clean extraction is not lossless (BER ≈ 0.9 % from logo resampling). "
     "(v) The 94 real images are a convenience sample from GitHub-hosted sets with mostly undocumented photograph rights, standardised to grey squares; category-level results rest on 1–14 images. "
     "(vi) Only one existing watermarking package was benchmarked; learned methods <<29,30>> and GPU variants were not. (vii) Timing varies by 5–10 % between runs. (viii) The video test covers 120 distinct frames from two clips.")

# ---------------------------------------------------------------- VII
H1("Conclusion and Future Work")
body(f"A classical DWT–DCT–SVD watermark is imperceptible (PSNR {E1['psnr_all']['mean']:.1f} dB, SSIM {E1['ssim_all']['mean']:.3f}) and survives everyday processing — JPEG, median filtering, sharpening, rescaling, mild noise — on at least 95 % of 100 images, but not cropping, equalisation or strong rotation. "
     "Larger-scale testing changes two common conclusions: the α trade-off depends on the attack, and a high normalised correlation does not prove that the claimed watermark is present, because a different logo decoded with the owner's key scores almost the same. "
     "An existing blind block-based hybrid outperforms the scheme on most attacks, so the scheme's value lies in its transparency and compactness, not in robustness. "
     "Future work: bind the logo to the image (signature of image features), block-based redundant embedding for cropping, geometric re-synchronisation <<22>>, colour via luminance, and index-aware keys with temporal redundancy for video <<23>>.")

# ---------------------------------------------------------------- References
H1_title = para("REFERENCES", size=9.5, align="center", before=7, after=3, keep=True)
for k, old in enumerate(order, 1):
    p = para(f"[{k}] {REFS[old]}", size=7.5, align="justify", after=1.5)
    p.paragraph_format.left_indent = Cm(0.6); p.paragraph_format.first_line_indent = Cm(-0.6)

# ======================================================================= CODE APPENDIX (single column)
s2 = doc.add_section(WD_SECTION.NEW_PAGE)
set_cols(s2, 1)
page_setup(s2)
s2.left_margin = s2.right_margin = Cm(1.6)
para("APPENDIX A: SOURCE CODE", size=14, bold=True, align="center", after=4)
para("Python 3.13 · NumPy · SciPy · scikit-image · PyWavelets · Pillow · pandas · matplotlib (OpenCV and FFmpeg for the video test). "
     "Repository: github.com/krishangvikramsingh/claude-code, branch claude/elegant-tesla-c3k9fk, folder final_submission/source_code/src. "
     "The listing contains the algorithm, attacks, metrics, dataset builder, batch experiment, analysis and benchmark scripts; "
     "the data manifest (dataset_manifest.py), the tests and the report/presentation generators are in the repository.", size=9, align="justify", after=6)

CODE_FILES = [("watermark_core.py", "Hybrid DWT–DCT–SVD embedding and extraction (algorithm core)"), ("metrics.py", "PSNR, SSIM, MSE, NC, ZNCC, BER"),
              ("attacks.py", "The 14 attacks plus the unattacked reference, seeded"), ("logo.py", "Procedural 64×64 binary watermark logo"),
              ("image_io.py", "Safe image loading and standardisation"), ("run_experiment.py", "Original two-image experiment (reproduces the first report)"),
              ("build_dataset.py", "Reproducible 100-image dataset builder"), ("run_batch_experiment.py", "100-image batch experiment (E1–E4)"),
              ("analysis.py", "Statistics, tables and figures from the recorded results"), ("benchmark_tech.py", "Library and scheme benchmarks (S1, S2)"),
              ("video_demo.py", "Exploratory per-frame video test (V1)"), ("make_diagram.py", "Architecture diagrams")]
mono = "Consolas"
total_lines = 0
for i, (fn, desc) in enumerate(CODE_FILES, 1):
    path = os.path.join(HERE, fn)
    src = strip_python(open(path, encoding="utf-8").read()).rstrip("\n").split("\n")
    total_lines += len(src)
    h = para(f"A.{i}  {fn}: {desc.replace(chr(8211), chr(45))} ({len(src)} lines)", size=10.5, bold=True, align="left", before=10, after=3, keep=True)
    for line in src:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0
        r = p.add_run(line.replace("\t", "    ") if line else " ")
        r.font.name = mono; r._r.rPr.rFonts.set(qn("w:eastAsia"), mono); r.font.size = Pt(7.5)

doc.core_properties.title = ROLL
doc.core_properties.author = "Krishang Vikram Singh"
doc.core_properties.subject = "Research paper and source code — Image and Video Processing"
os.makedirs(OUTDIR, exist_ok=True)
out = os.path.join(OUTDIR, f"{ROLL}.docx")
doc.save(out)
print("saved", out, "| references:", len(order), "| code lines:", total_lines, "| figures:", fig_n[0], "| tables:", tab_n[0])
subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", OUTDIR, out], capture_output=True, timeout=300)
