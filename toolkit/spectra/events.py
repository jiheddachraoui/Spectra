"""Reading the SPECTRA event files (events/left.h5, events/right.h5) by time window.

Layout: datasets events/x, events/y, events/p, events/t, ms_to_idx, t_offset. `t` is in microseconds after
`t_offset`, so the absolute time is t_offset + t (µs). ms_to_idx[k] is the index of the first event at or
after millisecond k. Sensor size: 1280 x 720.
"""

from __future__ import annotations

from pathlib import Path

import h5py
import hdf5plugin  # noqa: F401  (registers the compression filters h5py needs to read some files)
import numpy as np

SENSOR_WH = (1280, 720)


class EventFile:
    def __init__(self, path: str | Path):
        self.h5 = h5py.File(path, "r")
        self.t_offset = int(self.h5["t_offset"][0]) if "t_offset" in self.h5 else 0
        self.ms_to_idx = np.asarray(self.h5["ms_to_idx"], np.int64)
        self.n = self.h5["events/t"].shape[0]

    @property
    def t_start_us(self) -> int:
        return self.t_offset

    @property
    def t_end_us(self) -> int:
        return self.t_offset + int(self.h5["events/t"][-1])

    def window(self, t0_us: int, t1_us: int) -> dict:
        """Events with absolute time t0_us <= t < t1_us, as numpy arrays x, y, p, t (t absolute, µs)."""
        r0, r1 = t0_us - self.t_offset, t1_us - self.t_offset
        m0 = int(np.clip(r0 // 1000, 0, self.ms_to_idx.size - 1))
        m1 = int(np.clip(-(-r1 // 1000), 0, self.ms_to_idx.size))
        i0 = int(self.ms_to_idx[m0])
        i1 = int(self.ms_to_idx[m1]) if m1 < self.ms_to_idx.size else self.n
        t = np.asarray(self.h5["events/t"][i0:i1], np.int64)
        a, b = np.searchsorted(t, r0, "left"), np.searchsorted(t, r1, "left")
        out = {k: np.asarray(self.h5[f"events/{k}"][i0 + a : i0 + b]) for k in "xyp"}
        out["t"] = t[a:b] + self.t_offset
        return out

    def close(self):
        self.h5.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def render(events: dict, wh=SENSOR_WH) -> np.ndarray:
    """Event frame (H, W, 3, BGR): white background, positive events blue, negative red (last event wins).

    Same colours as the released event previews.
    """
    w, h = wh
    img = np.full((h, w, 3), 255, np.uint8)
    x, y, p = events["x"].astype(np.int64), events["y"].astype(np.int64), events["p"]
    ok = (x >= 0) & (x < w) & (y >= 0) & (y < h)
    img[y[ok], x[ok]] = np.where(p[ok, None] > 0, [255, 0, 0], [0, 0, 255]).astype(np.uint8)
    return img
