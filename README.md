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
# Default usage (topics & fps are fixed inside the script)
python scripts/rosbag/bag_to_video.py data/raw/<your_sequence>.bag

```
The ouput is a video .avi with teh same name of the Rosbag. If you wish to extract teh frames from the videos with no loss 
 you can follow thsi snippet : 

 ```bash
# --- edit these variables ---
VID="data/raw/sequence01.stereo_rgb.avi"   # input stereo video (left|right are side-by-side)
START="00:00:36.000"                       # start timestamp (HH:MM:SS.mmm)
END="00:00:37.000"                         # end timestamp (HH:MM:SS.mmm)  (or use DUR below)
# DUR="1.000"                              # duration in seconds, alternative to END
SIDE="left"                                # left | right
OUT_DIR="data/processed/seq01/frames_left" # output folder
FPS=""                                     # e.g., 30 to decimate; leave empty for all frames
# -----------------------------------------

mkdir -p "$OUT_DIR"

# Choose crop filter based on SIDE
if [ "$SIDE" = "left" ]; then
  CROP="crop=iw/2:ih:0:0"
else
  CROP="crop=iw/2:ih:iw/2:0"
fi

# Optional FPS filter
if [ -n "$FPS" ]; then
  VF="$CROP,fps=$FPS"
else
  VF="$CROP"
fi

# Extract using START..END (accurate seek). For START..DUR, see the alt command below.
ffmpeg -hide_banner -loglevel error \
  -i "$VID" -ss "$START" -to "$END" \
  -vf "$VF" -vsync 0 -frame_pts 1 \
  "$OUT_DIR/${SIDE}_%010d.png"

# --- Alternative: START + duration (fast seek) ---
# ffmpeg -hide_banner -loglevel error \
#   -ss "$START" -i "$VID" -t "${DUR:-1.0}" \
#   -vf "$VF" -vsync 0 -frame_pts 1 \
#   "$OUT_DIR/${SIDE}_%010d.png"



```
## Step 2 — Extract Event Frames (Left & Right) & .h5 files

To visualize the events in a video format run this in your bash: 

``` bash
python scripts/rosbag/bag_to_video_event_optimized.py \
  data/raw/sequence01.bag \
  /prophesee/camera1_master/cd_events_buffer \
  /prophesee/camera2_slave/cd_events_buffer \
  data/processed/seq01/previews \
  --fps 30
```
Convert the two Prophesee event topics (and triggers) from a ROS bag into a compressed HDF5 file.

```bash
python scripts/rosbag/2event_to_hdf5.py \
  data/raw/sequence01.bag \
  data/processed/seq01/events.h5
```


