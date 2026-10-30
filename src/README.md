# Recording and processing code

The code used to record SPECTRA and to build its LiDAR maps and labels. It is kept so that the processing can be
reproduced; **for working with the released data, use the [toolkit](../toolkit/README.md)**.

| Folder | What it is | Used for |
|---|---|---|
| [`prophesee_ros_wrapper/`](prophesee_ros_wrapper) | ROS 1 driver for the two Prophesee event cameras (master/slave, trigger input) | recording the `/prophesee/...` topics of the raw bags |
| [`faster-lio/`](faster-lio) | Faster-LIO LiDAR-inertial odometry, with an `ouster32` configuration for the Ouster OS1-32 | `lidar_ins/scans.pcd` and `lidar_ins/traj.txt` |
| [`Image-Segmentation/`](Image-Segmentation/README.md) | semantic segmentation of the RGB images with MMSegmentation | `semantic/{left,right}/` |

Each folder has its own build instructions (catkin workspace for the ROS packages, pip for the segmentation).

## Faster-LIO on a SPECTRA bag

Build `faster-lio` and `prophesee_ros_wrapper/prophesee_event_msgs` in a catkin workspace, then:

```bash
rosbag play raw/<id>.bag                         # terminal 1
roslaunch faster_lio mapping_ouster32.launch     # terminal 2: writes scans.pcd and the trajectory
```

A bag-splitting/merging tool (a modified `mpl_dataset_toolbox`) was also used during recording; it is not
included here.
