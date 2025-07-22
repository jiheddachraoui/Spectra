import os
import cv2
from segment_image import generate_segmentated_img
from tqdm import tqdm

def main():
    image_files = LoadImages()
    save_segmented_images(image_files)

def LoadImages():
    image_dir = "/media/litis/T5 EVO2/test/images"
    image_files = [os.path.join(image_dir, f) for f in os.listdir(image_dir) if f.endswith(".png")]
    image_files.sort(key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))
    return image_files

def save_segmented_images(image_files):
    save_dir = "/media/litis/T5 EVO2/test/seg_map"
    os.makedirs(save_dir, exist_ok=True)

    index = 0  # Track output index separately to avoid gaps when skipping existing files
    for image_path in tqdm(image_files, desc="Segmenting Images"):
        output_path = os.path.join(save_dir, f"seg_map_{index}.png")

        # Skip if already exists
        if os.path.exists(output_path):
            index += 1
            continue

        seg_img = generate_segmentated_img(image_path)
        cv2.imwrite(output_path, seg_img)
        index += 1

if __name__ == "__main__":
    main()

