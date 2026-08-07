from abc import ABC, abstractmethod
from .reactions import ReactionWaiter, ConsoleEnterReaction
from yolo.human_interpreter import HumanMoveInterpreter
from .actions import ChessAction
from .action_interpreter import ActionFactory
from arm.playing_robot import PlayingRobot 
from common.exceptions import RobotFailedException
from ChessLogic.engine import ChessEngine
from collections import Counter
from common.utils import convert_fen_char_to_type_and_color

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
    def __init__(self, name: str = "Human", reaction_waiter: ReactionWaiter = None, interpreter: HumanMoveInterpreter = None):
        super().__init__(name)
        # Default to pressing Enter if no reaction waiter is specified
        self.reaction_waiter : ReactionWaiter = reaction_waiter or ConsoleEnterReaction()
        self.interpreter: HumanMoveInterpreter = interpreter

    def prepare_move(self, fen: str):
        self.reaction_waiter.wait() #waits for human reaction

    def execute_move(self, fen: str) -> str:
        new_fen = self.interpreter.update_fen(fen)
        print(f"[HumanPlayer] Move executed. New FEN: {new_fen}")
        return new_fen
  
        



class RobotPlayer(Player):
    def __init__(self, name: str = "Robot", engine: ChessEngine=None, robot: PlayingRobot=None):
        super().__init__(name)
        self.engine = engine
        self.robot = robot
        self.cur_move = None
        self.action_factory = ActionFactory()
        self.last_seen_fen = None
    
    def prepare_move(self, fen: str):
        self._sync_storage_from_human_move(fen)
        self.cur_move = self.engine.choose_move(fen)
        print(f"[RobotPlayer] Move prepared: {self.cur_move}")

    def execute_move(self, fen: str) -> str:
        action: ChessAction = self.action_factory.interpret_action(self.cur_move, fen)
        if not action.execute_on_robot(self.robot): # TODO: should be future
            raise RobotFailedException("Robot failed while prforming a playing move")
        new_fen = action.update_fen(fen)
        self.last_seen_fen = new_fen
        return new_fen

    def _sync_storage_from_human_move(self, current_fen: str):
        if not self.last_seen_fen:
            return

        old_board = self.last_seen_fen.split()[0]
        new_board = current_fen.split()[0]

        old_counts = Counter(c for c in old_board if c.isalpha())
        new_counts = Counter(c for c in new_board if c.isalpha())

        # בדיקה 1: כלים שנעלמו מהלוח (נאכלו על ידי האדם -> הולכים לאחסון)
        for char, old_count in old_counts.items():
            new_count = new_counts.get(char, 0)
            if old_count > new_count:
                missing_qty = old_count - new_count
                piece_type, color = convert_fen_char_to_type_and_color(char)
                for _ in range(missing_qty):
                    self.robot.put_in_storage_pos(piece_type, color)
                    print(f"[Robot Memory] Human captured {color} {piece_type.name}. Storage updated.")

        # בדיקה 2: כלים שהופיעו בלוח (האדם הכתיר רגלי למלכה -> יוצאים מהאחסון)
        for char, new_count in new_counts.items():
            old_count = old_counts.get(char, 0)
            if new_count > old_count:
                added_qty = new_count - old_count
                piece_type, color = convert_fen_char_to_type_and_color(char)
                for _ in range(added_qty):
                    self.robot.remove_from_storage_pos(piece_type, color)
                    print(f"[Robot Memory] Human promoted to {color} {piece_type.name}. Storage updated.")