import pyzed.sl as sl
import cv2
import os
from datetime import datetime

# Folder where images will be saved (inside project)
SAVE_DIR = "zed_setting_images_2"


class Camera:
    def __init__(self, brightness: int = None):
        self.zed = sl.Camera()
        self.init_params = sl.InitParameters()
        self.init_params.camera_resolution = sl.RESOLUTION.HD2K
        self.init_params.depth_mode = sl.DEPTH_MODE.ULTRA
        self.init_params.coordinate_units = sl.UNIT.METER
        self.init_params.camera_fps = 15
        self.brightness = brightness #0-8

    def _take_photo(self, image_mat):
        """
        Private method, ZED takes the actual photo
        """
        if self.zed.grab() != sl.ERROR_CODE.SUCCESS:
            raise RuntimeError("Failed to grab image from ZED camera.")

        self.zed.retrieve_image(image_mat, sl.VIEW.LEFT)

        # Convert BGRA -> BGR
        frame = image_mat.get_data()    
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        return frame

    def _save_photo(self, output_dir:str, frame) -> str:
        """
        Private method, Saves photo at the specified dir
        """
        piece_type = "00"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        image_path = os.path.join(output_dir, f"{piece_type}_{timestamp}.png")

        if not cv2.imwrite(image_path, frame):
            raise RuntimeError(f"Failed to save image to {image_path}")
        print(f"Saved {image_path}")

        return os.path.abspath(image_path)

    def _crop_frame(
    self,
    frame,
    x: int,
    y: int,
    width: int,
    height: int,
    ):
        """
        Private method. Returns a cropped copy of the frame.
        """

        img_h, img_w = frame.shape[:2]

        x = max(0, min(x, img_w - 1))
        y = max(0, min(y, img_h - 1))
        width = min(width, img_w - x)
        height = min(height, img_h - y)

        return frame[y:y + height, x:x + width].copy()

    def take_photo(self, output_dir: str) -> str:
        """
        Takes a single photo with the ZED camera, saves it in output_dir,
        and returns the full path to the saved image.
        """
        os.makedirs(output_dir, exist_ok=True)

        image_mat = sl.Mat()

        frame = self._take_photo(image_mat)
        file_path = self._save_photo(output_dir, frame)
        return file_path



    
    def shoot_many(self, output_dir):
        os.makedirs(output_dir, exist_ok=True)

        image_mat = sl.Mat()

        print("Press ENTER to save an image.")
        print("Press 'q' to quit.")


        while True:
            frame = self._take_photo(image_mat)

            cv2.imshow("ZED Camera", frame)

            key = cv2.waitKey(1) & 0xFF

            # ENTER saves image
            if key == 13:
                self._save_photo(output_dir, frame)

            # q quits
            elif key == ord('q'):
                break

    def capture_and_crop(
        self,
        output_path: str,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> bool:
        """
        Shows a live preview.
        Press ENTER to save the cropped image.
        Press q to quit without saving.
        """
        cropped_path = output_path + "_cropped"
        os.makedirs(output_path, exist_ok=True)
        os.makedirs(cropped_path, exist_ok=True)

        image_mat = sl.Mat()

        print("Press ENTER to save the cropped image.")
        print("Press 'q' to quit.")

        while True:
            frame = self._take_photo(image_mat)

            cv2.imshow("ZED Camera", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == 13:
                img_h, img_w = frame.shape[:2]

                x0 = max(0, min(x, img_w - 1))
                y0 = max(0, min(y, img_h - 1))
                w = min(width, img_w - x0)
                h = min(height, img_h - y0)

                cropped = frame[y0:y0 + h, x0:x0 + w]

                #self._save_photo(output_path, frame)
                self._save_photo(cropped_path, cropped)

            elif key == ord("q"):
                return False
    
    def __enter__(self):
        status = self.zed.open(self.init_params)
        if status != sl.ERROR_CODE.SUCCESS:
            raise Exception(f"Failed to open camera: {status}")
        
        if self.brightness is not None:
            self.zed.set_camera_settings(sl.VIDEO_SETTINGS.BRIGHTNESS, self.brightness)

        # Let auto exposure stabilize
        for _ in range(30):
            self.zed.grab()

        return self
    
    def __exit__(self, *_):
        cv2.destroyAllWindows()
        self.zed.close()
