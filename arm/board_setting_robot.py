from abc import ABC, abstractmethod
from typing import Optional
from common.enums_and_dicts import PieceType
from chessbot import *

class BoardSettingRobot(ABC):

    """
    Interface to handle movement of pieces during setting board
    Each move method returns the True if successfull, otherwise False
    """

    @abstractmethod
    def move_piece_to_platform(self, middle, orientation, state, head_pos, base_pos) -> bool:
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

    def move_piece_to_platform(self, middle, orientation, state, head_pos, base_pos) -> bool:
        type = PieceType.QUEEN

        # calculate middle position
        dx = head_pos[0] - base_pos[0]
        dy = head_pos[1] - base_pos[1]
        dz = head_pos[2] - base_pos[2]
        orientation = math.degrees(math.atan2(dx, dy))

        # check if standing or lying
        if state == None:
            if np.abs(head_pos[Z] - base_pos[Z]) > np.sqrt(np.abs(dx)**2 + np.abs(dy)**2):
                state = 'standing'
            else:
                state = 'lying'

        if state == 'standing':
            bias = 0.5
        elif type == PieceType.BISHOP:
            bias = 0.5
        elif type == PieceType.KNIGHT:
            bias = 0.7
        else:
            bias = 0.6

        # add middle pos and height 
        middle = [
            *RobotHardware.weighted_avg(head_pos[:2], base_pos[:2], bias),
            0,
            *self.get_rotated_tcp_orientation(Rz=orientation+180)
        ]
        if middle[Z] < self.safe_height: # fix height
            self.move_to(z=self.safe_height)

        self.set_gripper(HALF_OPENED,wait=False)

        
        if state == 'lying':
            self.move_to(middle, z=self.safe_height)

            # grip the piece
            self.move_to(z=self.table_height+0.0015)
            self.set_gripper(CLOSED) 
            self.move_to(z=self.safe_height)

            self.move_to(cube_pose, z=self.safe_height) # go to cube
            self.move_to(orientation = self.get_rotated_tcp_orientation(Rx=85)) # rotate
            #self.move_to(z=cube_pose[Z] - self.floor_height + self.grip_height[type] + 0.01) # lower height
            self.move_to(z=cube_pose[Z] + dz/2 + 0.01) # lower height ?????
            
            # release standing piece
            self.set_gripper(open_by=GRIP_RELEASE_OFFSET)

            # straighten the arm back   
            #self.move_to(cube_pose,dx=-0.01, z=cube_pose[Z] - self.floor_height + self.grip_height[type]- 0.01) 
            self.move_to(cube_pose,dx=-0.01, z=cube_pose[Z] +0.05) 

            self.move_to(dz=0.05) # raise the arm

        elif state == 'standing':
            ##################################################### add knight support
            # move to pick up piece
            self.move_to([*middle[:3] , *self.down_orientation], z=self.safe_height)

            # grip the piece
            #self.move_to([middle[X], middle[Y], self.grip_height[type]+OFFSET_TO_TABLE_HEIGHT] + self.down_orientation)
            self.move_to(z=self.table_height + dz-0.01) # height ?????
            self.set_gripper(CLOSED)
            self.move_to(z=self.safe_height)

            self.move_to(cube_pose, z=self.safe_height) # go to cube

            # release for inspection
            #self.move_to(z=cube_pose[Z] - self.floor_height + self.grip_height[type] + 0.01) # lower height
            self.move_to(z=cube_pose[Z] + dz + 0.01) # lower height
            self.set_gripper(open_by=GRIP_RELEASE_OFFSET)

            self.move_to(z=cube_pose[Z] +0.1) # raise the arm
            
        else:
            raise ValueError("Invalid standing/lying state provided")
            
    def move_from_platform_to_target(self, target: str, type: str) -> bool:
        # grip from the cube
        self.move_to(cube_pose,dx=-0.01, z=cube_pose[Z] - self.floor_height + self.grip_height[type]- 0.01)     
        self.set_gripper(CLOSED) # grip the piece
        self.move_to(dz=0.05) # raise the arm

        # put back on the chess board
        self.move_to(
            self.positions[target],
            z=self.safe_height,
            orientation =
                self.get_rotated_tcp_orientation(Rz=90)
                if type == PieceType.KNIGHT and self.get_gripper() < grip_size[PieceType.KNIGHT]-7
                else None
        )
        self.move_to(z=self.grip_height[type] + GRIP_RELEASE_HEIGHT)
        
        self.set_gripper(open_by=GRIP_RELEASE_OFFSET)
        self.move_to(z=self.safe_height)
        #self.rtde_c.moveJ(BASE_EYAL, 1, 0.5)
        self.move_to(self.start_position, z=self.safe_height)


    
        
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
    
    def move_piece_to_platform(self, middle, orientation, state, head_pos, base_pos) -> bool:
        return self.res

    def move_from_platform_to_target(self, target: str, type: str) -> bool:
        return self.res
