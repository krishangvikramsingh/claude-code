"""
attacks.py
==========
Standard attack/distortion suite used to benchmark watermark robustness.
Each function takes a float image (0-255) and returns a same-size float image.

Changes w.r.t. the original submission (see CHANGELOG):
  * the two stochastic attacks now accept a ``rng`` seed -> runs are reproducible
  * ``make_attack_suite(seed)`` builds the 15-condition suite (14 attacks + "No Attack") with a given seed;
    ``ATTACK_SUITE`` (seed 0) is kept for backward compatibility
  * documentation of what "Cropping 25%" really does (see below)
  * JPEG attack validates its input and always returns a 2-D array
"""

from __future__ import annotations

import io

import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.exposure import equalize_hist
from skimage.transform import rotate, resize
from skimage.util import random_noise


def jpeg_compression(img: np.ndarray, quality: int = 50) -> np.ndarray:
    """Round-trip through Pillow's baseline JPEG encoder at the given quality (1-95)."""
    if not 1 <= quality <= 95:
        raise ValueError("quality must be in 1..95")
    im = Image.fromarray(np.clip(np.rint(img), 0, 255).astype(np.uint8))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    return np.array(Image.open(buf).convert("L")).astype(np.float64)


def gaussian_noise(img: np.ndarray, var: float = 0.01, rng=None) -> np.ndarray:
    """Additive Gaussian noise; ``var`` is the variance on the [0,1] intensity scale."""
    noisy = random_noise(img / 255.0, mode="gaussian", var=var, rng=rng)
    return noisy * 255.0


def salt_pepper_noise(img: np.ndarray, amount: float = 0.02, rng=None) -> np.ndarray:
    """Replace ``amount`` of the pixels by 0 or 255 with equal probability."""
    noisy = random_noise(img / 255.0, mode="s&p", amount=amount, rng=rng)
    return noisy * 255.0


def median_filter(img: np.ndarray, size: int = 3) -> np.ndarray:
    return ndimage.median_filter(img, size=size)


def gaussian_blur(img: np.ndarray, sigma: float = 1.5) -> np.ndarray:
    return ndimage.gaussian_filter(img, sigma=sigma)


def rotation_attack(img: np.ndarray, angle: float = 5.0) -> np.ndarray:
    """Rotate about the centre (counter-clockwise, degrees), keep size, replicate edges.
    No re-alignment is applied before extraction (a pure geometric-attack test)."""
    rotated = rotate(img / 255.0, angle, resize=False, mode="edge")
    return rotated * 255.0


def cropping_attack(img: np.ndarray, frac: float = 0.25) -> np.ndarray:
    """Zero a border so that ``frac`` of EACH DIMENSION is removed (frac/2 per side).

    For frac = 0.25 on a 512x512 image this blacks out a 64-px frame on every
    side, i.e. the surviving centre is 384x384 = 56.25 % of the area, so
    43.75 % of the *area* is removed.  (The original report called this
    "Cropping 25%"; the label is kept for comparability but the report now states
    the area fraction explicitly.)  The image is not resized, so geometry is kept.
    """
    h, w = img.shape
    ch, cw = int(h * frac / 2), int(w * frac / 2)
    out = img.copy()
    out[:ch, :] = 0
    out[h - ch:, :] = 0
    out[:, :cw] = 0
    out[:, w - cw:] = 0
    return out


def scaling_attack(img: np.ndarray, factor: float = 0.5) -> np.ndarray:
    h, w = img.shape
    small = resize(img, (int(h * factor), int(w * factor)), anti_aliasing=True, preserve_range=True)
    back = resize(small, (h, w), anti_aliasing=True, preserve_range=True)
    return back


def histogram_equalization(img: np.ndarray) -> np.ndarray:
    eq = equalize_hist(img / 255.0)
    return eq * 255.0


def sharpening_attack(img: np.ndarray, amount: float = 1.0) -> np.ndarray:
    blurred = ndimage.gaussian_filter(img, sigma=1.0)
    sharpened = img + amount * (img - blurred)
    return np.clip(sharpened, 0, 255)


ATTACK_NAMES = [
    "No Attack", "JPEG Q=90", "JPEG Q=50", "JPEG Q=20",
    "Gaussian Noise (var=0.005)", "Gaussian Noise (var=0.02)", "Salt & Pepper (2%)",
    "Median Filter 3x3", "Gaussian Blur (sigma=1.5)", "Rotation 5 deg", "Rotation 15 deg",
    "Cropping 25%", "Scaling 0.5x", "Histogram Equalization", "Sharpening",
]

ATTACK_FAMILY = {
    "No Attack": "none", "JPEG Q=90": "compression", "JPEG Q=50": "compression", "JPEG Q=20": "compression",
    "Gaussian Noise (var=0.005)": "noise", "Gaussian Noise (var=0.02)": "noise", "Salt & Pepper (2%)": "noise",
    "Median Filter 3x3": "filtering", "Gaussian Blur (sigma=1.5)": "filtering", "Sharpening": "filtering",
    "Rotation 5 deg": "geometric", "Rotation 15 deg": "geometric", "Cropping 25%": "geometric",
    "Scaling 0.5x": "geometric", "Histogram Equalization": "global intensity",
}


def make_attack_suite(seed: int = 0) -> dict:
    """Return {name: callable} for the 15-condition suite (14 attacks + "No Attack"); stochastic attacks use ``seed``."""
    return {
        "No Attack":                  lambda x: x.copy(),
        "JPEG Q=90":                  lambda x: jpeg_compression(x, 90),
        "JPEG Q=50":                  lambda x: jpeg_compression(x, 50),
        "JPEG Q=20":                  lambda x: jpeg_compression(x, 20),
        "Gaussian Noise (var=0.005)": lambda x: gaussian_noise(x, 0.005, rng=seed),
        "Gaussian Noise (var=0.02)":  lambda x: gaussian_noise(x, 0.02, rng=seed + 1),
        "Salt & Pepper (2%)":         lambda x: salt_pepper_noise(x, 0.02, rng=seed + 2),
        "Median Filter 3x3":          lambda x: median_filter(x, 3),
        "Gaussian Blur (sigma=1.5)":  lambda x: gaussian_blur(x, 1.5),
        "Rotation 5 deg":             lambda x: rotation_attack(x, 5),
        "Rotation 15 deg":            lambda x: rotation_attack(x, 15),
        "Cropping 25%":               lambda x: cropping_attack(x, 0.25),
        "Scaling 0.5x":               lambda x: scaling_attack(x, 0.5),
        "Histogram Equalization":     lambda x: histogram_equalization(x),
        "Sharpening":                 lambda x: sharpening_attack(x, 1.0),
    }


# Backward-compatible module-level suite (seed 0).
ATTACK_SUITE = make_attack_suite(0)
assert list(ATTACK_SUITE) == ATTACK_NAMES
