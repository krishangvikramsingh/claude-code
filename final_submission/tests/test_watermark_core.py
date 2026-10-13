import numpy as np
import pytest

from logo import make_watermark_logo
from metrics import normalized_correlation, psnr
from watermark_core import dct2, embed_watermark, extract_watermark, idct2


@pytest.fixture(scope="module")
def host():
    rng = np.random.default_rng(0)
    from scipy import ndimage
    return np.clip(128 + 40 * ndimage.gaussian_filter(rng.standard_normal((256, 256)), 3) * 6, 0, 255)


@pytest.fixture(scope="module")
def logo():
    return make_watermark_logo(32, "TEST")


def test_dct_roundtrip():
    a = np.random.default_rng(1).random((16, 16))
    assert np.allclose(idct2(dct2(a)), a)


def test_embed_shape_range_and_key(host, logo):
    w, key = embed_watermark(host, logo, alpha=0.1)
    assert w.shape == host.shape
    assert w.min() >= 0 and w.max() <= 255
    assert {"S_original", "Uw", "Vtw", "alpha", "target_shape", "wm_shape"} <= set(key)


def test_clean_roundtrip_recovers_logo(host, logo):
    w, key = embed_watermark(host, logo, alpha=0.1)
    ext = extract_watermark(w, key)
    assert ext.shape == logo.shape
    assert normalized_correlation(logo, ext) > 0.9


def test_imperceptibility_alpha_monotone(host, logo):
    p = [psnr(host, embed_watermark(host, logo, alpha=a)[0]) for a in (0.02, 0.1, 0.4)]
    assert p[0] > p[1] > p[2]


def test_unwatermarked_with_own_key_gives_zero(host, logo):
    _, key = embed_watermark(host, logo, alpha=0.1)
    assert normalized_correlation(logo, extract_watermark(host, key)) == 0.0


def test_odd_sized_host(logo):
    rng = np.random.default_rng(2)
    h = rng.random((101, 77)) * 255
    w, key = embed_watermark(h, logo)
    assert w.shape == h.shape
    assert extract_watermark(w, key).shape == logo.shape


def test_extract_handles_resized_image(host, logo):
    w, key = embed_watermark(host, logo)
    ext = extract_watermark(w[:200, :200], key)  # LL shape differs -> internal resize
    assert ext.shape == logo.shape


@pytest.mark.parametrize("bad", [np.zeros((4, 4)), np.zeros((8, 8, 3)), np.full((16, 16), np.nan), np.zeros(16)])
def test_invalid_host_rejected(bad, logo):
    with pytest.raises((ValueError, TypeError)):
        embed_watermark(bad, logo)


@pytest.mark.parametrize("alpha", [0, -0.1, float("nan")])
def test_invalid_alpha(host, logo, alpha):
    with pytest.raises(ValueError):
        embed_watermark(host, logo, alpha=alpha)


def test_invalid_subband(host, logo):
    with pytest.raises(ValueError):
        embed_watermark(host, logo, subband="XX")


def test_string_array_rejected(logo):
    with pytest.raises(TypeError):
        embed_watermark(np.array([["a"] * 16] * 16), logo)
