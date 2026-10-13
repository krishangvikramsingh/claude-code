"""
run_batch_experiment.py
=======================
Batch evaluation of the hybrid DWT-DCT-SVD watermarking scheme on the
100-image dataset (``data/original``).

    python run_batch_experiment.py [--config config.json] [--workers 4]

Experiments
-----------
E1  imperceptibility  : PSNR / SSIM of every watermarked image (alpha = config.alpha)
E2  robustness        : 15 conditions (14 attacks + an unattacked reference) x 2 protocols ("uint8": watermarked image is first
                        rounded to 8 bit as it would be when saved to disk; "float":
                        the original submission's protocol, attacks act on floats)
E3  alpha sweep       : PSNR / NC / ZNCC / BER vs alpha for JPEG Q=50, Gaussian noise,
                        Gaussian blur and 5-degree rotation
E4  false-positive controls (see watermark_core docstring):
      a) unwatermarked *other* host, key of image i
      b) watermarked *other* host (logo A embedded), key of image i
      c) same host watermarked with a DIFFERENT logo, decoded with logo-A key
      d) same host, unwatermarked, own key (degenerate by construction)

Every operation is wrapped so that a failure is recorded (status / error text)
instead of aborting the run; outputs are re-opened and validated.
"""

from __future__ import annotations

import os

# one BLAS thread per worker: reproducible timings, no oversubscription
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import concurrent.futures as cf
import json
import logging
import platform
import resource
import sys
import time

import numpy as np
import pandas as pd

from attacks import ATTACK_FAMILY, ATTACK_NAMES, make_attack_suite
from image_io import save_gray_png, verify_png
from logo import make_watermark_logo
from metrics import bit_error_rate, normalized_correlation, psnr, ssim, zero_normalized_correlation
from watermark_core import embed_watermark, extract_watermark

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = logging.getLogger("batch")

DEFAULT_CONFIG = {
    "alpha": 0.10,
    "image_size": 512,
    "logo_size": 64,
    "logo_text": "CYBERION",
    "other_logos": ["OTHERLOGO", "OWNER-B"],
    "protocols": ["uint8", "float"],
    "primary_protocol": "uint8",
    "base_seed": 20260713,
    "alphas": [0.02, 0.05, 0.08, 0.10, 0.15, 0.20, 0.30, 0.40],
    "sweep_attacks": ["JPEG Q=50", "Gaussian Noise (var=0.02)", "Gaussian Blur (sigma=1.5)", "Rotation 5 deg"],
    "n_controls_per_image": 5,
    "nc_threshold": 0.75,
    "data_dir": "../../data",
    "results_dir": "../../results",
    "outputs_dir": "../../outputs",
}


def _t():
    return time.perf_counter()


def _load_host(data_dir, image_id):
    from PIL import Image
    a = np.asarray(Image.open(os.path.join(data_dir, "original", image_id + ".png")), dtype=np.float64)
    if a.ndim != 2:
        raise ValueError(f"{image_id}: expected greyscale, got shape {a.shape}")
    return a


def _quantize(a):
    return np.clip(np.rint(a), 0, 255)


# ---------------------------------------------------------------------------
# per-image worker
# ---------------------------------------------------------------------------

def process_image(task):
    """Run E1-E4 for one image. Returns plain Python data (picklable)."""
    idx, image_id, cfg, others = task
    data_dir = cfg["data_dir"]
    rows_att, rows_ctl, rows_sw = [], [], []
    rec = {"image_id": image_id, "status": "ok", "error": ""}
    try:
        host = _load_host(data_dir, image_id)
        logo = make_watermark_logo(cfg["logo_size"], cfg["logo_text"])
        alpha = cfg["alpha"]

        # ---- E1: embedding ------------------------------------------------
        t0 = _t()
        wm_float, key = embed_watermark(host, logo, alpha=alpha)
        rec["t_embed_ms"] = (_t() - t0) * 1e3
        wm_u8 = _quantize(wm_float)
        out_path = os.path.join(cfg["outputs_dir"], "watermarked", f"{image_id}_wm.png")
        save_gray_png(wm_u8, out_path)
        rec["output_valid"] = bool(verify_png(out_path, host.shape))
        rec["psnr_float_db"] = psnr(host, wm_float)
        rec["ssim_float"] = ssim(host, wm_float)
        rec["psnr_db"] = psnr(host, wm_u8)          # primary: image as stored on disk
        rec["ssim"] = ssim(host, wm_u8)
        rec["max_abs_diff"] = float(np.abs(host - wm_u8).max())
        rec["mean_abs_diff"] = float(np.abs(host - wm_u8).mean())
        rec["key_bytes"] = int(sum(v.nbytes for v in key.values() if isinstance(v, np.ndarray)))

        # ---- E2: attacks ---------------------------------------------------
        suite = make_attack_suite(cfg["base_seed"] + 100 * idx)
        for protocol in cfg["protocols"]:
            base = wm_u8 if protocol == "uint8" else wm_float
            for name in ATTACK_NAMES:
                row = {"image_id": image_id, "protocol": protocol, "attack": name,
                       "family": ATTACK_FAMILY[name], "status": "ok", "error": ""}
                try:
                    t0 = _t()
                    attacked = suite[name](base)
                    row["t_attack_ms"] = (_t() - t0) * 1e3
                    t0 = _t()
                    ext = extract_watermark(attacked, key)
                    row["t_extract_ms"] = (_t() - t0) * 1e3
                    row["nc"] = normalized_correlation(logo, ext)
                    row["zncc"] = zero_normalized_correlation(logo, ext)
                    row["ber"] = bit_error_rate(logo, ext)
                except Exception as exc:  # noqa: BLE001
                    row.update(status="error", error=f"{type(exc).__name__}: {exc}")
                rows_att.append(row)

        # ---- E3: alpha sweep (uint8 protocol), several attacks -----------------
        sweep_suite = make_attack_suite(cfg["base_seed"] + 100 * idx + 50)
        for a in cfg["alphas"]:
            try:
                w, k = embed_watermark(host, logo, alpha=a)
                wq = _quantize(w)
                p_a, s_a = psnr(host, wq), ssim(host, wq)
            except Exception as exc:  # noqa: BLE001
                rows_sw.append({"image_id": image_id, "alpha": a, "attack": "(embed)", "status": "error",
                                "error": f"{type(exc).__name__}: {exc}"})
                continue
            for an in ["No Attack"] + list(cfg["sweep_attacks"]):
                row = {"image_id": image_id, "alpha": a, "attack": an, "psnr_db": p_a, "ssim": s_a,
                       "status": "ok", "error": ""}
                try:
                    ext = extract_watermark(sweep_suite[an](wq), k)
                    row["nc"] = normalized_correlation(logo, ext)
                    row["zncc"] = zero_normalized_correlation(logo, ext)
                    row["ber"] = bit_error_rate(logo, ext)
                except Exception as exc:  # noqa: BLE001
                    row.update(status="error", error=f"{type(exc).__name__}: {exc}")
                rows_sw.append(row)

        # ---- E4: controls ---------------------------------------------------
        def ctl(kind, other, ncv, berv, zz, extra=""):
            rows_ctl.append({"image_id": image_id, "control": kind, "other": other,
                             "nc": ncv, "ber": berv, "zncc": zz, "note": extra})

        # (genuine reference, no attack, uint8)
        ext = extract_watermark(wm_u8, key)
        ctl("genuine (own key, no attack)", image_id, normalized_correlation(logo, ext), bit_error_rate(logo, ext), zero_normalized_correlation(logo, ext))
        # (d) degenerate: own unwatermarked host with own key
        ext = extract_watermark(host, key)
        ctl("d: own host unwatermarked, own key", image_id, normalized_correlation(logo, ext), bit_error_rate(logo, ext), zero_normalized_correlation(logo, ext),
            extra="degenerate: S_att == S_original so Sw' = 0")
        for oid in others:
            oh = _load_host(data_dir, oid)
            ext = extract_watermark(oh, key)
            ctl("a: other host unwatermarked, key_i", oid, normalized_correlation(logo, ext), bit_error_rate(logo, ext), zero_normalized_correlation(logo, ext))
            ow, _ = embed_watermark(oh, logo, alpha=alpha)
            ext = extract_watermark(_quantize(ow), key)
            ctl("b: other host watermarked, key_i", oid, normalized_correlation(logo, ext), bit_error_rate(logo, ext), zero_normalized_correlation(logo, ext))
        for text in cfg["other_logos"]:
            logo_b = make_watermark_logo(cfg["logo_size"], text)
            wb, kb = embed_watermark(host, logo_b, alpha=alpha)
            wbq = _quantize(wb)
            ext_a = extract_watermark(wbq, key)       # decoded with logo-A key
            ext_b = extract_watermark(wbq, kb)        # decoded with its own key
            ctl("c: same host, other logo B, decoded with key A (NC vs A)", text,
                normalized_correlation(logo, ext_a), bit_error_rate(logo, ext_a), zero_normalized_correlation(logo, ext_a))
            ctl("c-ref: same host, logo B, decoded with key B (NC vs B)", text,
                normalized_correlation(logo_b, ext_b), bit_error_rate(logo_b, ext_b), zero_normalized_correlation(logo_b, ext_b))
    except Exception as exc:  # noqa: BLE001
        rec.update(status="error", error=f"{type(exc).__name__}: {exc}")
        LOG.exception("image %s failed", image_id)
    rec["peak_rss_mb"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    return rec, rows_att, rows_sw, rows_ctl


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------

def env_info():
    import PIL, pywt, scipy, skimage
    cpu = ""
    try:
        with open("/proc/cpuinfo") as f:
            cpu = next(l.split(":", 1)[1].strip() for l in f if l.startswith("model name"))
    except Exception:  # noqa: BLE001
        pass
    return {"python": sys.version.split()[0], "platform": platform.platform(), "cpu": cpu,
            "cpu_count": os.cpu_count(), "numpy": np.__version__, "scipy": scipy.__version__,
            "scikit-image": skimage.__version__, "PyWavelets": pywt.__version__, "Pillow": PIL.__version__,
            "pandas": pd.__version__}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--limit", type=int, default=None, help="process only the first N images (debug)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    cfg = dict(DEFAULT_CONFIG)
    if args.config:
        with open(args.config) as f:
            cfg.update(json.load(f))
    for k in ("data_dir", "results_dir", "outputs_dir"):
        cfg[k] = os.path.abspath(os.path.join(HERE, cfg[k]))
    os.makedirs(cfg["results_dir"], exist_ok=True)
    os.makedirs(os.path.join(cfg["outputs_dir"], "watermarked"), exist_ok=True)

    meta = pd.read_csv(os.path.join(cfg["data_dir"], "metadata.csv"))
    if args.limit:
        meta = meta.head(args.limit)
    ids = list(meta["image_id"])
    n = len(ids)
    rng = np.random.default_rng(cfg["base_seed"])
    tasks = []
    for i, iid in enumerate(ids):
        pool = [x for x in ids if x != iid]
        others = list(rng.choice(pool, size=min(cfg["n_controls_per_image"], len(pool)), replace=False))
        tasks.append((i, iid, cfg, others))

    LOG.info("processing %d images with %d worker(s)", n, args.workers)
    t_start = _t()
    results = []
    with cf.ProcessPoolExecutor(max_workers=args.workers) as ex:
        for res in ex.map(process_image, tasks):
            results.append(res)
            if len(results) % 10 == 0:
                LOG.info("  %d/%d images done", len(results), n)
    wall = _t() - t_start

    img_df = pd.DataFrame([r[0] for r in results]).sort_values("image_id")
    att_df = pd.DataFrame([row for r in results for row in r[1]])
    sw_df = pd.DataFrame([row for r in results for row in r[2]])
    ctl_df = pd.DataFrame([row for r in results for row in r[3]])
    rd = cfg["results_dir"]
    img_df.to_csv(os.path.join(rd, "results_images.csv"), index=False)
    att_df.to_csv(os.path.join(rd, "results_attacks.csv"), index=False)
    sw_df.to_csv(os.path.join(rd, "results_alpha_sweep.csv"), index=False)
    ctl_df.to_csv(os.path.join(rd, "results_controls.csv"), index=False)

    # processing status written back into the dataset metadata (merge; never drops rows)
    full = pd.read_csv(os.path.join(cfg["data_dir"], "metadata.csv"))
    st = img_df.set_index("image_id")["status"]
    att_ok = att_df.groupby("image_id")["status"].apply(lambda s: int((s == "ok").sum()))
    full["processing_status"] = full["image_id"].map(st).fillna(full.get("processing_status", "not processed"))
    full["attack_trials_ok"] = full["image_id"].map(att_ok).fillna(full.get("attack_trials_ok"))
    full["attack_trials_expected"] = len(ATTACK_NAMES) * len(cfg["protocols"])
    full.to_csv(os.path.join(cfg["data_dir"], "metadata.csv"), index=False)

    summary = {
        "config": {k: v for k, v in cfg.items() if not k.endswith("_dir")},
        "environment": env_info(),
        "images_requested": n,
        "images_ok": int((img_df["status"] == "ok").sum()),
        "watermarked_files_valid": int(img_df["output_valid"].fillna(False).sum()),
        "attack_trials_total": int(len(att_df)),
        "attack_trials_ok": int((att_df["status"] == "ok").sum()),
        "attack_trials_failed": int((att_df["status"] != "ok").sum()),
        "alpha_sweep_rows_ok": int((sw_df["status"] == "ok").sum()),
        "alpha_sweep_rows_total": int(len(sw_df)),
        "control_rows": int(len(ctl_df)),
        "wall_time_s": round(wall, 1),
        "workers": args.workers,
        "peak_rss_mb_max_over_workers": round(float(img_df["peak_rss_mb"].max()), 1),
    }
    with open(os.path.join(rd, "run_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    LOG.info("summary: %s", json.dumps({k: v for k, v in summary.items() if k not in ("config", "environment")}))
    return 0 if summary["attack_trials_failed"] == 0 and summary["images_ok"] == n else 1


if __name__ == "__main__":
    sys.exit(main())
