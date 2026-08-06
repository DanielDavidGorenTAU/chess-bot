from abc import ABC, abstractmethod
from typing import Optional
from common.typing import Pos
from common.utils import weighted_avg
from .chessbot import *

class BoardSettingRobot(ABC):

    """
    Interface to handle movement of pieces during setting board
    Each move method returns the True if successfull, otherwise False
    """

    @abstractmethod
    def move_piece_to_platform(self, head_pos: Pos, base_pos: Pos) -> bool:
        pass

    @abstractmethod
    def move_from_platform_to_target(self, target: str, type: str) -> bool:
        pass




class BoardSettingArm(BoardSettingRobot):

    """
    Real UR5E arm class for setting board before game
    """

    def __init__(self, robot_hardware: RobotHardware):
        self.robot_hardware = robot_hardware

    def move_piece_to_platform(self, head_pos: Pos, base_pos: Pos) -> bool:
        head_pos = self.robot_hardware.normalize_pos(head_pos)
        base_pos = self.robot_hardware.normalize_pos(base_pos)

        dx, dy, dz = [head_pos[i] - base_pos[i] for i in range(3)]
        drz = math.degrees(math.atan2(dx, dy))
        elevation = math.degrees(math.atan2(dz, math.hypot(dx, dy)))
        is_standing = (45.0 < elevation < 135.0)
        HEAD_BIAS = 0.6
        pickup_pos = self.robot_hardware.weighted_avg(head_pos[:3], base_pos[:3], HEAD_BIAS)
        if is_standing:
            pickup_pos = [*pickup_pos, *self.robot_hardware.down_orientation]
        else:
            pickup_pos = [*pickup_pos, *self.robot_hardware.get_rotated_tcp_orientation(Rz=drz+180)]

        self.robot_hardware.move_to(z=self.robot_hardware.safe_height)
        self.robot_hardware.set_gripper(HALF_OPENED, wait=False)
        self.robot_hardware.move_to(pickup_pos, z=self.robot_hardware.safe_height)
        self.robot_hardware.move_to(pickup_pos)
        self.robot_hardware.set_gripper(CLOSED)
        self.robot_hardware.move_to(z=self.robot_hardware.safe_height)
        self.robot_hardware.move_to(cube_pose, z=self.robot_hardware.safe_height)

        if not is_standing:
            self.robot_hardware.move_to(orientation = self.get_rotated_tcp_orientation(Rx=85))

        piece_height_worst_case = dz * 1.2
        self.robot_hardware.move_to(z=cube_pose[Z], dz=piece_height_worst_case * HEAD_BIAS)
        self.robot_hardware.set_gripper(HALF_OPENED)
        self.robot_hardware.move_to(z=self.robot_hardware.safe_height)


    def move_from_platform_to_target(self, target: str, type: str) -> bool:
        # grip from the cube   
        #               -0.01                                                              -0.01                                                      
        self.robot_hardware.move_to(dx=-0.00, z=cube_pose[Z] - self.robot_hardware.floor_height + self.robot_hardware.grip_height[type]- 0.00)     
        self.robot_hardware.set_gripper(CLOSED) # grip the piece
        self.robot_hardware.move_to(dz=0.05) # raise the arm

        # put back on the chess board
        self.robot_hardware.move_to(
            self.robot_hardware.positions[target],
            z=self.robot_hardware.safe_height,
            orientation =
                self.robot_hardware.get_rotated_tcp_orientation(Rz=90)
                if type == PieceType.KNIGHT and self.robot_hardware.get_gripper() < grip_size[PieceType.KNIGHT]-7
                else None
        )
        self.robot_hardware.move_to(z=self.robot_hardware.grip_height[type] + GRIP_RELEASE_HEIGHT)
        
        self.robot_hardware.set_gripper(open_by=GRIP_RELEASE_OFFSET)
        self.robot_hardware.move_to(z=self.safe_height)
        
        self.robot_hardware.move_to(self.robot_hardware.start_position, z=self.robot_hardware.sky_height)
        self.robot_hardware.rtde_c.moveJ(BASE_EYAL, 1, 0.5) # align gripper

    
        
class BoardSettingMock(BoardSettingRobot):

    """
    Mock Class for BoardSettingRobot
    res determines if will fail or succeed
    """
    def __init__(self, res: bool = True):
        """
        res = false -> fails / true -> succeeds
        """
        self.res = res
    
    def move_piece_to_platform(self, head_pos: Pos, base_pos: Pos) -> bool:
        return self.res

    def move_from_platform_to_target(self, target: str, type: str) -> bool:
        return self.res
