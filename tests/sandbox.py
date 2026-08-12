from sys import stdout
from common.enums_and_dicts import PieceType
from arm.abstract_robot_hardware import AbstractRobotHardware
from arm.mock_robot_hardware import MockRobotHardware
from arm.chessbot import RobotHardware

if __name__ == "__main__":
    with RobotHardware() as hw:
        hw.mov_chess_piece(PieceType.PAWN, "a1", "a3")
