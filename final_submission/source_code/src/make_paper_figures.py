"""Column-width (8.2 cm) figures for the research paper, drawn from the recorded results only."""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
RES, TAB, OUT = os.path.join(ROOT, "results"), os.path.join(ROOT, "results", "tables"), os.path.join(ROOT, "paper", "figs")
os.makedirs(OUT, exist_ok=True)
BLUE, ORANGE, AQUA, GREY, INK = "#2a78d6", "#eb6834", "#1baf7a", "#8a8a85", "#222222"
plt.rcParams.update({"font.family": "DejaVu Serif", "font.size": 7.5, "axes.titlesize": 8, "axes.labelsize": 7.5, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.color": "#e4e4e0", "grid.linewidth": .5, "axes.axisbelow": True,
                     "savefig.dpi": 300, "savefig.bbox": "tight", "legend.frameon": False, "legend.fontsize": 6.5, "xtick.labelsize": 7, "ytick.labelsize": 7})
W = 3.25  # inches (8.2 cm)

rob = pd.read_csv(os.path.join(TAB, "robustness_by_attack.csv"))
sw = pd.read_csv(os.path.join(TAB, "alpha_sweep_summary.csv"))
ctl = pd.read_csv(os.path.join(TAB, "controls_summary.csv"))
sch = pd.read_csv(os.path.join(RES, "tech_benchmark_schemes.csv"))
img = pd.read_csv(os.path.join(RES, "results_images.csv"))

# Fig 1: sample (original / watermarked / |diff| x10)
fig, ax = plt.subplots(1, 3, figsize=(W, 1.25))
host = np.asarray(Image.open(os.path.join(ROOT, "data", "original", "image_066.png")), float)
wm = np.asarray(Image.open(os.path.join(ROOT, "outputs", "watermarked", "image_066_wm.png")), float)
for a, im, t, cm, vmax in zip(ax, [host, wm, np.clip(np.abs(host - wm) * 10, 0, 255)], ["original", "watermarked", "|difference| ×10"], ["gray", "gray", "magma"], [255, 255, 255]):
    a.imshow(im, cmap=cm, vmin=0, vmax=vmax); a.set_title(t, fontsize=7); a.axis("off")
p = img.set_index("image_id").loc["image_066"]
fig.suptitle(f"PSNR {p.psnr_db:.1f} dB, SSIM {p.ssim:.3f}", fontsize=7, y=0.02)
fig.savefig(os.path.join(OUT, "fig1_sample.png")); plt.close(fig)

# Fig 2: pass rate per attack
r = rob.sort_values("pass_rate")
fig, ax = plt.subplots(figsize=(W, 2.9))
ax.barh(r.attack.str.replace("Gaussian ", "Gauss. ").str.replace("Histogram Equalization", "Hist. equalisation"), r.pass_rate * 100,
        color=[BLUE if v >= .9 else ORANGE for v in r.pass_rate], height=.65)
for i, v in enumerate(r.pass_rate):
    ax.text(min(v * 100 + 2, 101), i, f"{v*100:.0f}", va="center", fontsize=6.5)
ax.set_xlim(0, 112); ax.set_xlabel("images with NC ≥ 0.75 (%), n = 100"); ax.grid(axis="y", visible=False)
fig.savefig(os.path.join(OUT, "fig2_passrate.png")); plt.close(fig)

# Fig 3: alpha sweep (two stacked panels)
fig, ax = plt.subplots(2, 1, figsize=(W, 3.1), sharex=True)
p0 = sw[sw.attack == "No Attack"]
ax[0].plot(p0.alpha, p0.psnr, color=BLUE, marker="o", ms=3, lw=1.2); ax[0].axhline(30, color=INK, ls="--", lw=.7)
ax[0].set_ylabel("PSNR (dB)")
cols = {"JPEG Q=50": BLUE, "Gaussian Noise (var=0.02)": ORANGE, "Gaussian Blur (sigma=1.5)": AQUA, "Rotation 5 deg": GREY}
for an, c in cols.items():
    q = sw[sw.attack == an]
    ax[1].plot(q.alpha, q.pass_rate * 100, color=c, marker="o", ms=2.5, lw=1.1, label=an.replace("Gaussian ", "Gauss. ").replace(" (var=0.02)", " σ²=0.02").replace(" (sigma=1.5)", " σ=1.5"))
ax[1].set_ylabel("NC ≥ 0.75 (%)"); ax[1].set_xlabel("embedding strength α"); ax[1].legend(loc="lower right")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig3_alpha.png")); plt.close(fig)

# Fig 4: false positives
g = ctl.iloc[0]; cc = ctl[ctl.control.str.startswith("c: ")].iloc[0]; ca = ctl[ctl.control.str.startswith("a:")].iloc[0]; cb = ctl[ctl.control.str.startswith("b:")].iloc[0]
fig, ax = plt.subplots(figsize=(W, 1.9))
labs = ["genuine", "wrong logo\n(owner's key)", "other image\nunmarked", "other image\nwrong key"]
vals = [g.mean_nc, cc.mean_nc, ca.mean_nc, cb.mean_nc]
ax.bar(labs, vals, color=[BLUE, ORANGE, GREY, GREY], width=.55); ax.tick_params(axis="x", labelsize=6)
for i, v in enumerate(vals):
    ax.text(i, v + .02, f"{v:.3f}", ha="center", fontsize=7)
ax.axhline(0.75, color=INK, ls="--", lw=.7); ax.set_ylim(0, 1.15); ax.set_ylabel("mean NC"); ax.grid(axis="x", visible=False)
fig.savefig(os.path.join(OUT, "fig4_fpp.png")); plt.close(fig)

# Fig 5: scheme comparison (BER), selected attacks
order = ["Project: global DWT-DCT-SVD", "blind-watermark 0.4.4 (block DWT-DCT-SVD)", "Baseline: 8x8 block DCT", "Baseline: spatial LSB"]
names = ["Project", "blind-watermark", "block DCT", "LSB"]
atts = ["JPEG Q=50", "JPEG Q=20", "Gaussian Noise (var=0.02)", "Gaussian Blur (sigma=1.5)", "Rotation 5 deg", "Cropping 25%", "Scaling 0.5x"]
lab = ["JPEG 50", "JPEG 20", "Noise", "Blur", "Rot. 5°", "Crop", "Scale"]
v = sch.set_index(["scheme", "attack"])["mean_ber"]
fig, ax = plt.subplots(figsize=(W, 2.0))
w = .2
for i, (s, n, c) in enumerate(zip(order, names, [BLUE, ORANGE, AQUA, GREY])):
    ax.bar(np.arange(len(atts)) + (i - 1.5) * w, [v[(s, a)] for a in atts], width=w * .92, color=c, label=n)
ax.set_xticks(range(len(atts))); ax.set_xticklabels(lab, fontsize=6.5); ax.set_ylabel("mean BER"); ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(.5, 1.18), columnspacing=.8, handlelength=1)
ax.grid(axis="x", visible=False)
fig.savefig(os.path.join(OUT, "fig5_schemes.png")); plt.close(fig)
print("figures ok", os.listdir(OUT))
