from enum import IntEnum

class PieceType(IntEnum):
    BISHOP = 0
    KING = 1
    KNIGHT = 2
    PAWN = 3
    QUEEN = 4
    ROOK = 5

    @property
    def label(self):
        return self.name.lower()

class ColoredPieceType(IntEnum):
    BLACK_BISHOP = 0
    BLACK_KING = 1
    BLACK_KNIGHT = 2
    BLACK_PAWN = 3
    BLACK_QUEEN = 4
    BLACK_ROOK = 5
    WHITE_BISHOP = 6
    WHITE_KING = 7
    WHITE_KNIGHT = 8
    WHITE_PAWN = 9
    WHITE_QUEEN = 10
    WHITE_ROOK = 11    

    @property
    def label(self):
        return self.name.lower()
    
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

INT_TO_NAME = ["black-bishop", "black-king", "black-knight", "black-pawn", "black-queen", "black-rook", 
               "white-bishop", "white-king", "white-knight", "white-pawn", "white-queen", "white-rook"]

PROMOTED_PIECES = {
    'b' : PieceType.BISHOP,
    'n' : PieceType.KNIGHT,
    'q' : PieceType.QUEEN,
    'r' : PieceType.ROOK
}

COLOR_TO_INT = {
    "black": 0,
    "white": 1
}

class Orientation(IntEnum):
    """Enum representing the orientation state of a piece using integers."""
    LYING = 0
    STANDING = 1