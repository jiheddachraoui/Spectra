"""Semantic classes of SPECTRA (Cityscapes train ids) and conversions between colours and class ids."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

VOID = 255  # unlabelled / unknown pixel; drawn black

CLASSES = [
    ("road", (128, 64, 128)),
    ("sidewalk", (244, 35, 232)),
    ("building", (70, 70, 70)),
    ("wall", (102, 102, 156)),
    ("fence", (190, 153, 153)),
    ("pole", (153, 153, 153)),
    ("traffic light", (250, 170, 30)),
    ("traffic sign", (220, 220, 0)),
    ("vegetation", (107, 142, 35)),
    ("terrain", (152, 251, 152)),
    ("sky", (70, 130, 180)),
    ("person", (220, 20, 60)),
    ("rider", (255, 0, 0)),
    ("car", (0, 0, 142)),
    ("truck", (0, 0, 70)),
    ("bus", (0, 60, 100)),
    ("train", (0, 80, 100)),
    ("motorcycle", (0, 0, 230)),
    ("bicycle", (119, 11, 32)),
]
CLASS_ID = {name: i for i, (name, _) in enumerate(CLASSES)}


def colours_to_ids(rgb: np.ndarray) -> np.ndarray:
    """Colour label image (H, W, 3) -> class ids (H, W); colours not in CLASSES become VOID."""
    key = (rgb[..., 0].astype(np.int32) << 16) | (rgb[..., 1].astype(np.int32) << 8) | rgb[..., 2]
    ids = np.full(rgb.shape[:2], VOID, np.uint8)
    for i, (_, (r, g, b)) in enumerate(CLASSES):
        ids[key == (r << 16 | g << 8 | b)] = i
    return ids


def ids_to_colours(ids: np.ndarray) -> np.ndarray:
    """Class ids (H, W) -> colour label image (H, W, 3); VOID and unknown ids become black."""
    lut = np.zeros((256, 3), np.uint8)
    for i, (_, colour) in enumerate(CLASSES):
        lut[i] = colour
    return lut[ids]


def read_labels(path: str | Path) -> np.ndarray:
    """Read a label PNG: RGB in the colours above, or single channel with class ids (255 = void)."""
    img = Image.open(path)
    if img.mode in ("L", "P", "I", "I;16"):
        return np.asarray(img).astype(np.uint8)
    return colours_to_ids(np.asarray(img.convert("RGB")))
