"""
benchmark_tech.py
=================
Controlled comparison of the project against established technologies.

Part A  (component level)  - the *same* operation executed with different
        libraries on identical input: DCT, SVD, Haar DWT, JPEG round-trip,
        median / Gaussian filtering, rotation, rescaling, histogram
        equalisation, PSNR.  Reports median time (warm-up, repeats, single
        thread, in-memory, I/O excluded) and numerical agreement with the
        project's own implementation.
Part B  (scheme level)     - the project's global DWT-DCT-SVD scheme against
        (i) the open-source `blind-watermark` package (block DWT-DCT-SVD, blind),
        (ii) a spatial LSB baseline and (iii) an 8x8 block-DCT baseline, all
        carrying the same 4095-bit payload (the 64x64 logo, last bit dropped
        because blind-watermark needs strictly fewer bits than its 4096 blocks).

    python benchmark_tech.py            # writes results/tech_*.csv, tech_summary.json, figures
"""

from __future__ import annotations

import os
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import io
import json
import shutil
import subprocess
import sys
import tempfile
import time
import warnings

import cv2
import numpy as np
import pandas as pd
import pywt
import scipy
import scipy.fft
import scipy.linalg
import skimage
from PIL import Image, ImageFilter
from scipy import ndimage
from scipy.fftpack import dct as _dct
from skimage import exposure, filters as skfilters, transform as sktransform
from skimage.metrics import peak_signal_noise_ratio as sk_psnr

from attacks import make_attack_suite
from logo import make_watermark_logo
from metrics import psnr
from watermark_core import dct2, embed_watermark, extract_watermark

warnings.filterwarnings("ignore")
cv2.setNumThreads(1)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
RES = os.path.join(ROOT, "results")
VIS = os.path.join(ROOT, "visualizations")
DATA = os.path.join(ROOT, "data")


def load(iid):
    return np.asarray(Image.open(os.path.join(DATA, "original", iid + ".png")), dtype=np.float64)


def tmed(fn, repeats=9, warm=2):
    for _ in range(warm):
        fn()
    ts = []
    for _ in range(repeats):
        t = time.perf_counter()
        fn()
        ts.append((time.perf_counter() - t) * 1e3)
    return float(np.median(ts)), float(np.percentile(ts, 25)), float(np.percentile(ts, 75))


def have(cmd):
    return shutil.which(cmd) is not None


# ---------------------------------------------------------------------------
# Part A: component-level
# ---------------------------------------------------------------------------

def dct_matrix(n):
    k = np.arange(n)[:, None]; i = np.arange(n)[None, :]
    c = np.sqrt(2.0 / n) * np.cos(np.pi * (2 * i + 1) * k / (2 * n))
    c[0] /= np.sqrt(2)
    return c


def haar_numpy(a):
    a00, a01, a10, a11 = a[0::2, 0::2], a[0::2, 1::2], a[1::2, 0::2], a[1::2, 1::2]
    return (a00 + a01 + a10 + a11) / 2.0


def jpeg_pillow(a, q=50):
    b = io.BytesIO(); Image.fromarray(a.astype(np.uint8)).save(b, "JPEG", quality=q); n = b.tell(); b.seek(0)
    return np.array(Image.open(b)).astype(np.float64), n


def jpeg_cv2(a, q=50):
    ok, buf = cv2.imencode(".jpg", a.astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, q])
    return cv2.imdecode(buf, cv2.IMREAD_GRAYSCALE).astype(np.float64), len(buf)


def jpeg_magick(a, q=50, tmp=None):
    src, dst = os.path.join(tmp, "in.png"), os.path.join(tmp, "out.jpg")
    Image.fromarray(a.astype(np.uint8)).save(src)
    subprocess.run(["convert", src, "-quality", str(q), dst], check=True)
    return np.array(Image.open(dst).convert("L")).astype(np.float64), os.path.getsize(dst)


def rot_skimage(a):
    return sktransform.rotate(a / 255.0, 15, resize=False, mode="edge") * 255.0


def rot_cv2(a):
    h, w = a.shape
    M = cv2.getRotationMatrix2D(((w - 1) / 2, (h - 1) / 2), 15, 1.0)
    return cv2.warpAffine(a, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def rot_pillow(a):
    return np.array(Image.fromarray(a.astype(np.uint8)).rotate(15, resample=Image.BILINEAR)).astype(np.float64)


def scale_skimage(a):
    s = sktransform.resize(a, (a.shape[0] // 2, a.shape[1] // 2), anti_aliasing=True, preserve_range=True)
    return sktransform.resize(s, a.shape, anti_aliasing=True, preserve_range=True)


def scale_cv2(a):
    s = cv2.resize(a, (a.shape[1] // 2, a.shape[0] // 2), interpolation=cv2.INTER_AREA)
    return cv2.resize(s, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_LINEAR)


def scale_pillow(a):
    im = Image.fromarray(a.astype(np.uint8))
    s = im.resize((a.shape[1] // 2, a.shape[0] // 2), Image.BILINEAR, reducing_gap=None)
    return np.array(s.resize(im.size, Image.BILINEAR)).astype(np.float64)


def part_a(images):
    tmp = tempfile.mkdtemp()
    rows = []
    h512 = images[0]
    ll = h512[:256, :256].copy()
    u8 = h512.astype(np.uint8)
    C = dct_matrix(256)

    ops = {
        "2-D DCT-II 256x256": [
            ("scipy.fftpack.dct (project)", lambda: dct2(ll), "ref"),
            ("scipy.fft.dctn", lambda: scipy.fft.dctn(ll, norm="ortho"), ""),
            ("cv2.dct", lambda: cv2.dct(ll), ""),
            ("NumPy matrix C.A.C^T", lambda: C @ ll @ C.T, ""),
        ],
        "SVD 256x256": [
            ("numpy.linalg.svd (project)", lambda: np.linalg.svd(ll, full_matrices=False)[1], "ref"),
            ("scipy.linalg.svd (gesdd)", lambda: scipy.linalg.svd(ll, full_matrices=False, check_finite=False)[1], ""),
            ("scipy.linalg.svd (gesvd)", lambda: scipy.linalg.svd(ll, full_matrices=False, lapack_driver="gesvd", check_finite=False)[1], ""),
            ("cv2.SVDecomp", lambda: cv2.SVDecomp(ll)[0].ravel(), ""),
        ],
        "Haar DWT level-1 (LL) 512x512": [
            ("PyWavelets dwt2 (project)", lambda: pywt.dwt2(h512, "haar")[0], "ref"),
            ("NumPy slicing", lambda: haar_numpy(h512), ""),
        ],
        "JPEG round-trip Q=50, 512x512": [
            ("Pillow (project)", lambda: jpeg_pillow(h512)[0], "ref"),
            ("OpenCV imencode/imdecode", lambda: jpeg_cv2(h512)[0], ""),
        ] + ([("ImageMagick convert (process + file I/O)", lambda: jpeg_magick(h512, tmp=tmp)[0], "io")] if have("convert") else []),
        "Median filter 3x3": [
            ("scipy.ndimage (project)", lambda: ndimage.median_filter(h512, size=3), "ref"),
            ("cv2.medianBlur (uint8)", lambda: cv2.medianBlur(u8, 3), ""),
            ("skimage.filters.median (uint8)", lambda: skfilters.median(u8, np.ones((3, 3), bool)), ""),
        ],
        "Gaussian blur sigma=1.5": [
            ("scipy.ndimage (project)", lambda: ndimage.gaussian_filter(h512, 1.5), "ref"),
            ("cv2.GaussianBlur", lambda: cv2.GaussianBlur(h512, (0, 0), 1.5, borderType=cv2.BORDER_REFLECT), ""),
            ("skimage.filters.gaussian", lambda: skfilters.gaussian(h512, sigma=1.5, preserve_range=True), ""),
        ],
        "Rotation 15 deg (bilinear)": [
            ("skimage.transform.rotate (project)", lambda: rot_skimage(h512), "ref"),
            ("cv2.warpAffine", lambda: rot_cv2(h512), ""),
            ("Pillow Image.rotate", lambda: rot_pillow(h512), ""),
        ],
        "Down/up-scale 0.5x": [
            ("skimage.transform.resize (project)", lambda: scale_skimage(h512), "ref"),
            ("cv2.resize (AREA down, LINEAR up)", lambda: scale_cv2(h512), ""),
            ("Pillow resize (BILINEAR)", lambda: scale_pillow(h512), ""),
        ],
        "Histogram equalisation": [
            ("skimage.exposure.equalize_hist (project)", lambda: exposure.equalize_hist(h512 / 255.0) * 255.0, "ref"),
            ("cv2.equalizeHist (uint8)", lambda: cv2.equalizeHist(u8).astype(np.float64), ""),
        ],
        "PSNR 512x512": [
            ("skimage.metrics (project)", lambda: sk_psnr(h512, h512 + 1.0, data_range=255), "ref"),
            ("cv2.PSNR", lambda: cv2.PSNR(h512, h512 + 1.0), ""),
            ("NumPy formula", lambda: 10 * np.log10(255 ** 2 / np.mean((h512 - (h512 + 1.0)) ** 2)), ""),
        ],
    }
    for op, variants in ops.items():
        ref = np.asarray(variants[0][1]())
        for label, fn, tag in variants:
            out = np.asarray(fn())
            med, q1, q3 = tmed(fn)
            row = dict(operation=op, implementation=label, median_ms=med, q25_ms=q1, q75_ms=q3,
                       includes_process_and_io=(tag == "io"))
            if out.shape == ref.shape and out.size > 1:
                if op.startswith("Rotation"):
                    sl = (slice(128, 384), slice(128, 384))   # compare the interior only (border handling differs)
                    d = out[sl] - ref[sl]
                    row["agreement"] = "PSNR %.1f dB (interior)" % (10 * np.log10(255 ** 2 / max(np.mean(d ** 2), 1e-12)))
                elif op.startswith("SVD") or op.startswith("2-D DCT"):
                    scale = max(np.abs(ref).max(), 1e-12)
                    row["agreement"] = "max rel. diff %.1e" % (np.abs(out - ref).max() / scale)
                elif op.startswith("Haar"):
                    row["agreement"] = "max abs diff %.1e" % np.abs(out - ref).max()
                else:
                    d = out.astype(np.float64) - ref.astype(np.float64)
                    mse = np.mean(d ** 2)
                    row["agreement"] = "identical" if mse == 0 else "PSNR %.1f dB" % (10 * np.log10(255 ** 2 / mse))
            else:
                row["agreement"] = "%.4f vs %.4f" % (float(np.ravel(out)[0]), float(np.ravel(ref)[0]))
            rows.append(row)
    # extra facts for JPEG
    j = {"Pillow": jpeg_pillow(h512)[1], "OpenCV": jpeg_cv2(h512)[1]}
    if have("convert"):
        j["ImageMagick"] = jpeg_magick(h512, tmp=tmp)[1]
    shutil.rmtree(tmp, ignore_errors=True)
    return pd.DataFrame(rows), j


# ---------------------------------------------------------------------------
# Part B: scheme-level
# ---------------------------------------------------------------------------

NB = 4095  # payload bits


def bits_to_logo(bits):
    b = np.zeros(4096); b[:NB] = np.asarray(bits[:NB], dtype=float)
    return b.reshape(64, 64) * 255.0


class Scheme:
    name = ""
    blind = None
    needs = ""


class OursScheme(Scheme):
    name = "Project: global DWT-DCT-SVD"
    blind = False
    needs = "owner's key (S_orig, Uw, Vw), ~2.1 MB per image"

    def __init__(self, alpha=0.10):
        self.alpha = alpha
        self.logo = make_watermark_logo()

    def embed(self, host):
        w, self.key = embed_watermark(host, self.logo, alpha=self.alpha)
        return w

    def extract(self, img):
        return extract_watermark(img, self.key) > 127.5


class LSBScheme(Scheme):
    name = "Baseline: spatial LSB"
    blind = True
    needs = "payload length only"

    def __init__(self, bits):
        self.bits = np.asarray(bits[:NB], dtype=np.uint8)

    def embed(self, host):
        flat = np.rint(host).astype(np.uint8).flatten()
        flat[:NB] = (flat[:NB] & 0xFE) | self.bits
        return flat.reshape(host.shape).astype(np.float64)

    def extract(self, img):
        flat = np.clip(np.rint(img), 0, 255).astype(np.uint8).flatten()
        return bits_to_logo(flat[:NB] & 1) > 127.5


class BlockDCTScheme(Scheme):
    """8x8 block DCT; bit = sign of (c[4,3] - c[3,4]) forced to differ by >= delta (Koch-Zhao style)."""
    name = "Baseline: 8x8 block DCT"
    blind = True
    needs = "payload length only"

    def __init__(self, bits, delta=24.0):
        self.bits = np.asarray(bits[:NB], dtype=np.uint8)
        self.delta = delta
        n = 8
        k = np.arange(n)[:, None]; i = np.arange(n)[None, :]
        c = np.sqrt(2.0 / n) * np.cos(np.pi * (2 * i + 1) * k / (2 * n)); c[0] /= np.sqrt(2)
        self.C = c

    def embed(self, host):
        out = host.astype(np.float64).copy()
        H, W = host.shape
        idx = 0
        for by in range(0, H, 8):
            for bx in range(0, W, 8):
                if idx >= NB:
                    break
                blk = out[by:by + 8, bx:bx + 8]
                d = self.C @ blk @ self.C.T
                a, b = d[4, 3], d[3, 4]
                m = (a + b) / 2
                if self.bits[idx]:
                    d[4, 3], d[3, 4] = m + self.delta / 2, m - self.delta / 2
                else:
                    d[4, 3], d[3, 4] = m - self.delta / 2, m + self.delta / 2
                out[by:by + 8, bx:bx + 8] = self.C.T @ d @ self.C
                idx += 1
        return np.clip(out, 0, 255)

    def extract(self, img):
        H, W = img.shape
        bits = []
        for by in range(0, H, 8):
            for bx in range(0, W, 8):
                if len(bits) >= NB:
                    break
                d = self.C @ img[by:by + 8, bx:bx + 8] @ self.C.T
                bits.append(1 if d[4, 3] > d[3, 4] else 0)
        return bits_to_logo(bits) > 127.5


class BlindWMScheme(Scheme):
    name = "blind-watermark 0.4.4 (block DWT-DCT-SVD)"
    blind = True
    needs = "two integer passwords + payload length"

    def __init__(self, bits):
        from blind_watermark import WaterMark
        self.WaterMark = WaterMark
        self.bits = np.asarray(bits[:NB], dtype=bool)

    def embed(self, host):
        bwm = self.WaterMark(password_img=1, password_wm=1, processes=1)
        bwm.read_img(img=np.dstack([host.astype(np.uint8)] * 3))
        bwm.read_wm(self.bits, mode="bit")
        e = bwm.embed()
        return np.clip(np.rint(e), 0, 255)          # 3-channel (YUV-domain embedding), kept as 3 channels

    def extract(self, img3):
        bwm = self.WaterMark(password_img=1, password_wm=1, processes=1)
        ex = bwm.extract(embed_img=np.clip(np.rint(img3), 0, 255).astype(np.uint8), wm_shape=NB, mode="bit")
        return bits_to_logo(np.asarray(ex) > 0.5) > 127.5


def channelwise(fn, img):
    """Apply a greyscale attack to each channel of a (H,W,3) image."""
    if img.ndim == 2:
        return fn(img)
    return np.stack([fn(img[..., c]) for c in range(img.shape[2])], axis=-1)


def luma(img):
    return img if img.ndim == 2 else cv2.cvtColor(img.astype(np.float32), cv2.COLOR_BGR2GRAY).astype(np.float64)


def part_b(ids, attacks):
    logo = make_watermark_logo()
    bits = (logo.flatten() > 127)[:NB]
    ref_logo = bits_to_logo(bits)
    rows = []
    for k, iid in enumerate(ids):
        host = load(iid)
        suite = make_attack_suite(777 + k)
        schemes = [OursScheme(), BlindWMScheme(bits), LSBScheme(bits), BlockDCTScheme(bits)]
        for sch in schemes:
            try:
                t0 = time.perf_counter(); w = sch.embed(host); t_emb = (time.perf_counter() - t0) * 1e3
                wq = np.clip(np.rint(w), 0, 255)
                p = psnr(host, luma(wq))
            except Exception as exc:  # noqa: BLE001
                rows.append(dict(image_id=iid, scheme=sch.name, attack="(embed)", status=f"error: {exc}"))
                continue
            for an in attacks:
                row = dict(image_id=iid, scheme=sch.name, attack=an, psnr_db=p, t_embed_ms=t_emb, status="ok")
                try:
                    att = channelwise(suite[an], wq)
                    t0 = time.perf_counter(); ex = sch.extract(att); row["t_extract_ms"] = (time.perf_counter() - t0) * 1e3
                    ex_img = ex.astype(np.float64) * 255.0
                    row["ber"] = float(np.mean((ex_img > 127.5) != (ref_logo > 127.5)))
                    a, b = ref_logo.flatten(), ex_img.flatten()
                    den = np.sqrt((a ** 2).sum()) * np.sqrt((b ** 2).sum())
                    row["nc"] = float((a * b).sum() / den) if den else 0.0
                except Exception as exc:  # noqa: BLE001
                    row.update(status=f"error: {type(exc).__name__}: {exc}")
                rows.append(row)
        print("scheme comparison: image", k + 1, "/", len(ids), flush=True)
    return pd.DataFrame(rows)


def tune_delta(ids):
    """Choose the block-DCT strength so that its mean PSNR matches the project's (~36 dB)."""
    logo = make_watermark_logo(); bits = (logo.flatten() > 127)[:NB]
    target = np.mean([psnr(load(i), OursScheme().embed(load(i))) for i in ids])
    best = None
    for d in (8, 12, 16, 20, 24, 28, 32, 40, 48):
        p = np.mean([psnr(load(i), np.rint(BlockDCTScheme(bits, d).embed(load(i)))) for i in ids])
        if best is None or abs(p - target) < abs(best[1] - target):
            best = (d, p)
    return best, target


def main():
    os.makedirs(RES, exist_ok=True)
    meta = pd.read_csv(os.path.join(DATA, "metadata.csv"))
    real = meta[meta.is_synthetic == 0].image_id.tolist()
    rng = np.random.default_rng(20260713)

    # ---- Part A
    comp_ids = list(rng.choice(real, 3, replace=False))
    parts = []
    for iid in comp_ids:
        df, jsz = part_a([load(iid)])
        df["image_id"] = iid
        parts.append(df)
    A = pd.concat(parts)
    Agg = A.groupby(["operation", "implementation"], sort=False).agg(
        median_ms=("median_ms", "median"), q25_ms=("q25_ms", "median"), q75_ms=("q75_ms", "median"),
        includes_process_and_io=("includes_process_and_io", "first"), agreement=("agreement", "first")).reset_index()
    ref = Agg.groupby("operation", sort=False).median_ms.transform("first")
    Agg["speed_vs_project"] = ref / Agg.median_ms          # >1 = faster than the project's implementation
    Agg.round(4).to_csv(os.path.join(RES, "tech_benchmark_components.csv"), index=False)
    print(Agg.round(3).to_string())

    # ---- Part B
    sample = list(rng.choice(real, 30, replace=False))
    tune_ids = sample[:5]
    (delta, p_d), p_target = tune_delta(tune_ids)
    print("block-DCT delta tuned to", delta, "PSNR", round(p_d, 2), "target", round(p_target, 2))
    BlockDCTScheme.__init__.__defaults__ = (delta,)
    attacks = ["No Attack", "JPEG Q=50", "JPEG Q=20", "Gaussian Noise (var=0.02)", "Median Filter 3x3",
               "Gaussian Blur (sigma=1.5)", "Rotation 5 deg", "Cropping 25%", "Scaling 0.5x"]
    B = part_b(sample, attacks)
    B.to_csv(os.path.join(RES, "tech_benchmark_schemes_raw.csv"), index=False)
    ok = B[B.status == "ok"]
    S = ok.groupby(["scheme", "attack"], sort=False).agg(mean_ber=("ber", "mean"), median_ber=("ber", "median"),
                                                         mean_nc=("nc", "mean"), psnr_db=("psnr_db", "mean"),
                                                         t_embed_ms=("t_embed_ms", "median"), t_extract_ms=("t_extract_ms", "median"),
                                                         ber_le_0_10=("ber", lambda x: (x <= 0.10).mean()), n=("ber", "size")).reset_index()
    S.round(4).to_csv(os.path.join(RES, "tech_benchmark_schemes.csv"), index=False)
    print(S.round(3).to_string())

    env = {"python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__, "scikit-image": skimage.__version__,
           "opencv": cv2.__version__, "Pillow": __import__("PIL").__version__, "PyWavelets": pywt.__version__,
           "blind-watermark": __import__("importlib.metadata", fromlist=["version"]).version("blind-watermark"),
           "ImageMagick": (subprocess.run(["convert", "-version"], capture_output=True, text=True).stdout.splitlines() or [""])[0] if have("convert") else None,
           "ffmpeg": (subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout.splitlines() or [""])[0] if have("ffmpeg") else None,
           "cpu_threads_used": 1, "repeats": 9, "warmup": 2, "component_images": comp_ids, "scheme_images": sample,
           "jpeg_bytes_example": jsz, "blockdct_delta": delta, "blockdct_psnr": p_d, "project_psnr_tune": p_target}
    json.dump(env, open(os.path.join(RES, "tech_summary.json"), "w"), indent=2, default=str)


if __name__ == "__main__":
    main()
