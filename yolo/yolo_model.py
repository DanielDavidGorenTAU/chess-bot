from ultralytics import YOLO
import os
from typing import Optional
from ZED.cameralib import Camera

BINARY = "binary"
UNARY = "unary"
ADVANCED = "advanced"
MODEL_PATHS = {
    BINARY: "/home/checkmate/Documents/chess-bot/runs/detect/runs/train/chess_board-4/weights/best.pt",
    UNARY: "/home/checkmate/Documents/chess-bot/runs/detect/runs/train/chess_board-3/weights/best.pt",
    ADVANCED: "/home/checkmate/Documents/chess-bot/runs/detect/chess_training/run_1/weights/best.pt"
}
MODEL_CONF = {
    BINARY: 0.6,
    UNARY: 0.6,
    ADVANCED: 0.25
}

PREDICTION_OUTPUT_DIR = "/home/checkmate/Documents/chess-bot/yolo/predictions"
IMAGE_OUTPUT_DIR = "/home/checkmate/Documents/chess-bot/yolo/game_photos"





class YoloModel:
    """
    Wrapper class for loading and running predictions with Ultralytics YOLO models.
    """

    def __init__(self, model_name: str = BINARY, camera: Camera = None):
        """
        Initializes the YoloModel wrapper.

        :param model_name: Name of the model to load (e.g., 'binary', 'unary', 'advanced').
        :param output_dir: Directory where prediction results will be saved.
        :param conf: Default confidence threshold for predictions (0.0 to 1.0).
        """
        self.conf: float = MODEL_CONF[BINARY]
        self.model_path: str = ""
        self.model: YOLO = None
        self.camera: Camera = camera 

        self._ensure_directories()
        self.set_model(model_name)

    def _ensure_directories(self) -> None:
        """Ensures that image and prediction output directories exist."""
        os.makedirs(PREDICTION_OUTPUT_DIR, exist_ok=True)
        os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)

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
        
        if image_path is None:
            if self.camera is None:
                raise RuntimeError("No image path provided and camera is not configured.")
            image_path = self.camera.take_photo(IMAGE_OUTPUT_DIR)
        
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
        result.save(filename=output_image)
        return txt_path  # Return the path to the saved coordinates file for further processing
    
        