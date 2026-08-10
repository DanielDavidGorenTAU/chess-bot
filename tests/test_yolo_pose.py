import os
import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO

def annotate_and_save(
    image_path: str,
    output_dir: str,
    model_path: str = "runs/train/chess_board_dense_pose/weights/best.pt",
    conf_threshold: float = 0.25
):
    """
    Runs YOLOv11 Pose prediction on an image and saves an annotated version with:
    1. Bounding boxes around each piece (no text on boxes).
    2. Head and Base keypoints connected by a line.
    3. A clean summary label menu at the bottom panel.
    """
    model = YOLO(model_path)

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at: {image_path}")
    
    image = cv2.imread(image_path)
    img_h, img_w, _ = image.shape

    # Run inference
    results = model.predict(source=image, imgsz=[320, 960], conf=conf_threshold)[0]

    # Colors (BGR)
    CLASS_COLORS = {
        0: (0, 0, 255),    # Red for Lying
        1: (0, 255, 0)     # Green for Standing
    }
    
    KP_COLOR_HEAD = (255, 255, 0)   # Cyan for Head
    KP_COLOR_BASE = (255, 0, 255)   # Magenta for Base
    KP_LINE_COLOR = (0, 215, 255)   # Yellow/Orange connecting line

    class_counts = {0: 0, 1: 0}

    boxes = results.boxes
    keypoints = results.keypoints

    if boxes is not None:
        for i in range(len(boxes)):
            cls_id = int(boxes.cls[i].item())
            class_counts[cls_id] = class_counts.get(cls_id, 0) + 1
            color = CLASS_COLORS.get(cls_id, (255, 255, 255))

            # --- A. Bounding Box ---
            x1, y1, x2, y2 = map(int, boxes.xyxy[i].tolist())
            cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness=2)

            # --- B. Keypoints (Head & Base) ---
            if keypoints is not None and len(keypoints) > i:
                # Use keypoints.xy to get REAL PIXEL coordinates (not normalized 0-1)
                kpts_xy = keypoints.xy[i].cpu().numpy()  # shape: (2, 2)
                
                # Get keypoint confidences if available
                if keypoints.conf is not None:
                    kpts_conf = keypoints.conf[i].cpu().numpy()  # shape: (2,)
                else:
                    kpts_conf = [1.0, 1.0]

                if len(kpts_xy) >= 2:
                    head_x, head_y = int(kpts_xy[0][0]), int(kpts_xy[0][1])
                    base_x, base_y = int(kpts_xy[1][0]), int(kpts_xy[1][1])
                    
                    head_conf = kpts_conf[0]
                    base_conf = kpts_conf[1]

                    # 1. Connecting Line
                    if head_x > 0 and base_x > 0:
                        cv2.line(image, (head_x, head_y), (base_x, base_y), KP_LINE_COLOR, 2, cv2.LINE_AA)

                    # 2. Draw Head (Cyan dot with black outline for visibility)
                    if head_x > 0 and head_conf >= 0.1:
                        cv2.circle(image, (head_x, head_y), 5, (0, 0, 0), -1, cv2.LINE_AA)        # Black outer
                        cv2.circle(image, (head_x, head_y), 4, KP_COLOR_HEAD, -1, cv2.LINE_AA)  # Cyan inner

                    # 3. Draw Base (Magenta dot with black outline for visibility)
                    if base_x > 0 and base_conf >= 0.1:
                        cv2.circle(image, (base_x, base_y), 5, (0, 0, 0), -1, cv2.LINE_AA)        # Black outer
                        cv2.circle(image, (base_x, base_y), 4, KP_COLOR_BASE, -1, cv2.LINE_AA)  # Magenta inner

    # --- C. Create Bottom Menu Panel ---
    banner_height = 50
    banner = np.zeros((banner_height, img_w, 3), dtype=np.uint8)

    total_pieces = sum(class_counts.values())
    lying_count = class_counts.get(0, 0)
    standing_count = class_counts.get(1, 0)

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.55
    thickness = 2

    # Piece counts
    cv2.putText(banner, f"Total: {total_pieces}", (15, 30), font, font_scale, (255, 255, 255), thickness)

    cv2.rectangle(banner, (150, 15), (165, 30), CLASS_COLORS[1], -1)
    cv2.putText(banner, f"Standing: {standing_count}", (175, 30), font, font_scale, (255, 255, 255), thickness)

    cv2.rectangle(banner, (330, 15), (345, 30), CLASS_COLORS[0], -1)
    cv2.putText(banner, f"Lying: {lying_count}", (355, 30), font, font_scale, (255, 255, 255), thickness)

    # Keypoint legend
    cv2.circle(banner, (500, 22), 5, KP_COLOR_HEAD, -1)
    cv2.putText(banner, "Head", (512, 28), font, 0.45, (255, 255, 255), 1)

    cv2.circle(banner, (580, 22), 5, KP_COLOR_BASE, -1)
    cv2.putText(banner, "Base", (592, 28), font, 0.45, (255, 255, 255), 1)

    final_image = np.vstack((image, banner))

    os.makedirs(output_dir, exist_ok=True)
    img_name = Path(image_path).name
    save_path = os.path.join(output_dir, f"labeled_{img_name}")

    cv2.imwrite(save_path, final_image)
    print(f"✅ Prediction saved to: {save_path}")


if __name__ == "__main__":
    IMAGE_PATH = "/home/checkmate/Downloads/data_set_carton/tests/img_161_extra.png"
    OUTPUT_DIR = "/home/checkmate/Documents/chess-bot/yolo/predictions"
    MODEL_WEIGHTS = "/home/checkmate/Documents/chess-bot/runs/pose/runs/pose_train/chess_board-2/weights/best.pt"

    annotate_and_save(
        image_path=IMAGE_PATH,
        output_dir=OUTPUT_DIR,
        model_path=MODEL_WEIGHTS,
        conf_threshold=0.25
    )