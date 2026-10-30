<p align="center">
  <a href="docs/media/spectra_teaser.mp4">
    <img src="docs/media/spectra_teaser_poster.jpg" alt="SPECTRA teaser: click to play the video" width="900">
  </a>
</p>

<h1 align="center">SPECTRA</h1>

<p align="center">
  <b>A driving dataset with stereo event cameras, stereo RGB cameras, LiDAR and GPS</b><br>
  <sub>Day, dawn, night and tunnels, recorded on real roads in Normandy, France.</sub>
</p>

<p align="center">
  <a href="https://openreview.net/forum?id=mqCUxEsfsI"><img src="https://img.shields.io/badge/paper-OpenReview-b31b1b?style=flat-square" alt="Paper"></a>
  <a href="#download"><img src="https://img.shields.io/badge/data-link%20at%20publication-e5484d?style=flat-square" alt="Data"></a>
  <a href="toolkit/README.md"><img src="https://img.shields.io/badge/toolkit-python%203.8%2B-3d6cf5?style=flat-square" alt="Toolkit"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/code-BSD--3--Clause-434b5a?style=flat-square" alt="Code license"></a>
  <a href="https://anr.fr/Project-ANR-21-CE22-0006"><img src="https://img.shields.io/badge/ANR-CERBERE-0b5394?style=flat-square" alt="ANR CERBERE project"></a>
</p>

<p align="center">
  <a href="#what-is-spectra">About</a> ·
  <a href="#whats-inside">What's inside</a> ·
  <a href="#get-started">Get started</a> ·
  <a href="#download">Download</a> ·
  <a href="docs/DATA_FORMAT.md">Data format</a> ·
  <a href="#citation">Citation</a>
</p>

---

## What is SPECTRA?

Event cameras don't take pictures. Each pixel reports the moment its brightness changes, millions of times per
second. This makes them very good where normal cameras struggle: fast motion, darkness and harsh light.

**SPECTRA** lets you study them on the road. We mounted **two event cameras next to two normal (RGB) cameras**,
added a **LiDAR** and an **RTK-GPS/INS**, and drove through towns, suburbs and tunnels by day, at dawn and at
night. Every RGB frame comes with **dense depth**, **stereo disparity** and **semantic labels**, so you can train
and test models for depth, segmentation and more.

SPECTRA was made by the [LITIS laboratory](https://www.litislab.fr/) (Normandie Université / INSA Rouen) within
the [ANR CERBERE project](https://litis-cerbere.univ-rouen.fr/).

## News

- **2026-10-30**: SPECTRA v1.0. Disparity maps for every depth frame and a Python [toolkit](toolkit/README.md).
- **2025**: paper at the IROS 2025 Workshop on Neuromorphic Perception for Real World Robotics (NeuRobots).

## At a glance

| 🎬 **27** sequences | ⏱️ **26 min** of driving | 🛣️ **10.7 km** | 📅 **5** recording days |
|:---:|:---:|:---:|:---:|
| 📷 **31,206** stereo RGB pairs | 🌊 **29,292** frames with dense depth | ⚡ **28.4 billion** events | 💾 about **820 GB** |

## The car

<p align="center"><img src="docs/media/rig.png" alt="The sensor rig on the car roof, front view" width="820"></p>

All sensors sit on the roof, facing forward. From left to right: RGB camera, event camera, event camera, RGB camera,
with the LiDAR just above them.

| | Sensor | Model |
|---|---|---|
| ⚡ | 2 event cameras | Prophesee EVK4 |
| 📷 | 2 RGB cameras, 1280×720 at 20 Hz | FLIR Blackfly S |
| 📡 | LiDAR, 32 beams | Ouster OS1-32 |
| 🛰️ | GPS / INS with RTK | iXblue ATLANS A7 |

<p align="center"><img src="docs/media/four_views.jpg" alt="What the four cameras see, left to right" width="820"></p>
<p align="center"><sub>The same moment seen by the four cameras.</sub></p>

## What's inside

Each sequence folder holds:

| | What you get | Folder |
|---|---|---|
| 📷 | Stereo RGB images | `rgb/` |
| ⚡ | Stereo event streams, plus the camera trigger | `events/` |
| 🏷️ | Semantic segmentation of both RGB cameras (19 Cityscapes classes) | `semantic/` |
| 🌊 | Dense depth up to 50 m, and stereo disparity | `depth/` |
| 📡 | LiDAR map and the car's trajectory | `lidar_ins/` |
| 🎞️ | Small preview videos | `preview/` |
| 💾 | The original ROS recording with every sensor | `raw/` |

<p align="center"><img src="docs/media/depth_day_suburbs.jpg" alt="RGB image, events and dense depth of the same frames" width="900"></p>
<p align="center"><sub>One sequence, three views: RGB image, events and dense depth (red = near, blue = far).</sub></p>

The depth comes from the LiDAR, spread to every pixel with the help of the segmentation, so object borders stay
sharp. The full method, every file format and the calibration are explained in **[docs/DATA_FORMAT.md](docs/DATA_FORMAT.md)**.

### Sequences

Each sequence is named after the time it was recorded, `YYYY-MM-DD-HH-MM-SS`.

| Day | Conditions | Sequences |
|---|---|---|
| 2024-10-03 | 🏙️ city street, day | `2024-10-03-15-01-07` |
| 2024-10-24 | 🌅 dawn, low light | `2024-10-24-08-15-20`, `2024-10-24-08-15-34` |
| 2024-11-28 | 🌙 night, suburbs | `2024-11-28-18-25-59` |
| 2024-11-29 | 🚇 tunnels, and suburbs by day | `2024-11-29-11-08-17`, `2024-11-29-11-13-51`, `2024-11-29-11-27-15` |
| 2025-07-22 | ☀️ town and suburbs, afternoon | 20 sequences, `2025-07-22-15-51-18` to `2025-07-22-17-06-23` |

## Get started

**1. Download** one sequence (see [Download](#download)) and unzip it. You get a `SPECTRA/` folder.

**2. Install the toolkit:**

```bash
git clone https://github.com/jiheddachraoui/Cerbere.git
cd Cerbere/toolkit
pip install -r requirements.txt
```

**3. Open a sequence:**

```bash
python scripts/quickstart_read.py --root /path/to/SPECTRA --seq 2024-10-24-08-15-20
```

Or in Python:

```python
import spectra as sp

seq   = sp.Sequence("SPECTRA", "2024-10-24-08-15-20")
pair  = next(p for p in seq.pairs if seq.depth(p["stem"]) is not None)

image = seq.rgb(pair, "left")         # the left RGB image
depth = seq.depth(pair["stem"])       # depth in metres
```

The toolkit can also draw depth on the images, turn events into videos, make labels for the right camera and
extract data from the raw recordings. See the **[toolkit guide](toolkit/README.md)**.

## Download

The data will be available from the project page (link at publication). You can download **one archive per
sequence and per data type**, so you only fetch what you need:

| Archive | Contents |
|---|---|
| `<id>_rgb.zip` | stereo RGB images |
| `<id>_events.zip` | both event streams and the trigger file |
| `<id>_semantic.zip` | segmentation of both cameras |
| `<id>_depth.zip` | dense depth, disparity and their extra maps |
| `<id>_lidar_ins.zip` | LiDAR map and trajectory |
| `<id>_calib.zip` | calibration and the left/right frame pairs |
| `<id>_preview.zip` | the two preview videos |
| `<id>.bag` | the original ROS recording (large) |
| `calibration.zip`, `sequences.csv` | calibration files and the list of sequences |

Unzip all archives into the same folder: they rebuild the `SPECTRA/` tree. To check the files, run
`cd SPECTRA && sha256sum -c --ignore-missing SHA256SUMS`.

## Good to know

A few things worth reading before you use the data. The full list is in **[docs/DATA_NOTES.md](docs/DATA_NOTES.md)**.

- Depth is **pseudo ground truth** made from the LiDAR, up to 50 m. Some frames have no depth on purpose.
- Left and right images are matched through `pairs.csv`, **not by file name**.
- Some sequences drop frames, so don't assume a fixed frame rate.
- The clocks of the different sensors are not merged into one time axis.

## This repository

| Folder | What it is |
|---|---|
| [`toolkit/`](toolkit/README.md) | Python tools to read and visualise SPECTRA |
| [`docs/`](docs) | the data format, the data notes and the figures |

## Citation

If SPECTRA helps your work, please cite:

```bibtex
@inproceedings{dachraoui2025spectra,
  title     = {{SPECTRA}: Synchronized Stereo Event-Camera Driving Dataset for Diverse Perception Tasks},
  author    = {Dachraoui, Jihed and El Moudni, Anass and Planterose, Elsa and Kramm, S{\'e}bastien and Morbidi, Fabio and Boutteau, R{\'e}mi},
  booktitle = {IROS 2025 Workshop on Neuromorphic Perception for Real World Robotics (NeuRobots)},
  year      = {2025},
  url       = {https://openreview.net/forum?id=mqCUxEsfsI}
}
```

## License

The code in this repository is under the [BSD 3-Clause License](LICENSE). The license of the data will be
announced with the release.

## Acknowledgements

This work was supported by the French National Research Agency (ANR) through the
[CERBERE project](https://anr.fr/Project-ANR-21-CE22-0006) (ANR-21-CE22-0006), and funded by Région Normandie.
Computing resources were provided by CRIANN (Normandy, France).

## Contact

Questions about the data or the toolkit? Please [open an issue](https://github.com/jiheddachraoui/Cerbere/issues).
If you appear in the data and want an image removed, open an issue as well and we will get in touch.
