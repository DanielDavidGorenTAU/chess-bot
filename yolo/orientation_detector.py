import os
import cv2
from common.enums_and_dicts import Orientation
from .vision_model import VisionModel
from typing import Optional, Tuple
from dataclasses import dataclass
from ultralytics import YOLO
from ZED.cameralib import Camera


MODEL_PATH: str = "models/yolov8_pose_best.pt"
PREDICTION_OUTPUT_DIR = "/home/checkmate/Documents/chess-bot/yolo/predictions_setup"
IMAGE_OUTPUT_DIR = "/home/checkmate/Documents/chess-bot/yolo/photos_setup"
DEFAULT_CONF: float = 0.5

@dataclass
class PiecePose:
    """Dataclass representing the target piece's pose and metadata."""
    head: Tuple[float, float]
    base: Tuple[float, float]
    orientation: Orientation
    confidence: float


class OrientationDetector(VisionModel):
    """
    Wrapper class for running predictions with YOLO Pose to detect orientation 
    and center of chess piece for grabbing.
    """


    def __init__(self, camera: Optional[Camera] = None, model_path: str = MODEL_PATH, conf: float = DEFAULT_CONF):
        """Initializes the YOLO Model wrapper for piece orientation."""

        super().__init__(camera=camera, conf=conf, path_list=[IMAGE_OUTPUT_DIR, PREDICTION_OUTPUT_DIR])

        self.model_path: str = model_path
        print(f"Loading YOLO Pose model from: {self.model_path}")
        self.model: YOLO = YOLO(self.model_path)


    def set_model(self, model_path: str) -> None:
        """Reloads a new model if needed."""
        self.model_path = model_path
        self.model = YOLO(self.model_path)

    def detect_pickup_pose(self, image_path: Optional[str] = None) -> Optional[PiecePose]:
        """
        Detects piece poses and returns ONLY the piece with the lowest 
        middle coordinate in the picture (highest y-value).
        """
        image_path = self._resolve_image_path(image_path, IMAGE_OUTPUT_DIR)

        # Run inference
        results = self.model.predict(
            source=image_path, 
            conf=self.conf
            # verbose=False if terminal gets messy
        )
        
        result = results[0]
        target_piece: Optional[PiecePose] = None
        max_y_center = -1.0

        if result.boxes is not None and len(result.boxes) > 0 and result.keypoints is not None:
            boxes = result.boxes
            keypoints = result.keypoints

            for box, kp in zip(boxes, keypoints):
                # xywh = [[x_center, y_center, width, height]]
                y_center = float(box.xywh[0, 1])
                
                # Check if this piece is the lowest in the frame
                if y_center > max_y_center:
                    max_y_center = y_center
                    
                    # Class and confidence retrival
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    orientation = Orientation(class_id)

                    # Assumes in the labeling head is first, then base
                    kp_pts = kp.xy[0].tolist()

                    head_coords = tuple(kp_pts[0]) if len(kp_pts) >= 1 else (0.0, 0.0)
                    base_coords = tuple(kp_pts[1]) if len(kp_pts) >= 2 else (0.0, 0.0)

                    target_piece = PiecePose(
                        head=head_coords,
                        base=base_coords,
                        orientation=orientation,
                        confidence=confidence
                    )

        # Draw annotations and save
        annotated_image = result.plot()
        filename = os.path.basename(image_path)
        save_path = os.path.join(self.output_dir, f"result_{filename}")
        cv2.imwrite(save_path, annotated_image)
        print(f"Saved prediction result image to: {save_path}")

        return target_piece