import pyzed.sl as sl
import cv2
import numpy as np

def main():

    # ---------- CAMERA INIT ----------
    zed = sl.Camera()

    init_params = sl.InitParameters()
    init_params.camera_resolution = sl.RESOLUTION.HD720
    init_params.depth_mode = sl.DEPTH_MODE.ULTRA
    init_params.coordinate_units = sl.UNIT.MILLIMETER

    err = zed.open(init_params)
    if err != sl.ERROR_CODE.SUCCESS:
        print("Failed to open camera:", err)
        return

    runtime = sl.RuntimeParameters()

    image = sl.Mat()
    point_cloud = sl.Mat()

    print("Camera running. Press SPACE to capture point cloud. Press Q to quit.")

    while True:

        if zed.grab(runtime) == sl.ERROR_CODE.SUCCESS:

            # ---------- RGB IMAGE ----------
            zed.retrieve_image(image, sl.VIEW.LEFT)
            img = image.get_data()
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            cv2.imshow("ZED RGB", img)

        key = cv2.waitKey(1) & 0xFF

        # ---------- QUIT ----------
        if key == ord('q'):
            break

        # ---------- CAPTURE ----------
        if key == 32:  # SPACE

            print("Capturing point cloud...")

            zed.retrieve_measure(point_cloud, sl.MEASURE.XYZRGBA)

            # ---------- SAVE PLY ----------
            err = point_cloud.write("output_cloud.ply")

            if err == sl.ERROR_CODE.SUCCESS:
                print("Saved: output_cloud.ply")
            else:
                print("Failed to save point cloud")

            # ---------- PRINT SAMPLE POINTS ----------
            for i in range(5):
                x = 640 + i * 10
                y = 360

                err, p = point_cloud.get_value(x, y)

                if err == sl.ERROR_CODE.SUCCESS:
                    print(f"Point {i}: X={p[0]:.2f}, Y={p[1]:.2f}, Z={p[2]:.2f}")

    zed.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()