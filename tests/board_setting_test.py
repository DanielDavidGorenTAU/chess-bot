from sys import stdout
from common.utils import PieceType
from arm.mock_robot_hardware import MockRobotHardware
from arm.board_setting_robot import BoardSettingArm


if __name__ == "__main__":
    with MockRobotHardware(log=stdout) as hw:
        robot = BoardSettingArm(hw)
        base = hw.positions["a5"]
        head = base.copy()
        head[2] += 0.1
        robot.move_piece_to_platform(head, base)
        robot.move_from_platform_to_target("a6", PieceType.QUEEN)
