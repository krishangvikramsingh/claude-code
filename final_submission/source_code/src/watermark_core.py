"""
watermark_core.py
==================
Hybrid DWT-DCT-SVD Digital Image Watermarking Engine.

Algorithm summary
------------------
EMBEDDING:
  1. Host (cover) image  -> 1-level 2D DWT (Haar)  -> subbands {LL, LH, HL, HH}
  2. Target subband (default: LL)  -> 2D DCT of the WHOLE sub-band (global, not
     block-wise; see CHANGELOG 'doc-fix-1': earlier docstrings said "block-level")
  3. DCT coefficient matrix -> SVD:            A = U . S . V^T
  4. Watermark image (grayscale, resized to subband shape) -> SVD:
                                                W = Uw . Sw . Vw^T
  5. Modify singular values of the host subband:
                                     S' = S + alpha * Sw
  6. Reconstruct:      A' = U . S' . V^T   -> inverse DCT -> modified subband
  7. Replace subband, apply inverse DWT -> watermarked image

EXTRACTION (NON-blind: requires the embedding "key" = {S_original, Uw, Vtw,
alpha, ...} saved at embedding time, and in particular the singular values of the
ORIGINAL host sub-band; this is the usual set-up for SVD ownership schemes where
the key is held by the copyright owner).  [The original text called this
"semi-blind"; because S_original is derived from the unmarked host it is
non-blind in the standard taxonomy.]
  1. Possibly-attacked watermarked image -> DWT -> target subband -> DCT -> SVD -> S_att
  2. Sw_extracted = (S_att - S_original) / alpha
  3. Watermark_extracted = Uw . Sw_extracted . Vw^T

KNOWN LIMITATION (measured in `run_batch_experiment.py`, experiment E4):
the logo's *identity* lives in the key (Uw, Vtw), not in the image.  The
extractor therefore reproduces "the key owner's logo" even when a different logo
was embedded.  A high NC value measures *fidelity of the recovered singular
values*, not proof of ownership.  This is the well-known false-positive problem
of SVD-based watermarking.

alpha (embedding strength) trades off imperceptibility (PSNR/SSIM of watermarked
image) against robustness (NC/BER of extracted watermark after attacks).

The numerical behaviour of embed_watermark / extract_watermark is IDENTICAL to
the original submission; only input validation and documentation were added.
"""

from __future__ import annotations

import numpy as np
import pywt
from scipy.fftpack import dct, idct
from skimage.transform import resize

_SUBBANDS = ("LL", "LH", "HL", "HH")


# ---------------------------------------------------------------------------
# Transform helpers
# ---------------------------------------------------------------------------

def dct2(block: np.ndarray) -> np.ndarray:
    """Orthonormal 2-D DCT-II."""
    return dct(dct(block.T, norm="ortho").T, norm="ortho")


def idct2(block: np.ndarray) -> np.ndarray:
    """Inverse of :func:`dct2`."""
    return idct(idct(block.T, norm="ortho").T, norm="ortho")


def _check_2d(name: str, a: np.ndarray, min_side: int = 8) -> np.ndarray:
    a = np.asarray(a)
    if a.ndim != 2:
        raise ValueError(f"{name} must be a 2-D greyscale array, got shape {a.shape}")
    if min(a.shape) < min_side:
        raise ValueError(f"{name} too small: {a.shape}")
    if not np.issubdtype(a.dtype, np.number):
        raise TypeError(f"{name} must be numeric, got {a.dtype}")
    if not np.isfinite(a).all():
        raise ValueError(f"{name} contains NaN/Inf")
    return a.astype(np.float64)


# ---------------------------------------------------------------------------
# Watermark embedding
# ---------------------------------------------------------------------------

def embed_watermark(host: np.ndarray, watermark: np.ndarray, alpha: float = 0.10,
                     wavelet: str = "haar", subband: str = "LL"):
    """
    Embed `watermark` (2D float array, any size) into `host` (2D float array).

    Returns
    -------
    watermarked : np.ndarray  -- same shape/dtype range as host (0-255 float)
    key : dict                -- embedding key required for extraction
    """
    host = _check_2d("host", host)
    watermark = _check_2d("watermark", watermark)
    if not alpha > 0:
        raise ValueError(f"alpha must be > 0, got {alpha}")
    if subband not in _SUBBANDS:
        raise ValueError(f"subband must be one of {_SUBBANDS}, got {subband!r}")

    # 1) DWT decomposition of host
    LL, (LH, HL, HH) = pywt.dwt2(host, wavelet)
    subbands = {"LL": LL, "LH": LH, "HL": HL, "HH": HH}
    target = subbands[subband]

    # 2) Resize watermark to match target subband size
    wm_resized = resize(watermark, target.shape, anti_aliasing=True, preserve_range=True)

    # 3) DCT of target subband
    target_dct = dct2(target)

    # 4) SVD of host (DCT domain) and watermark
    U, S, Vt = np.linalg.svd(target_dct, full_matrices=False)
    Uw, Sw, Vtw = np.linalg.svd(wm_resized, full_matrices=False)

    # 5) Modify singular values
    S_mod = S + alpha * Sw

    # 6) Reconstruct modified subband
    target_dct_mod = (U * S_mod) @ Vt
    target_mod = idct2(target_dct_mod)

    # 7) Replace subband and invert DWT
    subbands[subband] = target_mod
    watermarked = pywt.idwt2((subbands["LL"], (subbands["LH"], subbands["HL"], subbands["HH"])), wavelet)

    # Crop / pad in case IDWT introduces a 1-pixel size mismatch
    watermarked = watermarked[:host.shape[0], :host.shape[1]]
    watermarked = np.clip(watermarked, 0, 255)

    key = {
        "U": U, "Vt": Vt, "S_original": S,
        "Uw": Uw, "Vtw": Vtw,
        "alpha": alpha, "wavelet": wavelet, "subband": subband,
        "wm_shape": watermark.shape, "target_shape": target.shape,
    }
    return watermarked, key


# ---------------------------------------------------------------------------
# Watermark extraction
# ---------------------------------------------------------------------------

def extract_watermark(possibly_attacked: np.ndarray, key: dict) -> np.ndarray:
    """
    Extract the watermark from a (possibly attacked) watermarked image using
    the embedding key produced by `embed_watermark`.
    """
    img = _check_2d("image", possibly_attacked)
    wavelet = key["wavelet"]
    subband = key["subband"]

    LL, (LH, HL, HH) = pywt.dwt2(img, wavelet)
    subbands = {"LL": LL, "LH": LH, "HL": HL, "HH": HH}
    target = subbands[subband]

    # Attacks (crop / resize / rotate) can change subband size slightly;
    # force it back to the size used at embedding time.
    target_shape = key["target_shape"]
    if target.shape != target_shape:
        target = resize(target, target_shape, anti_aliasing=True, preserve_range=True)

    target_dct = dct2(target)
    _, S_att, _ = np.linalg.svd(target_dct, full_matrices=False)

    Sw_extracted = (S_att - key["S_original"]) / key["alpha"]
    watermark_extracted = (key["Uw"] * Sw_extracted) @ key["Vtw"]

    watermark_extracted = resize(watermark_extracted, key["wm_shape"],
                                  anti_aliasing=True, preserve_range=True)
    return np.clip(watermark_extracted, 0, 255)
