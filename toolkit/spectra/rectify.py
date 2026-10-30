"""Stereo rectification of the RGB pair, from a sequence's calib.yaml (section stereo_rectification).

The released RGB images and semantic labels are on the raw (distorted) images. Depth, the support and
moving masks, and the disparity are on the rectified left image.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import yaml

from .semantic import VOID


class StereoRig:
    def __init__(self, calib_yaml: str | Path):
        calib = yaml.safe_load(open(calib_yaml))
        rect = calib["stereo_rectification"]
        self.size = tuple(rect["image_size_wh"])  # (W, H)
        self.K, self.dist, self.R, self.P = {}, {}, {}, {}
        for side in ("left", "right"):
            cam = calib["cameras"][f"rgb_{side}"]
            fu, fv, cu, cv = cam["intrinsics_fu_fv_cu_cv"]
            self.K[side] = np.array([[fu, 0, cu], [0, fv, cv], [0, 0, 1]], np.float64)
            self.dist[side] = np.array(cam["distortion"], np.float64)
            self.R[side] = np.array(rect[f"R_rect_{side}"], np.float64)
            self.P[side] = np.array(rect[f"P_rect_{side}"], np.float64)
        self.baseline_m = float(rect["baseline_m"])
        self.focal_px = float(self.P["left"][0, 0])
        self._rect_maps: dict = {}
        self._raw_maps: dict = {}

    def rect_maps(self, side: str):
        """For every rectified pixel: where to read in the raw image (cv2.remap maps)."""
        if side not in self._rect_maps:
            self._rect_maps[side] = cv2.initUndistortRectifyMap(
                self.K[side], self.dist[side], self.R[side], self.P[side][:, :3], self.size, cv2.CV_32FC1
            )
        return self._rect_maps[side]

    def raw_maps(self, side: str):
        """For every raw pixel: where to read in the rectified image (cv2.remap maps)."""
        if side not in self._raw_maps:
            w, h = self.size
            u, v = np.meshgrid(np.arange(w, dtype=np.float64), np.arange(h, dtype=np.float64))
            pts = np.stack([u.ravel(), v.ravel()], axis=-1)[:, None, :]
            rect = cv2.undistortPoints(
                pts, self.K[side], self.dist[side], R=self.R[side], P=self.P[side][:, :3]
            )[:, 0, :]
            self._raw_maps[side] = (
                rect[:, 0].reshape(h, w).astype(np.float32),
                rect[:, 1].reshape(h, w).astype(np.float32),
            )
        return self._raw_maps[side]

    def rectify_image(self, raw: np.ndarray, side: str) -> np.ndarray:
        mx, my = self.rect_maps(side)
        return cv2.remap(raw, mx, my, cv2.INTER_LINEAR)

    def rectify_labels(self, raw_ids: np.ndarray, side: str, fill: int = VOID) -> np.ndarray:
        """Nearest neighbour only: class ids must never be interpolated."""
        mx, my = self.rect_maps(side)
        return cv2.remap(raw_ids, mx, my, cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=fill)

    def unrectify_labels(self, rect_ids: np.ndarray, side: str, fill: int = VOID) -> np.ndarray:
        mx, my = self.raw_maps(side)
        return cv2.remap(rect_ids, mx, my, cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=fill)

    def depth_to_disparity(self, depth_m: np.ndarray) -> np.ndarray:
        """Disparity (px) of the rectified left image; 0 where depth is 0. disparity = f * B / depth."""
        disp = np.zeros(depth_m.shape, np.float32)
        ok = depth_m > 0
        disp[ok] = -self.P["right"][0, 3] / depth_m[ok]
        return disp
