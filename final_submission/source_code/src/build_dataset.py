"""
build_dataset.py
================
Reproducibly assemble the 100-image evaluation set.

    python build_dataset.py [--out ../../data] [--target 100]

Steps
-----
1. Download every entry of ``dataset_manifest.REAL_IMAGES`` (cached in
   ``<out>/source_images``; SHA-256 recorded).  Unreachable sources are logged
   and skipped - nothing is invented to replace them.
2. Standardise (see ``image_io``) to 512x512 8-bit greyscale PNG.
3. Reject near-duplicates (64-bit difference hash, Hamming distance <= 6).
4. Top the set up to ``--target`` images with clearly *labelled synthetic*
   control images (fixed seeds).  Synthetic images are never presented as
   real-world data; they form a separate stratum in every table.
5. Write ``original/image_XXX.png``, ``metadata.csv`` and a build log.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import sys
import time
import urllib.parse
import urllib.request

import numpy as np
from PIL import Image
from scipy import ndimage

from dataset_manifest import REAL_IMAGES
from image_io import ImageLoadError, load_gray_square, save_gray_png

LOG = logging.getLogger("build_dataset")
RAW = "https://raw.githubusercontent.com/"
SIZE = 512


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dhash64(arr: np.ndarray) -> int:
    """64-bit difference hash of a greyscale array."""
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).resize((9, 8), Image.LANCZOS)
    a = np.asarray(im, dtype=np.int16)
    bits = (a[:, 1:] > a[:, :-1]).flatten()
    return int("".join("1" if b else "0" for b in bits), 2)


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def download(rel: str, dest: str, retries: int = 3) -> bool:
    url = RAW + rel
    last = None
    for k in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "ivp-watermark-build/1.0"}), timeout=60) as r:
                data = r.read()
            if not data:
                raise IOError("empty response")
            with open(dest, "wb") as f:
                f.write(data)
            return True
        except Exception as exc:  # noqa: BLE001 - log and retry
            last = exc
            time.sleep(1.5 * (k + 1))
    LOG.warning("download failed %s (%s)", url, last)
    return False


def fetch_scipy(name: str, dest: str) -> bool:
    try:
        import scipy.datasets as sd
        arr = getattr(sd, name)()
        Image.fromarray(arr).save(dest)
        return True
    except Exception as exc:  # noqa: BLE001
        LOG.warning("scipy.datasets.%s unavailable: %s", name, exc)
        return False


# ---------------------------------------------------------------------------
# synthetic control images (all deterministic, labelled as synthetic)
# ---------------------------------------------------------------------------

def _smooth_noise(rng, sigma, mean, std):
    n = ndimage.gaussian_filter(rng.standard_normal((SIZE, SIZE)), sigma)
    n = (n - n.mean()) / n.std()
    return np.clip(mean + std * n, 0, 255)


def synth_images():
    rng = np.random.default_rng(20260713)
    yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float64)
    out = []
    out.append(("syn_hgradient", "horizontal linear gradient 0-255", np.tile(np.linspace(0, 255, SIZE), (SIZE, 1))))
    r = np.hypot(xx - SIZE / 2, yy - SIZE / 2)
    out.append(("syn_radial", "radial gradient (smooth, low detail)", np.clip(255 - r * 0.7, 0, 255)))
    out.append(("syn_grating", "2-D sinusoidal grating (periodic texture)", 128 + 100 * np.sin(2 * np.pi * (xx * 9 + yy * 5) / SIZE)))
    out.append(("syn_white_noise", "white Gaussian noise, mean 128 / std 40", np.clip(128 + 40 * rng.standard_normal((SIZE, SIZE)), 0, 255)))
    out.append(("syn_lowcontrast", "smooth noise, mean 128 / std 8 (very low contrast)", _smooth_noise(rng, 6, 128, 8)))
    out.append(("syn_checker", "32-px checkerboard (hard edges)", 255.0 * (((xx // 32) + (yy // 32)) % 2)))
    out.append(("syn_dark", "smooth noise, mean 25 / std 12 (dark)", _smooth_noise(rng, 5, 25, 12)))
    out.append(("syn_bright", "smooth noise, mean 230 / std 12 (bright)", _smooth_noise(rng, 5, 230, 12)))
    # 1/f-like fractal texture
    f = np.fft.fftfreq(SIZE)
    fx, fy = np.meshgrid(f, f)
    amp = 1.0 / np.maximum(np.hypot(fx, fy), 1.0 / SIZE)
    spec = amp * np.exp(2j * np.pi * rng.random((SIZE, SIZE)))
    frac = np.real(np.fft.ifft2(spec))
    frac = (frac - frac.mean()) / frac.std()
    out.append(("syn_fractal", "1/f fractal noise texture", np.clip(128 + 45 * frac, 0, 255)))
    # random blocks scene
    scene = np.full((SIZE, SIZE), 110.0)
    for _ in range(14):
        x0, y0 = rng.integers(0, SIZE - 80, 2)
        w, h = rng.integers(40, 160, 2)
        scene[y0:y0 + h, x0:x0 + w] = rng.integers(20, 240)
    out.append(("syn_blocks", "random grey rectangles on grey background", scene))
    return out


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--out", default=os.path.join(here, "..", "..", "data"))
    ap.add_argument("--target", type=int, default=100)
    ap.add_argument("--dup-threshold", type=int, default=6)
    args = ap.parse_args()
    out = os.path.abspath(args.out)
    src_dir = os.path.join(out, "source_images")
    orig_dir = os.path.join(out, "original")
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(orig_dir, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    rows, hashes, skipped = [], [], []
    for key, rel, group, lic, note, category in REAL_IMAGES:
        ext = os.path.splitext(urllib.parse.unquote(rel))[1] or ".png"
        if rel.startswith("scipy:"):
            dest = os.path.join(src_dir, f"{key}.png")
            ok = os.path.isfile(dest) or fetch_scipy(rel.split(":", 1)[1], dest)
            url = f"scipy.datasets.{rel.split(':', 1)[1]}()"
        else:
            dest = os.path.join(src_dir, f"{key}{ext}")
            ok = os.path.isfile(dest) and os.path.getsize(dest) > 0 or download(rel, dest)
            url = RAW + rel
        if not ok:
            skipped.append((key, "download failed"))
            continue
        try:
            arr, info = load_gray_square(dest, SIZE)
        except ImageLoadError as exc:
            skipped.append((key, str(exc)))
            LOG.warning("skip %s: %s", key, exc)
            continue
        if min(info.width, info.height) < 240:
            skipped.append((key, f"too small ({info.width}x{info.height})"))
            continue
        hsh = dhash64(arr)
        dup = next((k for k, h in hashes if hamming(h, hsh) <= args.dup_threshold), None)
        if dup:
            skipped.append((key, f"near-duplicate of {dup}"))
            LOG.info("duplicate %s ~ %s", key, dup)
            continue
        hashes.append((key, hsh))
        rows.append(dict(key=key, arr=arr, url=url, group=group, lic=lic, note=note,
                         category=category, info=info, sha=sha256_file(dest),
                         fname=os.path.basename(dest), synthetic=False))

    need = args.target - len(rows)
    if need < 0:
        rows = rows[:args.target]
        need = 0
    synth = synth_images()
    if need > len(synth):
        LOG.warning("only %d synthetic generators available; dataset will have %d images",
                    len(synth), len(rows) + len(synth))
    for key, desc, arr in synth[:need]:
        rows.append(dict(key=key, arr=arr, url="generated by build_dataset.py (seeded)", group="synthetic control",
                         lic="n/a (generated)", note=desc, category="synthetic_control",
                         info=None, sha="", fname="", synthetic=True))

    meta_path = os.path.join(out, "metadata.csv")
    cols = ["image_id", "key", "original_filename", "source_group", "source_url", "repository_license",
            "rights_note", "original_width", "original_height", "original_mode", "original_format",
            "original_file_size_bytes", "source_sha256", "standardized_shape", "standardized_channels",
            "category", "is_synthetic", "mean_intensity", "contrast_std", "brightness_class",
            "contrast_class", "applicable_operations"]
    with open(meta_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for i, r in enumerate(rows, 1):
            iid = f"image_{i:03d}"
            save_gray_png(r["arr"], os.path.join(orig_dir, iid + ".png"))
            a = np.rint(r["arr"])
            mean, std = float(a.mean()), float(a.std())
            info = r["info"]
            w.writerow(dict(
                image_id=iid, key=r["key"], original_filename=r["fname"], source_group=r["group"],
                source_url=r["url"], repository_license=r["lic"], rights_note=r["note"],
                original_width=info.width if info else SIZE, original_height=info.height if info else SIZE,
                original_mode=info.mode if info else "generated", original_format=info.fmt if info else "PNG",
                original_file_size_bytes=info.file_size if info else "", source_sha256=r["sha"],
                standardized_shape=f"{SIZE}x{SIZE}", standardized_channels=1, category=r["category"],
                is_synthetic=int(r["synthetic"]), mean_intensity=round(mean, 2), contrast_std=round(std, 2),
                brightness_class="dark" if mean < 80 else ("bright" if mean > 170 else "mid"),
                contrast_class="low" if std < 35 else ("high" if std > 65 else "medium"),
                applicable_operations="embed;extract;14 attacks + reference;PSNR;SSIM;NC;BER;alpha-sweep;controls"))

    with open(os.path.join(out, "build_log.json"), "w") as f:
        json.dump({"images_written": len(rows), "real": sum(not r["synthetic"] for r in rows),
                   "synthetic": sum(r["synthetic"] for r in rows), "skipped": skipped}, f, indent=2)
    LOG.info("wrote %d images (%d real, %d synthetic); skipped %d",
             len(rows), sum(not r["synthetic"] for r in rows), sum(r["synthetic"] for r in rows), len(skipped))
    for k, why in skipped:
        LOG.info("  skipped %-16s %s", k, why)
    return 0 if len(rows) == args.target else 1


if __name__ == "__main__":
    sys.exit(main())
