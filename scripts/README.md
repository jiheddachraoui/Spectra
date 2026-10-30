# Original processing scripts

These are the scripts used while recording and preparing SPECTRA. They are kept for reference and are not
maintained. **For working with the dataset, use the [toolkit](../toolkit/README.md)**: it reads the release tree
and replaces the scripts marked below.

Some scripts have the bag file name written inside (`extract_map.py`, `get_traj_csv.py`, ...): edit it before
running. Most need ROS 1 (`rosbag`).

## `rosbag/`: work on the raw bags (`raw/<id>.bag`)

| Script | Output | Toolkit equivalent |
|---|---|---|
| `bag_to_image.py` | RGB images, named by bag time | `raw_bag.py images` (same files as the release) |
| `event_topic_to_h5.py` | one event camera to HDF5 | `raw_bag.py events` (same files as the release) |
| `extract_timestamp.py` | trigger edges to text | `raw_bag.py trigger` (same file as the release) |
| `lidar_to_bin.py` | LiDAR scans to `.bin` / `.pcd` (needs open3d, ros_numpy) | `raw_bag.py lidar` (`.bin` only) |
| `get_traj_csv.py`, `get_trajectory.py` | GNSS track to CSV | `raw_bag.py gnss` |
| `get_map.py`, `get_map_satellite.py`, `extract_map.py` | GNSS track drawn on a map | |
| `2event_to_hdf5.py` | both event cameras and triggers in one HDF5 (not the release layout) | |
| `rostohdf5.py` | INS messages to HDF5 | |
| `bag_to_video_rgb.py`, `bag_to_video_event.py`, `bag_to_video_event_optimized.py`, `event_to_video.py` | preview videos | |
| `filter_lidar.py` | copy of a bag without some topics | |
| `event_per_second.py`, `event_to_graph.py` | event-rate plots | |
| `bin2pcd.py`, `extract_pcd_png.py`, `concat_2videos.py`, `rename_files.py`, `annotate.py` | small utilities | |

## `rosbag/h5_to_video.py`: works on the release event files

Renders `events/left.h5` or `right.h5` as a video. Toolkit equivalent: `render_events.py` (no numba or
scikit-video needed).

## `depth_map/`: first depth-map pipeline

The first version of the LiDAR-to-image depth projection. The released depth (`depth/`) was made with a later
pipeline described in the main README; these scripts are kept to document the history only.
