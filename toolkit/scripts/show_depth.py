#!/usr/bin/env python3
"""Draw the dense depth on the rectified left image (PNG per frame, or one MP4 video).

    python scripts/show_depth.py --root /path/to/SPECTRA --seq 2024-10-24-08-15-20 --out depth_view.mp4
    python scripts/show_depth.py --root ... --seq ... --out depth_view/ --every 10       # PNGs

Colour: near = red/yellow, far = blue (up to --max-depth metres); no depth = image only.
"""

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import spectra as sp  # noqa: E402


def overlay(rect_bgr: np.ndarray, depth: np.ndarray, max_depth: float, alpha: float = 0.6) -> np.ndarray:
    valid = depth > 0
    norm = np.clip(depth / max_depth, 0, 1)
    colour = cv2.applyColorMap((255 * (1 - norm)).astype(np.uint8), cv2.COLORMAP_JET)
    out = rect_bgr.copy()
    out[valid] = (alpha * colour[valid] + (1 - alpha) * rect_bgr[valid]).astype(np.uint8)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True)
    ap.add_argument("--seq", required=True)
    ap.add_argument("--out", required=True, help="a .mp4 file, or a folder for PNGs")
    ap.add_argument("--every", type=int, default=1, help="use every N-th pair")
    ap.add_argument("--max-depth", type=float, default=50.0)
    args = ap.parse_args()

    seq = sp.Sequence(args.root, args.seq)
    out = Path(args.out)
    video = out.suffix.lower() == ".mp4"
    writer = None
    if not video:
        out.mkdir(parents=True, exist_ok=True)
    n = 0
    for pair in seq.pairs[:: args.every]:
        depth = seq.depth(pair["stem"])
        if depth is None:
            continue
        img = overlay(seq.rig.rectify_image(seq.rgb(pair, "left"), "left"), depth, args.max_depth)
        if video:
            if writer is None:
                h, w = img.shape[:2]
                writer = cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*"mp4v"), 20 / args.every, (w, h))
            writer.write(img)
        else:
            cv2.imwrite(str(out / f"{pair['stem']}.png"), img)
        n += 1
    if writer is not None:
        writer.release()
    print(f"{n} frames written to {out}")


if __name__ == "__main__":
    main()
