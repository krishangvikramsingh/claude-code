"""
image_io.py
===========
Safe image loading and standardisation for the watermarking experiments.

The original project only ever handled two scikit-image samples that were
already single-channel arrays.  A heterogeneous 100-image set needs explicit
handling of colour modes, alpha channels, 16-bit data, odd aspect ratios and
corrupted files, otherwise results silently depend on how Pillow happens to
decode each file.

Standardisation rule (documented in the report, Section 5.1)
------------------------------------------------------------
1. Decode with Pillow; reject empty / corrupt / unsupported files.
2. Alpha channels are composited over white.
3. 16-bit / float data is linearly rescaled to 8 bit.
4. Colour -> grey with Pillow's ITU-R BT.601 luma  L = 0.299 R + 0.587 G + 0.114 B.
5. Centre-crop to a square (largest possible) so aspect ratio is not distorted.
6. Resize to ``size`` x ``size`` with Lanczos resampling.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np
from PIL import Image, UnidentifiedImageError

Image.MAX_IMAGE_PIXELS = 200_000_000  # allow big panoramas, still bounded


class ImageLoadError(RuntimeError):
    """Raised when an image cannot be decoded or is unusable."""


@dataclass
class SourceInfo:
    width: int
    height: int
    mode: str
    fmt: str
    file_size: int


def _to_uint8_rgbish(im: Image.Image) -> Image.Image:
    """Return an 8-bit 'L' or 'RGB' image regardless of the source mode."""
    mode = im.mode
    if mode in ("RGBA", "LA", "PA") or (mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        return Image.alpha_composite(bg, im).convert("RGB")
    if mode in ("I;16", "I;16B", "I;16L", "I", "F"):
        arr = np.asarray(im, dtype=np.float64)
        lo, hi = float(arr.min()), float(arr.max())
        if hi <= lo:
            raise ImageLoadError("constant-valued high-bit-depth image")
        return Image.fromarray(((arr - lo) / (hi - lo) * 255.0).round().astype(np.uint8), "L")
    if mode == "1":
        return im.convert("L")
    if mode in ("L", "RGB"):
        return im
    return im.convert("RGB")


def load_gray_square(path: str, size: int = 512) -> tuple[np.ndarray, SourceInfo]:
    """Load ``path`` and return a ``size`` x ``size`` float64 array in [0, 255]."""
    if not os.path.isfile(path):
        raise ImageLoadError(f"file not found: {path}")
    fsize = os.path.getsize(path)
    if fsize == 0:
        raise ImageLoadError(f"empty file: {path}")
    try:
        with Image.open(path) as im:
            fmt = im.format or ""
            w, h = im.size
            mode = im.mode
            im.load()
            rgb = _to_uint8_rgbish(im)
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as exc:
        raise ImageLoadError(f"cannot decode {os.path.basename(path)}: {exc}") from exc
    if min(w, h) < 16:
        raise ImageLoadError(f"image too small ({w}x{h})")

    gray = rgb.convert("L")
    side = min(gray.size)
    left, top = (gray.width - side) // 2, (gray.height - side) // 2
    gray = gray.crop((left, top, left + side, top + side)).resize((size, size), Image.LANCZOS)
    arr = np.asarray(gray, dtype=np.float64)
    return arr, SourceInfo(w, h, mode, fmt, fsize)


def save_gray_png(arr: np.ndarray, path: str) -> None:
    """Write an 8-bit greyscale PNG (values rounded and clipped)."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    Image.fromarray(np.clip(np.rint(arr), 0, 255).astype(np.uint8), "L").save(path)


def verify_png(path: str, expected_shape: tuple[int, int] | None = None) -> bool:
    """Re-open ``path`` and check it decodes to a non-degenerate 2-D uint8 image."""
    try:
        with Image.open(path) as im:
            im.load()
            a = np.asarray(im)
    except Exception:
        return False
    if a.ndim != 2 or a.dtype != np.uint8:
        return False
    if expected_shape is not None and a.shape != tuple(expected_shape):
        return False
    return bool(np.isfinite(a).all())
