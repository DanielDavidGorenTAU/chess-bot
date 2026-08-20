from main.config import AppConfig
from ZED.cameralib import Camera
from yolo.vision_inference.orientation_detector import *
from yolo.vision_inference.platform_piece_classifier import *
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
            return CNNPieceClassifier(camera=self.camera)

    def _create_placement_planner(self) -> PlacementPlanner:
        return PlacementPlanner(self.config.game.initial_fen)

    def _create_pipline(self) -> PieceIngestionPipeline:
        robot: BoardSettingRobot = self._create_setting_robot()
        orientation_detector: OrientationDetector = self._create_oreintation_detector()
        platform_classifier: PlatformPieceClassifier = self._create_platform_classifire()
        placement_planner: PlacementPlanner = self._create_placement_planner()
        return PieceIngestionPipeline(
            robot=robot,
            orientation_detector=orientation_detector,
            platform_classifier=platform_classifier,
            placement_planner=placement_planner
        )

    def create_setup_service(self) -> BoardSetupService:
        print("[Factory] Assembling BoardSetupService...")
        pipeline: PieceIngestionPipeline = self._create_pipline()
        return BoardSetupService(
            pipeline=pipeline
        )

    