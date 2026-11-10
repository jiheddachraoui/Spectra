"""Access to one SPECTRA sequence in the release tree:

    SPECTRA/sequences/<id>/
        calib.yaml, pairs.csv
        rgb/{left,right}/<stamp>.png          raw images
        semantic/{left,right}/                labels on the raw images, one per image (same stamp)
        depth/{dense,sparse,support,moving,disparity}/<stem>.png   rectified left frame
        events/{left,right}.h5, events/trigger.txt
        lidar_ins/traj.txt, lidar_ins/scans.pcd

Left and right frames are matched only through pairs.csv (stem -> right_file), never by name.
Not every pair has depth / disparity: the readers return None when a file is missing.
"""

from __future__ import annotations

import csv
from functools import cached_property
from pathlib import Path

import cv2
import numpy as np
import yaml

from .events import EventFile
from .rectify import StereoRig
from .semantic import read_labels

DEPTH_SCALE = 256.0  # depth/dense, depth/sparse: metres = value / 256
DISPARITY_SCALE = 64.0  # depth/disparity: pixels = value / 64


class Sequence:
    def __init__(self, root: str | Path, seq_id: str):
        self.id = seq_id
        self.dir = Path(root) / "sequences" / seq_id
        if not self.dir.is_dir():
            raise FileNotFoundError(f"no sequence folder {self.dir}")

    @cached_property
    def pairs(self) -> list:
        """Rows of pairs.csv: stem, left_file, right_file, t_left_ns, t_right_ns, dt_ms, residual_ms."""
        with open(self.dir / "pairs.csv") as f:
            return list(csv.DictReader(f))

    @cached_property
    def calib(self) -> dict:
        return yaml.safe_load(open(self.dir / "calib.yaml"))

    @cached_property
    def rig(self) -> StereoRig:
        return StereoRig(self.dir / "calib.yaml")

    # ---- images and labels (raw camera frames)

    def rgb(self, pair: dict, side: str = "left") -> np.ndarray:
        """BGR image (OpenCV order) of the left or right camera for a row of pairs.csv."""
        return cv2.imread(str(self.dir / "rgb" / side / pair[f"{side}_file"]), cv2.IMREAD_COLOR)

    def semantic_path(self, pair: dict, side: str = "left") -> Path | None:
        stamp = Path(pair[f"{side}_file"]).stem
        folder = self.dir / "semantic" / side
        for name in (f"{stamp}.png", f"seg_map_{stamp}.png"):
            if (folder / name).exists():
                return folder / name
        return None

    def semantic(self, pair: dict, side: str = "left") -> np.ndarray | None:
        """Class ids (Cityscapes train ids, 255 = void) or None if there is no label file."""
        path = self.semantic_path(pair, side)
        return None if path is None else read_labels(path)

    # ---- depth layers (rectified left frame)

    def _png(self, layer: str, stem: str) -> np.ndarray | None:
        path = self.dir / "depth" / layer / f"{stem}.png"
        return cv2.imread(str(path), cv2.IMREAD_UNCHANGED) if path.exists() else None

    def depth(self, stem: str, layer: str = "dense") -> np.ndarray | None:
        """Depth in metres (0 = none) of layer dense or sparse."""
        raw = self._png(layer, stem)
        return None if raw is None else raw.astype(np.float32) / DEPTH_SCALE

    def disparity(self, stem: str) -> np.ndarray | None:
        """Disparity in pixels (0 = none). Rectified left (x, y) matches rectified right (x - d, y)."""
        raw = self._png("disparity", stem)
        return None if raw is None else raw.astype(np.float32) / DISPARITY_SCALE

    def support(self, stem: str) -> np.ndarray | None:
        """0 = measured LiDAR point, 1..254 = px to the nearest measured pixel, 255 = no depth."""
        return self._png("support", stem)

    def moving(self, stem: str) -> np.ndarray | None:
        """255 = depth on a moving object, 0 = not."""
        return self._png("moving", stem)

    # ---- events, trigger, trajectory

    def events(self, side: str = "left") -> EventFile:
        return EventFile(self.dir / "events" / f"{side}.h5")

    def trigger_ns(self) -> np.ndarray:
        """Trigger edges of the left event camera (ns), two per 50 ms cycle."""
        return np.loadtxt(self.dir / "events" / "trigger.txt", dtype=np.int64, ndmin=1)

    def trajectory(self) -> np.ndarray:
        """lidar_ins/traj.txt as an (N, 8) array: timestamp_s, x, y, z, qx, qy, qz, qw (IMU pose in the map frame)."""
        return np.loadtxt(self.dir / "lidar_ins" / "traj.txt", comments="#", ndmin=2)


def sequence_ids(root: str | Path) -> list:
    """Ids of the sequences found under <root>/sequences."""
    return sorted(p.name for p in (Path(root) / "sequences").iterdir() if p.is_dir())
