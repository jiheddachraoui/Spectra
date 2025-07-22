# 📸 Image Segmentation

This repository performs the following tasks:

1. **Load** camera images.  
2. **Apply** semantic segmentation using a chosen model (e.g., DeepLabV3+).  
3. **Visualize and save** the segmentation results.

---

## 🧩 Dependencies

- Refer to [this page](https://github.com/open-mmlab/mmsegmentation/blob/main/docs/en/get_started.md#installation) to install **OpenMMLab's segmentation toolkit**.
- Download and place the desired model checkpoint and config in the `config/` folder.
- Adjust `segment_image.py` to match the selected model and configuration.
- Install OpenCV for visualization:

  ```bash
  pip install opencv-python
  ```

### ✅ Pretrained Model Used

- [DeepLabV3+ checkpoint (Google Drive)](https://drive.google.com/file/d/1La2oCvuufKtBQ4Ot_Xsl04wbIiocabLb/view?usp=sharing)

---

## 🚀 Run Instructions

To run semantic segmentation on a set of images and save the results:

```bash
python src/save_segmentation.py
```

---
