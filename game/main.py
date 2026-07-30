from player import HumanPlayer, RobotPlayer
from game import Game

if __name__ == "__main__":
    # Create player instances
    white_p = HumanPlayer(name="Alice")
    black_p = RobotPlayer(name="Stockfish Bot")

    # Initialize game with players and optional initial FEN
    chess_game = Game(
        white_player=white_p, 
        black_player=black_p
    )

    # Lifecycle calls
    chess_game.start_game()
    
    # Example state check
    print(f"White Player: {chess_game.white_player.name}")
    print(f"Black Player: {chess_game.black_player.name}")
    print(f"Turn: {chess_game.turn}") # Outputs 1 for White

    chess_game.stop_game()