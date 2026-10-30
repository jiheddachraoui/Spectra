#!/usr/bin/env python3
"""Render an event file of SPECTRA as a video (one frame per time window).

    python scripts/render_events.py --root /path/to/SPECTRA --seq 2024-10-24-08-15-20 --side left \
        --out events_left.mp4 --window-ms 50

Positive events blue, negative red, on white (same colours as the released previews).
"""

import argparse
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import spectra as sp  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True)
    ap.add_argument("--seq", required=True)
    ap.add_argument("--side", choices=("left", "right"), default="left")
    ap.add_argument("--out", required=True, help="output .mp4")
    ap.add_argument("--window-ms", type=float, default=50.0)
    ap.add_argument("--max-seconds", type=float, default=0, help="stop after this many seconds (0 = all)")
    args = ap.parse_args()

    seq = sp.Sequence(args.root, args.seq)
    step = int(args.window_ms * 1000)
    w, h = sp.events.SENSOR_WH
    writer = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*"mp4v"), 1000.0 / args.window_ms, (w, h))
    with seq.events(args.side) as ev:
        end = ev.t_end_us if not args.max_seconds else min(ev.t_end_us, ev.t_start_us + int(args.max_seconds * 1e6))
        n = 0
        for t0 in range(ev.t_start_us, end - step + 1, step):
            writer.write(sp.render(ev.window(t0, t0 + step)))
            n += 1
    writer.release()
    print(f"{n} frames ({args.window_ms:g} ms each) written to {args.out}")


if __name__ == "__main__":
    main()
