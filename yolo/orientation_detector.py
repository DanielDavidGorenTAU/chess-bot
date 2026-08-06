from ZED.cameralib import Camera

class OrientationDetector():
    """
    Wrapper class for running predictions with YOLO poseto detect orientation and center of chess piece for grabbing.
    """
    """
    def __init__(self, camera: Camera = None):
        
        Initializes the Yolo Model wrapper for orientation of pieces on desk.

        :param model_name: Name of the model to load (e.g., 'binary', 'unary', 'advanced').
        :param output_dir: Directory where prediction results will be saved.
        :param conf: Default confidence threshold for predictions (0.0 to 1.0).
        
        self.conf: float = MODEL_CONF[BINARY]
        self.model_path: str = ""
        self.model: YOLO = None
        self.camera: Camera = camera 

        self._ensure_directories()
        self.set_model(model_name)

    def detect_pickup_pose(self):
        pass
    """