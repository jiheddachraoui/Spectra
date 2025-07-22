SPECTRA Dataset & Tools

This dataset is released as part of the ANR CERBERE Project: link.
Overview

SPECTRA is a multimodal dataset designed for autonomous driving research. It features synchronized sensor data collected in real-world driving conditions, enabling work on perception, localization, sensor fusion, and depth estimation.
Sensor Setup

    📷 2× Stereo Event Cameras (Prophesee)

    📸 2× Global Shutter RGB Cameras

    🌀 LiDAR (Velodyne)

    📍 RTK GPS & IMU

    🎯 ATLANS A7 INS — providing high-precision ground truth for position and orientation

All sensors are hardware-synchronized, including satellite-based PPS signals and external trigger management.
Dataset Highlights

    8 sequences currently available

    Captured in varied environments and conditions

    Additional sequences to be released (including under diverse lighting and seasonal variations)

Included Resources

This repository also includes:

    🔧 ROS nodes for synchronizing event cameras (Prophesee master/slave setup)

    🧩 Post-processing scripts for synchronization and alignment

    🧭 Ground truth generation tools (LiDAR + ATLANS)

    🌁 Depth map densification from sparse LiDAR using semantic segmentation
