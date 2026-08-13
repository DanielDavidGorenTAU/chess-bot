from sys import stdout
import numpy as np
from common.enums_and_dicts import PieceType
from arm.abstract_robot_hardware import AbstractRobotHardware
from arm.mock_robot_hardware import MockRobotHardware
from arm.chessbot import RobotHardware

if __name__ == "__main__":
    with RobotHardware(log=stdout) as hw:
        print(hw.pose)
        print(hw.down_orientation)
        hw.move_to([-0.5121424624250651, 0.15612844851862082, -0.05219023284215582, -2.271505404516426, -0.9074891712366964, -0.027134494204603277])
