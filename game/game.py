from player import Player

DEFAULT_STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

class Game:
    def __init__(self, white_player: Player, black_player: Player, fen: str = DEFAULT_STARTING_FEN):
        self.players = [black_player, white_player]
        self.fen: str = fen
        self.turn: int = self._extract_turn_from_fen(fen) # 1 for white, 0 for black
        self.is_running: bool = False

    def _extract_turn_from_fen(self, fen_string: str) -> int:
        """
        Extracts active turn from FEN string:
        Returns 1 for White ('w'), 0 for Black ('b').
        """
        parts = fen_string.split()
        if len(parts) > 1 and parts[1].lower() == 'w':
            return 1
        return 0

    def start_game(self):
        """Starts the game loop or marks the game as active."""
        self.is_running = True
        current_turn_name = "White" if self.turn == 1 else "Black"
        print(f"Game started! Initial FEN: {self.fen}")
        print(f"Active turn: {current_turn_name} ({self.turn})")
        while self.is_running:
            cur_player = self.players[self.turn]
            self.fen = cur_player.execute_move(self.fen)
            self.turn = 1 - self.turn


    def stop_game(self):
        """Stops the game loop or marks the game as inactive."""
        self.is_running = False
        print("Game stopped.")