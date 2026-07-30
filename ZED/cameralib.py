import pyzed.sl as sl
import cv2
import os
from datetime import datetime

# Folder where images will be saved (inside project)
SAVE_DIR = "zed_setting_images_2"

BRIGHTNESS = None  # Usually 0-8

class Camera:
    def __init__(self):
        self.zed = sl.Camera()
        self.init_params = sl.InitParameters()
        self.init_params.camera_resolution = sl.RESOLUTION.HD2K
        self.init_params.depth_mode = sl.DEPTH_MODE.ULTRA
        self.init_params.coordinate_units = sl.UNIT.METER
        self.init_params.camera_fps = 15

        status = self.zed.open(self.init_params)
        if status != sl.ERROR_CODE.SUCCESS:
            raise Exception(f"Failed to open camera: {status}")
        
        if BRIGHTNESS is not None:
            self.zed.set_camera_settings(
                sl.VIDEO_SETTINGS.BRIGHTNESS,
                BRIGHTNESS
            )

        # Let auto exposure stabilize
        for _ in range(30):
            self.zed.grab()
    
    def shoot_many(self, output_dir):
        os.makedirs(output_dir, exist_ok=True)

        image = sl.Mat()

        print("Press ENTER to save an image.")
        print("Press 'q' to quit.")


        while True:
            if self.zed.grab() != sl.ERROR_CODE.SUCCESS:
                return

            self.zed.retrieve_image(image, sl.VIEW.LEFT)

            # Convert BGRA -> BGR (fix color issue)
            frame = image.get_data()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            cv2.imshow("ZED Camera", frame)

            key = cv2.waitKey(1) & 0xFF

            # ENTER saves image
            if key == 13:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                filename = os.path.join(output_dir, f"zed_{timestamp}.png")
                cv2.imwrite(filename, frame)
                print(f"Saved {filename}")

            # q quits
            elif key == ord('q'):
                break
    
    def __enter__(self):
        return self
    
    def __exit__(self, *_):
        cv2.destroyAllWindows()
        self.zed.close()
