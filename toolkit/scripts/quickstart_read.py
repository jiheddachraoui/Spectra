#!/usr/bin/env python3
"""Open one SPECTRA sequence and print what one stereo frame contains.

    python scripts/quickstart_read.py --root /path/to/SPECTRA --seq 2024-10-24-08-15-20
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import spectra as sp  # noqa: E402

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--root", required=True, help="the SPECTRA folder (holds sequences/)")
ap.add_argument("--seq", required=True)
args = ap.parse_args()

seq = sp.Sequence(args.root, args.seq)
# not every pair has depth: take the first one that does
pair = next(p for p in seq.pairs if seq.depth(p["stem"]) is not None)
stem = pair["stem"]

left, right = seq.rgb(pair, "left"), seq.rgb(pair, "right")          # raw images, BGR
labels = seq.semantic(pair, "left")                                   # class ids, raw left image
depth = seq.depth(stem)                                               # metres, rectified left image
disp = seq.disparity(stem)                                            # pixels, rectified left image
left_rect = seq.rig.rectify_image(left, "left")                       # draw depth on this one

print(f"sequence {seq.id}: {len(seq.pairs)} stereo pairs; frame {stem}")
print(f"  rgb left {left.shape}, right {right.shape}; right minus left stamp {float(pair['dt_ms']):.1f} ms")
if labels is not None:
    present = [sp.CLASSES[i][0] for i in np.unique(labels) if i != sp.VOID]
    print(f"  semantic: {len(present)} classes ({', '.join(present)})")
valid = depth > 0
print(f"  depth: {valid.mean():.0%} of pixels, {depth[valid].min():.1f} to {depth[valid].max():.1f} m")
if disp is not None:
    print(f"  disparity: {disp[disp > 0].min():.1f} to {disp.max():.1f} px")

with seq.events("left") as ev:
    t0 = int(pair["t_left_ns"]) // 1000                               # RGB stamp, ns -> µs
    win = ev.window(t0 - 25_000, t0 + 25_000)                         # 50 ms around the left exposure
    print(f"  events: {win['t'].size} left events in the 50 ms around this frame "
          f"(file covers {(ev.t_end_us - ev.t_start_us) / 1e6:.1f} s)")
traj = seq.trajectory()
print(f"  trajectory: {len(traj)} poses over {traj[-1, 0] - traj[0, 0]:.1f} s")
