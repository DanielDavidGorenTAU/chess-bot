from abc import ABC, abstractmethod
from typing import Optional
from common.enums_and_dicts import *
from .chessbot import *
from main.config import AppConfig
from common.utils import convert_type_and_color_to_fen_char

class PlayingRobot(ABC):

    """
    Interface to handle moving pieces according to command during game
    Each move method returns the True if successfull, otherwise False
    """

    @abstractmethod
    def move(self, from_square: str, to_square: str, piece: PieceType) -> bool:
        pass

    @abstractmethod
    def capture(self, from_square: str, to_square: str, remove_square: str, moving_piece: PieceType, captured_piece: PieceType) -> bool:
        pass

    @abstractmethod
    def castle(self, king_from_square: str, king_to_square: str, rook_from_square: str, rook_to_square: str) -> bool: 
        pass

    @abstractmethod
    def upgrade(self, from_square: str, to_square: str, promoted_piece: PieceType = PieceType.QUEEN, captured_piece: Optional[PieceType] = None) -> bool:
        pass



  
        



class PlayingArm(PlayingRobot):

    """
    Real UR5E arm class for playing
    """

    def __init__(self, robot_hardware: RobotHardware):
        self.robot_hardware = robot_hardware
        self.storage_state =  {
            'sP': 0, 'sp': 0,   
            'sR': 0, 'sr': 0,
            'sN': 0, 'sn': 0,   
            'sB': 0, 'sb': 0,
            'sQ': 0, 'sq': 0,
            'sK': 0, 'sk': 0
        }

        config = AppConfig.load("/home/checkmate/Documents/chess-bot/main/config.yaml")
        self.human_color = config.game.get_color_for("human")
        self.robot_color = config.game.get_color_for("robot")

    # return storage location to store piece
    def put_in_storage_pos(self, type: PieceType=None, color: Optional[str]=None):
        
        if type == None or color == None:
            raise Exception("Error pieceType or color for storage")
        
        fen_char = convert_type_and_color_to_fen_char(type, color)

        self.storage_state[f"s{fen_char}"] += 1 # update storage state
        index = self.storage_state[f"s{fen_char}"]

        return f"s{fen_char}{index}"
        
    # return storage location to get piece
    def remove_from_storage_pos(self, type: PieceType=None, color: Optional[str]=None):
        
        if type == None or color == None:
            raise Exception("Error pieceType or color for storage")
        
        fen_char = convert_type_and_color_to_fen_char(type, color)

        index = self.storage_state[f"s{fen_char}"]
        if index <= 0:
            raise Exception(f"No {fen_char} in storage to remove!")
        self.storage_state[f"s{fen_char}"] -= 1 # update storage state

        return f"s{fen_char}{index}"

    def _move_piece(self, type=None, start_pos=None, end_pos=None, speed=None, acceleration=None, rz_rotation_start=None, rz_rotation_end=None, move_to_start=True):
        """
        Private method for moving a piece, using the hardware class
        """
        robot = self.robot_hardware
        if speed is None:
            speed = robot.speed
        if acceleration is None:
            acceleration = robot.acceleration
        if robot.pose[Z] < robot.safe_height:
            robot.move_to(z=robot.safe_height)

        # update chess board locations
        start_pos = robot.normalize_pos(start_pos)
        end_pos = robot.normalize_pos(end_pos)
        if rz_rotation_start is not None:
            start_pos[3:6] = robot.get_rotated_tcp_orientation(start_pos,Rz=rz_rotation_start)
        if rz_rotation_end is not None:
            end_pos[3:6] = robot.get_rotated_tcp_orientation(end_pos,Rz=rz_rotation_end)

        robot.set_gripper(grip_size[type] - GRIP_RELEASE_OFFSET,wait=False) #  open the gripper

        # move to first spot
        robot.move_to(start_pos, z=robot.safe_height, speed=speed, acceleration=acceleration) 

        # grip the piece
        robot.move_to(z=robot.grip_height[type])
        robot.set_gripper(CLOSED) 
        robot.move_to(start_pos, z=robot.safe_height)

        # move to end spot
        robot.move_to(end_pos, z=robot.safe_height, speed=speed, acceleration=acceleration)
        robot.move_to(z=robot.grip_height[type] + GRIP_RELEASE_HEIGHT)
        
        robot.set_gripper(robot.get_gripper() - GRIP_RELEASE_OFFSET) # release the piece
        
        # return to start postion
        robot.move_to(z=robot.safe_height)
        if move_to_start:
            robot.move_to(robot.start_position, z=robot.sky_height, speed=speed, acceleration=acceleration)

    def _remove_piece(self, type: PieceType, start_pos, end_pos = None, rz_start=None, move_to_start=True):
        """
        Private method for remove a piece, using the hardware class
        """
        robot = self.robot_hardware
        if end_pos is None:
            end_pos = list(map(float, get_head_camera_point())) + robot.down_orientation
        else:
            end_pos = robot.normalize_pos(end_pos)
        # or get a location to put the piece

        start_pos = robot.normalize_pos(start_pos)
        end_pos = robot.normalize_pos(end_pos)
        robot.move_to(start_pos, z=robot.safe_height, orientation=robot.down_orientation)
        robot.set_gripper(grip_size[type] - GRIP_RELEASE_OFFSET,wait=False) #  open the gripper
        robot.move_to(z=robot.grip_height[type])
        robot.set_gripper(CLOSED)
        robot.move_to(z=robot.safe_height)
        
        robot.move_to(end_pos, z=robot.safe_height)
        robot.move_to(z=robot.grip_height[type]+OFFSET_TO_TABLE_HEIGHT)
        robot.set_gripper(open_by=GRIP_RELEASE_OFFSET)
        robot.move_to(z=robot.safe_height)
        if move_to_start:
            robot.move_to(robot.start_position, z=robot.sky_height)

    def _bring_on_board(self, type: PieceType, end_pos, start_pos=None, rz_end=None, move_to_start=True):
        """
        Private method for bringing a piece onto the board from off-board storage/graveyard
        (e.g., for pawn promotions).
        """
        robot = self.robot_hardware

        # 1. Default start_pos to the off-board storage / camera position if None
        if start_pos is None:
            start_pos = list(map(float, get_head_camera_point())) + robot.down_orientation
        else:
            start_pos = robot.normalize_pos(start_pos)  
        # or get a location to pick up the piece

        start_pos = robot.normalize_pos(start_pos)
        end_pos = robot.normalize_pos(end_pos)

        # 2. Apply Rz rotation to destination orientation if provided (important for Knights)
        if rz_end is not None:
            end_pos[3:6] = robot.get_rotated_tcp_orientation(end_pos, Rz=rz_end)

        # 3. Safety check: ensure robot arm is at safe height
        if robot.pose[Z] < robot.safe_height:
            robot.move_to(z=robot.safe_height)

        # --- PICKUP FROM STORAGE ---
        # Move over storage, open gripper, lower, and grab
        robot.move_to(start_pos, z=robot.safe_height)
        robot.set_gripper(grip_size[type] - GRIP_RELEASE_OFFSET, wait=False)
        robot.move_to(z=robot.grip_height[type] + OFFSET_TO_TABLE_HEIGHT)
        robot.set_gripper(CLOSED)
        robot.move_to(z=robot.safe_height)

        # --- PLACE ON BOARD ---
        # Move over board square, lower to board release height, and open gripper
        robot.move_to(end_pos, z=robot.safe_height)
        robot.move_to(z=robot.grip_height[type] + GRIP_RELEASE_HEIGHT)
        robot.set_gripper(open_by=GRIP_RELEASE_OFFSET)

        # --- RETURN TO SAFE POSITION ---
        robot.move_to(z=robot.safe_height)
        if move_to_start:
            robot.move_to(robot.start_position, z=robot.sky_height)

    # return true if pos is on board
    def _is_on_board(self, pos: str) -> bool:
        if pos is None or not pos:
            return False
        return len(pos) == 2 and pos[0] in "abcdefgh" and pos[1] in "12345678"

    # general movement of robot
    # examples
    # "e3" -> "b6" : from square -> square
    # "sP2" -> "b6" : from storage -> square
    # "e3" -> "sP2" : from square -> storage
    def _execute_movement(self, piece: PieceType, start_pos: Optional[str] = None, end_pos: Optional[str] = None, move_to_start: bool = True):
        start_on_board = self._is_on_board(start_pos)
        end_on_board = self._is_on_board(end_pos)

        robot = self.robot_hardware
        if start_pos == "storage":
            start_pos = robot.positions['sP1']
        if end_pos == "storage":
            end_pos = robot.positions['sP1']

        if start_on_board is True and end_on_board is True:                             # from square -> square
            self._move_piece(piece, start_pos, end_pos, move_to_start=move_to_start)
        elif start_on_board is True and end_on_board is False:                          # from square -> storage
            self._remove_piece(piece, start_pos, end_pos,move_to_start=move_to_start)
        elif start_on_board is False and end_on_board is True:                          # from storage -> square
            self._bring_on_board(piece, end_pos, start_pos, move_to_start=move_to_start)
        else:
            raise Exception("Invalid square/borad coordinations provided")



    def move(self, from_square: str, to_square: str, piece: PieceType) -> bool:
        try:
            print(f"Moving {piece} from {from_square} to {to_square}")
            self._execute_movement(piece, start_pos=from_square, end_pos=to_square) # move
            return True
        except Exception as e:
            print(f"[Robot] Move failed: {type(e).__name__}: {e}")
            return False

    def capture(self, from_square: str, to_square: str, remove_square: str, moving_piece: PieceType, captured_piece: PieceType) -> bool:
        try:
            storage_pos = self.put_in_storage_pos(captured_piece, self.human_color)
            self._execute_movement(captured_piece, remove_square, storage_pos, move_to_start=False) # remove
            self._execute_movement(moving_piece, from_square, to_square)                          # move
            return True
        except Exception as e:
            print(f"[Robot] Capture failed: {type(e).__name__}: {e}")
            return False

    def castle(self, king_from_square: str, king_to_square: str, rook_from_square: str, rook_to_square: str) -> bool: 
        try:
            self._execute_movement(PieceType.KING, king_from_square, king_to_square, move_to_start=False) # move
            self._execute_movement(PieceType.ROOK, rook_from_square, rook_to_square)                      # move
            return True
        except Exception as e:
            print(f"[Robot] Castle failed: {type(e).__name__}: {e}")
            return False

    def upgrade(self, from_square: str, to_square: str, promoted_piece: PieceType = PieceType.QUEEN, captured_piece: Optional[PieceType] = None) -> bool:
        try:
            if captured_piece is not None: 
                storage_pos = self.put_in_storage_pos(captured_piece, self.human_color)
                self._execute_movement(captured_piece, to_square, storage_pos)                        # remove
            storage_pos = self.put_in_storage_pos(PieceType.PAWN, self.robot_color)
            self._execute_movement(PieceType.PAWN, from_square, storage_pos, move_to_start=False)     # remove
            storage_pos = self.remove_from_storage_pos(promoted_piece, self.robot_color)
            self._execute_movement(promoted_piece, storage_pos, to_square)                            # get
            return True
        except Exception as e:
            print(f"[Robot] Upgrade failed: {type(e).__name__}: {e}")
            return False        



        
class PlayingMock(PlayingRobot):

    """
    Mock Class for PlayingRobot
    res determines if will fail or succeed
    """
    def __init__(self, res: bool = True):
        """
        res = false -> fails / true -> succeeds
        """
        self.res = res
    
    def move(self, from_square: str, to_square: str, piece: PieceType) -> bool:
        return self.res

    def capture(self, from_square: str, to_square: str, remove_square: str, moving_piece: PieceType, captured_piece: PieceType) -> bool:
        return self.res

    def castle(self, king_from_square: str, king_to_square: str, rook_from_square: str, rook_to_square: str) -> bool: 
        return self.res

    def upgrade(self, from_square: str, to_square: str, promoted_piece: PieceType = PieceType.QUEEN, captured_piece: Optional[PieceType] = None) -> bool:
        return self.res