
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


from arm.playing_robot import PlayingArm
from arm.chessbot import RobotHardware
from game.actions import ChessAction
from game.action_interpreter import ActionFactory


if __name__ == "__main__":
    
    test = "upgrade"


    if test == "castle":
        # test castling move execution on robot
        with RobotHardware() as robot:
            fen = "8/8/8/8/8/8/8/4K2R w - - 0 1"
            cur_move = "e1g1" #castle
            action_factory = ActionFactory()
            playing_arm = PlayingArm(robot)
            action: ChessAction = action_factory.interpret_action(cur_move, fen)
            if not action.execute_on_robot(playing_arm): 
                print("failed to execute action on robot")
            print(action.update_fen(fen))

    if test == "upgrade":
        # test pawn promotion move execution on robot
        with RobotHardware() as robot:
            fen = "2B5/3p4/8/8/8/8/8/8 b - - 0 1"
            cur_move = "d7c8q" #upgrade
            action_factory = ActionFactory()
            playing_arm = PlayingArm(robot)
            action: ChessAction = action_factory.interpret_action(cur_move, fen)
            if not action.execute_on_robot(playing_arm): 
                print("failed to execute action on robot")
            print(action.update_fen(fen))


    
    