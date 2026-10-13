"""Figures for the technology comparison (reads results/tech_*.csv)."""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
RES, VIS = os.path.join(ROOT, "results"), os.path.join(ROOT, "visualizations")
BLUE, ORANGE, AQUA, GREY, INK = "#2a78d6", "#eb6834", "#1baf7a", "#8a8a85", "#222222"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": "#e4e4e0", "axes.axisbelow": True, "savefig.dpi": 200, "savefig.bbox": "tight",
                     "legend.frameon": False})

A = pd.read_csv(os.path.join(RES, "tech_benchmark_components.csv"))
fig, ax = plt.subplots(figsize=(9, 8))
labels, vals, cols, ypos = [], [], [], []
y = 0
for op, g in A.groupby("operation", sort=False):
    ax.text(0.0008, y - 0.1, op, fontsize=9, fontweight="bold", va="bottom", transform=ax.get_yaxis_transform() if False else ax.transData)
    y += 0.9
    for _, r in g.iterrows():
        labels.append(r.implementation); vals.append(r.median_ms)
        cols.append(BLUE if "(project)" in r.implementation else (ORANGE if r.includes_process_and_io else GREY))
        ypos.append(y); y += 1
    y += 0.5
ax.barh(ypos, vals, color=cols, height=.7)
ax.set_yticks(ypos); ax.set_yticklabels(labels, fontsize=8); ax.invert_yaxis(); ax.set_xscale("log")
for yy, v in zip(ypos, vals):
    ax.text(v * 1.08, yy, f"{v:.2f} ms", va="center", fontsize=7.5)
ax.set_xlim(0.03, 400); ax.set_xlabel("median time per call, ms (log scale; single thread, in-memory)"); ax.grid(axis="y", visible=False)
ax.set_title("Same operation, different libraries (blue = implementation used by the project;\norange = includes process start-up and file I/O)", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(VIS, "fig_tech_component_speed.png")); plt.close(fig)

S = pd.read_csv(os.path.join(RES, "tech_benchmark_schemes.csv"))
atts = ["No Attack", "JPEG Q=50", "JPEG Q=20", "Gaussian Noise (var=0.02)", "Median Filter 3x3", "Gaussian Blur (sigma=1.5)",
        "Rotation 5 deg", "Cropping 25%", "Scaling 0.5x"]
order = ["Project: global DWT-DCT-SVD", "blind-watermark 0.4.4 (block DWT-DCT-SVD)", "Baseline: 8x8 block DCT", "Baseline: spatial LSB"]
cols = {order[0]: BLUE, order[1]: ORANGE, order[2]: AQUA, order[3]: GREY}
fig, ax = plt.subplots(figsize=(10, 4.2))
w = 0.2
for i, s in enumerate(order):
    d = S[S.scheme == s].set_index("attack").reindex(atts)
    ax.bar(np.arange(len(atts)) + (i - 1.5) * w, d.mean_ber, width=w * .92, color=cols[s],
           label=f"{s}  (PSNR {d.psnr_db.mean():.1f} dB)")
ax.axhline(0.5, color=INK, lw=.8, ls=":"); ax.text(len(atts) - .5, 0.505, "0.5 = random guess", ha="right", fontsize=8)
ax.set_xticks(range(len(atts))); ax.set_xticklabels([a.replace(" (", "\n(") for a in atts], fontsize=8)
ax.set_ylabel("mean bit-error rate of recovered logo (30 images)"); ax.set_ylim(0, .6)
ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(0, 1.32), ncol=2)
ax.set_title("Same 4095-bit payload, same attacks", y=1.0, loc="right", fontsize=9)
fig.tight_layout(); fig.savefig(os.path.join(VIS, "fig_tech_scheme_ber.png")); plt.close(fig)
print("ok")

# ---- slide-friendly summary: best alternative per operation vs the project's implementation
best = (A[~A.includes_process_and_io].sort_values("speed_vs_project", ascending=False).groupby("operation", sort=False).head(1)
        .sort_values("speed_vs_project"))
fig, ax = plt.subplots(figsize=(8.2, 4.6))
y = np.arange(len(best))
cols_ = [BLUE if v > 1.5 else GREY for v in best.speed_vs_project]
ax.barh(y, best.speed_vs_project, color=cols_, height=.62)
ax.set_xscale("log"); ax.set_xlim(0.7, 1500)
ax.axvline(1, color=INK, lw=1)
ax.set_yticks(y); ax.set_yticklabels([o.replace(", 512x512", "").replace(" 512x512", "").replace(" 256x256", "") for o in best.operation], fontsize=9.5)
for yy, (_, r) in zip(y, best.iterrows()):
    lab = "project's own library is fastest" if "(project)" in r.implementation else r.implementation.replace(" (project)", "")
    ax.text(r.speed_vs_project * 1.12, yy, f"{r.speed_vs_project:.1f}×  {lab}", va="center", fontsize=8.8)
ax.set_xlabel("speed-up of the fastest alternative vs the project's implementation (× , log scale)")
ax.set_title("Best alternative per operation (single thread, in-memory; outputs identical or ≥ 48 dB PSNR apart)", fontsize=10.5)
ax.grid(axis="y", visible=False)
fig.tight_layout(); fig.savefig(os.path.join(VIS, "fig_tech_speedup.png")); plt.close(fig)
print("speedup ok")
