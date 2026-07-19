import pyzed.sl as sl
import cv2
import os
from datetime import datetime

# Folder where images will be saved (inside project)
SAVE_DIR = "zed_board_images_2"

# Create folder if it doesn't exist
os.makedirs(SAVE_DIR, exist_ok=True)

# Create ZED camera
zed = sl.Camera()

# Camera parameters
init_params = sl.InitParameters()
init_params.camera_resolution = sl.RESOLUTION.HD2K
init_params.camera_fps = 15

# Open camera
status = zed.open(init_params)
if status != sl.ERROR_CODE.SUCCESS:
    print(f"Failed to open camera: {status}")
    exit(1)

# Let auto exposure stabilize
for _ in range(30):
    zed.grab()

image = sl.Mat()

print("Press ENTER to save an image.")
print("Press 'q' to quit.")

while True:
    if zed.grab() != sl.ERROR_CODE.SUCCESS:
        continue

    zed.retrieve_image(image, sl.VIEW.LEFT)

    # Convert BGRA -> BGR (fix color issue)
    frame = image.get_data()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    cv2.imshow("ZED Camera", frame)

    key = cv2.waitKey(1) & 0xFF

    # ENTER saves image
    if key == 13:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = os.path.join(SAVE_DIR, f"zed_{timestamp}.png")
        cv2.imwrite(filename, frame)
        print(f"Saved {filename}")

    # q quits
    elif key == ord('q'):
        break

cv2.destroyAllWindows()
zed.close()