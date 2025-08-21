# SPECTRA Dataset: Sensor and  Ground-Truth Toolkit

This dataset is released as part of the [ANR CERBERE Project](#).

<p align="center">
  <img src="system-overview.pdf" alt="SPECTRA system overview" width="860">
  <br>
  <em>Figure 1 — The SPECTRA pipeline and sensor suite used to produce ground truths.</em>
</p>
---
## Overview

**SPECTRA** is a multimodal dataset designed for autonomous driving research. It features synchronized sensor data collected in real-world driving conditions, enabling research in:

- Perception
- Localization
- Sensor fusion
- Depth estimation

---

## Sensor Setup

- 📷 **2× Stereo Event Cameras** (Prophesee EVK4)
- 📸 **2× Global Shutter RGB Cameras** (Flir Blackfly S)
- 🌀 **LiDAR** (Ouster32)
- 📍 **RTK GNSS & IMU**
- 🎯 **ATLANS A7 INS** — high-precision ground truth for position and orientation

All sensors are **hardware-synchronized**, including **satellite-based PPS** signals and **external trigger management**.

---

## Dataset Highlights

- ✅ **8 sequences** currently available
- 🛣️ Captured in **varied environments and conditions**
- 🌤️ More sequences to come (lighting and seasonal variations)

---

## Included Resources

This repository also includes:

- 🔧 **ROS nodes** for synchronizing event cameras (Prophesee master/slave setup)
- 🧩 **Post-processing scripts** for data extraction
- 🧭 **Ground truth generation tools**
- 🌁 **Depth map densification** from sparse LiDAR using semantic segmentation
