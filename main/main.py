from .config import AppConfig
from factories.hardware_factory import HardwareFactory
from factories.board_setup_factory import BoardSetupFactory
from factories.game_factory import GameFactory
from .session import ChessSession


if __name__ == "__main__":
    # 1. Load system settings
    config = AppConfig.load("/home/checkmate/Documents/chess-bot/main/config.yaml")

    # 2. Instantiate hardware factory (creates shared camera/robot references)
    hw_factory = HardwareFactory(config)
    camera = hw_factory.get_camera()
    robot_hw = hw_factory.get_robot_hardware()
    ## Base case: the robot is white so no need to flip, otherwise we need to flip the FEN structure is constant.
    if config.game.white_player == "human":
        robot_hw.flip_board_robot_view()

    # 3. Create domain-specific setup service (if configured)
    board_setup_service = None
    if config.game.run_board_setup:
        setup_factory = BoardSetupFactory(config, camera=camera, robot=robot_hw)
        board_setup_service = setup_factory.create_setup_service()

    # 4. Create gameplay domain
    game_factory = GameFactory(config, camera=camera, robot=robot_hw)
    chess_game = game_factory.create_game()

    # 5. Assemble session and run execution pipeline
    session = ChessSession(
        config=config,
        hardware_resources=hw_factory.get_active_resources(),
        game=chess_game,
        board_setup_service=board_setup_service
    )

    session.run()