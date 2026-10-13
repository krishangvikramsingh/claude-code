"""
logo.py
=======
Procedural binary watermark logo (moved out of run_experiment.py unchanged so that
every script uses exactly the same watermark; no external/copyrighted asset).
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def make_watermark_logo(size=64, text="CYBERION"):
    """Procedurally generate a binary logo watermark (no external/copyrighted asset)."""
    img = Image.new("L", (size * 4, size), color=0)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    draw.rectangle([0, 0, size * 4 - 1, size - 1], outline=255, width=3)
    draw.text((10, size // 2 - 6), text, fill=255, font=font)
    img = img.resize((size, size))
    arr = np.array(img).astype(np.float64)
    arr = (arr > 100).astype(np.float64) * 255.0
    return arr
