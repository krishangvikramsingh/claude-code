import numpy as np
import pytest

from attacks import (ATTACK_NAMES, cropping_attack, jpeg_compression, make_attack_suite, rotation_attack,
                     scaling_attack)


@pytest.fixture(scope="module")
def img():
    return np.random.default_rng(0).random((128, 128)) * 255


def test_suite_complete_and_shape_preserving(img):
    suite = make_attack_suite(1)
    assert list(suite) == ATTACK_NAMES and len(suite) == 15
    for name, fn in suite.items():
        out = fn(img)
        assert out.shape == img.shape, name
        assert np.isfinite(out).all(), name


def test_stochastic_attacks_are_seeded(img):
    a = make_attack_suite(7)["Gaussian Noise (var=0.02)"](img)
    b = make_attack_suite(7)["Gaussian Noise (var=0.02)"](img)
    c = make_attack_suite(8)["Gaussian Noise (var=0.02)"](img)
    assert np.array_equal(a, b) and not np.array_equal(a, c)


def test_cropping_removes_expected_area():
    out = cropping_attack(np.full((512, 512), 200.0), 0.25)
    kept = (out > 0).mean()
    assert kept == pytest.approx(0.5625, abs=1e-6)  # 43.75 % of the area is zeroed


def test_jpeg_quality_bounds(img):
    with pytest.raises(ValueError):
        jpeg_compression(img, 0)
    assert jpeg_compression(img, 90).shape == img.shape


def test_zero_rotation_and_unit_scale_identity(img):
    assert np.allclose(rotation_attack(img, 0), img, atol=1e-6)
    assert np.allclose(scaling_attack(img, 1.0), img, atol=1e-6)
