"""
watermark_core.py
==================
Hybrid DWT-DCT-SVD Digital Image Watermarking Engine.

Algorithm summary
------------------
EMBEDDING:
  1. Host (cover) image  -> 1-level 2D DWT (Haar)  -> subbands {LL, LH, HL, HH}
  2. Target subband (default: LL)  -> block-level 2D DCT
  3. DCT coefficient matrix -> SVD:            A = U . S . V^T
  4. Watermark image (grayscale, resized to subband shape) -> SVD:
                                                W = Uw . Sw . Vw^T
  5. Modify singular values of the host subband:
                                     S' = S + alpha * Sw
  6. Reconstruct:      A' = U . S' . V^T   -> inverse DCT -> modified subband
  7. Replace subband, apply inverse DWT -> watermarked image

EXTRACTION (semi-blind: requires the embedding "key" = {U, V, Uw, Vw, S_original, alpha}
saved at embedding time -- standard for robust/non-blind SVD watermarking schemes
used for ownership/copyright proof, where the key is held by the copyright owner):
  1. Possibly-attacked watermarked image -> DWT -> target subband -> DCT -> SVD -> S_att
  2. Sw_extracted = (S_att - S_original) / alpha
  3. Watermark_extracted = Uw . Sw_extracted . Vw^T

alpha (embedding strength) trades off imperceptibility (PSNR/SSIM of watermarked
image) against robustness (NC/BER of extracted watermark after attacks).
"""

import numpy as np
import pywt
from scipy.fftpack import dct, idct


# ---------------------------------------------------------------------------
# Transform helpers
# ---------------------------------------------------------------------------

def dct2(block: np.ndarray) -> np.ndarray:
    return dct(dct(block.T, norm="ortho").T, norm="ortho")


def idct2(block: np.ndarray) -> np.ndarray:
    return idct(idct(block.T, norm="ortho").T, norm="ortho")


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
    host = host.astype(np.float64)

    # 1) DWT decomposition of host
    LL, (LH, HL, HH) = pywt.dwt2(host, wavelet)
    subbands = {"LL": LL, "LH": LH, "HL": HL, "HH": HH}
    target = subbands[subband]

    # 2) Resize watermark to match target subband size
    from skimage.transform import resize
    wm_resized = resize(watermark.astype(np.float64), target.shape,
                         anti_aliasing=True, preserve_range=True)

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
    from skimage.transform import resize

    img = possibly_attacked.astype(np.float64)
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
