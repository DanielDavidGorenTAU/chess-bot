from enums_and_dicts import *
def convert_square_to_coordinates(square: str):
    """
    Takes a string of chessboard square and converts to matrix coordinate (row, col)
    For example: e4 -> (4,4), a1 -> (7,0)
    """
    if len(square) != 2:
        raise ValueError(f"Invalid square: {square}")

    file, rank = square[0].lower(), square[1]

    if file not in "abcdefgh" or rank not in "12345678":
        raise ValueError(f"Invalid square: {square}")

    col = ord(file) - ord('a')
    row = 8 - int(rank)
    return row, col

def convert_coordinates_to_square(row: int, col: int) -> str:
    """
    Converts 0-indexed matrix coordinates (row, col) to algebraic chess square notation.
    Assumes standard FEN layout where row 0 = Rank 8 and col 0 = File 'a'.
    
    Examples:
        (0, 0) -> 'a8'
        (7, 4) -> 'e1'
        (6, 4) -> 'e2'
    """
    if not (0 <= row <= 7 and 0 <= col <= 7):
        raise ValueError(f"Coordinates ({row}, {col}) are out of bounds. Must be 0-7.")

    file_char = chr(ord('a') + col)
    rank_char = str(8 - row)

    return f"{file_char}{rank_char}"

def convert_string_to_chessType(letter: str) -> PieceType:
    """
    Converts a UCI promotion character ('q', 'r', 'b', 'n') to a PieceType.
    Raises ValueError if letter is None, empty, or an invalid piece character.
    """
    if letter.lower() not in PROMOTED_PIECES:
        raise ValueError(
            f"Invalid promotion piece: {letter}. "
            f"Expected one of: {list(PROMOTED_PIECES.keys())}"
        )

    return PROMOTED_PIECES[letter.lower()]


def parse_fen_to_int_grid(fen_string: str):
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

def grid_to_fen(board_grid, active_turn=1):
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
    char_active_turn = "b" if active_turn == 0 else "w"
    board_fen = "/".join(fen_rows)
    return f"{board_fen} {char_active_turn} - - 0 1"