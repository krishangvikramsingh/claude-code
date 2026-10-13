"""
run_experiment.py
==================
End-to-end pipeline:
  1. Load host (cover) images -- standard grayscale test images
  2. Generate a synthetic binary watermark logo (procedurally drawn, not
     copyrighted material)
  3. Embed watermark using the hybrid DWT-DCT-SVD scheme (watermark_core.py)
  4. Measure imperceptibility (PSNR / SSIM) of the watermarked image
  5. Run the full attack suite (attacks.py)
  6. Extract watermark after each attack, measure NC / BER (metrics.py)
  7. Save all figures + a results CSV/JSON to ../results/
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
from skimage import data as skdata
from skimage.transform import resize

from watermark_core import embed_watermark, extract_watermark
from metrics import psnr, ssim, normalized_correlation, bit_error_rate
from attacks import ATTACK_SUITE

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def make_watermark_logo(size=64, text="CYBERION"):
    """Procedurally generate a binary logo watermark (no external/copyrighted asset)."""
    img = Image.new("L", (size * 4, size), color=0)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    draw.rectangle([0, 0, size * 4 - 1, size - 1], outline=255, width=3)
    draw.text((10, size // 2 - 6), text, fill=255, font=font)
    img = img.resize((size, size))
    arr = np.array(img).astype(np.float64)
    arr = (arr > 100).astype(np.float64) * 255.0
    return arr


def load_host_images():
    hosts = {
        "cameraman": resize(skdata.camera().astype(np.float64), (512, 512), preserve_range=True),
        "astronaut_gray": resize(skdata.astronaut().mean(axis=2).astype(np.float64), (512, 512), preserve_range=True),
    }
    return hosts


def save_image(arr, path):
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(path)


def main():
    alpha = 0.10
    hosts = load_host_images()
    watermark = make_watermark_logo(size=64, text="CYBERION")
    save_image(watermark, os.path.join(RESULTS_DIR, "watermark_logo.png"))

    all_rows = []
    per_host_extracted = {}

    for host_name, host in hosts.items():
        watermarked, key = embed_watermark(host, watermark, alpha=alpha)
        save_image(host, os.path.join(RESULTS_DIR, f"{host_name}_original.png"))
        save_image(watermarked, os.path.join(RESULTS_DIR, f"{host_name}_watermarked.png"))

        imperceptibility_psnr = psnr(host, watermarked)
        imperceptibility_ssim = ssim(host, watermarked)

        extracted_examples = {}
        for attack_name, attack_fn in ATTACK_SUITE.items():
            attacked = attack_fn(watermarked)
            extracted = extract_watermark(attacked, key)
            nc = normalized_correlation(watermark, extracted)
            ber = bit_error_rate(watermark, extracted)

            all_rows.append({
                "Host Image": host_name,
                "Attack": attack_name,
                "Watermarked PSNR (dB)": round(imperceptibility_psnr, 3),
                "Watermarked SSIM": round(imperceptibility_ssim, 4),
                "Extracted NC": round(nc, 4),
                "Extracted BER": round(ber, 4),
            })
            extracted_examples[attack_name] = extracted

        per_host_extracted[host_name] = extracted_examples

    df = pd.DataFrame(all_rows)
    df.to_csv(os.path.join(RESULTS_DIR, "results_table.csv"), index=False)
    print(df.to_string(index=False))

    # ---- Figure 1: original / watermarked / difference (per host) ----
    for host_name, host in hosts.items():
        watermarked = np.array(Image.open(os.path.join(RESULTS_DIR, f"{host_name}_watermarked.png"))).astype(np.float64)
        diff = np.abs(host - watermarked)
        fig, axes = plt.subplots(1, 3, figsize=(12, 4.2))
        axes[0].imshow(host, cmap="gray"); axes[0].set_title("Original Host"); axes[0].axis("off")
        axes[1].imshow(watermarked, cmap="gray"); axes[1].set_title("Watermarked"); axes[1].axis("off")
        im = axes[2].imshow(diff, cmap="hot"); axes[2].set_title("Absolute Difference (x1)"); axes[2].axis("off")
        fig.colorbar(im, ax=axes[2], fraction=0.046)
        plt.tight_layout()
        plt.savefig(os.path.join(RESULTS_DIR, f"{host_name}_comparison.png"), dpi=150)
        plt.close(fig)

    # ---- Figure 2: watermark extraction gallery under attacks (cameraman) ----
    gallery_attacks = ["No Attack", "JPEG Q=50", "JPEG Q=20", "Gaussian Noise (var=0.02)",
                        "Median Filter 3x3", "Rotation 15 deg", "Cropping 25%", "Scaling 0.5x"]
    fig, axes = plt.subplots(2, 4, figsize=(14, 7))
    for ax, aname in zip(axes.flat, gallery_attacks):
        ex = per_host_extracted["cameraman"][aname]
        ax.imshow(ex, cmap="gray")
        row = df[(df["Host Image"] == "cameraman") & (df["Attack"] == aname)].iloc[0]
        ax.set_title(f"{aname}\nNC={row['Extracted NC']:.3f}", fontsize=9)
        ax.axis("off")
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "extraction_gallery.png"), dpi=150)
    plt.close(fig)

    # ---- Figure 3: NC bar chart across attacks ----
    sub = df[df["Host Image"] == "cameraman"].sort_values("Extracted NC")
    fig, ax = plt.subplots(figsize=(9, 6))
    colors = ["#c0392b" if v < 0.75 else "#27ae60" for v in sub["Extracted NC"]]
    ax.barh(sub["Attack"], sub["Extracted NC"], color=colors)
    ax.axvline(0.75, color="black", linestyle="--", linewidth=1, label="Recognizability threshold (NC=0.75)")
    ax.set_xlabel("Normalized Correlation (NC)")
    ax.set_title("Watermark Robustness Across Attack Types (host: cameraman)")
    ax.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "nc_bar_chart.png"), dpi=150)
    plt.close(fig)

    # ---- Figure 4: alpha sensitivity sweep (PSNR vs NC tradeoff) ----
    host = hosts["cameraman"]
    alphas = [0.02, 0.05, 0.08, 0.10, 0.15, 0.20, 0.30, 0.40]
    sweep_rows = []
    for a in alphas:
        wm_img, k = embed_watermark(host, watermark, alpha=a)
        p = psnr(host, wm_img)
        attacked = ATTACK_SUITE["JPEG Q=50"](wm_img)
        ext = extract_watermark(attacked, k)
        nc = normalized_correlation(watermark, ext)
        sweep_rows.append({"alpha": a, "PSNR": p, "NC_after_JPEG50": nc})
    sweep_df = pd.DataFrame(sweep_rows)
    sweep_df.to_csv(os.path.join(RESULTS_DIR, "alpha_sweep.csv"), index=False)

    fig, ax1 = plt.subplots(figsize=(8, 5.5))
    ax2 = ax1.twinx()
    ax1.plot(sweep_df["alpha"], sweep_df["PSNR"], "o-", color="#2980b9", label="PSNR (imperceptibility)")
    ax2.plot(sweep_df["alpha"], sweep_df["NC_after_JPEG50"], "s-", color="#e67e22", label="NC after JPEG Q=50 (robustness)")
    ax1.set_xlabel("Embedding strength (alpha)")
    ax1.set_ylabel("PSNR (dB)", color="#2980b9")
    ax2.set_ylabel("NC after JPEG-50 attack", color="#e67e22")
    ax1.set_title("Imperceptibility vs. Robustness Trade-off")
    fig.legend(loc="upper center", bbox_to_anchor=(0.5, 0.02), ncol=2)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "alpha_tradeoff.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)

    summary = {
        "alpha_used_main_experiment": alpha,
        "hosts": list(hosts.keys()),
        "num_attacks_tested": len(ATTACK_SUITE),
        "mean_watermarked_psnr_db": round(df["Watermarked PSNR (dB)"].mean(), 3),
        "mean_watermarked_ssim": round(df["Watermarked SSIM"].mean(), 4),
        "mean_nc_all_attacks": round(df["Extracted NC"].mean(), 4),
        "attacks_with_NC_above_0.75": int((df["Extracted NC"] > 0.75).sum()),
        "attacks_total_rows": len(df),
    }
    with open(os.path.join(RESULTS_DIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print("\nSUMMARY:", json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
