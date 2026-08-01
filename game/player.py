from abc import ABC, abstractmethod
from reactions import ReactionWaiter, ConsoleEnterReaction
from yolo.human_interpreter import HumanMoveInterpreter
from actions import ChessAction
from action_interpreter import ActionFactory
from arm.playing_robot import PlayingRobot 
from common.exceptions import RobotFailedException
from ChessLogic.engine import ChessEngine

class Player(ABC):
    def __init__(self, name: str = "Player"):
        self.name : str = name

    def make_move(self, fen):
        """
        Calculates or waits for a move given the current board FEN.
        Returns the new FEN after the move.
        """
        self.prepare_move(fen)
        return self.execute_move(fen)

    @abstractmethod
    def prepare_move(self, fen: str):
        pass

    @abstractmethod
    def execute_move(self, fen: str) -> str:
        pass



class HumanPlayer(Player):
    def __init__(self, name: str = "Human", reaction_waiter: ReactionWaiter = None, interpeter: HumanMoveInterpreter = None):
        super().__init__(name)
        # Default to pressing Enter if no reaction waiter is specified
        self.reaction_waiter : ReactionWaiter = reaction_waiter or ConsoleEnterReaction()
        self.interpeter: HumanMoveInterpreter = interpeter

    def prepare_move(self, fen: str):
        self.reaction_waiter.wait() #waits for human reaction

    def execute_move(self, fen: str) -> str:
        return self.interpeter.update_fen(fen)
  
        



class RobotPlayer(Player):
    def __init__(self, name: str = "Robot", engine: ChessEngine=None, robot: PlayingRobot=None):
        super().__init__(name)
        self.engine = engine
        self.robot = robot
        self.cur_move = None
        self.action_factory = ActionFactory()
    
    def prepare_move(self, fen: str):
        self.cur_move = self.engine.choose_move(fen)

    def execute_move(self, fen: str) -> str:
        action: ChessAction = self.action_factory.interpret_action(self.cur_move, fen)
        if not action.execute_on_robot(self.robot): # TODO: should be future
            raise RobotFailedException("Robot failed while prforming a playing move")
        return action.update_fen(fen)
        

