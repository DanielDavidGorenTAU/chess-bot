import os
import random
import shutil

# =====================================================
# CHANGE THIS TO YOUR IMAGE FOLDER
# =====================================================
input_dir = r"C:\Users\USER\Projects\chess-bot\ZED\zed_board_images"

# =====================================================
# Number of images for each person/folder
# (Must sum to the number of images available)
# =====================================================
distribution = {
    "test": 10,
    "Michael": 20,
    "Elad": 20,
    "Moataz": 20,
    "Daniel": 20
}

# =====================================================
# Output folder (created next to the input folder)
# =====================================================
output_root = os.path.join(input_dir, "split_dataset")

# Supported image formats
image_extensions = (
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tif",
    ".tiff",
    ".webp"
)

# =====================================================
# Collect all images
# =====================================================
images = [
    f for f in os.listdir(input_dir)
    if f.lower().endswith(image_extensions)
]

total_needed = sum(distribution.values())

if len(images) != total_needed:
    raise ValueError(
        f"Expected exactly {total_needed} images, but found {len(images)}."
    )

# Randomize image order
random.shuffle(images)

# =====================================================
# Create folders and copy images
# =====================================================
current = 0

for folder_name, amount in distribution.items():
    folder_path = os.path.join(output_root, folder_name)
    os.makedirs(folder_path, exist_ok=True)

    selected_images = images[current:current + amount]

    for image_name in selected_images:
        src = os.path.join(input_dir, image_name)
        dst = os.path.join(folder_path, image_name)
        shutil.move(src, dst)

    current += amount

print("Done!")
print(f"Output folder: {output_root}")

for folder_name, amount in distribution.items():
    print(f"{folder_name}: {amount} images")