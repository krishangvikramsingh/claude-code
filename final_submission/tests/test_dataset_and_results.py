"""Integrity checks on the produced dataset / results (skipped if they were not generated)."""
import os

import numpy as np
import pandas as pd
import pytest
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
META = os.path.join(ROOT, "data", "metadata.csv")
pytestmark = pytest.mark.skipif(not os.path.exists(META), reason="dataset not built")


@pytest.fixture(scope="module")
def meta():
    return pd.read_csv(META)


def test_exactly_100_unique_images(meta):
    assert len(meta) == 100
    assert meta.image_id.is_unique and meta.key.is_unique
    hashes = []
    for iid in meta.image_id:
        a = np.asarray(Image.open(os.path.join(ROOT, "data", "original", iid + ".png")))
        assert a.shape == (512, 512) and a.dtype == np.uint8
        hashes.append(a.tobytes().__hash__())
    assert len(set(hashes)) == 100


def test_synthetic_labelled(meta):
    assert set(meta[meta.is_synthetic == 1].category) == {"synthetic_control"}
    assert (meta[meta.is_synthetic == 0].category != "synthetic_control").all()
    assert meta[meta.is_synthetic == 0].source_sha256.str.len().eq(64).all()


@pytest.mark.skipif(not os.path.exists(os.path.join(ROOT, "results", "results_attacks.csv")), reason="no results")
def test_batch_completeness(meta):
    att = pd.read_csv(os.path.join(ROOT, "results", "results_attacks.csv"))
    assert len(att) == 100 * 15 * 2
    assert (att.status == "ok").all()
    assert att.groupby(["image_id", "protocol"]).size().eq(15).all()
    assert att.nc.between(0, 1).all() and att.ber.between(0, 1).all()
    imgs = pd.read_csv(os.path.join(ROOT, "results", "results_images.csv"))
    assert imgs.output_valid.all() and (imgs.status == "ok").all()
    for iid in meta.image_id:
        assert os.path.exists(os.path.join(ROOT, "outputs", "watermarked", iid + "_wm.png"))
