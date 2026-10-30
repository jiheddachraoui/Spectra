#!/usr/bin/env python3
"""Make full semantic labels for the right RGB camera from left-camera labels.

    python scripts/label_right.py --root /path/to/SPECTRA --seq 2024-10-24-08-15-34 --out right_labels
    python scripts/label_right.py --root /path/to/SPECTRA --seq all --out right_labels
    python scripts/label_right.py --root ... --seq ... --left-labels my_predictions/ --out ...

Left labels: by default the released ones (sequences/<id>/semantic/left); with --left-labels any folder
of label PNGs named <stamp>.png or seg_map_<stamp>.png (colours as in spectra/semantic.py, or class ids).

Writes to <out>/<id>/:
    <right stamp>.png          right labels, colours (black = void)
    ids/<right stamp>.png      right labels, class ids (255 = void)              with --save-ids
    source/<right stamp>.png   0 = measured disparity, 1 = completed, 2 = filled  with --save-source
Frames without a left label or without disparity are skipped. Method: spectra/stereo_labels.py.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import spectra as sp  # noqa: E402


def left_label(seq: sp.Sequence, pair: dict, folder: Path | None):
    if folder is None:
        return seq.semantic(pair, "left")
    stamp = Path(pair["left_file"]).stem
    for name in (f"{stamp}.png", f"seg_map_{stamp}.png"):
        if (folder / name).exists():
            return sp.read_labels(folder / name)
    return None


def run(root: Path, seq_id: str, args) -> None:
    seq = sp.Sequence(root, seq_id)
    out = Path(args.out) / seq_id
    out.mkdir(parents=True, exist_ok=True)
    for sub, on in (("ids", args.save_ids), ("source", args.save_source)):
        if on:
            (out / sub).mkdir(exist_ok=True)
    folder = Path(args.left_labels) / seq_id if args.left_labels and args.per_sequence else (
        Path(args.left_labels) if args.left_labels else None)
    done = skipped = 0
    for pair in seq.pairs:
        left = left_label(seq, pair, folder)
        disp = seq.disparity(pair["stem"])
        if left is None or disp is None:
            skipped += 1
            continue
        right, source = sp.label_right(seq.rig, left, disp)
        name = f"{Path(pair['right_file']).stem}.png"
        Image.fromarray(sp.ids_to_colours(right)).save(out / name)
        if args.save_ids:
            Image.fromarray(right).save(out / "ids" / name)
        if args.save_source:
            Image.fromarray(source).save(out / "source" / name)
        done += 1
    print(f"{seq_id}: {done} right label maps in {out} ({skipped} pairs skipped: no left label or no disparity)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, help="the SPECTRA folder (holds sequences/)")
    ap.add_argument("--seq", required=True, help="sequence id, or 'all'")
    ap.add_argument("--out", required=True)
    ap.add_argument("--left-labels", help="folder of left label PNGs instead of the released ones")
    ap.add_argument("--per-sequence", action="store_true", help="--left-labels has one sub-folder per sequence id")
    ap.add_argument("--save-ids", action="store_true")
    ap.add_argument("--save-source", action="store_true")
    args = ap.parse_args()
    ids = sp.sequence_ids(args.root) if args.seq == "all" else [args.seq]
    for seq_id in ids:
        run(Path(args.root), seq_id, args)


if __name__ == "__main__":
    main()
