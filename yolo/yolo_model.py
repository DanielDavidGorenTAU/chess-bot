from ultralytics import YOLO
import glob
import os
from fen_translator import BinaryToFenTranslator, Translator

# Load model
#model = YOLO("/home/checkmate/Documents/chess-bot/runs/detect/runs/train/chess_board-3/weights/best.pt") #unary
#model = YOLO("/home/checkmate/Documents/chess-bot/runs/detect/chess_training/run_1/weights/best.pt") #advanced
model = YOLO("/home/checkmate/Documents/chess-bot/runs/detect/runs/train/chess_board-4/weights/best.pt") #binary
image_paths = glob.glob("/home/checkmate/Documents/chess-bot/test_yolo_board/EN_PASSANT_D5_C6.png")
MODEL_PATHS = {
    "binary": "/home/checkmate/Documents/chess-bot/runs/detect/runs/train/chess_board-4/weights/best.pt",
    "unary": "/home/checkmate/Documents/chess-bot/runs/detect/runs/train/chess_board-3/weights/best.pt",
    "advanced": "/home/checkmate/Documents/chess-bot/runs/detect/chess_training/run_1/weights/best.pt"
}
OUTPUT_DIR = "/home/checkmate/Documents/chess-bot/yolo/predictions"

# Create only if it doesn't already exist
if not os.path.isdir(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

for image_path in image_paths:
    results = model(image_path, conf=0.6)
    result = results[0]

    base_name = os.path.splitext(os.path.basename(image_path))[0]

    # Save coordinates
    txt_path = os.path.join(OUTPUT_DIR, base_name + ".txt")

    with open(txt_path, "w") as f:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            label = result.names[cls_id]

            x1, y1, x2, y2 = box.xyxy[0].tolist()

            center_x = (x1 + x2) / 2
            baseline_y = y2 - 25 #fix offset for baseline.

            f.write(f"{label} {center_x:.1f} {baseline_y:.1f}\n")

    # Save annotated image
    output_image = os.path.join(OUTPUT_DIR, os.path.basename(image_path))
    result.save(filename=output_image)




class YoloModel:
    """
    Wrapper class for loading and running predictions with Ultralytics YOLO models.
    """

    def __init__(self, model_name: str = "binary", output_dir: str = OUTPUT_DIR, conf: float = 0.25):
        """
        Initializes the YoloModel wrapper.

        :param model_name: Name of the model to load (e.g., 'binary', 'unary', 'advanced').
        :param output_dir: Directory where prediction results will be saved.
        :param conf: Default confidence threshold for predictions (0.0 to 1.0).
        """
        self.conf: float = conf
        self.output_dir: str = output_dir
        self.model_path: str = ""
        self.model: YOLO = None
        self.translator: Translator = BinaryToFenTranslator()  # Default translator for binary model
        self.camera = None  # Placeholder for camera object if needed in the future
        
        # Load the model via the private method
        self._set_model_path(model_name)

    def _set_model_path(self, name: str):
        """
        Updates the model path field and loads/reloads the YOLO model instance.

        :param name: Path or identifier string for the model weights.
        """
        if name not in MODEL_PATHS:
            raise ValueError(f"Model name '{name}' not recognized. Available models: {list(MODEL_PATHS.keys())}")
        
        self.model_path = MODEL_PATHS[name]
        self.model = YOLO(self.model_path)

    def _predict(self)-> str:
        """
        Takes an image and runs object detection using the loaded YOLO model.
        Saves the results in png and txt formats in the specified output directory.
        """
        if self.model is None:
            raise RuntimeError("Model is not loaded. Ensure a valid model path is set.")
        image_path = self.camera.capture_image()  # Capture image from camera
        results = self.model(image_path, conf=self.conf)
        result = results[0]

        base_name = os.path.splitext(os.path.basename(image_path))[0]

        # Save coordinates
        txt_path = os.path.join(self.output_dir, base_name + ".txt")

        with open(txt_path, "w") as f:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                label = result.names[cls_id]

                x1, y1, x2, y2 = box.xyxy[0].tolist()

                center_x = (x1 + x2) / 2
                baseline_y = y2 - 25 #fix offset for baseline.

                f.write(f"{label} {center_x:.1f} {baseline_y:.1f}\n")

        # Save annotated image
        output_image = os.path.join(self.output_dir, os.path.basename(image_path))
        result.save(filename=output_image)
        return txt_path  # Return the path to the saved coordinates file for further processing
    
    def update_fen(self, old_fen: str) -> str:
        """
        Updates the FEN string based on the detected pieces from the YOLO model.

        :param old_fen: The previous FEN string representing the board state.
        :return: Updated FEN string after processing detections.
        """
        if self.translator is None:
            raise RuntimeError("Translator is not set. Ensure a valid translator is initialized.")
            
        detections_file = self._predict()  # Run prediction and get the path to the detections file
        new_fen = self.translator.translate_to_fen(old_fen, detections_file)
        return new_fen
        