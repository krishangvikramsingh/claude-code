"""
attacks.py
==========
Standard attack/distortion suite used to benchmark watermark robustness.
Each function takes a float image (0-255) and returns a same-size float image.
"""

import io
import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.transform import rotate, resize
from skimage.util import random_noise


def jpeg_compression(img: np.ndarray, quality: int = 50) -> np.ndarray:
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    return np.array(Image.open(buf).convert("L")).astype(np.float64)


def gaussian_noise(img: np.ndarray, var: float = 0.01) -> np.ndarray:
    noisy = random_noise(img / 255.0, mode="gaussian", var=var)
    return noisy * 255.0


def salt_pepper_noise(img: np.ndarray, amount: float = 0.02) -> np.ndarray:
    noisy = random_noise(img / 255.0, mode="s&p", amount=amount)
    return noisy * 255.0


def median_filter(img: np.ndarray, size: int = 3) -> np.ndarray:
    return ndimage.median_filter(img, size=size)


def gaussian_blur(img: np.ndarray, sigma: float = 1.5) -> np.ndarray:
    return ndimage.gaussian_filter(img, sigma=sigma)


def rotation_attack(img: np.ndarray, angle: float = 5.0) -> np.ndarray:
    rotated = rotate(img / 255.0, angle, resize=False, mode="edge")
    return rotated * 255.0


def cropping_attack(img: np.ndarray, frac: float = 0.25) -> np.ndarray:
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
    from skimage.exposure import equalize_hist
    eq = equalize_hist(img / 255.0)
    return eq * 255.0


def sharpening_attack(img: np.ndarray, amount: float = 1.0) -> np.ndarray:
    blurred = ndimage.gaussian_filter(img, sigma=1.0)
    sharpened = img + amount * (img - blurred)
    return np.clip(sharpened, 0, 255)


ATTACK_SUITE = {
    "No Attack":                lambda x: x.copy(),
    "JPEG Q=90":                lambda x: jpeg_compression(x, 90),
    "JPEG Q=50":                lambda x: jpeg_compression(x, 50),
    "JPEG Q=20":                lambda x: jpeg_compression(x, 20),
    "Gaussian Noise (var=0.005)": lambda x: gaussian_noise(x, 0.005),
    "Gaussian Noise (var=0.02)":  lambda x: gaussian_noise(x, 0.02),
    "Salt & Pepper (2%)":       lambda x: salt_pepper_noise(x, 0.02),
    "Median Filter 3x3":        lambda x: median_filter(x, 3),
    "Gaussian Blur (sigma=1.5)": lambda x: gaussian_blur(x, 1.5),
    "Rotation 5 deg":            lambda x: rotation_attack(x, 5),
    "Rotation 15 deg":           lambda x: rotation_attack(x, 15),
    "Cropping 25%":              lambda x: cropping_attack(x, 0.25),
    "Scaling 0.5x":              lambda x: scaling_attack(x, 0.5),
    "Histogram Equalization":    lambda x: histogram_equalization(x),
    "Sharpening":                 lambda x: sharpening_attack(x, 1.0),
}
