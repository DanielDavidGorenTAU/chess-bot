import os
import cv2

Y_MIN, Y_MAX = 40, 360   # height = 320
X_MIN, X_MAX = 650, 1610 # width = 960

VALID_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')

def crop_carton_roi_dir(input_dir: str, output_dir: str) -> None:
    """
    Crops the carton ROI from all images in input_dir and saves them 
    inside output_dir under their original filenames.
    
    :param input_dir: Directory containing full-size source images.
    :param output_dir: Directory where cropped images will be saved.
    """
    # 1. Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # 2. Get list of image files
    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    filenames = [f for f in os.listdir(input_dir) if f.lower().endswith(VALID_EXTENSIONS)]
    
    if not filenames:
        print(f"No valid image files found in: {input_dir}")
        return

    print(f"Found {len(filenames)} images. Cropping to ({Y_MAX - Y_MIN}x{X_MAX - X_MIN})...\n")

    processed_count = 0

    # 3. Loop over all images
    for filename in filenames:
        image_path = os.path.join(input_dir, filename)
        img = cv2.imread(image_path)
        
        if img is None:
            print(f"Warning: Failed to load {filename}, skipping...")
            continue

        # Crop ROI [y_min:y_max, x_min:x_max]
        carton_roi = img[Y_MIN:Y_MAX, X_MIN:X_MAX]

        # Save cropped ROI
        save_path = os.path.join(output_dir, filename)
        cv2.imwrite(save_path, carton_roi)
        processed_count += 1

    print(f"Finished! Successfully cropped and saved {processed_count} images to: {output_dir}")


# --- Execution ---
input_dir = "C:/Users/m1478/Downloads/data/data"
output_dir = "C:/Users/m1478/Downloads/cropped_data"

crop_carton_roi_dir(input_dir, output_dir)