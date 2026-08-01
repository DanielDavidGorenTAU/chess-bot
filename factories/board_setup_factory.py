from main.config import AppConfig
from ZED.cameralib import Camera
from arm.chessbot import RobotHardware


class BoardSetupService:
    """Handles pre-game board arrangement and piece alignment."""
    def __init__(self, camera: Camera, robot: RobotHardware):
        self.camera = camera
        self.robot = robot

    def setup_board(self):
        print("[BoardSetupService] Running board setup & piece alignment...")


class BoardSetupFactory:
    """Builds BoardSetupService with its specific dependencies."""

    def __init__(self, config: AppConfig, camera: Camera, robot: RobotHardware):
        self.config = config
        self.camera = camera
        self.robot = robot

    def create_setup_service(self) -> BoardSetupService:
        print("[Factory] Assembling BoardSetupService...")
        # If set_board needs custom detectors/calibrators in the future,
        # instantiate and pass them here!
        return BoardSetupService(
            camera=self.camera,
            robot=self.robot
        )