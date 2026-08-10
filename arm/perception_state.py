

class PerceptionState:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PerceptionState, cls).__new__(cls)
            cls._instance.latest_detections_file = None

        return cls._instance

    def set_latest_detections(self, file_path: str):
        self.latest_detections_file = file_path

    def get_latest_detections(self) -> str:
        return self.latest_detections_file