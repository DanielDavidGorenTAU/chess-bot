from typing import Optional
from common.enums_and_dicts import PieceType
from common.utils import convert_type_and_color_to_fen_char

class StorageManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        # Singleton 
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            
            # Inventory management tracking pieces off the board
            cls._instance.storage_state = {
                'sP': 0, 'sp': 0,   
                'sR': 0, 'sr': 0,
                'sN': 0, 'sn': 0,   
                'sB': 0, 'sb': 0,
                'sQ': 0, 'sq': 0,
                'sK': 0, 'sk': 0
            }
        return cls._instance

    # ==============================================================
    # Synchronization functions for human moves (Memory update only)
    # ==============================================================
    
    def register_human_capture(self, type: PieceType, color: str):
        """
        Updates the inventory state when a human captures a piece and places it in storage.
        """
        fen_char = convert_type_and_color_to_fen_char(type, color)
        self.storage_state[f"s{fen_char}"] += 1 

    def register_human_promotion(self, type: PieceType, color: str):
        """
        Updates the inventory state when a human takes a piece from storage for a promotion.
        """
        fen_char = convert_type_and_color_to_fen_char(type, color)
        self.storage_state[f"s{fen_char}"] -= 1 

    # ==============================================================
    # Movement functions for robot moves
    # ==============================================================

    def get_slot_for_robot_capture(self, type: PieceType, color: str) -> str:
        """
        Updates the inventory when the robot captures a piece, 
        and returns the exact slot name the robotic arm should move to.
        """
        fen_char = convert_type_and_color_to_fen_char(type, color)
        self.storage_state[f"s{fen_char}"] += 1 
        index = self.storage_state[f"s{fen_char}"]
        
        return f"s{fen_char}{index}"
        
    def get_slot_for_robot_promotion(self, type: PieceType, color: str) -> str:
        """
        Returns the exact slot name from which the robot should take a piece for promotion, 
        and updates the inventory state accordingly.
        """
        fen_char = convert_type_and_color_to_fen_char(type, color)
        index = self.storage_state[f"s{fen_char}"]
        
        if index <= 0:
            raise Exception(f"No {fen_char} in storage to remove!")
            
        slot_name = f"s{fen_char}{index}"
        self.storage_state[f"s{fen_char}"] -= 1 

        return slot_name