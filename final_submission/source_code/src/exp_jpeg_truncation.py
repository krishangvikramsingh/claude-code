"""
exp_jpeg_truncation.py
======================
Why did the first submission's alpha-sweep figure show NC after JPEG Q=50 rising from 0.93 (alpha=0.02)
to 0.99 (alpha>=0.05)?  Re-creates its conditions exactly (scikit-image `camera()` resized to 512x512,
CYBERION logo, JPEG Q=50 applied to the *float* watermarked image) with the original attack code path
(`astype(np.uint8)` = truncation) and with the corrected path (rounding).
"""
import io

import numpy as np
from PIL import Image
from skimage import data as skdata
from skimage.transform import resize

from logo import make_watermark_logo
from metrics import normalized_correlation as nc, psnr
from watermark_core import embed_watermark, extract_watermark


def jpeg(img, q, mode):
    a = np.clip(img, 0, 255)
    a = a.astype(np.uint8) if mode == "truncate" else np.rint(a).astype(np.uint8)
    b = io.BytesIO(); Image.fromarray(a).save(b, "JPEG", quality=q); b.seek(0)
    return np.array(Image.open(b).convert("L")).astype(np.float64)


if __name__ == "__main__":
    wm = make_watermark_logo()
    host = resize(skdata.camera().astype(np.float64), (512, 512), preserve_range=True)
    print(f"{'alpha':>6} {'PSNR':>7} {'NC trunc.':>10} {'NC round':>9} {'mean(trunc.-float)':>19}")
    for a in (0.02, 0.05, 0.08, 0.10, 0.15, 0.20, 0.30, 0.40):
        w, k = embed_watermark(host, wm, alpha=a)
        t, r = jpeg(w, 50, "truncate"), jpeg(w, 50, "round")
        print(f"{a:6.2f} {psnr(host, w):7.2f} {nc(wm, extract_watermark(t, k)):10.3f} {nc(wm, extract_watermark(r, k)):9.3f} "
              f"{float((jpeg(w, 100, 'truncate') - w).mean()):19.3f}")
