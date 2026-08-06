
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


from yolo.board_pieces_detector import BoardPiecesDetector
from ZED.cameralib import Camera

if __name__ == "__main__":
    image_path = "/home/checkmate/Documents/chess-bot/yolo/game_photos/00_20260806_125747_340.png"
    with Camera() as camera:
        yolo_model = BoardPiecesDetector(model_name="advanced", camera=camera, save_regularly=False)
        yolo_model.predict(image_path)
        

    
    