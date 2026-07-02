import pyzed.sl as sl
import cv2
import numpy as np

# Global variables
clicked_point = None
point_cloud = sl.Mat()

def mouse_callback(event, x, y, flags, param):
    global clicked_point

    if event == cv2.EVENT_LBUTTONDOWN:
            clicked_point = (x, y)



def get_base_and_head_camera_points():

    global clicked_point, point_cloud
    base_point = None
    head_point = None

    # Create camera
    zed = sl.Camera()

    init_params = sl.InitParameters()
    init_params.depth_mode = sl.DEPTH_MODE.ULTRA
    init_params.coordinate_units = sl.UNIT.METER

    if zed.open(init_params) != sl.ERROR_CODE.SUCCESS:
        print("Failed to open ZED")
        return

    image = sl.Mat()

    runtime_params = sl.RuntimeParameters()

    cv2.namedWindow("ZED")
    cv2.setMouseCallback("ZED", mouse_callback)

    while head_point==None:

        if zed.grab(runtime_params) == sl.ERROR_CODE.SUCCESS:

            # Left image
            zed.retrieve_image(image, sl.VIEW.LEFT)

            # Point cloud
            zed.retrieve_measure(
                point_cloud,
                sl.MEASURE.XYZ
            )

            frame = image.get_data()

            if clicked_point is not None:

                x, y = clicked_point

                err, point3d = point_cloud.get_value(x, y)

                if err == sl.ERROR_CODE.SUCCESS:

                    X, Y, Z = point3d[:3]

                    if np.isfinite(X) and np.isfinite(Y) and np.isfinite(Z):

                        print(f"Pixel ({x}, {y})")
                        print(f"3D point: X={X:.3f}, Y={Y:.3f}, Z={Z:.3f} meters")
                        if(base_point is None):
                            base_point = [X, Y, Z]
                            print(f"base_point is set")
                        else:
                            head_point = [X, Y, Z]
                            print(f"head_point is set")
                    else:
                        print("Invalid depth at this pixel")
                clicked_point = None


            cv2.imshow("ZED", frame)

        key = cv2.waitKey(1)

        if key == 27:  # ESC
            break
    

    zed.close()
    cv2.destroyAllWindows()
    return base_point, head_point

