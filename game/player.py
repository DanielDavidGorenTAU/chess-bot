from abc import ABC, abstractmethod
from reactions import ReactionWaiter, ConsoleEnterReaction

class Player(ABC):
    def __init__(self, name: str = "Player"):
        self.name = name

    @abstractmethod
    def make_move(self, fen: str) -> str:
        """
        Calculates or prompts for a move given the current board FEN.
        Can be left as pass for now.
        Returns the new FEN after the move.
        """
        pass



class HumanPlayer(Player):
    def __init__(self, name: str = "Human"):
        super().__init__(name)
        # Default to pressing Enter if no reaction waiter is specified
        self.reaction_waiter = reaction_waiter or ConsoleEnterReaction()

    def make_move(self, fen: str) -> str:
        # Stub for human move (e.g. CLI input or UI interaction)
        pass


class RobotPlayer(Player):
    def __init__(self, name: str = "Robot"):
        super().__init__(name)

    def make_move(self, fen: str) -> str:
        # Stub for robot move (e.g. engine computation or robotic arm action)
        pass