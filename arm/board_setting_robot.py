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
    def move_piece_to_platform(self, middle, orientation) -> bool:
        pass

    @abstractmethod
    def move_from_platform_to_target(self, target: str) -> bool:
        pass




class BoardSettingArm(BoardSettingRobot):

    """
    Real UR5E arm class for setting board before game
    """

    def __init__(self, robot_hardware: RobotHardware):
        self.robot_hardware = robot_hardware


    
        
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
    
    def move_piece_to_platform(self, middle, orientation) -> bool:
        return self.res

    def move_from_platform_to_target(self, target: str) -> bool:
        return self.res
