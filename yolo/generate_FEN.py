import json
import cv2
import numpy as np

# Mapping your custom label format to standard FEN notation
LABEL_TO_FEN = {
    "white-pawn": "P",   "black-pawn": "p",
    "white-knight": "N", "black-knight": "n",
    "white-bishop": "B", "black-bishop": "b",
    "white-rook": "R",   "black-rook": "r",
    "white-queen": "Q",  "black-queen": "q",
    "white-king": "K",   "black-king": "k"
}

def get_warp_matrix(corners, target_size=800):
    src_pts = np.array(corners, dtype="float32")
    dst_pts = np.float32([
        [0, 0],
        [target_size - 1, 0],
        [target_size - 1, target_size - 1],
        [0, target_size - 1]
    ])
    return cv2.getPerspectiveTransform(src_pts, dst_pts)

def get_grid_position(x, y, matrix, target_size=800):
    """Maps (x, y) image coordinates into an 8x8 matrix (row, col)."""
    pt = np.array([[[x, y]]], dtype=np.float32)
    warped_pt = cv2.perspectiveTransform(pt, matrix)
    wx, wy = warped_pt[0][0]
    
    square_size = target_size / 8.0
    col = int(wx // square_size)
    row = int(wy // square_size)
    
    # Clamp coordinates inside [0, 7]
    col = max(0, min(7, col))
    row = max(0, min(7, row))
    return row, col

def build_fen(board_grid, active_color="w"):
    """Converts 8x8 piece grid into standard FEN string."""
    fen_rows = []
    for row in range(8):
        empty_count = 0
        row_str = ""
        for col in range(8):
            piece = board_grid[row][col]
            if piece is None:
                empty_count += 1
            else:
                if empty_count > 0:
                    row_str += str(empty_count)
                    empty_count = 0
                row_str += piece
        if empty_count > 0:
            row_str += str(empty_count)
        fen_rows.append(row_str)
    
    return "/".join(fen_rows) + f" {active_color} - - 0 1"

def process_fen(corners_file="corners.json", detections_file="/home/checkmate/Documents/chess-bot/predictions/zed_20260729_133021_178.txt"):
    # 1. Load saved 4 corners
    with open(corners_file, "r") as f:
        corners = json.load(f)

    matrix = get_warp_matrix(corners, target_size=800)
    board_grid = [[None for _ in range(8)] for _ in range(8)]

    # 2. Read piece detections file
    with open(detections_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split()
            if len(parts) < 3:
                continue
            
            label = parts[0].lower()
            x = float(parts[1])
            y = float(parts[2])

            fen_symbol = LABEL_TO_FEN.get(label)
            if fen_symbol:
                row, col = get_grid_position(x, y, matrix)
                board_grid[row][col] = fen_symbol
            else:
                print(f"Warning: Unrecognized piece label '{label}'")

    # 3. Generate and return FEN
    fen = build_fen(board_grid)
    return fen

if __name__ == "__main__":
    fen_result = process_fen("/home/checkmate/Documents/chess-bot/corners.json", "/home/checkmate/Documents/chess-bot/predictions/zed_20260729_145441_791.txt")
    print("Generated FEN:\n", fen_result)