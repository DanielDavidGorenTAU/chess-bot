from abc import ABC, abstractmethod
from typing import Optional
from common.enums_and_dicts import *
from .chessbot import *
from main.config import AppConfig
from .StorageManager import StorageManager
from .robot_board_mapper import RobotBoardMapper
import math
from perception_state import PerceptionState

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
        self.storage = StorageManager() # call Singleton
        self.board_mapper = RobotBoardMapper()

        config = AppConfig.load("/home/checkmate/Documents/chess-bot/main/config.yaml")
        self.human_color = config.game.get_color_for("human")
        self.robot_color = config.game.get_color_for("robot")

        if self.human_color == "white": # flip the board
            self.board_mapper.flip = True
    

    def _move_piece(self, type=None, start_pos=None, end_pos=None, speed=None, acceleration=None, rz_rotation_start=None, rz_rotation_end=None, move_to_start=True):
        """
        Private method for moving a piece, using the hardware class
        """
        robot = self.robot_hardware
        
        if speed is None:
            speed = robot.speed
        if acceleration is None:
            acceleration = robot.acceleration

        # --- APPLY HEIGHT SAFTEY ---
        if robot.pose[Z] < robot.safe_height:
            robot.move_to(z=robot.safe_height)

        # get chess board deviations 
        dx, dy = self.board_mapper.get_piece_grasping_data(square_name=start_pos)

        # --- GET PHYSICAL POSITIONS ---
        start_pos = robot.normalize_pos(start_pos)
        end_pos = robot.normalize_pos(end_pos)

        if rz_rotation_start is not None:
            start_pos[3:6] = robot.get_rotated_tcp_orientation(start_pos,Rz=rz_rotation_start)
        if rz_rotation_end is not None:
            end_pos[3:6] = robot.get_rotated_tcp_orientation(end_pos,Rz=rz_rotation_end)

        robot.set_gripper(grip_size[type] - GRIP_RELEASE_OFFSET,wait=False) #  open the gripper

        # --- PICKUP FROM BOARD ---
        bias = 0.7
        start_pos = robot.move_on_chessboard(start_pos, right = bias * dx, up = bias * dy) # update deviation
        robot.move_to(start_pos, z=robot.safe_height, speed=speed, acceleration=acceleration) 
        robot.move_to(z=robot.grip_height[type])
        robot.set_gripper(CLOSED) # grip the piece
        robot.move_to(z=robot.safe_height)

        # --- PLACE ON BOARD ---
        robot.move_to(end_pos, z=robot.safe_height, speed=speed, acceleration=acceleration)
        robot.move_to(z=robot.grip_height[type] + GRIP_RELEASE_HEIGHT)
        robot.set_gripper(robot.get_gripper() - GRIP_RELEASE_OFFSET) # release the piece
        robot.move_to(z=robot.safe_height)

        if move_to_start:
            robot.move_to(robot.start_position, z=robot.sky_height, speed=speed, acceleration=acceleration)

    def _get_dynamic_yaw(self, dx, dy, piece_type=None, threshold=0.005):
        """
        Calculates the rotation angle (Rz) in radians based on the deviation zone (9-zone grid).
        The threshold is in meters (e.g., 0.01 meters = 1 cm).
        """

        # Hard exception: Knights should never rotate to avoid slipping from the gripper TODO (elad) delete
        #if piece_type and piece_type.lower() == 'knight':
        #    return 0.0

        # Determine position relative to the center safe zone
        is_right = dx > threshold
        is_left = dx < -threshold
        is_bottom = dy > threshold
        is_top = dy < -threshold

        # Corner checks (45 degrees rotation)
        if is_top and is_right:
            return math.radians(45)
        elif is_bottom and is_left:
            return math.radians(45)
        elif is_top and is_left:
            return math.radians(-45)
        elif is_bottom and is_right:
            return math.radians(-45)
        
        # Side checks (90 degrees rotation to avoid side collisions)
        elif is_left or is_right:
            return math.radians(90)
        
        # Center, top, or bottom (0 degrees - default angle)
        else:
            return 0.0

    # experimental fix daviations
    def _move_piece_advanced(self, type=None, start_pos=None, end_pos=None, speed=None, acceleration=None, move_to_start=True):
            """
            Private method for moving a piece, using the hardware class
            """
            robot = self.robot_hardware
            
            if speed is None:
                speed = robot.speed  
            if acceleration is None:
                acceleration = robot.acceleration
    
            # --- APPLY HEIGHT SAFTEY ---
            if robot.pose[Z] < robot.safe_height:
                robot.move_to(z=robot.safe_height)
    
            # get chess board deviations 
            dx, dy = self.board_mapper.get_piece_grasping_data(square_name=start_pos)
    
            # --- GET PHYSICAL POSITIONS ---
            start_pos = robot.normalize_pos(start_pos)
            end_pos = robot.normalize_pos(end_pos)
    
            #if rz_rotation_start is None:
            rz = self._get_dynamic_yaw(dx, dy)
            if rz != 0:
                start_pos[3:6] = robot.get_rotated_tcp_orientation(start_pos,Rz=rz)
            #if rz_rotation_end is not None:
            #    end_pos[3:6] = robot.get_rotated_tcp_orientation(end_pos,Rz=rz_rotation_end)

            # --- OPEN THE GRIPPER ---
            if type is not PieceType.KNIGHT and rz != 0:
                robot.set_gripper(grip_size[type] - GRIP_RELEASE_OFFSET,wait=False) 
            elif math.isclose(abs(rz), math.radians(45)):
                robot.set_gripper(HALF_OPENED, wait=False) # TODO (elad) test smaller sizes
            else: # 90 degrees knight
                robot.set_gripper(HALF_OPENED, wait=False)
                end_pos[3:6] = robot.get_rotated_tcp_orientation(end_pos,Rz=rz) # put it back straight
            
            # --- PICKUP FROM BOARD ---
            bias = 0.7
            start_pos = robot.move_on_chessboard(start_pos, right = bias * dx, up = bias * dy) # update deviation
            robot.move_to(start_pos, z=robot.safe_height, speed=speed, acceleration=acceleration) 
            robot.move_to(z=robot.grip_height[type])
            robot.set_gripper(CLOSED) # grip the piece
            robot.move_to(z=robot.safe_height)
    
            # --- PLACE ON BOARD ---
            robot.move_to(end_pos, z=robot.safe_height, speed=speed, acceleration=acceleration)
            robot.move_to(z=robot.grip_height[type] + GRIP_RELEASE_HEIGHT)
            robot.set_gripper(robot.get_gripper() - GRIP_RELEASE_OFFSET) # release the piece
            robot.move_to(z=robot.safe_height)
    
            if move_to_start:
                robot.move_to(robot.start_position, z=robot.sky_height, speed=speed, acceleration=acceleration)

    
    def is_path_clear(self, start_pos_name, end_pos_name, piece_type):
        """
        Checks if the trajectory between start and end squares is completely empty.
        Returns True if clear (can hover low), False if blocked (must fly high).
        """
        # 1. Knights always fly high to avoid knocking pieces during their jump
        if piece_type == PieceType.KNIGHT:
            return False
            
        board = PerceptionState.get_latest_board()
        
        # 2. Convert standard names (e.g., 'e2') to 0-7 indices
        # col (file): 'a'=0, 'h'=7. row (rank): '1'=0, '8'=7
        start_col = ord(start_pos_name.lower()[0]) - ord('a')
        start_row = int(start_pos_name[1]) - 1
        
        end_col = ord(end_pos_name.lower()[0]) - ord('a')
        end_row = int(end_pos_name[1]) - 1
        
        # 3. Determine the step direction (-1, 0, or 1) for rows and columns
        step_col = 0 if end_col == start_col else (1 if end_col > start_col else -1)
        step_row = 0 if end_row == start_row else (1 if end_row > start_row else -1)
        
        # Safety check: if it's not a valid straight or diagonal line, fly high
        if step_col != 0 and step_row != 0 and abs(end_col - start_col) != abs(end_row - start_row):
            return False 
            
        # 4. Traverse the squares strictly BETWEEN start and end
        cur_col = start_col + step_col
        cur_row = start_row + step_row
        
        while (cur_col, cur_row) != (end_col, end_row):
            # Convert (row, col) back to python-chess square index (0 to 63)
            # In python-chess, A1 is 0, B1 is 1, A2 is 8, etc.
            sq_index = cur_row * 8 + cur_col
            
            # If any square in between has a piece, the path is blocked
            if board.piece_at(sq_index) is not None:
                return False 
                
            cur_col += step_col
            cur_row += step_row
            
        # If the loop finishes without hitting a piece, the path is completely clear
        return True

    # experimental - shorten the time to travel
    def _move_piece_advanced2(self, type=None, start_pos=None, end_pos=None, speed=None, acceleration=None, rz_rotation_start=None, rz_rotation_end=None, move_to_start=True):
            """
            Private method for moving a piece, using the hardware class
            """
            robot = self.robot_hardware
            
            if speed is None:
                speed = robot.speed
            if acceleration is None:
                acceleration = robot.acceleration
    
            # --- APPLY HEIGHT SAFTEY ---
            if robot.pose[Z] < robot.safe_height:
                robot.move_to(z=robot.safe_height)
    
            # get chess board deviations 
            dx, dy = self.board_mapper.get_piece_grasping_data(square_name=start_pos)

            path_is_clear = self.is_path_clear(start_pos, end_pos, type)
            

            # --- GET PHYSICAL POSITIONS ---
            start_pos = robot.normalize_pos(start_pos)
            end_pos = robot.normalize_pos(end_pos)
    
            if rz_rotation_start is not None:
                start_pos[3:6] = robot.get_rotated_tcp_orientation(start_pos,Rz=rz_rotation_start)
            if rz_rotation_end is not None:
                end_pos[3:6] = robot.get_rotated_tcp_orientation(end_pos,Rz=rz_rotation_end)
    
            robot.set_gripper(grip_size[type] - GRIP_RELEASE_OFFSET,wait=False) #  open the gripper
    
            # --- PICKUP FROM BOARD ---
            bias = 0.7
            start_pos = robot.move_on_chessboard(start_pos, right = bias * dx, up = bias * dy) # update deviation
            robot.move_to(start_pos, z=robot.safe_height, speed=speed, acceleration=acceleration) 
            robot.move_to(z=robot.grip_height[type])
            robot.set_gripper(CLOSED) # grip the piece
            if path_is_clear:
                robot.move_to(dz=0.02)
            else:
                robot.move_to(z=robot.safe_height)

            # --- PLACE ON BOARD ---
            if path_is_clear:
                robot.move_to(end_pos, dz=0.02, speed=speed, acceleration=acceleration)
            else:
                robot.move_to(end_pos, z=robot.safe_height, speed=speed, acceleration=acceleration)
            robot.move_to(z=robot.grip_height[type] + GRIP_RELEASE_HEIGHT)
            robot.set_gripper(robot.get_gripper() - GRIP_RELEASE_OFFSET) # release the piece
            robot.move_to(z=robot.safe_height)
    
            if move_to_start:
                robot.move_to(robot.start_position, z=robot.sky_height, speed=speed, acceleration=acceleration)

    def _remove_piece(self, type: PieceType, start_pos, end_pos = None, rz_start = None, speed=None, move_to_start=True):
        """
        Private method for remove a piece, using the hardware class
        """
        robot = self.robot_hardwar

        if speed is None:
            speed = robot.speed

        # --- GET PHYSICAL POSITIONS ---
        start_pos = robot.normalize_pos(start_pos)
        end_pos = robot.normalize_pos(end_pos)

        if rz_start is not None:
            end_pos[3:6] = robot.get_rotated_tcp_orientation(end_pos, Rz=rz_start)

        # --- APPLY HEIGHT SAFTEY ---
        if robot.pose[Z] < robot.safe_height:
            robot.move_to(z=robot.safe_height)

        robot.set_gripper(grip_size[type] - GRIP_RELEASE_OFFSET,wait=False) #  open the gripper

        # --- PICKUP FROM BOARD ---
        robot.move_to(start_pos, z=robot.safe_height, speed=speed)
        robot.move_to(z=robot.grip_height[type])
        robot.set_gripper(CLOSED)
        robot.move_to(z=robot.safe_height)

        # --- PLACE IN STORAGE ---
        robot.move_to(end_pos, z=robot.safe_height, speed=speed)
        robot.move_to(z=robot.grip_height[type] + OFFSET_TO_TABLE_HEIGHT)
        robot.set_gripper(open_by=GRIP_RELEASE_OFFSET)
        robot.move_to(z=robot.safe_height)

        if move_to_start:
            robot.move_to(robot.start_position, z=robot.sky_height, speed=speed)

    def _bring_on_board(self, type: PieceType, end_pos, start_pos=None, rz_end=None, speed=None, move_to_start=True):
        """
        Private method for bringing a piece onto the board from off-board storage/graveyard
        (e.g., for pawn promotions).
        """
        robot = self.robot_hardware

        if speed is None:
            speed = robot.speed

        # --- GET PHYSICAL POSITIONS ---
        start_pos = robot.normalize_pos(start_pos)
        end_pos = robot.normalize_pos(end_pos)

        if rz_end is not None:
            end_pos[3:6] = robot.get_rotated_tcp_orientation(end_pos, Rz=rz_end)

        # --- APPLY HEIGHT SAFTEY ---
        if robot.pose[Z] < robot.safe_height:
            robot.move_to(z=robot.safe_height)

        robot.set_gripper(grip_size[type] - GRIP_RELEASE_OFFSET, wait=False)  #  open the gripper

        # --- PICKUP FROM STORAGE ---
        robot.move_to(start_pos, z=robot.safe_height, speed=speed)
        robot.move_to(z=robot.grip_height[type] + OFFSET_TO_TABLE_HEIGHT)
        robot.set_gripper(CLOSED)
        robot.move_to(z=robot.safe_height)

        # --- PLACE ON BOARD ---
        robot.move_to(end_pos, z=robot.safe_height, speed=speed)
        robot.move_to(z=robot.grip_height[type] + GRIP_RELEASE_HEIGHT)
        robot.set_gripper(open_by=GRIP_RELEASE_OFFSET)
        robot.move_to(z=robot.safe_height)

        # --- RETURN TO SAFE POSITION ---
        if move_to_start:
            robot.move_to(robot.start_position, z=robot.sky_height, speed=speed)


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

        if start_on_board and end_on_board:                                              # from square -> square
            self._move_piece(piece, start_pos, end_pos, speed=0.5 ,move_to_start=move_to_start)
        elif start_on_board and not end_on_board:                                        # from square -> storage
            self._remove_piece(piece, start_pos, end_pos, speed=0.5, move_to_start=move_to_start)
        elif not start_on_board and end_on_board:                                        # from storage -> square
            self._bring_on_board(piece, end_pos, start_pos, speed=0.5, move_to_start=move_to_start)
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
            storage_pos = self.storage.get_slot_for_robot_capture(captured_piece, self.human_color)
            self._execute_movement(captured_piece, remove_square, storage_pos, move_to_start=False) # remove
            self._execute_movement(moving_piece, from_square, to_square)                            # move
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
                storage_pos = self.storage.get_slot_for_robot_capture(captured_piece, self.human_color)
                self._execute_movement(captured_piece, to_square, storage_pos, move_to_start=False)   # remove
            storage_pos = self.storage.get_slot_for_robot_capture(PieceType.PAWN, self.robot_color)
            self._execute_movement(PieceType.PAWN, from_square, storage_pos, move_to_start=False)     # remove
            storage_pos = self.storage.get_slot_for_robot_promotion(promoted_piece, self.robot_color)
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