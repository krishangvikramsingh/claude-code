import numpy as np
import pytest

from metrics import (PSNR_CAP_DB, bit_error_rate, mse, normalized_correlation, psnr, ssim,
                     zero_normalized_correlation)


def test_psnr_identical_is_capped():
    a = np.random.default_rng(0).random((32, 32)) * 255
    assert psnr(a, a) == PSNR_CAP_DB


def test_psnr_known_value():
    a = np.zeros((16, 16)); b = np.full((16, 16), 10.0)
    assert mse(a, b) == pytest.approx(100.0)
    assert psnr(a, b) == pytest.approx(10 * np.log10(255 ** 2 / 100.0))


def test_ssim_identical_is_one():
    a = np.random.default_rng(1).random((32, 32)) * 255
    assert ssim(a, a) == pytest.approx(1.0)


def test_nc_basic():
    w = np.zeros((8, 8)); w[2:5, 2:5] = 255
    assert normalized_correlation(w, w) == pytest.approx(1.0)
    assert normalized_correlation(w, np.zeros_like(w)) == 0.0
    assert normalized_correlation(w, np.full_like(w, 255)) == pytest.approx(np.sqrt(9 / 64))


def test_zncc_properties():
    rng = np.random.default_rng(3)
    w = (rng.random((16, 16)) > .8) * 255.0
    assert zero_normalized_correlation(w, w) == pytest.approx(1.0)
    assert zero_normalized_correlation(w, 255 - w) == pytest.approx(-1.0)
    assert zero_normalized_correlation(w, np.full_like(w, 5)) == 0.0
    assert zero_normalized_correlation(w, 0.5 * w + 30) == pytest.approx(1.0)


def test_ber():
    a = np.zeros((4, 4)); b = a.copy(); b[0, :] = 255
    assert bit_error_rate(a, b) == pytest.approx(0.25)


@pytest.mark.parametrize("fn", [psnr, ssim, normalized_correlation, zero_normalized_correlation, bit_error_rate, mse])
def test_shape_mismatch_raises(fn):
    with pytest.raises(ValueError):
        fn(np.zeros((8, 8)), np.zeros((9, 9)))
