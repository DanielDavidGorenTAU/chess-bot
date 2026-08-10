from main.config import AppConfig
from ZED.cameralib import Camera
from yolo.orientation_detector import *
from yolo.platform_piece_classifier import *
from arm.chessbot import RobotHardware
from arm.board_setting_robot import BoardSettingRobot, BoardSettingArm
from board_setup.board_setup import BoardSetupService, PieceIngestionPipeline
from board_setup.placement_planner import PlacementPlanner





class BoardSetupFactory:
    """Builds BoardSetupService with its specific dependencies."""

    def __init__(self, config: AppConfig, camera: Camera, robot: RobotHardware):
        self.config = config
        self.camera = camera
        self.robot = robot

    def _create_setting_robot(self) -> BoardSettingRobot:
        return BoardSettingArm(self.robot)

    def _create_oreintation_detector(self) -> OrientationDetector:
        if self.config.vision.manual_orientation:
            return ManualOrientationDetector(self.camera)
        else:
            return YoloOrientationDetector(self.camera)

    def _create_platform_classifire(self) -> PlatformPieceClassifier:
        if self.config.vision.manual_on_platform:
            return ManualPieceClassifier(self.camera)
        else:
            return YOLOPieceClassifier(self.camera)

    def _create_placement_planner(self) -> PlacementPlanner:
        return PlacementPlanner(self.config.game.initial_fen)

    def _create_pipline(self) -> PieceIngestionPipeline:
        #, , placement_planner: PlacementPlanner
        robot: BoardSettingRobot = self._create_setting_robot()
        orientation_detector: OrientationDetector = self._create_oreintation_detector()
        platform_classifier: PlatformPieceClassifier = self._create_platform_classifire()
        placement_planner: PlacementPlanner = self._create_placement_planner()
    def create_setup_service(self) -> BoardSetupService:
        print("[Factory] Assembling BoardSetupService...")
        pipeline: PieceIngestionPipeline = self._create_pipline()
        return BoardSetupService(
            camera=self.camera,
            robot=self.robot
        )

    