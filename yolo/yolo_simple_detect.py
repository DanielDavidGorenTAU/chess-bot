from ultralytics import YOLO
from pathlib import Path

# Model
model = YOLO("https://huggingface.co/KanisornPutta/chess-model-yolov8m/resolve/main/chess-model-yolov8m.pt")

# Directory containing images
IMAGE_DIR = Path("/home/checkmate/Documents/chess-bot/zed_platform_test_cropped")  # change this

# Supported image extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# Get all images
images = [
    img for img in IMAGE_DIR.iterdir()
    if img.suffix.lower() in IMAGE_EXTENSIONS
]

for image_path in images:
    print("=" * 60)
    print(f"Image: {image_path.name}")

    results = model(image_path)

    result = results[0]

    if result.boxes is None or len(result.boxes) == 0:
        print("No detections")
        continue

    names = result.names

    for box in result.boxes:
        cls_id = int(box.cls[0])
        confidence = float(box.conf[0])

        xyxy = box.xyxy[0].tolist()
        x1, y1, x2, y2 = map(int, xyxy)

        print(
            f"  Class: {names[cls_id]}, "
            f"Confidence: {confidence:.3f}, "
            f"Box: ({x1}, {y1}, {x2}, {y2})"
        )