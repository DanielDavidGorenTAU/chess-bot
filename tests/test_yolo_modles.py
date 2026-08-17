
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from yolo.platform_piece_classifier import *


from yolo.board_pieces_detector import BoardPiecesDetector
from ZED.cameralib import Camera

if __name__ == "__main__":
    image_path = "/home/checkmate/Documents/chess-bot/yolo/photos_game/00_20260813_194939_aaa.png"
    cropped_path = "/home/checkmate/Documents/chess-bot/zed_platform_test_cropped/00_20260804_171642_987.png"
    with Camera() as camera:
        classifier = CNNPieceClassifier(camera = camera)
        classifier.identify_piece()
        

    
    