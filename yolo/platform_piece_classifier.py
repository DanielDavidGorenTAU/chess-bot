from abc import abstractmethod
from common.enums_and_dicts import ColoredPieceType
from .vision_model import VisionModel
from common.exceptions import YoloVisionException
from typing import Optional
from ultralytics import YOLO
from ZED.cameralib import Camera


DEFAULT_CONF = 0.5
IMAGE_OUTPUT_DIR = "/home/checkmate/Documents/chess-bot/yolo/photos_platform"

class PlatformPieceClassifier(VisionModel):
    """
    Abstract Base Class for piece classification on the platform.
    """

    def __init__(self, camera: Optional[Camera] = None, conf: float = DEFAULT_CONF):
        super().__init__(camera=camera, conf=conf, path_list=[IMAGE_OUTPUT_DIR])

    @abstractmethod
    def identify_piece(self, image_path: Optional[str] = None) -> ColoredPieceType:
        """
        Abstract method to identify the piece on the platform.
        """
        pass



class YOLOPieceClassifier(PlatformPieceClassifier):
    """
    YOLO implementation for platform piece classification.
    """
    def __init__(self, model_path: str, camera: Optional[Camera] = None, conf: float = DEFAULT_CONF):
        super().__init__(camera=camera, conf=conf)
        self.model_path: str = model_path
        print(f"Loading YOLO Classifier from: {self.model_path}")
        self.model: YOLO = YOLO(self.model_path)

    def identify_piece(self, image_path: Optional[str] = None) -> ColoredPieceType:

        image_path = self._resolve_image_path(image_path, IMAGE_OUTPUT_DIR)

        #Run inference
        results = self.model.predict(source=image_path, conf=self.conf)
        result = results[0]

        if result.boxes is not None and len(result.boxes) > 0:
            top_box = max(result.boxes, key=lambda b: float(b.conf[0]))
            class_id = int(top_box.cls[0])
            return ColoredPieceType(class_id)
        else:
            raise YoloVisionException("No class detected on platform")

class ManualPieceClassifier(PlatformPieceClassifier):
    """ (almost) Mock Class"""
    def __init__(self, camera: Optional[Camera] = None, conf: float = DEFAULT_CONF):
        super().__init__(camera=camera, conf=conf)

    def identify_piece(self, image_path: Optional[str] = None) -> ColoredPieceType:
        """
        Get piece class by user shell dialog.
        """
        return ColoredPieceType.parse(input("Choose piece class: "))



#### IF NEEDED ####
class CNNPieceClassifier(PlatformPieceClassifier):
    """
     CNN implementation for platform piece classification. 
    """
    def __init__(self, model_path: str, camera: Optional[Camera] = None, conf: float = DEFAULT_CONF):
            super().__init__(camera=camera, conf=conf)

    def identify_piece(self, image_path: Optional[str] = None) -> ColoredPieceType:
        return ColoredPieceType(-1)