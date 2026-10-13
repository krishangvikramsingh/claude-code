"""
analysis.py
===========
Statistics, tables and figures for the 100-image experiment.  Reads ONLY the
recorded CSV files in ``results/`` (written by run_batch_experiment.py) and the
dataset metadata - no number in the report is typed by hand.

    python analysis.py
"""

from __future__ import annotations

import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
from scipy import stats

from attacks import ATTACK_FAMILY, ATTACK_NAMES, make_attack_suite
from logo import make_watermark_logo
from metrics import normalized_correlation, psnr, ssim, zero_normalized_correlation
from watermark_core import embed_watermark, extract_watermark

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
RES = os.path.join(ROOT, "results")
TAB = os.path.join(RES, "tables")
VIS = os.path.join(ROOT, "visualizations")
DATA = os.path.join(ROOT, "data")
os.makedirs(TAB, exist_ok=True)
os.makedirs(VIS, exist_ok=True)

THR = 0.75
BLUE, ORANGE, AQUA, GREY, INK = "#2a78d6", "#eb6834", "#1baf7a", "#8a8a85", "#222222"
plt.rcParams.update({
    "font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10, "axes.edgecolor": "#888888",
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": "#e4e4e0",
    "grid.linewidth": 0.7, "axes.axisbelow": True, "figure.facecolor": "white", "axes.facecolor": "white",
    "savefig.dpi": 200, "savefig.bbox": "tight", "legend.frameon": False,
})
rng = np.random.default_rng(20260713)


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def boot_ci(x, n=2000):
    x = np.asarray(x)
    means = rng.choice(x, size=(n, len(x)), replace=True).mean(axis=1)
    return np.percentile(means, [2.5, 97.5])


def save(fig, name):
    fig.savefig(os.path.join(VIS, name))
    plt.close(fig)


def main():
    meta = pd.read_csv(os.path.join(DATA, "metadata.csv"))
    img = pd.read_csv(os.path.join(RES, "results_images.csv"))
    att = pd.read_csv(os.path.join(RES, "results_attacks.csv"))
    sw = pd.read_csv(os.path.join(RES, "results_alpha_sweep.csv"))
    ctl = pd.read_csv(os.path.join(RES, "results_controls.csv"))
    summ = json.load(open(os.path.join(RES, "run_summary.json")))
    prim = summ["config"]["primary_protocol"]
    cat = meta.set_index("image_id")[["category", "is_synthetic", "mean_intensity", "contrast_std", "key"]]
    out = {}

    # ------------------------------------------------------------------ E1
    im = img.merge(meta[["image_id", "is_synthetic", "category"]], on="image_id")
    def desc(s):
        return dict(mean=s.mean(), std=s.std(), median=s.median(), min=s.min(), max=s.max())
    out["E1"] = {
        "n_images": int(len(im)),
        "psnr_all": desc(im.psnr_db), "ssim_all": desc(im.ssim),
        "psnr_real": desc(im[im.is_synthetic == 0].psnr_db), "ssim_real": desc(im[im.is_synthetic == 0].ssim),
        "psnr_synthetic": desc(im[im.is_synthetic == 1].psnr_db), "ssim_synthetic": desc(im[im.is_synthetic == 1].ssim),
        "n_psnr_below_30": int((im.psnr_db < 30).sum()),
        "n_ssim_below_0.98": int((im.ssim < 0.98).sum()),
        "ssim_below_0.98_ids": list(im[im.ssim < 0.98].image_id),
        "psnr_float_mean": float(im.psnr_float_db.mean()),
        "max_abs_diff_max": float(im.max_abs_diff.max()), "mean_abs_diff_mean": float(im.mean_abs_diff.mean()),
        "t_embed_ms_median": float(im.t_embed_ms.median()), "key_mb": float(im.key_bytes.median() / 1e6),
    }
    t1 = pd.DataFrame({"PSNR (dB)": im.psnr_db.describe(), "SSIM": im.ssim.describe()}).round(4)
    t1.to_csv(os.path.join(TAB, "imperceptibility_summary.csv"))

    # ------------------------------------------------------------------ E2
    a = att[att.protocol == prim].merge(cat, left_on="image_id", right_index=True)
    rows = []
    for name in ATTACK_NAMES:
        x = a[a.attack == name]
        lo, hi = boot_ci(x.nc)
        k = int((x.nc >= THR).sum())
        wl, wh = wilson(k, len(x))
        real = x[x.is_synthetic == 0]
        rows.append(dict(attack=name, family=ATTACK_FAMILY[name], n=len(x), mean_nc=x.nc.mean(), ci_lo=lo, ci_hi=hi,
                         median_nc=x.nc.median(), std_nc=x.nc.std(), min_nc=x.nc.min(), pass_rate=k / len(x),
                         mean_zncc=x.zncc.mean(), median_zncc=x.zncc.median(), zncc_pass_rate=(x.zncc >= THR).mean(),
                         pass_lo=wl, pass_hi=wh, mean_ber=x.ber.mean(), mean_nc_real_only=real.nc.mean(),
                         pass_rate_real_only=(real.nc >= THR).mean(), t_attack_ms=x.t_attack_ms.median(),
                         t_extract_ms=x.t_extract_ms.median()))
    rob = pd.DataFrame(rows)
    rob.to_csv(os.path.join(TAB, "robustness_by_attack.csv"), index=False)
    fam = a.groupby("family").agg(mean_nc=("nc", "mean"), pass_rate=("nc", lambda s: (s >= THR).mean()), n=("nc", "size")).reset_index()
    fam.to_csv(os.path.join(TAB, "robustness_by_family.csv"), index=False)

    other = att[att.protocol != prim].merge(cat, left_on="image_id", right_index=True)
    cmp_rows = []
    for name in ATTACK_NAMES:
        u = a[a.attack == name].set_index("image_id").nc
        f = other[other.attack == name].set_index("image_id").nc
        cmp_rows.append(dict(attack=name, mean_nc_uint8=u.mean(), mean_nc_float=f.mean(),
                             max_abs_diff_per_image=(u - f.reindex(u.index)).abs().max()))
    pd.DataFrame(cmp_rows).to_csv(os.path.join(TAB, "protocol_comparison.csv"), index=False)

    out["E2"] = {
        "protocol": prim, "n_trials": int(len(a)), "mean_nc": float(a.nc.mean()),
        "n_trials_attacks_only": int((a.attack != "No Attack").sum()),
        "n_pass_attacks_only": int(((a.attack != "No Attack") & (a.nc >= THR)).sum()),
        "pass_rate_attacks_only": float((a[a.attack != "No Attack"].nc >= THR).mean()),
        "mean_nc_attacks_only": float(a[a.attack != "No Attack"].nc.mean()),
        "pass_rate": float((a.nc >= THR).mean()), "n_pass": int((a.nc >= THR).sum()),
        "pass_rate_real_only": float((a[a.is_synthetic == 0].nc >= THR).mean()),
        "mean_nc_real_only": float(a[a.is_synthetic == 0].nc.mean()),
        "mean_nc_float_protocol": float(other.nc.mean()), "pass_rate_float_protocol": float((other.nc >= THR).mean()),
        "mean_ber": float(a.ber.mean()), "mean_zncc": float(a.zncc.mean()), "zncc_pass_rate": float((a.zncc >= THR).mean()),
        "zncc_clean_mean": float(a[a.attack == "No Attack"].zncc.mean()),
        "clean_nc_mean": float(a[a.attack == "No Attack"].nc.mean()), "clean_nc_min": float(a[a.attack == "No Attack"].nc.min()),
        "attacks_with_pass_rate_ge_0.95": list(rob[rob.pass_rate >= 0.95].attack),
        "weakest": rob.sort_values("pass_rate").head(3)[["attack", "pass_rate", "mean_nc"]].to_dict("records"),
    }

    # correlations with image statistics (Spearman) ------------------------
    piv = a.pivot(index="image_id", columns="attack", values="nc").join(cat)
    cor = []
    for name in ATTACK_NAMES:
        if name == "No Attack":
            continue
        r1 = stats.spearmanr(piv["contrast_std"], piv[name])
        r2 = stats.spearmanr(piv["mean_intensity"], piv[name])
        cor.append(dict(attack=name, rho_contrast=r1[0], p_contrast=r1[1], rho_mean_intensity=r2[0], p_mean_intensity=r2[1]))
    pd.DataFrame(cor).round(4).to_csv(os.path.join(TAB, "nc_vs_image_statistics.csv"), index=False)

    # category x attack-family heat table -----------------------------------
    ct = a.groupby(["category", "family"]).nc.mean().unstack().round(3)
    ct["n_images"] = meta.groupby("category").size()
    ct.to_csv(os.path.join(TAB, "nc_by_category_family.csv"))
    ca = a.groupby(["category", "attack"]).nc.mean().unstack().round(3)
    ca.to_csv(os.path.join(TAB, "nc_by_category_attack.csv"))

    # ------------------------------------------------------------------ E3
    swo = sw[sw.status == "ok"]
    s = swo.groupby(["attack", "alpha"]).agg(psnr=("psnr_db", "mean"), psnr_sd=("psnr_db", "std"), ssim=("ssim", "mean"),
                                             nc_mean=("nc", "mean"), nc_median=("nc", "median"),
                                             nc_q25=("nc", lambda x: x.quantile(.25)), nc_q75=("nc", lambda x: x.quantile(.75)),
                                             zncc_mean=("zncc", "mean"), ber_mean=("ber", "mean"),
                                             pass_rate=("nc", lambda x: (x >= THR).mean())).reset_index()
    s.round(4).to_csv(os.path.join(TAB, "alpha_sweep_summary.csv"), index=False)
    out["E3"] = {"table": s.round(4).to_dict("records")}
    # metric reference points for this logo
    logo0 = make_watermark_logo(summ["config"]["logo_size"], summ["config"]["logo_text"])
    U_, S_, Vt_ = np.linalg.svd(logo0)
    rank1 = np.clip((U_[:, :1] * S_[:1]) @ Vt_[:1], 0, 255)
    out["metric_baselines"] = {
        "logo_fill_ratio": float((logo0 > 0).mean()),
        "nc_constant_white_image": normalized_correlation(logo0, np.full_like(logo0, 255.0)),
        "nc_rank1_approximation": normalized_correlation(logo0, rank1),
        "zncc_rank1_approximation": zero_normalized_correlation(logo0, rank1),
        "sigma1_energy_fraction": float(S_[0] ** 2 / (S_ ** 2).sum()),
    }

    # ------------------------------------------------------------------ E4
    def sel(prefix):
        return ctl[ctl.control.str.startswith(prefix)].nc
    g = sel("genuine")
    crow = []
    for lbl, pre in [("genuine: own key, clean watermarked image", "genuine"),
                     ("a: other host, UNwatermarked, key of image i", "a:"),
                     ("b: other host, watermarked, key of image i", "b:"),
                     ("c: same host, different logo embedded, decoded with key A (NC vs logo A)", "c: "),
                     ("c-ref: same host, logo B decoded with its own key (NC vs logo B)", "c-ref"),
                     ("d: own host unwatermarked, own key (degenerate)", "d:")]:
        x = sel(pre)
        z = ctl[ctl.control.str.startswith(pre)].zncc
        crow.append(dict(control=lbl, n=len(x), mean_nc=x.mean(), median=x.median(), p95=x.quantile(.95), max=x.max(),
                         frac_ge_0_75=(x >= THR).mean(), frac_ge_0_90=(x >= .9).mean(),
                         mean_zncc=z.mean(), p95_zncc=z.quantile(.95), max_zncc=z.max(), frac_zncc_ge_0_75=(z >= THR).mean()))
    pd.DataFrame(crow).round(4).to_csv(os.path.join(TAB, "controls_summary.csv"), index=False)
    auc = {}
    for k, pre in [("a", "a:"), ("b", "b:"), ("c", "c: ")]:
        x = sel(pre)
        u = stats.mannwhitneyu(g, x, alternative="greater")
        auc[k] = float(u.statistic / (len(g) * len(x)))
    out["E4"] = {"summary": pd.DataFrame(crow).round(4).to_dict("records"), "auc_genuine_vs_control": auc}

    # attacked genuine vs wrong-image controls: how much of the attack range is separable by 0.75?
    wrong_p95 = float(pd.concat([sel("a:"), sel("b:")]).quantile(.95))
    out["E4"]["wrong_image_p95"] = wrong_p95
    out["E4"]["attacked_genuine_below_wrong_p95"] = float((a.nc < wrong_p95).mean())

    # timing ------------------------------------------------------------------
    tim = a.groupby("attack").agg(t_attack_ms=("t_attack_ms", "median"), t_extract_ms=("t_extract_ms", "median")).reset_index()
    tim.round(3).to_csv(os.path.join(TAB, "timing_by_attack.csv"), index=False)
    out["timing"] = {"embed_ms_median": float(img.t_embed_ms.median()),
                     "extract_ms_median": float(a.t_extract_ms.median()),
                     "throughput_embed_per_s_single_core": float(1000 / img.t_embed_ms.median()),
                     "peak_rss_mb": float(img.peak_rss_mb.max())}

    json.dump(out, open(os.path.join(RES, "analysis_summary.json"), "w"), indent=2, default=float)

    # ================================================================ FIGURES
    # Fig: imperceptibility distributions
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.3))
    real = im[im.is_synthetic == 0]; syn = im[im.is_synthetic == 1]
    ax[0].hist(real.psnr_db, bins=np.arange(35.4, 44.2, 0.2), color=BLUE, label=f"real (n={len(real)})")
    ax[0].hist(syn.psnr_db, bins=np.arange(35.4, 44.2, 0.2), color=ORANGE, label=f"synthetic (n={len(syn)})")
    ax[0].axvline(30, color=INK, lw=1, ls="--"); ax[0].text(30.1, ax[0].get_ylim()[1] * .9, "30 dB", fontsize=8)
    ax[0].set_xlabel("PSNR of watermarked image (dB)"); ax[0].set_ylabel("images"); ax[0].legend()
    ax[1].hist(real.ssim, bins=np.linspace(0.55, 1.0, 46), color=BLUE)
    ax[1].hist(syn.ssim, bins=np.linspace(0.55, 1.0, 46), color=ORANGE)
    ax[1].axvline(0.98, color=INK, lw=1, ls="--"); ax[1].text(0.9805, ax[1].get_ylim()[1] * .9, "0.98", fontsize=8)
    ax[1].set_xlabel("SSIM of watermarked image"); ax[1].set_ylabel("images")
    fig.suptitle(f"Imperceptibility at alpha = {summ['config']['alpha']} across {len(im)} images", y=1.02, fontsize=11)
    fig.tight_layout(); save(fig, "fig_imperceptibility_hist.png")

    # Fig: NC distribution per attack (box + pass-rate)
    order = rob.sort_values("median_nc")["attack"].tolist()
    fig, ax = plt.subplots(figsize=(8.6, 6.2))
    data = [a[a.attack == n].nc.values for n in order]
    bp = ax.boxplot(data, orientation="horizontal", patch_artist=True, widths=0.6, showfliers=True,
                    flierprops=dict(marker="o", markersize=2.5, markerfacecolor=GREY, markeredgecolor="none", alpha=.6),
                    medianprops=dict(color=INK, lw=1.4), whiskerprops=dict(color=GREY), capprops=dict(color=GREY),
                    boxprops=dict(edgecolor=GREY))
    for patch, n in zip(bp["boxes"], order):
        patch.set_facecolor(BLUE if rob.set_index("attack").loc[n, "median_nc"] >= THR else ORANGE)
        patch.set_alpha(.85)
    ax.set_yticklabels(order)
    ax.axvline(THR, color=INK, ls="--", lw=1)
    ax.text(THR - .005, len(order) + 0.55, "threshold 0.75", fontsize=8, ha="right", va="center")
    for i, n in enumerate(order, 1):
        pr = rob.set_index("attack").loc[n, "pass_rate"]
        ax.text(1.03, i, f"{pr*100:.0f}%", va="center", fontsize=8.5, color=INK)
    ax.text(1.03, len(order) + 0.55, "NC >= 0.75", fontsize=8, color=INK, va="center")
    ax.set_xlim(-0.02, 1.12); ax.set_xlabel("Normalized correlation (NC) of extracted watermark, 100 images")
    ax.set_title("Robustness per attack: NC over 100 images (box = IQR, line = median)", loc="left")
    ax.grid(axis="y", visible=False)
    fig.tight_layout(); save(fig, "fig_nc_boxplot.png")

    # Fig: pass-rate bars with Wilson CI
    r = rob.sort_values("pass_rate")
    fig, ax = plt.subplots(figsize=(8, 5.4))
    ax.barh(r.attack, r.pass_rate * 100, color=[BLUE if v >= .9 else ORANGE for v in r.pass_rate], height=.62)
    ax.errorbar(r.pass_rate * 100, np.arange(len(r)), xerr=[np.clip((r.pass_rate - r.pass_lo) * 100, 0, None), np.clip((r.pass_hi - r.pass_rate) * 100, 0, None)],
                fmt="none", ecolor=INK, elinewidth=1, capsize=2)
    for i, v in enumerate(r.pass_rate):
        ax.text(min(v * 100 + 3.5, 104), i, f"{v*100:.0f}%", va="center", fontsize=8.5)
    ax.set_xlim(0, 112); ax.set_xlabel("Images with NC >= 0.75 (%)  - error bars: 95% Wilson interval")
    ax.set_title("Detection pass rate per attack (n = 100 images each)")
    ax.grid(axis="y", visible=False)
    fig.tight_layout(); save(fig, "fig_pass_rate.png")

    # Fig: alpha trade-off - small multiples, one axis per panel (no dual axis)
    fig, ax = plt.subplots(1, 3, figsize=(11.5, 3.5))
    p0 = s[s.attack == "No Attack"]
    ax[0].plot(p0.alpha, p0.psnr, color=BLUE, marker="o", ms=4, lw=1.6)
    ax[0].fill_between(p0.alpha, p0.psnr - p0.psnr_sd, p0.psnr + p0.psnr_sd, color=BLUE, alpha=.15, lw=0)
    ax[0].axhline(30, color=INK, lw=1, ls="--"); ax[0].set_ylabel("mean PSNR (dB)")
    ax[0].set_title("Imperceptibility (band = +-1 sd)")
    cols = {"JPEG Q=50": BLUE, "Gaussian Noise (var=0.02)": ORANGE, "Gaussian Blur (sigma=1.5)": AQUA, "Rotation 5 deg": GREY}
    for an, c in cols.items():
        q = s[s.attack == an]
        ax[1].plot(q.alpha, q.nc_mean, color=c, marker="o", ms=3.5, lw=1.5, label=an)
        ax[2].plot(q.alpha, q.pass_rate * 100, color=c, marker="o", ms=3.5, lw=1.5, label=an)
    ax[1].axhline(THR, color=INK, lw=1, ls="--"); ax[1].set_ylim(0.4, 1.02); ax[1].set_ylabel("mean NC (100 images)")
    ax[1].set_title("Robustness: mean NC after attack"); ax[1].legend(fontsize=7.5, loc="lower right")
    ax[2].set_ylim(0, 102); ax[2].set_ylabel("images with NC >= 0.75 (%)"); ax[2].set_title("Robustness: detection pass rate")
    for x_ in ax:
        x_.set_xlabel("embedding strength alpha")
    fig.tight_layout(); save(fig, "fig_alpha_tradeoff.png")

    # Fig: NC vs ZNCC per attack
    fig, ax = plt.subplots(figsize=(8, 5.2))
    rr = rob.sort_values("mean_nc")
    yy = np.arange(len(rr))
    ax.barh(yy + .18, rr.mean_nc, height=.34, color=BLUE, label="NC (original metric)")
    ax.barh(yy - .18, rr.mean_zncc, height=.34, color=ORANGE, label="ZNCC (mean-centred)")
    ax.set_yticks(yy); ax.set_yticklabels(rr.attack); ax.axvline(THR, color=INK, ls="--", lw=1)
    ax.set_xlabel("mean over 100 images"); ax.legend(loc="lower right"); ax.grid(axis="y", visible=False)
    ax.set_title("Plain NC is optimistic: ZNCC removes the brightness offset")
    fig.tight_layout(); save(fig, "fig_nc_vs_zncc.png")

    # Fig: controls
    fig, ax = plt.subplots(figsize=(8, 4))
    bins = np.linspace(0, 1, 41)
    ax.hist(sel("a:"), bins=bins, alpha=.85, color=ORANGE, label="a: other host, unwatermarked", density=True)
    ax.hist(sel("b:"), bins=bins, alpha=.55, color=AQUA, label="b: other host, watermarked (wrong key)", density=True)
    ax.hist(g, bins=bins, alpha=.75, color=BLUE, label="genuine: own key", density=True)
    ax.axvline(THR, color=INK, ls="--", lw=1)
    ax.set_xlabel("NC against the owner's logo"); ax.set_ylabel("density")
    ax.set_title("Control experiments: wrong-image/wrong-key NC overlaps the 0.75 threshold")
    ax.legend(loc="upper center", fontsize=8)
    fig.tight_layout(); save(fig, "fig_controls_hist.png")

    # Fig: FPP bar (wrong logo decoded with the key-A)
    cc = sel("c: "); cr = sel("c-ref")
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    vals = [g.mean(), cc.mean(), cr.mean(), sel("a:").mean(), sel("b:").mean()]
    labs = ["genuine\n(logo A, key A)", "logo B embedded,\ndecoded with key A", "logo B embedded,\ndecoded with key B", "other host,\nunwatermarked", "other host,\nwrong key"]
    ax.bar(labs, vals, color=[BLUE, ORANGE, BLUE, GREY, GREY], width=.6)
    for i, v in enumerate(vals):
        ax.text(i, v + .015, f"{v:.3f}", ha="center", fontsize=9)
    ax.set_ylim(0, 1.12); ax.set_ylabel("mean NC vs the logo tested")
    ax.set_title("False-positive problem: the wrong logo is reported as the owner's logo")
    ax.tick_params(axis="x", labelsize=8); ax.grid(axis="x", visible=False)
    fig.tight_layout(); save(fig, "fig_false_positive.png")

    # Fig: category x family heatmap
    hm = ct.drop(columns="n_images")
    hm = hm.loc[hm.index != "synthetic_control"]
    fig, ax = plt.subplots(figsize=(8.4, 6.2))
    im_ = ax.imshow(hm.values, cmap="Blues", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(hm.shape[1])); ax.set_xticklabels(hm.columns, rotation=30, ha="right")
    ax.set_yticks(range(hm.shape[0])); ax.set_yticklabels([f"{c} ({int(ct.loc[c,'n_images'])})" for c in hm.index])
    for i in range(hm.shape[0]):
        for j in range(hm.shape[1]):
            v = hm.values[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8, color="white" if v > .62 else INK)
    ax.grid(False); fig.colorbar(im_, ax=ax, fraction=.04, label="mean NC")
    ax.set_title("Mean NC by image category and attack family (real images)")
    fig.tight_layout(); save(fig, "fig_category_heatmap.png")

    # Fig: NC vs contrast scatter for 3 attacks
    fig, ax = plt.subplots(1, 3, figsize=(10.5, 3.3), sharey=True)
    for k, name in enumerate(["Gaussian Noise (var=0.02)", "Rotation 15 deg", "Histogram Equalization"]):
        d = piv
        ax[k].scatter(d["contrast_std"], d[name], s=14, c=np.where(d["is_synthetic"] == 1, ORANGE, BLUE), alpha=.8, lw=0)
        rho = stats.spearmanr(d["contrast_std"], d[name])[0]
        ax[k].set_title(f"{name}\nSpearman rho = {rho:.2f}", fontsize=9.5)
        ax[k].set_xlabel("image contrast (std of grey levels)"); ax[k].axhline(THR, color=INK, ls="--", lw=1)
    ax[0].set_ylabel("NC after attack")
    fig.tight_layout(); save(fig, "fig_nc_vs_contrast.png")

    # Fig: timing
    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    ax.hist(img.t_embed_ms, bins=20, color=BLUE, label=f"embed (median {img.t_embed_ms.median():.0f} ms)")
    ax.hist(a.t_extract_ms, bins=40, color=ORANGE, alpha=.8, label=f"extract (median {a.t_extract_ms.median():.0f} ms)")
    ax.set_xlabel("time per 512x512 image (ms, single thread)"); ax.set_ylabel("operations"); ax.legend()
    fig.tight_layout(); save(fig, "fig_timing.png")

    # ------------------------------------------------- qualitative figures
    cfg = summ["config"]; alpha = cfg["alpha"]
    logo = make_watermark_logo(cfg["logo_size"], cfg["logo_text"])
    Image.fromarray(logo.astype(np.uint8)).save(os.path.join(VIS, "watermark_logo.png"))
    reps = ["image_066", "image_064", "image_001", "image_051", "image_055", "image_100"]
    fig, axes = plt.subplots(len(reps), 3, figsize=(8.4, 2.8 * len(reps)))
    for r_i, iid in enumerate(reps):
        host = np.asarray(Image.open(os.path.join(DATA, "original", iid + ".png")), dtype=np.float64)
        w = np.asarray(Image.open(os.path.join(ROOT, "outputs", "watermarked", iid + "_wm.png")), dtype=np.float64)
        d = np.abs(host - w)
        row = img.set_index("image_id").loc[iid]
        key = meta.set_index("image_id").loc[iid, "key"]
        axes[r_i, 0].imshow(host, cmap="gray", vmin=0, vmax=255); axes[r_i, 0].set_title(f"{iid} ({key}) original", fontsize=8.5)
        axes[r_i, 1].imshow(w, cmap="gray", vmin=0, vmax=255); axes[r_i, 1].set_title(f"watermarked  PSNR {row.psnr_db:.1f} dB, SSIM {row.ssim:.3f}", fontsize=8.5)
        im2 = axes[r_i, 2].imshow(np.clip(d * 10, 0, 255), cmap="magma", vmin=0, vmax=255); axes[r_i, 2].set_title(f"|difference| x10 (max {d.max():.0f} grey levels)", fontsize=8.5)
        for x in axes[r_i]:
            x.axis("off")
    fig.tight_layout(); save(fig, "fig_representative_comparison.png")

    # extraction gallery for the cameraman image under the 14 attacks and the unattacked reference
    iid = "image_066"
    host = np.asarray(Image.open(os.path.join(DATA, "original", iid + ".png")), dtype=np.float64)
    w, key = embed_watermark(host, logo, alpha=alpha)
    wq = np.clip(np.rint(w), 0, 255)
    suite = make_attack_suite(cfg["base_seed"] + 100 * (int(iid[-3:]) - 1))
    fig, axes = plt.subplots(3, 6, figsize=(12, 6.6))
    axes[0, 0].imshow(logo, cmap="gray"); axes[0, 0].set_title("original logo", fontsize=8.5)
    for ax_, name in zip(axes.flat[1:], ATTACK_NAMES):
        ext = extract_watermark(suite[name](wq), key)
        ax_.imshow(ext, cmap="gray", vmin=0, vmax=255)
        ax_.set_title(f"{name}\nNC={normalized_correlation(logo, ext):.3f}", fontsize=7.8)
    for ax_ in axes.flat[16:]:
        ax_.axis("off")
    for ax_ in axes.flat:
        ax_.set_xticks([]); ax_.set_yticks([]); ax_.grid(False)
    fig.suptitle("Extracted watermark under each attack (image_066, cameraman)", y=1.0, fontsize=11)
    fig.tight_layout(); save(fig, "fig_extraction_gallery.png")

    # contact sheet of watermarked outputs
    T = 128
    sheet = Image.new("L", (10 * T, 10 * T), 255)
    for i, iid in enumerate(meta.image_id):
        sheet.paste(Image.open(os.path.join(ROOT, "outputs", "watermarked", iid + "_wm.png")).resize((T, T)), ((i % 10) * T, (i // 10) * T))
    sheet.save(os.path.join(VIS, "contact_sheet_watermarked.png"))
    print(json.dumps({k: out[k] for k in ("E1", "E2")}, indent=1, default=float)[:3000])


if __name__ == "__main__":
    main()
