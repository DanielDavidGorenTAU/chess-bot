from abc import ABC, abstractmethod
from typing import Optional
from common.enums_and_dicts import PieceType
from chessbot import *

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


    def _move_piece(self, type=None, start_pos=None, end_pos=None, speed=None, acceleration=None, rz_rotation_start=None, rz_rotation_end=None, move_to_start=True):
        """
        Private method for moving a piece, using the hardware class
        """
        robot = self.robot_hardware
        if speed is None:
            speed = robot.speed
        if acceleration is None:
            acceleration = robot.acceleration
        if robot[Z] < robot.safe_height:
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
        robot.move_to(z=robot.grip_height[type])

        robot.set_gripper(CLOSED) # grip the piece

        # move to end spot
        robot.move_to(start_pos, z=robot.safe_height)
        robot.move_to(end_pos, z=robot.safe_height, speed=speed, acceleration=acceleration)
        robot.move_to(z=robot.grip_height[type] + GRIP_RELEASE_HEIGHT)
        
        robot.set_gripper(robot.get_gripper() - GRIP_RELEASE_OFFSET) # release the piece
        
        # return to start postion
        robot.move_to(z=robot.safe_height)
        if move_to_start:
            robot.move_to(robot.start_position, z=robot.safe_height, speed=speed, acceleration=acceleration)


    def _remove_piece(self, type: PieceType, start_pos, end_pos = None, rz_start=None, move_to_start=True):
        """
        Private method for remove a piece, using the hardware class
        """
        robot = self.robot_hardware
        if end_pos is None:
            end_pos = list(map(float, get_head_camera_point())) + robot.down_orientation
        start_pos = robot.normalize_pos(start_pos)
        end_pos = robot.normalize_pos(end_pos)
        robot.move_to(start_pos, z=robot.safe_height, orientation=robot.down_orientation)
        robot.set_gripper(grip_size[type] - GRIP_RELEASE_OFFSET,wait=False) #  open the gripper
        robot.move_to(z=robot.grip_height[type])
        robot.set_gripper(CLOSED)
        robot.move_to(z=robot.safe_height)
        #print(f"{end_pos = }")
        robot.move_to(end_pos, z=robot.safe_height)
        robot.move_to(z=robot.grip_height[type]+OFFSET_TO_TABLE_HEIGHT)
        robot.set_gripper(open_by=GRIP_RELEASE_OFFSET)
        robot.move_to(z=robot.safe_height)
        if move_to_start:
            robot.move_to(robot.start_position, z=robot.safe_height)

    def _bring_on_board(self, type: PieceType, end_pos, start_pos=None, rz_end=None, move_to_start=True):
        """
        Private method for bringing a piece onto the board from off-board storage/graveyard
        (e.g., for pawn promotions).
        """
        robot = self.robot_hardware

        # 1. Default start_pos to the off-board storage / camera position if None
        if start_pos is None:
            start_pos = list(map(float, get_head_camera_point())) + robot.down_orientation

        start_pos = robot.normalize_pos(start_pos)
        end_pos = robot.normalize_pos(end_pos)

        # 2. Apply Rz rotation to destination orientation if provided (important for Knights/Rooks)
        if rz_end is not None:
            end_pos[3:6] = robot.get_rotated_tcp_orientation(end_pos, Rz=rz_end)

        # 3. Safety check: ensure robot arm is at safe height
        if robot[Z] < robot.safe_height:
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
            robot.move_to(robot.start_position, z=robot.safe_height)
    
    def move(self, from_square: str, to_square: str, piece: PieceType) -> bool:
        try:
            self._move_piece(piece, from_square, to_square)
            return True
        except Exception:
            return False

    def capture(self, from_square: str, to_square: str, remove_square: str, moving_piece: PieceType, captured_piece: PieceType) -> bool:
        try:
            self._remove_piece(captured_piece, remove_square, move_to_start=False)
            self._move_piece(moving_piece, from_square, to_square)
            return True
        except Exception:
            return False

    def castle(self, king_from_square: str, king_to_square: str, rook_from_square: str, rook_to_square: str) -> bool: 
        try:
            self._move_piece(PieceType.KING, king_from_square, king_to_square, move_to_start=False)
            self._move_piece(PieceType.ROOK, rook_from_square, rook_to_square)
            return True
        except Exception:
            return False

    def upgrade(self, from_square: str, to_square: str, promoted_piece: PieceType = PieceType.QUEEN, captured_piece: Optional[PieceType] = None) -> bool:
        try:
            if captured_piece is not None:
                self._remove_piece(captured_piece, to_square)
            self._remove_piece(PieceType.PAWN, from_square, move_to_start=False)
            self._bring_on_board(promoted_piece, to_square)       
            return True
        except Exception:
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