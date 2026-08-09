from ultralytics import YOLO
import os
from typing import Optional
from ZED.cameralib import Camera
from .vision_model import VisionModel
import cv2
import random
from pathlib import Path
#from common.utils import ensure_directories

BINARY = "binary"
UNARY = "unary"
ADVANCED = "advanced"
MODEL_PATHS = {
    BINARY: "/home/checkmate/Documents/chess-bot/runs/detect/runs/train/chess_board-4/weights/best.pt",
    UNARY: "/home/checkmate/Documents/chess-bot/runs/detect/runs/train/chess_board-3/weights/best.pt",
    ADVANCED: "/home/checkmate/Documents/chess-bot/runs/detect/chess_training/run_1/weights/best.pt"
}
MODEL_CONF = {
    BINARY: 0.5,
    UNARY: 0.6,
    ADVANCED: 0.25
}

PREDICTION_OUTPUT_DIR = "/home/checkmate/Documents/chess-bot/yolo/predictions_game"
IMAGE_OUTPUT_DIR = "/home/checkmate/Documents/chess-bot/yolo/photos_game"





class BoardPiecesDetector(VisionModel):
    """
    Wrapper class for loading and running predictions with Ultralytics YOLO models.
    """

    def __init__(self, model_name: str = BINARY, camera: Camera = None, save_regularly: bool = True):
        super().__init__(camera=camera, conf=MODEL_CONF[BINARY], path_list=[IMAGE_OUTPUT_DIR, PREDICTION_OUTPUT_DIR])
        self.model_path: str = ""
        self.model: YOLO = None
        self.camera: Camera = camera 
        self.save_regularly: bool = save_regularly

        self.set_model(model_name)
        
    def save_yolo_prediction_clean(self, result, image, output_path):
        """
        Saves YOLO prediction with only bounding boxes and a class legend.

        Args:
            result: YOLO result object (result[0])
            image: Original image as numpy array (cv2 image)
            output_path: Path where the image will be saved
        """

        img = image.copy()

        colors = {}

        def get_color(class_id):
            if class_id not in colors:
                colors[class_id] = (
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255)
                )
            return colors[class_id]

        legend = []

        for box in result.boxes:
            cls_id = int(box.cls[0])
            name = result.names[cls_id]

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            color = get_color(cls_id)

            # Draw bounding box only
            cv2.rectangle(
                img,
                (x1, y1),
                (x2, y2),
                color,
                3
            )

            if name not in [item[0] for item in legend]:
                legend.append((name, color))

        # Add legend at bottom
        legend_height = 40 * len(legend)

        canvas = cv2.copyMakeBorder(
            img,
            0,
            legend_height,
            0,
            0,
            cv2.BORDER_CONSTANT,
            value=(30, 30, 30)
        )

        y = img.shape[0] + 30

        for name, color in legend:
            cv2.rectangle(
                canvas,
                (20, y - 20),
                (50, y + 10),
                color,
                -1
            )

            cv2.putText(
                canvas,
                name,
                (70, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

            y += 40

        cv2.imwrite(str(output_path), canvas)


    def set_model(self, name: str):
        """
        Updates the model path field and loads/reloads the YOLO model instance.

        :param name: Path or identifier string for the model weights.
        """
        if name not in MODEL_PATHS:
            raise ValueError(f"Model name '{name}' not recognized. Available models: {list(MODEL_PATHS.keys())}")
        
        self.model_path = MODEL_PATHS[name]
        self.model = YOLO(self.model_path)
        self.conf = MODEL_CONF[name]

    def predict(self, image_path: Optional[str] = None)-> str:
        """
        Takes an image (if none provided) and runs object detection using the loaded YOLO model.
        Saves the results in png and txt formats in the specified output directory.
        """
        if self.model is None:
            raise RuntimeError("Model is not loaded. Ensure a valid model path is set.")

        image_path = self._resolve_image_path(image_path, IMAGE_OUTPUT_DIR)
        
        results = self.model(image_path, conf=self.conf)
        result = results[0]

        base_name = os.path.splitext(os.path.basename(image_path))[0]

        # Save coordinates
        txt_path = os.path.join(PREDICTION_OUTPUT_DIR, base_name + ".txt")

        with open(txt_path, "w") as f:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                label = result.names[cls_id]

                x1, y1, x2, y2 = box.xyxy[0].tolist()

                center_x = (x1 + x2) / 2
                baseline_y = y2 - 25 #fix offset for baseline.

                f.write(f"{label} {center_x:.1f} {baseline_y:.1f}\n")

        # Save annotated image
        output_image = os.path.join(PREDICTION_OUTPUT_DIR, os.path.basename(image_path))
        if not self.save_regularly:
            self.save_yolo_prediction_clean(result, cv2.imread(image_path), output_image)
        else:
            result.save(filename=output_image)
        return txt_path  # Return the path to the saved coordinates file for further processing
    
        