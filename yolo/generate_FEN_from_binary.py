import json
import cv2
import numpy as np

corners_file = "/home/checkmate/Documents/chess-bot/corners.json"
# Step 1 & 2 mapping: FEN piece -> integer index (0 to 11)
FEN_TO_INT = {
    'b': 0,   # black-bishop
    'k': 1,   # black-king
    'n': 2,   # black-knight
    'p': 3,   # black-pawn
    'q': 4,   # black-queen
    'r': 5,   # black-rook
    'B': 6,   # white-bishop
    'K': 7,   # white-king
    'N': 8,   # white-knight
    'P': 9,   # white-pawn
    'Q': 10,  # white-queen
    'R': 11   # white-rook
}
INT_TO_FEN = {
    0: 'b',  # black-bishop
    1: 'k',  # black-king
    2: 'n',  # black-knight
    3: 'p',  # black-pawn
    4: 'q',  # black-queen
    5: 'r',  # black-rook
    6: 'B',  # white-bishop
    7: 'K',  # white-king
    8: 'N',  # white-knight
    9: 'P',  # white-pawn
    10: 'Q', # white-queen
    11: 'R'  # white-rook
}

# Step 3 mapping: Color label -> integer index
COLOR_TO_INT = {
    "black": 0,
    "white": 1
}
def get_color(label):
    if label<0:
        return -1
    elif label <= 5:
        return 0  # black
    else:
        return 1  # white
def debug_boards(matrices):
    for mat in matrices:
        for row in mat:
            print(row)
        print("\n")

def parse_fen_to_int_grid(fen_string):
    """
    Converts FEN string into an 8x8 grid of integers (0-11, empty=-1)
    and extracts active turn (1 for white, 0 for black).
    
    Returns:
        tuple: (int_grid, active_turn)
    """
    parts = fen_string.split()
    board_part = parts[0]
    
    # 1 for white ('w'), 0 for black ('b')
    active_turn = 1 if (len(parts) > 1 and parts[1].lower() == 'w') else 0

    rows = board_part.split('/')
    int_grid = []

    for row_str in rows:
        grid_row = []
        for char in row_str:
            if char.isdigit():
                grid_row.extend([-1] * int(char))
            else:
                grid_row.append(FEN_TO_INT[char])
        int_grid.append(grid_row)

    return int_grid, active_turn

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
    """Transforms image (x, y) coordinates into grid (row, col) indices."""
    pt = np.array([[[x, y]]], dtype=np.float32)
    warped_pt = cv2.perspectiveTransform(pt, matrix)
    wx, wy = warped_pt[0][0]
    
    square_size = target_size / 8.0
    col = int(wx // square_size)
    row = int(wy // square_size)
    
    return max(0, min(7, row)), max(0, min(7, col))

def create_color_grid(detections_file, corners_file, target_size=800):
    """
    Creates an 8x8 color occupancy grid.
    Values: -1 = empty, 0 = black, 1 = white
    """
    with open(corners_file, "r") as f:
        corners = json.load(f)

    matrix = get_warp_matrix(corners, target_size=target_size)
    
    # Initialize all 64 squares as -1 (empty)
    color_grid = [[-1 for _ in range(8)] for _ in range(8)]

    with open(detections_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split()
            if len(parts) < 3:
                continue
            
            label = parts[0].lower()  # Expected: 'white' or 'black'
            x = float(parts[1])
            y = float(parts[2])

            color_val = COLOR_TO_INT.get(label)
            if color_val is not None:
                row, col = get_grid_position(x, y, matrix, target_size=target_size)
                color_grid[row][col] = color_val

    return color_grid

def grid_to_fen(board_grid, active_turn="w"):
    """
    Converts an 8x8 integer grid (0-11, -1) into a FEN string.
    """
    fen_rows = []
    for row in range(8):
        empty_count = 0
        row_str = ""
        for col in range(8):
            val = board_grid[row][col]
            if val == -1 or val is None:
                empty_count += 1
            else:
                if empty_count > 0:
                    row_str += str(empty_count)
                    empty_count = 0
                row_str += INT_TO_FEN[val]
        if empty_count > 0:
            row_str += str(empty_count)
        fen_rows.append(row_str)
    
    board_fen = "/".join(fen_rows)
    return f"{board_fen} {active_turn} - - 0 1"

def build_fen(old_fen, detections_file):
    """
    Generates a new FEN string based on the old FEN and detected colors.
    """
    old_board_grid, active_turn = parse_fen_to_int_grid(old_fen)
    detected_color_grid = create_color_grid(detections_file, corners_file)
    debug_boards([old_board_grid, detected_color_grid])

    new_board_grid = [[None for _ in range(8)] for _ in range(8)]

    moved_source=[]
    moved_target=[]
    captured=[]

    for row in range(8):
        for col in range(8):
            old_piece = old_board_grid[row][col]
            old_piece_type = get_color(old_piece)
            new_piece_type = detected_color_grid[row][col]

            if old_piece_type == new_piece_type:
                continue  # No change in piece type
            elif old_piece_type == -1 and new_piece_type != -1:
                # moved here
                moved_target.append((row, col))
            elif old_piece_type != -1 and new_piece_type == -1:
                # moved from here
                moved_source.append((row, col))
            elif old_piece_type != -1 and new_piece_type != -1:
                # captured here
                captured.append((row, col))

    print(f"Moved Source: {moved_source}, Moved Target: {moved_target}, Captured: {captured}")
    if len(captured) > 0:
        # Handle capture: Move the piece from moved_source to captured square
        capturing_piece = old_board_grid[moved_source[0][0]][moved_source[0][1]]
        old_board_grid[moved_source[0][0]][moved_source[0][1]] = -1
        old_board_grid[captured[0][0]][captured[0][1]] = capturing_piece
    elif len(moved_source) == 1 and len(moved_target) == 1:
        # Handle normal move: Move the piece from moved_source to moved_target
        moving_piece = old_board_grid[moved_source[0][0]][moved_source[0][1]]
        old_board_grid[moved_source[0][0]][moved_source[0][1]] = -1
        old_board_grid[moved_target[0][0]][moved_target[0][1]] = moving_piece
    elif len(moved_source) == 2 and len(moved_target) == 2:
        # Handle castling: Move the king and rook to their new positions
        king_source = None
        rook_source = None
        king_target = None
        rook_target = None

        distance_from_mid_source_0 = abs(moved_source[0][1] - 4) 
        distance_from_mid_source_1 = abs(moved_source[1][1] - 4) 
        distance_from_mid_target_0 = abs(moved_target[0][1] - 4) 
        distance_from_mid_target_1 = abs(moved_target[1][1] - 4) 

        if distance_from_mid_source_0 < distance_from_mid_source_1:
            king_source = moved_source[0]
            rook_source = moved_source[1]
        else:
            king_source = moved_source[1]
            rook_source = moved_source[0]
        if distance_from_mid_target_0 > distance_from_mid_target_1:
            king_target = moved_target[0]
            rook_target = moved_target[1]
        else:
            king_target = moved_target[1]
            rook_target = moved_target[0]
        
        king_piece = old_board_grid[king_source[0]][king_source[1]]
        rook_piece = old_board_grid[rook_source[0]][rook_source[1]]
        old_board_grid[king_source[0]][king_source[1]] = -1
        old_board_grid[rook_source[0]][rook_source[1]] = -1
        old_board_grid[king_target[0]][king_target[1]] = king_piece
        old_board_grid[rook_target[0]][rook_target[1]] = rook_piece
    elif len(moved_source) == 2 and len(moved_target) == 1:
        source0_label = old_board_grid[moved_source[0][0]][moved_source[0][1]]
        source1_label = old_board_grid[moved_source[1][0]][moved_source[1][1]]
        if [source0_label, source1_label].sort() == [3, 9].sort():  # one black pawn and one white pawn
            # Handle en passant: Move the pawn from moved_source to moved_target and remove the captured pawn
            for source in moved_source:
                old_board_grid[source[0]][source[1]] = -1  # Clear both source squares
            old_board_grid[moved_target[0][0]][moved_target[0][1]] = 3+active_turn*6  # Set the moving pawn in the target square
        else:
            print("Error: Unexpected move scenario.")
        
    else:
        print("Error: Unexpected move scenario.")
    return grid_to_fen(old_board_grid)
        

            

    


# --- EXECUTION ---

if __name__ == "__main__":
    old_fen = "RN1KQ2R/Pq1P1PP1/3P2B1/2Pp4/b2N1p2/7n/pbpp4/rn2rk2 b - - 0 1"

    print(build_fen(old_fen, "/home/checkmate/Documents/chess-bot/yolo/predictions/EN_PASSANT_D5_C6.txt"))