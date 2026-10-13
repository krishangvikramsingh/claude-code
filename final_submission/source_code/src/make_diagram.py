import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "visualizations")


def box(ax, xy, w, h, text, fc="#eaf2f8", ec="#2874a6", fontsize=9.5):
    x, y = xy
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.02",
                        fc=fc, ec=ec, linewidth=1.6)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
             fontsize=fontsize, wrap=True)


def arrow(ax, p1, p2, color="#333333"):
    a = FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=14,
                         color=color, linewidth=1.5)
    ax.add_patch(a)


def embedding_diagram():
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.set_xlim(0, 11); ax.set_ylim(0, 4.2); ax.axis("off")
    ax.set_title("Watermark Embedding Pipeline", fontsize=13, fontweight="bold", pad=16)

    steps = [
        "Host Image\n(512x512, grayscale)",
        "2D DWT\n(Haar, 1-level)\n-> LL sub-band",
        "2-D DCT\nof LL sub-band\n(global)",
        "SVD\nA = U.S.V^T",
        "S' = S + alpha*Sw\n(Sw: singular\nvalues of logo)",
        "Inverse DCT\n+ Inverse DWT",
        "Watermarked\nImage",
    ]
    n = len(steps)
    w, h = 1.35, 1.5
    gap = (11 - n * w) / (n + 1)
    x = gap
    y = 1.1
    centers = []
    for s in steps:
        box(ax, (x, y), w, h, s, fontsize=9.2)
        centers.append((x, x + w))
        x += w + gap
    for i in range(n - 1):
        arrow(ax, (centers[i][1], y + h / 2), (centers[i + 1][0], y + h / 2))

    # watermark input branch
    box(ax, (centers[4][0] - 0.1, y + h + 0.55), 1.5, 0.85, "Watermark\nLogo (64x64)", fc="#fdebd0", ec="#b9770e", fontsize=9.2)
    arrow(ax, (centers[4][0] + 0.6, y + h + 0.55), (centers[4][0] + 0.6, y + h), color="#b9770e")

    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "diagram_embedding.png"), dpi=170)
    plt.close(fig)


def extraction_diagram():
    fig, ax = plt.subplots(figsize=(11, 4.0))
    ax.set_xlim(0, 11); ax.set_ylim(0, 4.0); ax.axis("off")
    ax.set_title("Watermark Extraction Pipeline (non-blind, key-based)", fontsize=13, fontweight="bold", pad=16)

    steps = [
        "Received Image\n(possibly attacked:\nJPEG / noise / crop /\nrotate / scale ...)",
        "2D DWT\n-> LL sub-band",
        "2-D DCT\n+ SVD -> S_att",
        "Sw' = (S_att - S_orig)\n/ alpha",
        "Reconstruct:\nUw . Sw' . Vw^T",
        "Extracted\nWatermark",
    ]
    n = len(steps)
    w, h = 1.55, 1.5
    gap = (11 - n * w) / (n + 1)
    x = gap
    y = 0.9
    centers = []
    for s in steps:
        box(ax, (x, y), w, h, s, fontsize=9.2, fc="#eafaf1", ec="#1e8449")
        centers.append((x, x + w))
        x += w + gap
    for i in range(n - 1):
        arrow(ax, (centers[i][1], y + h / 2), (centers[i + 1][0], y + h / 2))

    box(ax, (centers[3][0] - 0.3, y + h + 0.5), 2.0, 0.75,
        "Embedding Key\n{S_orig, Uw, Vw, alpha, shapes}", fc="#f9ebea", ec="#943126", fontsize=8.6)
    arrow(ax, (centers[3][0] + 0.7, y + h + 0.5), (centers[3][0] + 0.7, y + h), color="#943126")

    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "diagram_extraction.png"), dpi=170)
    plt.close(fig)


if __name__ == "__main__":
    embedding_diagram()
    extraction_diagram()
    print("done")
