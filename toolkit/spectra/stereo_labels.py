"""Full semantic labels for the right RGB camera, made from the left labels and the stereo geometry.

The SPECTRA semantic labels are made on the left RGB camera. `label_right` turns a left label map into a
complete right label map (every pixel the left map labels gets a class), without any segmentation model:

1. The left labels are rectified. Every rectified left pixel gets a disparity:
   - the released disparity (depth/disparity), where the LiDAR depth exists       -> source MEASURED
   - otherwise a completed disparity                                               -> source COMPLETED
       sky: 0 (infinitely far);
       road, sidewalk, terrain: a plane d = a*x + b*y + c fitted to this frame's measured ground disparity;
       anything else: the background (smaller) disparity of the nearest measured pixels in the same row.
2. Every left pixel is moved to x - disparity in the rectified right image. Where several land on the
   same place, the nearest (larger disparity) wins.
3. Right pixels that nothing lands on (surfaces hidden from the left camera, the image border) take the
   class of the background neighbour in the same row                                -> source FILLED
4. The result is mapped back to the raw right image; raw pixels outside the rectified view take the
   nearest class                                                                     -> source FILLED

Pixels that are void in the left map stay void. The source map tells how each right pixel was made.
"""

from __future__ import annotations

import cv2
import numpy as np

from .rectify import StereoRig
from .semantic import CLASS_ID, VOID

MEASURED, COMPLETED, FILLED = 0, 1, 2
GROUND = [CLASS_ID["road"], CLASS_ID["sidewalk"], CLASS_ID["terrain"]]
SKY = CLASS_ID["sky"]


def _row_neighbours(valid: np.ndarray):
    """Column of the nearest valid pixel at or left of each pixel (-1 if none), and at or right (W if none)."""
    h, w = valid.shape
    cols = np.arange(w)[None, :]
    left = np.maximum.accumulate(np.where(valid, cols, -1), axis=1)
    right = np.minimum.accumulate(np.where(valid, cols, w)[:, ::-1], axis=1)[:, ::-1]
    return left, right


def _background_pick(valid: np.ndarray, key: np.ndarray):
    """For every pixel, the column of the row neighbour (left or right valid pixel) with the smaller key.

    Returns (columns, found); columns are only meaningful where found is True.
    """
    h, w = valid.shape
    rows = np.arange(h)[:, None]
    left, right = _row_neighbours(valid)
    kl = np.where(left >= 0, key[rows, np.clip(left, 0, w - 1)], np.inf)
    kr = np.where(right < w, key[rows, np.clip(right, 0, w - 1)], np.inf)
    cols = np.where(kl <= kr, left, right)
    return np.clip(cols, 0, w - 1), np.isfinite(np.minimum(kl, kr))


def _fit_ground_plane(disp: np.ndarray, ground: np.ndarray, min_pixels: int = 500):
    """Least-squares plane d = a*x + b*y + c on measured ground pixels, refined twice without outliers."""
    ys, xs = np.nonzero(ground & (disp > 0))
    if xs.size < min_pixels:
        return None
    if xs.size > 50000:  # a subsample is plenty for 3 parameters
        pick = np.random.default_rng(0).choice(xs.size, 50000, replace=False)
        ys, xs = ys[pick], xs[pick]
    d = disp[ys, xs]
    A = np.stack([xs, ys, np.ones_like(xs)], axis=1).astype(np.float64)
    keep = np.ones(xs.size, bool)
    for _ in range(3):
        coef = np.linalg.lstsq(A[keep], d[keep], rcond=None)[0]
        keep = np.abs(A @ coef - d) < 2.0
        if keep.sum() < min_pixels:
            return None
    return coef


def complete_disparity(left_rect_ids: np.ndarray, disparity: np.ndarray):
    """Disparity for every labelled rectified left pixel. Returns (disparity, source), source as above."""
    disp = disparity.astype(np.float32).copy()
    source = np.full(disp.shape, MEASURED, np.uint8)
    measured = disp > 0
    todo = ~measured & (left_rect_ids != VOID)
    source[todo] = COMPLETED

    sky = todo & (left_rect_ids == SKY)
    disp[sky] = 0.0

    ground = np.isin(left_rect_ids, GROUND)
    coef = _fit_ground_plane(disp, ground)
    rest = todo & ~sky
    if coef is not None:
        ys, xs = np.nonzero(rest & ground)
        pred = coef[0] * xs + coef[1] * ys + coef[2]
        ok = pred > 0
        disp[ys[ok], xs[ok]] = pred[ok]
        rest[ys[ok], xs[ok]] = False

    if measured.any():
        cols, found = _background_pick(measured, np.where(measured, disp, np.inf))
        rows = np.arange(disp.shape[0])[:, None]
        fill = rest & found
        disp[fill] = disp[rows, cols][fill]
        rest &= ~found
        disp[rest] = disp[measured].min()  # rows without any measurement: as far as the farthest point
    else:
        disp[rest] = 0.0
    return disp, source


def warp_to_right(values: np.ndarray, disparity: np.ndarray, use: np.ndarray, fill):
    """Move rectified left pixels (where `use`) to x - disparity in the rectified right image.

    The nearest (larger disparity) wins where several land on one pixel. Also returns the disparity that
    landed on each right pixel (-1 where nothing landed).
    """
    h, w = disparity.shape
    ys, xs = np.nonzero(use)
    d = disparity[ys, xs]
    xr = np.rint(xs - d).astype(np.int64)
    keep = (xr >= 0) & (xr < w)
    ys, xs, xr, d = ys[keep], xs[keep], xr[keep], d[keep]
    order = np.argsort(d, kind="stable")  # ascending: the last write, the nearest, is kept
    ys, xs, xr, d = ys[order], xs[order], xr[order], d[order]
    out = np.full(values.shape, fill, values.dtype)
    out[ys, xr] = values[ys, xs]
    landed = np.full((h, w), -1.0, np.float32)
    landed[ys, xr] = d
    return out, landed


def label_right(rig: StereoRig, left_ids: np.ndarray, disparity: np.ndarray):
    """Left labels (raw left image) + released disparity -> (right labels, source), both on the raw right image."""
    left_rect = rig.rectify_labels(left_ids, "left")
    disp, source = complete_disparity(left_rect, disparity)

    # every pixel is moved; left void pixels stay void on the right but still hide what is behind them
    use = np.ones(disp.shape, bool)
    right_rect, landed = warp_to_right(left_rect, disp, use, VOID)
    right_src, _ = warp_to_right(source, disp, use, FILLED)

    hole = landed < 0
    if hole.any():
        rows = np.arange(hole.shape[0])[:, None]
        cols, found = _background_pick(~hole, np.where(hole, np.inf, landed))
        take = hole & found
        right_rect[take] = right_rect[rows, cols][take]
        # gaps of 1-2 px between landed pixels are rounding cracks, not hidden surfaces: keep their source
        left, right_nb = _row_neighbours(~hole)
        crack = hole & (left >= 0) & (right_nb < hole.shape[1]) & (right_nb - left - 1 <= 2)
        right_src[crack] = right_src[rows, cols][crack]
        right_src[hole & ~crack] = FILLED

    right = rig.unrectify_labels(right_rect, "right", fill=VOID)
    src = rig.unrectify_labels(right_src, "right", fill=VOID)
    outside = src == VOID
    if outside.any() and (~outside).any():
        # nearest class for raw pixels outside the rectified view
        _, nearest = cv2.distanceTransformWithLabels(
            outside.astype(np.uint8), cv2.DIST_L2, 3, labelType=cv2.DIST_LABEL_PIXEL
        )
        inside_vals = right[~outside]
        idx = np.zeros(int(nearest.max()) + 1, np.int64)
        idx[nearest[~outside]] = np.arange(inside_vals.size)
        right[outside] = inside_vals[idx[nearest[outside]]]
        src[outside] = FILLED
    return right, src
