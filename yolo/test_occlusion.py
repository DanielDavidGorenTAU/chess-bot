import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from yolo.fen_translator import BinaryToFenTranslator
import yolo.fen_translator

# ---------------------------------------------------------
# MOCK SETUP: MATCHING REAL YOLO CLASSES
# ---------------------------------------------------------
# 0-5 are Black (0), 6-11 are White (1)
def mock_get_color(piece):
    if piece == -1: return -1
    if piece >= 6: return 1  # White
    return 0                 # Black

yolo.fen_translator.get_color = mock_get_color

# Real Piece IDs from your YAML
B_BISHOP = 0
B_KING = 1
B_KNIGHT = 2
B_PAWN = 3
B_QUEEN = 4
B_ROOK = 5

W_BISHOP = 6
W_KING = 7
W_KNIGHT = 8
W_PAWN = 9
W_QUEEN = 10
W_ROOK = 11

def create_empty_grid():
    return [[-1 for _ in range(8)] for _ in range(8)]

def run_scenario(translator, name, active_turn, old_setup, detected_setup, expected_results):
    print(f"--- {name} ---")
    
    old_board = create_empty_grid()
    for r, c, val in old_setup:
        old_board[r][c] = val
        
    detected_board = create_empty_grid()
    for r, c, val in detected_setup:
        detected_board[r][c] = val
        
    repaired = translator._repair_occlusions(old_board, detected_board, active_turn)
    
    passed = True
    for r, c, expected in expected_results:
        if repaired[r][c] != expected:
            print(f"  [FAIL] Square ({r}, {c}) -> Expected {expected}, got {repaired[r][c]}")
            passed = False
            
    if passed:
        print("  [PASS] All assertions met.\n")
    else:
        print("  [FAIL] Scenario failed.\n")

def run_all_tests():
    translator = BinaryToFenTranslator()
    
    run_scenario(
        translator,
        name="Scenario 1: White moves, occludes Black Pawn",
        active_turn=1,  # White
        old_setup=[(2, 3, B_PAWN), (6, 3, W_QUEEN)],
        detected_setup=[(3, 3, 1)], 
        expected_results=[(2, 3, 0), (6, 3, -1), (3, 3, 1)]
    )

    run_scenario(
        translator,
        name="Scenario 2: Black moves, occludes White Knight",
        active_turn=0,  # Black
        old_setup=[(4, 4, W_KNIGHT), (1, 4, B_ROOK)],
        detected_setup=[(3, 4, 0)], 
        expected_results=[(4, 4, 1), (1, 4, -1), (3, 4, 0)]
    )

    run_scenario(
        translator,
        name="Scenario 3: Capture! (Should NOT restore captured piece)",
        active_turn=1, 
        old_setup=[(2, 2, B_PAWN), (5, 5, W_QUEEN)],
        detected_setup=[(2, 2, 1)], 
        expected_results=[(2, 2, 1), (5, 5, -1)]
    )

    run_scenario(
        translator,
        name="Scenario 4: Active piece missed by YOLO",
        active_turn=1, 
        old_setup=[(7, 4, W_QUEEN)],
        detected_setup=[], 
        expected_results=[(7, 4, -1)]
    )

    run_scenario(
        translator,
        name="Scenario 5: Multiple Occlusions at once",
        active_turn=1, 
        old_setup=[(1, 1, B_PAWN), (1, 2, B_PAWN), (5, 1, W_QUEEN)],
        detected_setup=[(2, 1, 1)], 
        expected_results=[(1, 1, 0), (1, 2, 0), (5, 1, -1)]
    )

    run_scenario(
        translator,
        name="Scenario 6: The En Passant Edge Case",
        active_turn=1, 
        old_setup=[(3, 4, W_PAWN), (3, 3, B_PAWN)],  # Using accurate Pawn IDs!
        detected_setup=[(2, 3, 1)], 
        expected_results=[(2, 3, 1), (3, 3, -1), (3, 4, -1)]
    )

    run_scenario(
        translator,
        name="Scenario 7: YOLO False Positive",
        active_turn=1,
        old_setup=[(7, 0, B_ROOK)],
        detected_setup=[(7, 0, 0), (4, 4, 1)], 
        expected_results=[(7, 0, 0), (4, 4, 1)]
    )

    run_scenario(
        translator,
        name="Scenario 8: YOLO Color Misclassification",
        active_turn=0, 
        old_setup=[(0, 0, W_QUEEN)],
        detected_setup=[(0, 0, 0)], 
        expected_results=[(0, 0, 0)]
    )

    run_scenario(
        translator,
        name="Scenario 9: Total Camera Glitch",
        active_turn=1,
        old_setup=[(0, 0, B_ROOK), (0, 7, B_ROOK), (7, 4, W_QUEEN)],
        detected_setup=[], 
        expected_results=[(0, 0, 0), (0, 7, 0), (7, 4, -1)]
    )
    
    run_scenario(
        translator,
        name="Scenario 10: Castling Occlusion",
        active_turn=1, 
        old_setup=[(7, 4, W_KING), (7, 7, W_ROOK)], 
        detected_setup=[(7, 6, 1)], 
        expected_results=[(7, 6, 1), (7, 5, -1), (7, 4, -1), (7, 7, -1)]
    )

if __name__ == "__main__":
    run_all_tests()