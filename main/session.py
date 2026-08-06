from contextlib import ExitStack
from typing import List, Any, Optional
from .config import AppConfig
from game.game import Game
from factories.board_setup_factory import BoardSetupService


class ChessSession:
    """Manages the full lifecycle from hardware context opening to teardown."""

    def __init__(
        self, 
        config: AppConfig, 
        hardware_resources: List[Any],
        game: Game,
        board_setup_service: Optional[BoardSetupService] = None
    ):
        self.config = config
        self.hardware_resources = hardware_resources
        self.game = game
        self.board_setup_service = board_setup_service
        self._exit_stack = ExitStack()

    def run(self):
        try:
            print("\n=== MOUNTING HARDWARE ===")
            # Entering the context
            for res in self.hardware_resources:
                if hasattr(res, "__enter__"):
                    self._exit_stack.enter_context(res)
            print("[Session] All hardware connected and ready.")

            # Optional Pre-game setup phase
            if self.config.game.run_board_setup and self.board_setup_service:
                print("\n=== STAGE 1: BOARD SETUP ===")
                self.board_setup_service.setup_board()

            # Gameplay phase
            print("\n=== STAGE 2: CHESS GAME ===")
            self.game.start_game()

        finally:
            print("\n=== UNMOUNTING HARDWARE ===")
            self._exit_stack.close()
            print("[Session] Hardware successfully safely unmounted.")