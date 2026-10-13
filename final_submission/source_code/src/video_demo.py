"""
video_demo.py
=============
EXPLORATORY extension (the submitted project is image-only; video was listed as
"future scope").  Per-frame application of the same DWT-DCT-SVD scheme:

  1. read N frames from a real clip with OpenCV (cv2.VideoCapture)
  2. standardise each frame like the still images (grey, centre-crop, 512x512)
  3. embed the logo into EVERY frame with its own key (non-blind scheme => one
     key per frame; temporal redundancy is NOT exploited)
  4. re-encode the watermarked frames with a lossy codec (FFmpeg: H.264 at three
     CRF values, MJPEG), decode again, extract from every frame
  5. report frames processed, PSNR, NC/BER, bit-rate, timing

This is a feasibility test on two short clips, NOT a video-watermarking benchmark:
it does not test temporal attacks (frame dropping/re-ordering, frame-rate change),
colour video, or hardware encoders.  One naive frame-drop test shows why per-frame
keys need timestamp/index bookkeeping.

    python video_demo.py [--frames 60]
"""

from __future__ import annotations

import os
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import json
import subprocess
import tempfile
import time
import urllib.request

import cv2
import numpy as np
import pandas as pd
from PIL import Image

from logo import make_watermark_logo
from metrics import bit_error_rate, normalized_correlation, psnr
from watermark_core import embed_watermark, extract_watermark

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
RES = os.path.join(ROOT, "results")
CACHE = os.path.join(ROOT, "data", "source_videos")
CLIPS = {
    "vtest.avi": "opencv/opencv/4.x/samples/data/vtest.avi",
    "Megamind.avi": "opencv/opencv/4.x/samples/data/Megamind.avi",
}
SIZE = 512
CODECS = {
    "lossless (FFV1)":  ["-c:v", "ffv1"],
    "H.264 CRF 18":     ["-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p"],
    "H.264 CRF 23":     ["-c:v", "libx264", "-crf", "23", "-pix_fmt", "yuv420p"],
    "H.264 CRF 28":     ["-c:v", "libx264", "-crf", "28", "-pix_fmt", "yuv420p"],
    "MJPEG q=5":        ["-c:v", "mjpeg", "-q:v", "5", "-pix_fmt", "yuvj420p"],
    "MJPEG q=15":       ["-c:v", "mjpeg", "-q:v", "15", "-pix_fmt", "yuvj420p"],
}


def fetch(name):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, name)
    if not os.path.exists(p):
        urllib.request.urlretrieve("https://raw.githubusercontent.com/" + CLIPS[name], p)
    return p


def gray_square(frame_bgr):
    g = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    s = min(g.shape)
    y0, x0 = (g.shape[0] - s) // 2, (g.shape[1] - s) // 2
    g = g[y0:y0 + s, x0:x0 + s]
    return np.asarray(Image.fromarray(g).resize((SIZE, SIZE), Image.LANCZOS), dtype=np.float64)


def read_frames(path, n):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise IOError(f"cannot open {path}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frames = []
    try:
        while len(frames) < n:
            ok, f = cap.read()
            if not ok:
                break
            frames.append(gray_square(f))
    finally:
        cap.release()
    return frames, dict(fps=fps, total_frames=total, width=w, height=h)


def encode_decode(frames, codec_args, fps, tmp):
    """Pipe 8-bit frames into ffmpeg, then decode them back as raw grey frames."""
    out = os.path.join(tmp, "clip." + ("mkv" if "ffv1" in codec_args else ("avi" if "mjpeg" in codec_args else "mp4")))
    raw = b"".join(np.clip(np.rint(f), 0, 255).astype(np.uint8).tobytes() for f in frames)
    enc = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{SIZE}x{SIZE}",
                          "-r", str(fps), "-i", "-", *codec_args, out], input=raw, capture_output=True)
    if enc.returncode != 0:
        raise RuntimeError(enc.stderr.decode()[:300])
    dec = subprocess.run(["ffmpeg", "-v", "error", "-i", out, "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
    if dec.returncode != 0:
        raise RuntimeError(dec.stderr.decode()[:300])
    buf = np.frombuffer(dec.stdout, dtype=np.uint8)
    n = buf.size // (SIZE * SIZE)
    decoded = [buf[i * SIZE * SIZE:(i + 1) * SIZE * SIZE].reshape(SIZE, SIZE).astype(np.float64) for i in range(n)]
    return decoded, os.path.getsize(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=60)
    args = ap.parse_args()
    logo = make_watermark_logo()
    rows, meta = [], {}
    for clip in CLIPS:
        frames, info = read_frames(fetch(clip), args.frames)
        meta[clip] = dict(info, frames_read=len(frames))
        t0 = time.perf_counter()
        marked, keys = [], []
        for f in frames:
            w, k = embed_watermark(f, logo, alpha=0.10)
            k = {kk: vv for kk, vv in k.items() if kk not in ("U", "Vt")}   # extraction does not need U, V^T
            marked.append(np.clip(np.rint(w), 0, 255)); keys.append(k)
        t_embed = (time.perf_counter() - t0) / len(frames)
        fps = info["fps"] if info["fps"] and info["fps"] > 0 else 25
        with tempfile.TemporaryDirectory() as tmp:
            for codec, args_ in CODECS.items():
                row = dict(clip=clip, codec=codec, frames_in=len(frames), status="ok")
                try:
                    dec_wm, size_wm = encode_decode(marked, args_, fps, tmp)
                    dec_ref, size_ref = encode_decode(frames, args_, fps, tmp)
                    n = min(len(dec_wm), len(frames))
                    row["frames_decoded"] = len(dec_wm)
                    t0 = time.perf_counter()
                    ncs, bers = [], []
                    for i in range(n):
                        ex = extract_watermark(dec_wm[i], keys[i])
                        ncs.append(normalized_correlation(logo, ex)); bers.append(bit_error_rate(logo, ex))
                    row["t_extract_ms_per_frame"] = (time.perf_counter() - t0) / n * 1e3
                    row["psnr_wm_vs_orig_db"] = float(np.mean([psnr(frames[i], dec_wm[i]) for i in range(n)]))
                    row["psnr_codec_only_db"] = float(np.mean([psnr(frames[i], dec_ref[i]) for i in range(n)]))
                    row["nc_mean"] = float(np.mean(ncs)); row["nc_min"] = float(np.min(ncs))
                    row["frames_nc_ge_0_75"] = int(np.sum(np.array(ncs) >= 0.75)); row["ber_mean"] = float(np.mean(bers))
                    row["size_wm_kb"] = size_wm / 1024; row["size_ref_kb"] = size_ref / 1024
                    # naive frame-drop test: remove every 10th frame, extract with index-aligned keys
                    if codec == "lossless (FFV1)":
                        keep = [i for i in range(len(dec_wm)) if i % 10 != 9]
                        naive = [normalized_correlation(logo, extract_watermark(dec_wm[j], keys[i])) for i, j in enumerate(keep)]
                        aware = [normalized_correlation(logo, extract_watermark(dec_wm[j], keys[j])) for j in keep]
                        row["framedrop_nc_naive_index"] = float(np.mean(naive))
                        row["framedrop_nc_with_frame_ids"] = float(np.mean(aware))
                except Exception as exc:  # noqa: BLE001
                    row.update(status=f"error: {type(exc).__name__}: {exc}")
                rows.append(row)
        meta[clip]["embed_ms_per_frame"] = t_embed * 1e3
        meta[clip]["embed_fps_single_thread"] = 1 / t_embed
        print(clip, meta[clip], flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(RES, "video_demo_results.csv"), index=False)
    json.dump(meta, open(os.path.join(RES, "video_demo_meta.json"), "w"), indent=2)
    pd.set_option("display.width", 250)
    print(df.round(3).to_string())


if __name__ == "__main__":
    main()
