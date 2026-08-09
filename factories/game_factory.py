from main.config import AppConfig
from game.game import Game
from game.player import Player, HumanPlayer, RobotPlayer
from yolo.human_interpreter import HumanMoveInterpreter
from yolo.board_pieces_detector import BoardPiecesDetector
from yolo.fen_translator import BinaryToFenTranslator  # or factory for translators
from arm.playing_robot import *
from ZED.cameralib import Camera
from arm.chessbot import RobotHardware
from ChessLogic.engine import ChessEngine


class GameFactory:
    """Dependency Injector responsible for constructing all sub-systems."""

    def __init__(self, config: AppConfig, camera: Camera, robot: RobotHardware):
        self.config = config
        self.camera = camera  
        self.robot = robot 

    def create_robot_hardware(self) -> PlayingRobot:
        """Builds real or mock robot hardware driver."""
        if self.config.robot.is_mock:
            print("[Factory] Injecting MockPlayingRobot")
            return PlayingMock()
        else:
            print(f"[Factory] Injecting Real PlayingRobot")
            return PlayingArm(self.robot)

    def create_engine(self):
        return ChessEngine()

    def _build_human_interpreter(self) -> HumanMoveInterpreter:
        """Assembles Vision + Translator pipeline."""
        print(f"[Factory] Assembling Vision Pipeline with model '{self.config.vision.model_name}'")
        
        yolo_model = BoardPiecesDetector(model_name=self.config.vision.model_name, camera=self.camera)
        translator = BinaryToFenTranslator()
        
        return HumanMoveInterpreter(yolo_model=yolo_model, translator=translator)

    def _build_player(self, player_type: str, name: str) -> Player:
        """Constructs a Human or Robot player based on config type."""
        if player_type.lower() == "human":
            interpreter = self._build_human_interpreter()
            return HumanPlayer(name=name, interpreter=interpreter)
            
        elif player_type.lower() in ("robot", "ai"):
            playing_robot = self.create_robot_hardware()
            engine = self.create_engine()
            return RobotPlayer(name=name, engine=engine, robot=playing_robot)
            
        else:
            raise ValueError(f"Unknown player type: '{player_type}' in configuration.")

    def create_game(self) -> Game:
        """Factory entrypoint to build the full Game orchestrator."""
        white_player = self._build_player(
            player_type=self.config.game.white_player, 
            name=self.config.game.white_name
        )
        black_player = self._build_player(
            player_type=self.config.game.black_player, 
            name=self.config.game.black_name
        )
        storage = StorageManager()
        print(self.config.game.initial_fen)
        return Game(
            white_player=white_player,
            black_player=black_player,
            fen=self.config.game.initial_fen
        )