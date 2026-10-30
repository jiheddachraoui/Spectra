#!/usr/bin/env python3
"""Extract data from a raw SPECTRA recording (sequences/<id>/raw/<id>.bag, ROS 1).

    python scripts/raw_bag.py info    BAG
    python scripts/raw_bag.py images  BAG --side left  --out rgb_left/        # <bag time ns>.png, as in rgb/left
    python scripts/raw_bag.py events  BAG --side left  --out left.h5          # same layout as events/left.h5
    python scripts/raw_bag.py trigger BAG              --out trigger.txt      # as events/trigger.txt
    python scripts/raw_bag.py lidar   BAG              --out lidar/           # <bag time ns>.bin, float32 x y z intensity
    python scripts/raw_bag.py gnss    BAG              --out gnss.csv         # INS position fixes

Needs the ROS 1 Python package `rosbag` (ROS Noetic, or `pip install --extra-index-url
https://rospypi.github.io/simple rosbag`). The message packages of the cameras and the INS are not needed.
"""

import argparse
import csv
import os
import sys

import numpy as np

TOPICS = {
    "image_left": "/stereo/left/image_color",
    "image_right": "/stereo/right/image_color",
    "events_left": "/prophesee/camera1_master/cd_events_buffer",
    "events_right": "/prophesee/camera2_slave/cd_events_buffer",
    "trigger": "/prophesee/camera1_master/trigger_event",
    "lidar": "/ouster/points",
    "gnss": "/ixblue_ins_driver/standard/navsatfix",
}


def open_bag(path):
    try:
        import rosbag
    except ImportError:
        sys.exit("needs the ROS 1 package 'rosbag' (see the help of this script)")
    return rosbag.Bag(path, "r")


def cmd_info(args):
    with open_bag(args.bag) as bag:
        info = bag.get_type_and_topic_info()
        print(f"{args.bag}: {bag.get_end_time() - bag.get_start_time():.1f} s")
        for topic, t in sorted(info.topics.items()):
            print(f"  {topic:<46} {t.msg_type:<38} {t.message_count:>8} msgs")


def image_from_msg(msg):
    h, w = msg.height, msg.width
    data = np.frombuffer(msg.data, np.uint8)
    if msg.encoding in ("bgr8", "rgb8"):
        img = data.reshape(h, msg.step)[:, : w * 3].reshape(h, w, 3)
        return img[..., ::-1] if msg.encoding == "rgb8" else img
    if msg.encoding == "mono8":
        return data.reshape(h, msg.step)[:, :w]
    raise ValueError(f"image encoding {msg.encoding} not handled")


def cmd_images(args):
    import cv2

    os.makedirs(args.out, exist_ok=True)
    n = 0
    with open_bag(args.bag) as bag:
        for _, msg, t in bag.read_messages(topics=[TOPICS[f"image_{args.side}"]]):
            # the released file names are the bag record times, in ns
            cv2.imwrite(os.path.join(args.out, f"{t.to_nsec()}.png"), image_from_msg(msg))
            n += 1
    print(f"{n} images written to {args.out}")


def cmd_events(args):
    """Write events in the layout of the release: events/{x,y,p,t}, ms_to_idx, t_offset (t in µs after t_offset)."""
    import h5py
    import hdf5plugin

    out = h5py.File(args.out, "w")
    comp = hdf5plugin.Zstd()
    for k, dt in (("x", "u2"), ("y", "u2"), ("p", "u1"), ("t", "u4")):
        out.create_dataset(f"events/{k}", shape=(0,), maxshape=(None,), dtype=dt, chunks=(1 << 20,), **comp)
    t0_ns = None
    buf = {k: [] for k in "xypt"}
    buffered = written = 0
    ms_to_idx = []

    def flush():
        nonlocal buffered, written
        if not buffered:
            return
        arrays = {k: np.concatenate(v) for k, v in buf.items()}
        t = arrays["t"]
        # ms_to_idx[k] = index of the first event with t >= k ms
        first_ms = len(ms_to_idx)
        last_ms = int(t[-1]) // 1000
        if last_ms >= first_ms:
            ms = np.arange(first_ms, last_ms + 1, dtype=np.int64) * 1000
            ms_to_idx.extend((written + np.searchsorted(t, ms, "left")).tolist())
        for k, a in arrays.items():
            ds = out[f"events/{k}"]
            ds.resize((written + a.size,))
            ds[written:] = a
            buf[k].clear()
        written += t.size
        buffered = 0

    with open_bag(args.bag) as bag:
        for _, msg, _ in bag.read_messages(topics=[TOPICS[f"events_{args.side}"]]):
            if not msg.events:
                continue
            ts = np.fromiter((e.ts.to_nsec() for e in msg.events), np.int64, len(msg.events))
            if t0_ns is None:
                t0_ns = int(ts[0])
            buf["t"].append(((ts - t0_ns) // 1000).astype(np.uint32))
            buf["x"].append(np.fromiter((e.x for e in msg.events), np.uint16, len(msg.events)))
            buf["y"].append(np.fromiter((e.y for e in msg.events), np.uint16, len(msg.events)))
            buf["p"].append(np.fromiter((e.polarity for e in msg.events), np.uint8, len(msg.events)))
            buffered += len(msg.events)
            if buffered >= 5_000_000:
                flush()
    flush()
    if t0_ns is None:
        sys.exit("no events on this topic")
    out.create_dataset("ms_to_idx", data=np.asarray(ms_to_idx, np.uint64), **comp)
    out.create_dataset("t_offset", data=np.asarray([t0_ns // 1000], np.int64))
    out.close()
    print(f"{written} events written to {args.out}")


def cmd_trigger(args):
    with open_bag(args.bag) as bag, open(args.out, "w") as f:
        n = 0
        for _, msg, _ in bag.read_messages(topics=[TOPICS["trigger"]]):
            ts = msg.ts if isinstance(msg.ts, int) else msg.ts.to_nsec()
            f.write(f"{ts}\n")
            n += 1
    print(f"{n} trigger edges written to {args.out}")


_PC2_TYPES = {1: "i1", 2: "u1", 3: "i2", 4: "u2", 5: "i4", 6: "u4", 7: "f4", 8: "f8"}


def cmd_lidar(args):
    os.makedirs(args.out, exist_ok=True)
    n = 0
    with open_bag(args.bag) as bag:
        for _, msg, t in bag.read_messages(topics=[TOPICS["lidar"]]):
            fields = {f.name: (_PC2_TYPES[f.datatype], f.offset) for f in msg.fields}
            names = ["x", "y", "z", "intensity"]
            dtype = np.dtype({"names": names, "formats": [fields[k][0] for k in names],
                              "offsets": [fields[k][1] for k in names], "itemsize": msg.point_step})
            pts = np.frombuffer(msg.data, dtype, msg.width * msg.height)
            xyzi = np.stack([pts[k].astype(np.float32) for k in names], axis=1)  # all points, (0,0,0) = no return
            xyzi.tofile(os.path.join(args.out, f"{t.to_nsec()}.bin"))
            n += 1
    print(f"{n} scans written to {args.out} (float32 x y z intensity, LiDAR frame, metres)")


def cmd_gnss(args):
    with open_bag(args.bag) as bag, open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["bag_time_ns", "stamp_ns", "latitude", "longitude", "altitude", "status"])
        n = 0
        for _, msg, t in bag.read_messages(topics=[TOPICS["gnss"]]):
            w.writerow([t.to_nsec(), msg.header.stamp.to_nsec(), f"{msg.latitude:.9f}", f"{msg.longitude:.9f}",
                        f"{msg.altitude:.3f}", msg.status.status])
            n += 1
    print(f"{n} fixes written to {args.out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn, side, out in (
        ("info", cmd_info, False, False),
        ("images", cmd_images, True, True),
        ("events", cmd_events, True, True),
        ("trigger", cmd_trigger, False, True),
        ("lidar", cmd_lidar, False, True),
        ("gnss", cmd_gnss, False, True),
    ):
        p = sub.add_parser(name)
        p.add_argument("bag")
        if side:
            p.add_argument("--side", choices=("left", "right"), default="left")
        if out:
            p.add_argument("--out", required=True)
        p.set_defaults(fn=fn)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
