from main.config import AppConfig
from ZED.cameralib import Camera
from yolo.human_interpreter import HumanMoveController
from yolo.board_pieces_detector import *
from yolo.fen_translator import AdvancedToFenTranslator, BinaryToFenTranslator  




class InitDetectorFactory:
    """Builds BoardSetupService with its specific dependencies."""
    def __init__(self, config: AppConfig, camera: Camera):
        self.config = config
        self.camera = camera

    def create_initial_board_detector(self) -> HumanMoveController:
        """Assembles Vision + Translator pipeline."""
        print("[Factory] Assembling InitBoardDetector...")
        flip = self.config.game.white_player == "human"
        yolo_model = BoardPiecesDetector(model_name=ADVANCED, camera=self.camera)
        translator = AdvancedToFenTranslator(flip=flip)
        return HumanMoveController(yolo_model=yolo_model, translator=translator)

        