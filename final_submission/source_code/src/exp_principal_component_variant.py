"""
exp_principal_component_variant.py
==================================
Small negative-result experiment: does embedding the logo's principal component
PC = Uw.diag(Sw) (instead of only its singular values) cure the false-positive
problem?  Variant: D = diag(S) + alpha*PC ; SVD(D) = U1 S1 V1^T ; host' = U S1 Vt.
Extraction: D* = U1 S1* V1^T ; PC* = (D* - diag(S))/alpha ; W* = PC* Vw^T.

Outcome (printed): the key {U1, V1^T, S, Vw^T} already contains the whole logo, so an
UNWATERMARKED host decodes to NC ~ 0.98 -> the variant is *worse* than the project's
scheme with respect to false positives.  Not used anywhere else.
"""
import os
import numpy as np
import pywt
from PIL import Image
from skimage.transform import resize

from logo import make_watermark_logo
from metrics import normalized_correlation as nc, psnr
from watermark_core import dct2, idct2

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def emb_pc(host, wm, alpha):
    LL, (LH, HL, HH) = pywt.dwt2(host, "haar")
    wr = resize(wm, LL.shape, anti_aliasing=True, preserve_range=True) / 255.0
    U, S, Vt = np.linalg.svd(dct2(LL))
    Uw, Sw, Vtw = np.linalg.svd(wr)
    D = np.diag(S) + alpha * (Uw * Sw)
    U1, S1, V1t = np.linalg.svd(D)
    out = pywt.idwt2((idct2((U * S1) @ Vt), (LH, HL, HH)), "haar")[:host.shape[0], :host.shape[1]]
    return np.clip(out, 0, 255), dict(U1=U1, V1t=V1t, S=S, Vtw=Vtw, alpha=alpha, ts=LL.shape, ws=wm.shape)


def ext_pc(img, key):
    LL, _ = pywt.dwt2(img, "haar")
    if LL.shape != key["ts"]:
        LL = resize(LL, key["ts"], anti_aliasing=True, preserve_range=True)
    S1s = np.linalg.svd(dct2(LL), compute_uv=False)
    D = (key["U1"] * S1s) @ key["V1t"]
    W = ((D - np.diag(key["S"])) / key["alpha"]) @ key["Vtw"]
    return np.clip(resize(W, key["ws"], anti_aliasing=True, preserve_range=True) * 255, 0, 255)


if __name__ == "__main__":
    wm, wmB = make_watermark_logo(), make_watermark_logo(text="OTHERLOGO")
    host = np.asarray(Image.open(os.path.join(ROOT, "data", "original", "image_066.png")), dtype=np.float64)
    other = np.asarray(Image.open(os.path.join(ROOT, "data", "original", "image_064.png")), dtype=np.float64)
    for a in (0.1, 1.0, 5.0):
        w, k = emb_pc(host, wm, a)
        wB, kB = emb_pc(host, wmB, a)
        print(f"alpha={a:<4} PSNR={psnr(host, w):6.2f} dB | genuine NC={nc(wm, ext_pc(w, k)):.3f} | "
              f"UNwatermarked host NC={nc(wm, ext_pc(host, k)):.3f} | other image NC={nc(wm, ext_pc(other, k)):.3f} | "
              f"logo B decoded with key A NC_A={nc(wm, ext_pc(wB, k)):.3f}")
