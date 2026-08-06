from typing import Optional
from .board_pieces_detector import BoardPiecesDetector
from .fen_translator import Translator, BinaryToFenTranslator


class HumanMoveInterpreter:
    """
    Coordinates between the vision system (BoardPiecesDetector) and state translation (Translator)
    to compute updated FEN strings after a human player makes a move.
    """

    def __init__(self, yolo_model: BoardPiecesDetector, translator: Optional[Translator] = None):
        self.yolo_model: BoardPiecesDetector = yolo_model
        # Default to BinaryToFenTranslator if none is supplied
        self.translator: Translator = translator or BinaryToFenTranslator()

    def update_fen(self, old_fen: str, image_path: Optional[str] = None) -> str:
        """
        Captures/processes an image, runs detection, and translates the detected 
        pieces into an updated FEN string.

        :param old_fen: The previous game state FEN string.
        :param image_path: Optional static image path for testing/debugging.
        :return: Updated FEN string.
        """
        detections_file = self.yolo_model.predict(image_path=image_path)
        new_fen = self.translator.translate_to_fen(old_fen, detections_file)
        return new_fen