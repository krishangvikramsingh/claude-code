import numpy as np
import pytest
from PIL import Image

from image_io import ImageLoadError, load_gray_square, save_gray_png, verify_png


def _save(tmp_path, name, im):
    p = tmp_path / name
    im.save(p)
    return str(p)


def test_rgb_wide_image_is_cropped_to_square(tmp_path):
    arr = np.zeros((100, 300, 3), np.uint8); arr[..., 0] = 255
    a, info = load_gray_square(_save(tmp_path, "w.png", Image.fromarray(arr)), 64)
    assert a.shape == (64, 64) and (info.width, info.height) == (300, 100)
    assert a.mean() == pytest.approx(0.299 * 255, abs=1.0)  # BT.601 luma of pure red


def test_rgba_composited_on_white(tmp_path):
    arr = np.zeros((64, 64, 4), np.uint8)  # fully transparent black
    a, _ = load_gray_square(_save(tmp_path, "t.png", Image.fromarray(arr)), 32)
    assert a.min() > 250


def test_16bit_rescaled(tmp_path):
    arr = (np.arange(64 * 64).reshape(64, 64) * 10).astype(np.uint16)
    a, _ = load_gray_square(_save(tmp_path, "s.png", Image.fromarray(arr)), 32)
    # linear rescale to 0..255, then Lanczos down-sampling shaves a few levels off the extremes
    assert 245 <= a.max() <= 255 and 0 <= a.min() <= 10


def test_palette_and_bilevel(tmp_path):
    im = Image.fromarray((np.random.default_rng(0).random((64, 64)) > .5).astype(np.uint8) * 255).convert("1")
    a, _ = load_gray_square(_save(tmp_path, "b.png", im), 32)
    assert a.shape == (32, 32)


def test_missing_empty_corrupt_unsupported(tmp_path):
    with pytest.raises(ImageLoadError):
        load_gray_square(str(tmp_path / "nope.png"))
    e = tmp_path / "empty.png"; e.write_bytes(b"")
    with pytest.raises(ImageLoadError):
        load_gray_square(str(e))
    c = tmp_path / "corrupt.png"; c.write_bytes(b"\x89PNG\r\n\x1a\n" + b"garbage" * 20)
    with pytest.raises(ImageLoadError):
        load_gray_square(str(c))
    t = tmp_path / "doc.txt"; t.write_text("not an image")
    with pytest.raises(ImageLoadError):
        load_gray_square(str(t))


def test_tiny_and_constant_16bit_rejected(tmp_path):
    with pytest.raises(ImageLoadError):
        load_gray_square(_save(tmp_path, "tiny.png", Image.fromarray(np.zeros((8, 8), np.uint8))))
    with pytest.raises(ImageLoadError):
        load_gray_square(_save(tmp_path, "c16.png", Image.fromarray(np.full((64, 64), 500, np.uint16))))


def test_save_and_verify_roundtrip(tmp_path):
    p = str(tmp_path / "sub" / "x.png")
    save_gray_png(np.full((20, 30), 300.7), p)
    assert verify_png(p, (20, 30))
    assert not verify_png(p, (30, 20))
    assert not verify_png(str(tmp_path / "missing.png"))
    assert np.asarray(Image.open(p)).max() == 255  # clipped
