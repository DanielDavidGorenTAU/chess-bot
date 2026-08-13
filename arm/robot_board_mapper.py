import json
import cv2
import numpy as np
from .perception_state import PerceptionState

from yolo.fen_translator import CORNERS_FILE
from .measurements import CELL_LENGTH

class RobotBoardMapper:
    def __init__(self, corners_file=CORNERS_FILE, target_size=800, cell_size_mm=CELL_LENGTH*10):
        
        self.target_size = target_size
        self.cell_size_mm = cell_size_mm
        self.board_size_mm = 8.0 * cell_size_mm
        self.flip = False # robot is white
        
        with open(corners_file, "r") as f:
            corners = json.load(f)
        
        # Calculate the transformation matrix from the vision module to unwarp the image
        src_pts = np.array(corners, dtype="float32")
        dst_pts = np.float32([
            [0, 0], [target_size - 1, 0], 
            [target_size - 1, target_size - 1], [0, target_size - 1]
        ])
        self.matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)

    def get_all_pieces_physical_locations(self, detections_file=None):
        """
        Reads the detections file and returns a dictionary mapping 
        (row, col) to physical (X, Y) coordinates in millimeters.
        """

        # Fetch the latest file from PerceptionState if none was provided
        if detections_file is None:
            detections_file = PerceptionState().get_latest_detections()
            if detections_file is None:
                return None
            
        piece_locations = {}
        
        with open(detections_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split()
                if len(parts) < 3:
                    continue
                
                x_img = float(parts[1])
                y_img = float(parts[2])
                
                # Unwarp the image coordinates using the perspective matrix 
                pt = np.array([[[x_img, y_img]]], dtype=np.float32)
                warped_pt = cv2.perspectiveTransform(pt, self.matrix)
                wx, wy = warped_pt[0][0]
                
                # Calculate the chess board row and column (0 to 7)
                square_size = self.target_size / 8.0
                col = int(wx // square_size)
                row = int(wy // square_size)
                
                # Clamp the values to the board limits to handle potential noise
                row = max(0, min(7, row))
                col = max(0, min(7, col))
                
                # Convert to millimeters (physical coordinates for the robot)
                x_mm = wx * (self.board_size_mm / self.target_size)
                y_mm = wy * (self.board_size_mm / self.target_size)
                
                # Store in the dictionary by board location
                piece_locations[(row, col)] = (x_mm, y_mm)
                
        return piece_locations

    def get_piece_grasping_data(self, square_name):
        """
        Takes a square name (e.g., 'a3'), the locations dictionary, and an optional piece type.
        Returns the deviation from the square's center dx, dy.
        """
        
        piece_locations = self.get_all_pieces_physical_locations()
        if piece_locations is None: # not created yet
            return 0.0, 0.0

        # Convert square name to row and column (0 to 7)
        square_name = square_name.lower()
        logical_col = ord(square_name[0]) - ord('a')
        logical_row = 8 - int(square_name[1])

        if self.flip:
            col = 7 - logical_col
            row = 7 - logical_row
        else:
            col = logical_col
            row = logical_row

        # Input validation
        if not (0 <= row <= 7 and 0 <= col <= 7):
            raise Exception(f"Error: Invalid square name {square_name}")

        # Calculate the theoretical center of the square in millimeters
        theoretical_x = (col * self.cell_size_mm) + (self.cell_size_mm / 2.0)
        theoretical_y = (row * self.cell_size_mm) + (self.cell_size_mm / 2.0)

        # Find the deviation of the detected piece from the theoretical center
        if (row, col) in piece_locations:
            actual_x, actual_y = piece_locations[(row, col)]
            dx = actual_x - theoretical_x
            dy = actual_y - theoretical_y
        else:
            print(f"Warning: No piece detected at {square_name}")
            # If no piece is detected, return a deviation of 0 to move to the theoretical center anyway
            dx, dy = 0.0, 0.0

        return dx/1000.0, dy/1000.0 # return as meters