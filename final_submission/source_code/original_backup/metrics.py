"""
metrics.py
==========
Quantitative evaluation metrics for watermarking quality (imperceptibility)
and robustness (extraction fidelity under attack).
"""

import numpy as np
from skimage.metrics import peak_signal_noise_ratio as _psnr
from skimage.metrics import structural_similarity as _ssim


def psnr(original: np.ndarray, test: np.ndarray) -> float:
    """Peak Signal-to-Noise Ratio in dB. Higher = more imperceptible."""
    original = np.clip(original, 0, 255).astype(np.float64)
    test = np.clip(test, 0, 255).astype(np.float64)
    return float(_psnr(original, test, data_range=255))


def ssim(original: np.ndarray, test: np.ndarray) -> float:
    """Structural Similarity Index (0-1). Higher = more structurally similar."""
    original = np.clip(original, 0, 255).astype(np.float64)
    test = np.clip(test, 0, 255).astype(np.float64)
    return float(_ssim(original, test, data_range=255))


def normalized_correlation(original_wm: np.ndarray, extracted_wm: np.ndarray) -> float:
    """
    Normalized Correlation (NC) between the original and extracted watermark.
    NC = 1.0 -> perfect extraction. NC used ubiquitously in watermarking
    literature to score robustness (typically NC > 0.75 is "recognizable").
    """
    a = original_wm.astype(np.float64).flatten()
    b = extracted_wm.astype(np.float64).flatten()
    num = np.sum(a * b)
    den = np.sqrt(np.sum(a ** 2)) * np.sqrt(np.sum(b ** 2))
    if den == 0:
        return 0.0
    return float(num / den)


def bit_error_rate(original_wm: np.ndarray, extracted_wm: np.ndarray, thresh: float = 127.5) -> float:
    """
    BER between binarized original and extracted watermark (0-1, lower better).
    """
    a = (original_wm.astype(np.float64) > thresh).astype(np.uint8).flatten()
    b = (extracted_wm.astype(np.float64) > thresh).astype(np.uint8).flatten()
    return float(np.mean(a != b))
