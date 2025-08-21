# SPECTRA Dataset: Sensor and  Ground-Truth Toolkit

This dataset is released as part of the [ANR CERBERE Project](#).

<p align="center">
  <img src="docs/media/sensor_system.png" alt="SPECTRA system overview" width="860">
  <br>
  <em>Figure 1 — The SPECTRA sensor system used for the data aquisition.</em>
</p>


**SPECTRA** is a multimodal dataset designed for autonomous driving research. It features synchronized sensor data collected in real-world driving conditions, enabling research in:

- Perception
- Localization
- Sensor fusion
- Depth estimation


## Sensor Setup

- 📷 **2× Stereo Event Cameras** (Prophesee EVK4)
- 📸 **2× Global Shutter RGB Cameras** (Flir Blackfly S)
- 🌀 **LiDAR** (Ouster32)
- 📍 **RTK GNSS & IMU**
- 🎯 **ATLANS A7 INS** — high-precision ground truth for position and orientation

All sensors are **hardware-synchronized**, including **satellite-based PPS** signals and **external trigger management**.

The sections below are a step-by-step guide to recreate these ground truths from your own ROS bag, using the scripts provided in this repo.

## ROS bag contents
| Topic                                        | Type                              | Description               |
| -------------------------------------------- | --------------------------------- | ------------------------- |
| `/ixblue_ins_driver/ix/ins`                  | `ixblue_ins_msgs/Ins`             | Navigation solution (INS) |
| `/ixblue_ins_driver/standard/imu`            | `sensor_msgs/Imu`                 | IMU (INS unit)            |
| `/ixblue_ins_driver/standard/navsatfix`      | `sensor_msgs/NavSatFix`           | GNSS fix (RTK)            |
| `/ixblue_ins_driver/standard/timereference`  | `sensor_msgs/TimeReference`       | GNSS time reference       |
| `/ouster/imu`                                | `sensor_msgs/Imu`                 | IMU (LiDAR unit)          |
| `/ouster/points`                             | `sensor_msgs/PointCloud2`         | 3D LiDAR point cloud      |
| `/prophesee/camera1_master/cd_events_buffer` | `prophesee_event_msgs/EventArray` | Left event stream         |
| `/prophesee/camera1_master/trigger_event`    | `prophesee_event_msgs/Trigger`    | Left trigger events       |
| `/prophesee/camera2_slave/cd_events_buffer`  | `prophesee_event_msgs/EventArray` | Right event stream        |
| `/stereo/left/image_color`                   | `sensor_msgs/Image`               | Left RGB image            |
| `/stereo/right/image_color`                  | `sensor_msgs/Image`               | Right RGB image           |
| `/synchrobox_msg`                            | `std_msgs/String`                 | Sync box status           |
| `/synchrobox_pin0`                           | `std_msgs/Int64MultiArray`        | Sync box digital pin data |


---
```bash
rosbag info </path/toyourrosbag.bag> 

```

## Step 1 — Extract RGB Frames (Left & Right)

Use the snippet below to extract PNG frames and timestamps from your bag.  
Update only the variables at the top to match your setup.

```bash
#!/usr/bin/env bash
# Extract RGB frames from a SPECTRA rosbag
# Works with ROS1 .bag or ROS2 bag directory (set BAG accordingly)

set -euo pipefail

# --- EDIT THESE ---
BAG="data/raw/<your_rosbag>.bag"             # ROS1: .bag file, ROS2: set to bag directory
OUT="data/processed/<sequence_id>"           # e.g., data/processed/seq01
TOPIC_LEFT="/stereo/left/image_color"        # change if your topic names differ
TOPIC_RIGHT="/stereo/right/image_color"
FPS=30                                       # set 0 to keep all frames (no decimation)
# ---------------

mkdir -p "$OUT/images_left" "$OUT/images_right"

echo "[RGB] Extracting LEFT frames from $TOPIC_LEFT …"
python scripts/02_extract_frames.py \
  --bag  "$BAG" \
  --topic "$TOPIC_LEFT" \
  --out  "$OUT/images_left" \
  --rate "$FPS"

echo "[RGB] Extracting RIGHT frames from $TOPIC_RIGHT …"
python scripts/02_extract_frames.py \
  --bag  "$BAG" \
  --topic "$TOPIC_RIGHT" \
  --out  "$OUT/images_right" \
  --rate "$FPS"

echo "[RGB] Done. Outputs:"
echo "  - $OUT/images_left/*.png"
echo "  - $OUT/images_left/timestamps.txt"
echo "  - $OUT/images_right/*.png"
echo "  - $OUT/images_right/timestamps.txt"

