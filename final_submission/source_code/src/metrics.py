"""
metrics.py
==========
Quantitative evaluation metrics for watermarking quality (imperceptibility)
and robustness (extraction fidelity under attack).

Definitions (x = reference, y = test, N = number of pixels)
    MSE  = (1/N) * sum (x - y)^2
    PSNR = 10 * log10(255^2 / MSE)                       [dB]; undefined (inf) if MSE = 0
    SSIM = mean local structural similarity (Wang et al., 2004), 7x7 uniform window
    NC   = sum(W * W') / (||W|| * ||W'||)                [0..1 for non-negative images]
    ZNCC = Pearson correlation of the two images (mean-centred NC), in [-1, 1]
    BER  = fraction of pixels whose binarised value differs

Notes
  * NC as defined here is NOT mean-centred, so two non-negative images always
    have NC >= 0 and a fully black extraction gives NC = 0 by convention.
  * PSNR is capped at 100 dB when the images are identical so that averages stay
    finite (the original code returned scikit-image's inf).
"""

import numpy as np
from skimage.metrics import peak_signal_noise_ratio as _psnr
from skimage.metrics import structural_similarity as _ssim

PSNR_CAP_DB = 100.0


def _prep(a: np.ndarray, b: np.ndarray):
    a = np.clip(np.asarray(a, dtype=np.float64), 0, 255)
    b = np.clip(np.asarray(b, dtype=np.float64), 0, 255)
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch: {a.shape} vs {b.shape}")
    return a, b


def mse(original: np.ndarray, test: np.ndarray) -> float:
    a, b = _prep(original, test)
    return float(np.mean((a - b) ** 2))


def psnr(original: np.ndarray, test: np.ndarray) -> float:
    """Peak Signal-to-Noise Ratio in dB. Higher = more imperceptible."""
    a, b = _prep(original, test)
    if np.array_equal(a, b):
        return PSNR_CAP_DB
    return float(min(_psnr(a, b, data_range=255), PSNR_CAP_DB))


def ssim(original: np.ndarray, test: np.ndarray) -> float:
    """Structural Similarity Index (0-1). Higher = more structurally similar."""
    a, b = _prep(original, test)
    return float(_ssim(a, b, data_range=255))


def normalized_correlation(original_wm: np.ndarray, extracted_wm: np.ndarray) -> float:
    """
    Normalized Correlation (NC) between the original and extracted watermark.
    NC = 1.0 -> perfect extraction. NC used ubiquitously in watermarking
    literature to score robustness (typically NC > 0.75 is "recognizable").
    """
    a = np.asarray(original_wm, dtype=np.float64).flatten()
    b = np.asarray(extracted_wm, dtype=np.float64).flatten()
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch: {original_wm.shape} vs {extracted_wm.shape}")
    num = np.sum(a * b)
    den = np.sqrt(np.sum(a ** 2)) * np.sqrt(np.sum(b ** 2))
    if den == 0:
        return 0.0
    return float(num / den)


def zero_normalized_correlation(original_wm: np.ndarray, extracted_wm: np.ndarray) -> float:
    """
    Mean-centred NC (Pearson correlation of the flattened images).

    Plain NC rewards any bright-ish image: a constant white image already scores
    sqrt(fill ratio) = 0.359 against the 64x64 logo, and a rank-1 approximation of the
    logo scores 0.868.  ZNCC removes the DC offset so that it measures agreement of
    the *shape* only.  Returns 0.0 if either image has zero variance.
    """
    a = np.asarray(original_wm, dtype=np.float64).flatten()
    b = np.asarray(extracted_wm, dtype=np.float64).flatten()
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch: {original_wm.shape} vs {extracted_wm.shape}")
    a = a - a.mean()
    b = b - b.mean()
    den = np.sqrt(np.sum(a ** 2)) * np.sqrt(np.sum(b ** 2))
    if den == 0:
        return 0.0
    return float(np.sum(a * b) / den)


def bit_error_rate(original_wm: np.ndarray, extracted_wm: np.ndarray, thresh: float = 127.5) -> float:
    """
    BER between binarized original and extracted watermark (0-1, lower better).
    """
    a = (np.asarray(original_wm, dtype=np.float64) > thresh).astype(np.uint8).flatten()
    b = (np.asarray(extracted_wm, dtype=np.float64) > thresh).astype(np.uint8).flatten()
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch: {original_wm.shape} vs {extracted_wm.shape}")
    return float(np.mean(a != b))
