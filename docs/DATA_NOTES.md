# SPECTRA data notes

Facts a user needs to interpret the data correctly. Sequence ids are the release ids; the original recording
name is in brackets (`sequences.csv`, column `recording_name`).

## Timing

- The RGB cameras are wired to the 20 Hz trigger. The stored RGB timestamps are **PC-clock** times, not trigger
  times.
- In 2024 the left and right frames were taken together (within 0.4 ms). In the 2025-07-22 session the right
  camera exposes **3.6 ms to 22 ms after the left**, growing through the session. `pairs.csv` gives each pair and
  both timestamps.
- The event-camera trigger is **GPS-aligned** and records two edges per RGB exposure (`events/trigger.txt`).
- The event time is `t_offset + t` (µs).
- A mapping of the RGB, event, LiDAR and INS clocks to one time axis is not part of this release. Event, PC, LiDAR
  and INS clocks are not mapped to one another beyond what the bag stamps give.

## Stereo rectification

- Residual yaw at most 1.5 px on 23 sequences; 1.6 to 2.1 px on `2024-10-03-15-01-07` (street_03),
  `2025-07-22-15-51-18` and `2025-07-22-16-44-09`.
- For the night sequence (`2024-11-28-18-25-59`, night_suburbs2) the yaw could not be measured: 10.7 px is applied
  (the 2024-11 day sequences have 10.6 to 11.6 px); the true value is probably between 11 and 16 px.
- A vertical offset of 0.9 to 2.4 px between the rectified images remains (3.2 px at night).
- Each sequence's values are in its `calib.yaml`.

## Depth

- Depth is **pseudo ground truth** from the LiDAR map, up to 50 m.
- On 1,739 of 31,031 frames (5.6 %) the map could not be confirmed on the live LiDAR sweeps, so their depth is
  empty (all values 0); they are the rows with `m2s_src` = `unsure` in `depth/frames.csv`.
- Three frames have no moving-object mask; their depth is valid.
- Not every stereo pair has a depth file (31,031 of 31,206 do). Always test that a file exists.

## Disparity

- `depth/disparity/<stem>.png` is computed from `depth/dense` with disparity = f · B / depth, so it exists exactly
  where the dense depth exists, and it is empty on the frames whose depth is empty.
- 16-bit PNG, disparity in pixels = value / 64, 0 = none, on the rectified left image.
- It inherits the depth's limits: no disparity beyond 50 m (sky, far background) or where the LiDAR did not see.

## Semantic segmentation

- The labels are automatic (a network trained on Cityscapes), one per RGB image, on the raw images.
- About 3 to 6 % of the pixels of the left and right labels carry colours outside the 19 Cityscapes classes;
  treat them as unknown (the toolkit maps them to void, 255).
- Right labels generated with the toolkit (`toolkit/scripts/label_right.py`) are derived from the left labels and
  the disparity; their source map says which pixels were moved with measured disparity, with completed disparity,
  or filled.

## Frame rate and gaps

- 10 sequences have camera frame drops, and two have short recorder gaps on every sensor: `2025-07-22-16-02-25`
  and `2024-11-29-11-13-51` (tunnel_day2).
- Do not assume a constant frame rate; `pairs.csv` lists only real pairs. Frame counts per sequence are in
  `sequences.csv`.

## Event files and trigger

- `2025-07-22-16-48-53` and `2025-07-22-16-56-39` have extra edges in `events/trigger.txt`; filter them by the
  50 ms period or use the RGB timestamps.
- Some 2025 event files begin with a few stray events long before the real stream. The absolute time
  `t_offset + t` is correct; the real stream starts at the first trigger edge.
- The event-camera extrinsics come from Kalibr and were not checked on the driving data.

## Raw bags

- The 2024 bags have no `/ixblue_ins_driver/standard/timereference` topic.
- RGB file names in the release are the bag record times (ns) of the image messages.

## Short sequences

- `2024-10-24-08-15-20` (dawn_01, 4.7 s) and `2025-07-22-15-51-18` (7.9 s).
