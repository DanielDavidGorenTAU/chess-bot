from ultralytics import YOLO
import os
from typing import Optional
from ZED.cameralib import Camera

class PlatformPieceClassifier():
    """
    Wrapper class for running predictions with CNN to classify piece on the platform.
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


    def identify_piece(self):
        pass