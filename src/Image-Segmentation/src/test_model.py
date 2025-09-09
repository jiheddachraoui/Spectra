from mmseg.apis import inference_model, init_model, show_result_pyplot
import mmcv
import os
import cv2
import numpy as np

config_dir = 'config'
config_path = os.path.join(config_dir, 'segformer_mit-b5_8xb1-160k_cityscapes-1024x1024.py')
checkpoint_path = os.path.join(config_dir, 'segformer_mit-b5_8x1_1024x1024_160k_cityscapes_20211206_072934-87a052ec.pth')

# Build the model from a config file and a checkpoint file
model = init_model(config_path, checkpoint_path, device='cuda:0')

# Test a single image and get results
img_path = 'data/image_00/good_data/000000.png'
result = inference_model(model, img_path)

# Get visualization result (as ndarray, not shown in matplotlib)
vis_image = show_result_pyplot(model, img_path, result, opacity=0.99, out_file=None,with_labels=False)
vis_image = cv2.cvtColor(vis_image, cv2.COLOR_RGB2BGR)

# Read original image
original_image = cv2.imread(img_path)

# Resize vis_image to match original image if needed
if vis_image.shape[:2] != original_image.shape[:2]:
    vis_image = cv2.resize(vis_image, (original_image.shape[1], original_image.shape[0]))

# Concatenate images side by side
combined = np.concatenate((original_image, vis_image), axis=1)

# Resize for display (scale down if too big)
max_display_width = 1600  # You can tweak this as needed
scale_factor = min(1.0, max_display_width / combined.shape[1])
display_size = (int(combined.shape[1] * scale_factor), int(combined.shape[0] * scale_factor))
resized_combined = cv2.resize(combined, display_size)

# Show the result
cv2.imshow("Original | Segmentation", resized_combined)
cv2.waitKey(0)
cv2.destroyAllWindows()
