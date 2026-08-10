from typing import Optional
from .board_pieces_detector import BoardPiecesDetector
from .fen_translator import Translator, BinaryToFenTranslator
from arm.StorageManager import StorageManager
from common.utils import convert_fen_char_to_type_and_color
from collections import Counter
from arm.perception_state import PerceptionState

class HumanMoveInterpreter:
    """
    Coordinates between the vision system (BoardPiecesDetector) and state translation (Translator)
    to compute updated FEN strings after a human player makes a move.
    """

    def __init__(self, yolo_model: BoardPiecesDetector, translator: Optional[Translator] = None):
        self.yolo_model: BoardPiecesDetector = yolo_model
        # Default to BinaryToFenTranslator if none is supplied
        self.translator: Translator = translator or BinaryToFenTranslator()
        self.storage = StorageManager() # Singleton

    def update_fen(self, old_fen: str, image_path: Optional[str] = None) -> str:
        """
        Captures/processes an image, runs detection, updates storage, and translates the detected 
        pieces into an updated FEN string.

        :param old_fen: The previous game state FEN string.
        :param image_path: Optional static image path for testing/debugging.
        :return: Updated FEN string.
        """
        detections_file = self.yolo_model.predict(image_path=image_path)
        PerceptionState().set_latest_detections(detections_file)
        new_fen = self.translator.translate_to_fen(old_fen, detections_file)
        self._sync_storage(old_fen, new_fen)
        return new_fen

    def _sync_storage(self, old_fen: str, current_fen: str):

        if not old_fen or not current_fen:
            return

        old_board = old_fen.split()[0]
        new_board = current_fen.split()[0]

        old_counts = Counter(c for c in old_board if c.isalpha())
        new_counts = Counter(c for c in new_board if c.isalpha())

        # check for missing pieces
        for char, old_count in old_counts.items():
            new_count = new_counts.get(char, 0)
            if old_count > new_count:
                missing_qty = old_count - new_count
                piece_type, color = convert_fen_char_to_type_and_color(char)
                for _ in range(missing_qty):
                    self.storage.register_human_capture(piece_type, color) 
                    #print(f"[Robot Memory] Human captured {color} {piece_type.name}. Storage memory updated.")

        # check for new pieces
        for char, new_count in new_counts.items():
            old_count = old_counts.get(char, 0)
            if new_count > old_count:
                added_qty = new_count - old_count
                piece_type, color = convert_fen_char_to_type_and_color(char)
                for _ in range(added_qty):
                    self.storage.register_human_promotion(piece_type, color) 
                    #print(f"[Robot Memory] Human promoted to {color} {piece_type.name}. Storage memory updated.")