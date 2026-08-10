#!/usr/bin/python3

import os
import time
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from collections.abc import Sequence
from typing_extensions import override
from rtde_control import RTDEControlInterface
from rtde_receive import RTDEReceiveInterface
import numpy as np
from scipy.spatial.transform import Rotation
import cv2
import pyzed.sl as sl
import math
from common.enums_and_dicts import *
from common.utils import *
from typing import Optional
from main.config import AppConfig

from arm.robotiq_gripper import RobotiqGripper
from arm.measurements import *
from arm.abstract_robot_hardware import AbstractRobotHardware

#if __name__ == "__main__":
#    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#    if ROOT_DIR not in sys.path:
#        sys.path.insert(0, ROOT_DIR)
        
#        from robotiq_gripper import RobotiqGripper
#        from measurements import *
#        from abstract_robot_hardware import AbstractRobotHardware

#    else:  
#        from .robotiq_gripper import RobotiqGripper
#        from .measurements import *
#        from .abstract_robot_hardware import AbstractRobotHardware
        





clicked_point = None
point_cloud = sl.Mat()


def reset_gripper(robot_ip=ROBOT_IP, base_tcp_port=BASE_TCP_PORT):
    print("Reset arg detected: resetting and activating gripper...")
    g = None
    try:
        g = RobotiqGripper()
        g.connect(robot_ip, base_tcp_port)
        try:
            g._reset()
        except Exception as exc:
            print("Warning during gripper reset:", exc)
        try:
            g.activate()
        except Exception as exc:
            print("Warning during gripper activate:", exc)
        print("Gripper reset+activate completed.")
    except Exception as exc:
        print("Error communicating with gripper:", exc)
    finally:
        if g is not None:
            try:
                g.disconnect()
            except Exception:
                pass
    sys.exit(0)

def move_to_start_postion():
    with RobotHardware(robot_ip=ROBOT_IP, base_tcp_port=BASE_TCP_PORT, A1=A1_, H8=H8_) as robot:
        robot.move_to(robot.start_position, z=robot.sky_height)
    sys.exit(0)

def grip_close():
    with RobotHardware(robot_ip=ROBOT_IP, base_tcp_port=BASE_TCP_PORT, A1=A1_, H8=H8_) as robot:
        robot.set_gripper(CLOSED)
    sys.exit(0)

def grip_open():
    with RobotHardware(robot_ip=ROBOT_IP, base_tcp_port=BASE_TCP_PORT, A1=A1_, H8=H8_) as robot:
        robot.set_gripper(OPENED)
    sys.exit(0)

def print_position():
    with RobotHardware(robot_ip=ROBOT_IP, base_tcp_port=BASE_TCP_PORT, A1=A1_, H8=H8_) as robot:
        print(robot.pose[:3])
    sys.exit(0)

def align_position():
    with RobotHardware(robot_ip=ROBOT_IP, base_tcp_port=BASE_TCP_PORT, A1=A1_, H8=H8_) as robot:
        robot.move_joint(BASE_EYAL, 1, 0.5)
    sys.exit(0)

def get_grip():
    with RobotHardware(robot_ip=ROBOT_IP, base_tcp_port=BASE_TCP_PORT, A1=A1_, H8=H8_) as robot:
        print(robot.get_gripper())
    sys.exit(0)

def print_joints():
    with RobotHardware(robot_ip=ROBOT_IP, base_tcp_port=BASE_TCP_PORT, A1=A1_, H8=H8_) as robot:
        print(list(robot.rtde_r.getActualQ()))
    sys.exit(0)





class RobotHardware(AbstractRobotHardware):
    def __init__(self, robot_ip=ROBOT_IP, base_tcp_port=BASE_TCP_PORT, speed=0.5, acceleration=0.5, A1 = A1_, H8 = H8_):
        super().__init__()
        self.robot_ip = robot_ip
        self.base_tcp_port = base_tcp_port
        self.speed = speed
        self.acceleration = acceleration
        self.rtde_c = None
        self.rtde_r = None
        self.gripper = None
        self.A1 = A1
        self.H8 = H8
        self.floor_height = 0
        self.sky_height = 0
        self.safe_height = 0.15
        self.grip_height = {}
        self.table_height = 0
        self.storage_state = {}

    @override
    def __enter__(self):
        self.rtde_c = RTDEControlInterface(self.robot_ip)
        self.rtde_r = RTDEReceiveInterface(self.robot_ip)
        self.gripper = RobotiqGripper()

        self.gripper.connect(self.robot_ip, self.base_tcp_port)

        time.sleep(0.1)

        self.calibrate_board_positions(self.A1, self.H8)

        if not self.gripper.is_active():
            self.gripper.activate()
        return self

    def calibrate_board_positions(self, a1=None, h8=None):
       
        if a1 is None or h8 is None:
            raise Exception("error with a1 and h8 set values")

        dx = h8[X] - a1[X]
        dy = h8[Y] - a1[Y]
        h1 = [a1[X] + (dx + dy) / 2.0, a1[Y] + (dy - dx) / 2.0]

        self.step_right = [(h1[X] - a1[X]) / 7.0, (h1[Y] - a1[Y]) / 7.0]
        self.step_up = [-self.step_right[Y], self.step_right[X]]

        rad = math.atan2(h8[1] - a1[1], h8[0] - a1[0])
        #self.down_orientation = [0, np.pi, rad-np.pi/4] // backwards board
        self.down_orientation = [0, np.pi, rad-np.pi/4 + np.pi]
        self.floor_height = (h8[Z] + a1[Z]) / 2 + 0.0015 # offset
        self.sky_height = self.floor_height + 0.3

        tmp_pos = [a1[X], a1[Y]]
        for row in range(1, 9):
            for col in "abcdefgh":
                square = f"{col}{row}"
                self.positions[square] = tmp_pos + [self.floor_height] + self.down_orientation
                tmp_pos = self.move_on_chessboard(tmp_pos, right=CELL_LENGTH, up=0)
            tmp_pos = self.move_on_chessboard(tmp_pos, right=-8*CELL_LENGTH, up=CELL_LENGTH)

        # rotated board self.start_position = self.move_on_chessboard(self.positions['a5'], right = -CELL_LENGTH/2, up = -CELL_LENGTH/2)
        self.start_position = self.move_on_chessboard(self.positions['h5'], right = CELL_LENGTH/2, up = CELL_LENGTH/2)


        self.start_position[Z] = self.sky_height

        self.grip_height[PieceType.QUEEN] = self.floor_height + 0.04
        self.grip_height[PieceType.PAWN] = self.floor_height + 0.025 
        self.grip_height[PieceType.KING] = self.floor_height + 0.04
        self.grip_height[PieceType.ROOK] = self.floor_height + 0.025
        self.grip_height[PieceType.KNIGHT] = self.floor_height + 0.03
        self.grip_height[PieceType.BISHOP] = self.floor_height + 0.03

        self.safe_height = 0.15 + self.floor_height
        self.table_height = self.floor_height + OFFSET_TO_TABLE_HEIGHT

        #global cube_pose
        #cube_pose = RobotHardware.modify_pose(self.positions["a8"], dx=-0.02, dy=-0.09, dz=0.09)

        self.create_physical_storage_positions()    
        

    @override
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if self.rtde_c is not None:
                self.rtde_c.stopScript()
        except Exception:
            pass
        try:
            if self.gripper is not None:
                self.gripper.disconnect()
        except Exception:
            pass
        try:
            if self.rtde_c is not None:
                self.rtde_c.disconnect()
        except Exception:
            pass
        try:
            if self.rtde_r is not None:
                self.rtde_r.disconnect()
        except Exception:
            pass

    @property
    @override
    def pose(self):
        return self.rtde_r.getActualTCPPose()

    @override
    def move_raw(self, target_pose, speed, acceleration):
        self.rtde_c.moveL(target_pose, speed, acceleration)

    @override
    def move_joint(self, target_pose, speed, acceleration):
        self.rtde_c.moveJ(target_pose, speed, acceleration)

    @override
    def set_gripper_raw(self, position, speed, force, wait):
        if wait:
            self.gripper.move_and_wait_for_pos(position, speed, force)
        else:
            self.gripper.move(position, speed, force)

    @override
    def get_gripper(self):
        return self.gripper.get_current_position()

    def create_physical_storage_positions(self, storage_start = None):
        if storage_start == None:
            #storage_start = self.move_on_chessboard(self.positions['a1'], right=-0.4*CELL_LENGTH, up=-2.5*CELL_LENGTH)
            storage_start = self.move_on_chessboard(self.positions['h8'], right=0.4*CELL_LENGTH, up=2.5*CELL_LENGTH)

        STORAGE_WIDTH = 5.3
        STORAGE_HEIGHT = 5

        tmp_pos = storage_start
        for i in range(1,5):
        
            if i == 1: # add special black pieces
                for type in "rnbqk":
                    self.positions[f's{type}1'] = [tmp_pos[X] ,tmp_pos[Y], self.table_height] + self.down_orientation
                    tmp_pos = self.move_on_chessboard(tmp_pos, right=-STORAGE_WIDTH, up=0)
                for type in "bnr":
                    self.positions[f's{type}2'] = [tmp_pos[X] ,tmp_pos[Y], self.table_height] + self.down_orientation
                    tmp_pos = self.move_on_chessboard(tmp_pos, right=-STORAGE_WIDTH, up=0)

            elif i == 4: # add special white pieces
                for type in "RNBQK":
                    self.positions[f's{type}1'] = [tmp_pos[X] ,tmp_pos[Y], self.table_height] + self.down_orientation
                    tmp_pos = self.move_on_chessboard(tmp_pos, right=-STORAGE_WIDTH, up=0)
                for type in "BNR":
                    self.positions[f's{type}2'] = [tmp_pos[X] ,tmp_pos[Y], self.table_height] + self.down_orientation
                    tmp_pos = self.move_on_chessboard(tmp_pos, right=-STORAGE_WIDTH, up=0)

            elif i == 2: # add regular black pieces
                for counter in range(1,9):
                    self.positions[f'sp{counter}'] = [tmp_pos[X] ,tmp_pos[Y], self.table_height] + self.down_orientation
                    tmp_pos = self.move_on_chessboard(tmp_pos, right=-STORAGE_WIDTH, up=0)

            else: # i == 3 # add regular white pieces
                for counter in range(1,9):
                    self.positions[f'sP{counter}'] = [tmp_pos[X] ,tmp_pos[Y], self.table_height] + self.down_orientation
                    tmp_pos = self.move_on_chessboard(tmp_pos, right=-STORAGE_WIDTH, up=0)

            # next line        
            tmp_pos = self.move_on_chessboard(tmp_pos, right=8*STORAGE_WIDTH, up=1*STORAGE_HEIGHT)
            
    def move_smooth_path___experimental(self, steps, blend_radius=0.03, speed=None, acceleration=None):
        
        if speed is None:
            speed = self.speed
        if acceleration is None:
            acceleration = self.acceleration

        path = []
        current_pose = self.pose 

        for i, step in enumerate(steps):
            step_kwargs = step.copy()
            if 'pose' not in step_kwargs: # save current pose as base pose
                step_kwargs['pose'] = current_pose
                
            next_pose = self.calculate_target_pose(**step_kwargs)
            radius = 0.0 if i == len(steps) - 1 else blend_radius
            path.append(next_pose + [speed, acceleration, radius]) # build the path
            
            current_pose = next_pose
            
        self.rtde_c.moveL(path)
        return current_pose

    def mov_chess_piece___experimental(self, type: PieceType=None, start_pos=None, end_pos=None, blend_radius = 0.05):
        if self.pose[Z] < self.safe_height:
            self.move_to(z=self.safe_height)

        self.set_gripper(grip_size[type] - GRIP_RELEASE_OFFSET, wait=False) #  release the piece

        path_steps1 = [
            {'pose': [start_pos[X], start_pos[Y], self.safe_height] + self.get_rotated_tcp_orientation(start_pos,Rz=45)},
            {'z': self.grip_height[type]}, 
        ]
        self.move_smooth_path(path_steps1, blend_radius=blend_radius) # move smoothly
        
        self.set_gripper(grip_size[type]) # grip the piece

        path_steps2 = [
            {'pose': [start_pos[X], start_pos[Y], self.safe_height] + self.get_rotated_tcp_orientation(start_pos,Rz=45), 'z':self.safe_height},
            {'pose': [end_pos[X], end_pos[Y], self.safe_height] + self.get_rotated_tcp_orientation(end_pos,Rz=45), 'z':self.safe_height}, 
            {'z': self.grip_height[type] + 0.005}
        ]
        self.move_smooth_path(path_steps2, blend_radius=blend_radius, speed=0.05) # move smoothly
        self.move_to(z=self.grip_height[type] + GRIP_RELEASE_HEIGHT)
        
        self.set_gripper(grip_size[type] - GRIP_RELEASE_OFFSET) # release the piece
        
        path_steps3 = [
            {'z':self.safe_height},
            {'pose': self.start_position}, 
        ]
        self.move_smooth_path(path_steps3, blend_radius=blend_radius, speed=0.05) # move smoothly

    def camera_vector_to_robot_vector(self, camera_vector):
        R, t = estimate_transform(camera_points, robot_points)
        return list(map(float, R @ camera_vector + t)) + self.down_orientation

    def pick_up_dead_piece(self, type: PieceType = PieceType.QUEEN, state=None, end_pos=None):
        ############################################################### add knight support
        # get robot postions from the interactable camera
        base_point, head_point = get_base_and_head_camera_points()
        R, t = estimate_transform(camera_points, robot_points)
        base_robot =  R @ base_point + t
        head_robot = R @ head_point + t

        # fix alignment
        #base_robot[Y]+=0.00
        #head_robot[Y]+=0.00
        #base_robot[X]+=0.01
        #head_robot[X]+=0.01

        # calculate middle position
        dx = head_robot[0] - base_robot[0]
        dy = head_robot[1] - base_robot[1]
        dz = math.degrees(math.atan2(dx, dy))

        # check if standing or lying
        if state == None:
            if np.abs(head_robot[Z] - base_robot[Z]) > np.sqrt(np.abs(dx)**2 + np.abs(dy)**2):
                state = 'standing'
            else:
                state = 'lying'

        if state == 'standing':
            bias = 0.5
        elif type == PieceType.BISHOP:
            bias = 0.5
        elif type == PieceType.KNIGHT:
            bias = 0.7
        else:
            bias = 0.6
        middle_position = [
            *weighted_avg(head_robot[:2], base_robot[:2], bias),
            0,
            *self.get_rotated_tcp_orientation(Rz=dz+180)
        ]
        
        # fix height
        # TODO (daniel): the following condition is always True.
        if middle_position[Z] < self.safe_height:
            self.move_to(z=self.safe_height)

        self.set_gripper(HALF_OPENED,wait=False)

        
        if state == 'lying':
            self.move_to(middle_position, z=self.safe_height)

            self.move_to(z=self.table_height+0.005)

            self.set_gripper(CLOSED) # grip the piece

            self.move_to(z=self.safe_height)
            self.move_to(cube_pose, z=self.safe_height)

            # rotate slowly
            self.move_to(orientation = self.get_rotated_tcp_orientation(Rx=85))
            self.move_to(z=cube_pose[Z] - self.floor_height + self.grip_height[type] + 0.01)
            
            # release standing piece
            self.set_gripper(self.get_gripper() - GRIP_RELEASE_OFFSET)

            # straighten the arm back   /    dx = 0.01                                                     -00.01
            self.move_to(cube_pose,dx=-0.005, z=cube_pose[Z] - self.floor_height + self.grip_height[type]- 0.00) 

            self.set_gripper(CLOSED) # grip the piece

            self.move_to(dz=0.05) # raise the arm

        elif state == 'standing':
            ##################################################### add knight support

            self.move_to([*middle_position[:3] , *self.down_orientation], z=self.safe_height)

            self.move_to([middle_position[X], middle_position[Y], self.grip_height[type]+OFFSET_TO_TABLE_HEIGHT] + self.down_orientation)
            
            self.set_gripper(CLOSED)
            
            self.move_to(dz=0.05)
            
        else:
            print("error on state")
            return 
            
        
        # put back on the chess board
        self.move_to(
            self.positions[end_pos],
            z=self.safe_height,
            orientation =
                self.get_rotated_tcp_orientation(Rz=90)
                if state == 'lying' and type == PieceType.KNIGHT and self.get_gripper() < grip_size[PieceType.KNIGHT]-7
                else None
        )
        self.move_to(z=self.grip_height[type] + GRIP_RELEASE_HEIGHT)
       
        self.set_gripper(open_by=GRIP_RELEASE_OFFSET)
        self.move_to(z=self.safe_height)
        #self.rtde_c.moveJ(BASE_EYAL, 1, 0.5)
        self.move_to(self.start_position, z=self.sky_height)

    ### I moved it to the right class, so can delete here ###        
    def capture_piece(self, type: PieceType, start_pos, end_pos = None, rz_start=None, move_to_start=True):
        if end_pos is None:
            end_pos = list(map(float, get_head_camera_point())) + self.down_orientation
        start_pos = self.normalize_pos(start_pos)
        end_pos = self.normalize_pos(end_pos)
        self.move_to(start_pos, z=self.safe_height, orientation=self.down_orientation)
        self.set_gripper(grip_size[type] - GRIP_RELEASE_OFFSET,wait=False) #  open the gripper
        self.move_to(z=self.grip_height[type])
        self.set_gripper(CLOSED)
        self.move_to(z=self.safe_height)
        
        self.move_to(end_pos, z=self.safe_height)
        self.move_to(z=self.grip_height[type]+OFFSET_TO_TABLE_HEIGHT)
        self.set_gripper(open_by=GRIP_RELEASE_OFFSET)
        self.move_to(z=self.safe_height)
        if move_to_start:
            self.move_to(self.start_position, z=self.safe_height)

    ### I moved it to the right class, so can delete here ###
    def move_and_capture_piece(self, capturer, captured, empty_pos=None):
        (capturer_type, capturer_pos) = capturer
        (captured_type, captured_pos) = captured
        capturer_pos = self.normalize_pos(capturer_pos)
        captured_pos = self.normalize_pos(captured_pos)

        self.capture_piece(captured_type, captured_pos, empty_pos, move_to_start=False)
        self.mov_chess_piece(capturer_type, capturer_pos, captured_pos)

######################## zed camera #########################
def estimate_transform(camera_points, robot_points):
    """
    camera_points: Nx3 numpy array
    robot_points:  Nx3 numpy array

    Returns:
        R (3x3 rotation matrix)
        t (3-vector translation)
    """

    assert camera_points.shape == robot_points.shape
    assert camera_points.shape[1] == 3

    # Centroids
    centroid_cam = np.mean(camera_points, axis=0)
    centroid_robot = np.mean(robot_points, axis=0)

    # Center points
    cam_centered = camera_points - centroid_cam
    robot_centered = robot_points - centroid_robot

    # Covariance matrix
    H = cam_centered.T @ robot_centered

    # SVD
    U, S, Vt = np.linalg.svd(H)

    R = Vt.T @ U.T

    # Reflection correction
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = Vt.T @ U.T

    t = centroid_robot - R @ centroid_cam

    return R, t

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
    init_params.camera_resolution = sl.RESOLUTION.HD2K

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
                    X_, Y_, Z_ = point3d[:3]
                    if np.isfinite(X_) and np.isfinite(Y_) and np.isfinite(Z_):
                        print(f"Pixel ({x}, {y})")
                        print(f"3D point: X={X_:.3f}, Y={Y_:.3f}, Z={Z_:.3f} meters")
                        if(base_point is None):
                            base_point = [X_, Y_, Z_]
                            print(f"base_point is set")
                        else:
                            head_point = [X_, Y_, Z_]
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

def get_12_camera_points():
    global clicked_point, point_cloud
    points = []

    zed = sl.Camera()
    init_params = sl.InitParameters()
    init_params.depth_mode = sl.DEPTH_MODE.ULTRA
    init_params.coordinate_units = sl.UNIT.METER
    init_params.camera_resolution = sl.RESOLUTION.HD2K

    if zed.open(init_params) != sl.ERROR_CODE.SUCCESS:
        print("Failed to open ZED")
        return []

    image = sl.Mat()
    runtime_params = sl.RuntimeParameters()

    cv2.namedWindow("ZED")
    cv2.setMouseCallback("ZED", mouse_callback)

    while len(points) < 12:
        if zed.grab(runtime_params) == sl.ERROR_CODE.SUCCESS:
            zed.retrieve_image(image, sl.VIEW.LEFT)
            zed.retrieve_measure(point_cloud, sl.MEASURE.XYZ)
            frame = image.get_data()

            if clicked_point is not None:
                x, y = clicked_point
                err, point3d = point_cloud.get_value(x, y)
                if err == sl.ERROR_CODE.SUCCESS:
                    X_, Y_, Z_ = point3d[:3]
                    if np.isfinite(X_) and np.isfinite(Y_) and np.isfinite(Z_):
                        points.append([float(X_), float(Y_), float(Z_)])
                        print(f"Captured point #{len(points) - 1}: X={X_:.3f}, Y={Y_:.3f}, Z={Z_:.3f} meters")
                    else:
                        print("Invalid depth at this pixel")

                clicked_point = None

            cv2.imshow("ZED", frame)

        key = cv2.waitKey(1)
        if key == 27:  # ESC
            break

    zed.close()
    cv2.destroyAllWindows()

    print("camera_points = np.array([")
    for i, point in enumerate(points):
        print(f"    [{point[0]:.17f}, {point[1]:.17f}, {point[2]:.17f}],  # {i}")
    print("])")

    return points

def get_head_camera_point():
    global clicked_point, point_cloud
    base_point = None
    head_point = None

    # Create camera
    zed = sl.Camera()
    init_params = sl.InitParameters()
    init_params.depth_mode = sl.DEPTH_MODE.ULTRA
    init_params.coordinate_units = sl.UNIT.METER
    init_params.camera_resolution = sl.RESOLUTION.HD2K

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
                    X_, Y_, Z_ = point3d[:3]
                    if np.isfinite(X_) and np.isfinite(Y_) and np.isfinite(Z_):
                       head_point = [X_, Y_, Z_] 
                    else:
                        print("Invalid depth at this pixel")

                clicked_point = None
            cv2.imshow("ZED", frame)
        key = cv2.waitKey(1)

        if key == 27:  # ESC
            break

    zed.close()
    cv2.destroyAllWindows()

    R, t = estimate_transform(camera_points, robot_points)
    head_robot = R @ head_point + t

    # fix alignment
    #head_robot[Y]-=0.01
    #head_robot[X]+=0.01

    return head_robot




def main():
    with RobotHardware(robot_ip=ROBOT_IP, base_tcp_port=BASE_TCP_PORT, A1=A1_, H8=H8_, speed=0.1) as robot:
       # מלך, מלכה, רץ, פרש, צריח, רגלי = king, queen, bishop, knight, rook, pawn
        print("starting session")
        #robot.rtde_c.moveJ(BASE_URI, 1, 0.5)
        #robot.move_to(robot.start_position, z=robot.sky_height)
        #robot.move_to(robot.positions['b2'],z=robot.safe_height)
        #pawn
        #robot.set_gripper(grip_size[PieceType.PAWN] - GRIP_RELEASE_OFFSET, wait=False) #  open the gripper
        #robot.move_to(robot.positions['b2'],z=robot.grip_height[PieceType.PAWN], orientation=robot.get_rotated_tcp_orientation(robot.positions['b2'],Rz=45))
        #robot.set_gripper(134)
        #robot.move_to(robot.move_on_chessboard(robot.pose, right=-0.5, up=-0.5))
        #robot.set_gripper(CLOSED)

        # knight left side
        #robot.set_gripper(grip_size[PieceType.ROOK] - GRIP_RELEASE_OFFSET)
        #robot.move_to(robot.positions['b2'],z=robot.safe_height, orientation=robot.get_rotated_tcp_orientation(robot.positions['b1'],Rz=45))
        #robot.move_to(robot.move_on_chessboard(robot.pose, right=-0.5, up=-0.0))
        #robot.set_gripper(140)
        #robot.move_to(robot.move_on_chessboard(robot.pose, right=-0.5, up=-0.0))
        #robot.move_to(z=robot.grip_height[PieceType.KNIGHT])
        #robot.set_gripper(CLOSED)

        #print(robot.normalize_pos(get_head_camera_point()))
        

        #point = get_head_camera_point()

        #print("point:", point)
        #print("type:", type(point))

        #print(robot.normalize_pos(point.tolist()))
        #robot.move_to(robot.normalize_pos(get_head_camera_point().tolist()))

        #robot.pick_up_dead_piece(PieceType.PAWN, "lying", "c1")
        robot.move_to(cube_pose, dz = 0.11)
        robot.move_to(orientation = robot.get_rotated_tcp_orientation(Rx=85))

        #robot.move_to(z=robot.safe_height)
        #robot.move_to([-0.7012659839948736, -0.36316477753682014, -0.32982245547551975] + robot.down_orientation)

        #robot.move_to(z=robot.safe_height)
        #robot.move_to([-0.5900482619985574, -0.3595256257140383, -0.32982245547551975] + robot.down_orientation)

        #robot.move_to(z=robot.safe_height)

        #robot.move_to([-0.6480715733896221, -0.37616930509489405, -0.32982245547551975] + robot.down_orientation)
        
        #get_12_camera_points()
        
        
        #robot.move_to(robot.normalize_pos(get_head_camera_point().tolist()))
        #robot.move_to([-0.7012659839948736, -0.36316477753682014, -0.2629104676755676] + robot.down_orientation)
        print(robot.get_gripper())
        #robot.move_to(robot.start_position, z=robot.sky_height)
        print("end of session")

        
        
if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "reset":
            reset_gripper()
        if sys.argv[1].lower() == "start":
            move_to_start_postion()
        if sys.argv[1].lower() == "print":
            print_position()
        if sys.argv[1].lower() == "close":
            grip_close()
        if sys.argv[1].lower() == "open":
            grip_open()
        if sys.argv[1].lower() == "align":
            align_position()
        if sys.argv[1].lower() == "grip":
            get_grip()
        if sys.argv[1].lower() == "joints":
            print_joints()
    else:
        main()





    #robot.mov_chess_piece(PieceType.PAWN, "b1", "c3")
    #robot.move_and_capture_piece((PieceType.PAWN, "b2"), (PieceType.QUEEN,"c3"))
    #robot.pick_up_dead_piece(PieceType.QUEEN, "lying", "c1")
    #robot.move_to([*get_head_camera_point()] + robot.down_orientation)