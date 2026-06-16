import time
import sys
from rtde_control import RTDEControlInterface
from rtde_receive import RTDEReceiveInterface
from robotiq_gripper import RobotiqGripper
import numpy as np
from scipy.spatial.transform import Rotation
import cv2
import pyzed.sl as sl
import math

ROBOT_IP = "192.168.56.101"
BASE_TCP_PORT = 63352



camera_points = np.array([
    [-0.3103788495063782, 0.20816968381404877, 0.9021732211112976],
    [-0.2412874549627304, 0.21155597269535065, 0.9092869758605957],
    [-0.19911204278469086, 0.2076052576303482, 0.8924124836921692],
    [-0.23708832263946533, 0.18825772404670715, 0.9412122368812561],
    [-0.2746868431568146, 0.17273056507110596, 0.9655194878578186],
    [-0.27698686718940735, 0.1568019539117813, 0.9937079548835754],
    [-0.20621158182621002, 0.13297036290168762, 1.0304497480392456],
    [-0.3061258792877197, 0.11988385021686554, 1.0544846057891846],
    [-0.24355772137641907, 0.1199633926153183, 1.0552380084991455],
    [-0.30645254254341125, 0.1024651825428009, 1.0843398571014404],
    [-0.24740150570869446, 0.096726194024086, 1.089730143547058],

#    [-0.12599721550941467, 0.19377468526363373, 0.8839865922927856],
#    [-0.11357908695936203, 0.505807638168335, 2.656207323074341],
#    [0.10381188988685608, 0.45070210099220276, 2.8906421661376953],
#    [0.07288794219493866, 0.08622042834758759, 1.063478946685791],
#    [0.15284010767936707, 0.06357734650373459, 1.0952370166778564],
#    [0.15698301792144775, 0.14513954520225525, 0.9543092846870422],
#    [-0.09062656760215759, 0.06751318275928497, 1.0909947156906128],
#    [-0.047709643840789795, 0.08860450983047485, 1.0676332712173462],
])



robot_points = np.array([
[0.07165449155305594, -0.8689120342824104, 0.00761849382290658], #1
[0.0746530566617607, -0.7953362242005896, 0.004351846959708611], #2
[0.07251428629002046, -0.7563871277745808, 0.004090195582639206], #3
[0.0297674262951436, -0.7946321237172691, 0.004359263137356434], #4
[0.002640284170454068, -0.8300784899379653, 0.005978647005982551], #5
[-0.03088749462845628, -0.8305381263150142, 0.006450310317636543], #6
[-0.07661470188311771, -0.7625228718765196, 0.005115601503159012], #7
[-0.10240466056378457, -0.8607379650664497, 0.005362619851522338], #8
[-0.10241297195056764, -0.7979398917752542, 0.0042431200006042835], #9
[-0.13430503939697003, -0.8594993130056128, 0.004450275407329174], #10
[-0.1462758604281513, -0.8000864040037845, 0.00473211183153302], #11

#[0.08205673493996721, -0.6753187762204925, 0.025300681966506575], #a1
#[0.04006300568110827, -0.5963315088823268, 0.025300681966506575], #c2
#[-0.001930723577750662, -0.517344241544161, 0.025300681966506575], #e3
#[-0.12291172017477514, -0.48035070346485403, 0.025300681966506575], #f6
#[-0.16490544943363408, -0.4013634361266884, 0.025300681966506575], #h7
#[-0.0049308382854820615, -0.3973632831830471, 0.025300681966506575], #h3
#[-0.15890522001817128, -0.6413253528489165, 0.025300681966506575], #b7
#[-0.11991160546704374, -0.6003316618259681, 0.025300681966506575] #c6
])

grip_offset = 0
grip_size = {
    "queen": 180 +grip_offset, # מלכה
    "pawn": 193+grip_offset,   # רגלי
    "king": 180+grip_offset,   # מלך
    "rook": 178+grip_offset,   # צריח
    "knight": 198+grip_offset, # פרש
    "bishop": 185+grip_offset, # רץ

    "king_alignment": 179+grip_offset,
    "queen_alignment": 181 +grip_offset,
    "pawn_alignment": 195+grip_offset,
    "rook_alignment": 179+grip_offset,
    "knight_alignment": 167+grip_offset,
    "bishop_alignment": 177+grip_offset, 
}

X, Y, Z, RX, RY, RZ = 0,1,2,3,4,5
GRIP_RELEASE_OFFSET = 24
GRIP_REALIGNMENT_OFFSET = 4
GRIP_RELEASE_HEIGHT = 0.005
A1_ = [0.08402962108584439, -0.676097716024815, 0.028387340797933758, 2.2085369502005876, 2.212499868868369, -0.0007045682471379121]
H8_ = [-0.20806546653597902, -0.40398542992701425, 0.02470172121064082, 2.2085529406690534, 2.2124634903015785, -0.0007412473852994461]
A1 = [0.08205673493996721, -0.6753187762204925, 0.024844870270488956, 2.247469008346155, -2.146149708890044, 0]
H8 = [-0.20489910222067206, -0.4023634743625998, 0.025756493662524194, 2.247613176209329, -2.1463343846561838, 0]


clicked_point = None
point_cloud = sl.Mat()

cube_pose = [-0.21923474289144815, -0.7716860104142782, 0.06772034126120247, 2.247590849983201, -2.1462403402250865, -8.055377065164397e-05]


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

class ChessBot:
    def __init__(self, robot_ip=None, base_tcp_port=None, speed=0.1, acceleration=0.1, A1 = None, H8 = None):
        self.robot_ip = robot_ip
        self.base_tcp_port = base_tcp_port
        self.speed = speed
        self.acceleration = acceleration
        self.rtde_c = None
        self.rtde_r = None
        self.gripper = None
        self.A1 = A1
        self.H8 = H8
        self.step_right = [0, 0]
        self.step_up = [0, 0]
        self.floor_height = 0
        self.sky_height = 0
        self.safe_height = 0.15
        self.start_position = [0, 0, 0, 0, 0, 0]
        self.positions = {}
        self.grip_height = {}
        self.release_lying_height = {}
        self.down_orientation = [2.0107452890463056, -2.3743186369030598, -0.0762631964824858]
        self.free_platform = [0,0,0,0,0,0]
        self.table_height = 0

    def __enter__(self):
        self.rtde_c = RTDEControlInterface(self.robot_ip)
        self.rtde_r = RTDEReceiveInterface(self.robot_ip)
        self.gripper = RobotiqGripper()
        self.gripper.connect(self.robot_ip, self.base_tcp_port)
        time.sleep(0.1)
        self.calibrate_board_positions(self.A1, self.H8)
        #self.rtde_c.moveL(self.start_position, self.speed, self.acceleration)
        if not self.gripper.is_active():
            self.gripper.activate()
        return self

    # return a position moved right and up by the given number of centimeters, can also use negative numbers to move left and down
    # must before use the calibrate_board_positions function at least once to set the step_right and step_up values
    def move_on_chessboard(self, current_pos, right=0, up=0):
        position = current_pos.copy()
        position[X] = position[X] + (self.step_right[X] / 4.0) * right + (self.step_up[X] / 4.0) * up
        position[Y] = position[Y] + (self.step_right[Y] / 4.0) * right + (self.step_up[Y] / 4.0) * up
        return position

    def calibrate_board_positions(self, a1=None, h8=None):
       
        if a1 is None:
            a1 = A1
        if h8 is None:
            h8 = H8

        dx = h8[X] - a1[X]
        dy = h8[Y] - a1[Y]
        h1 = [a1[X] + (dx + dy) / 2.0, a1[Y] + (dy - dx) / 2.0]

        self.step_right[0] = (h1[X] - a1[X]) / 7.0
        self.step_right[1] = (h1[Y] - a1[Y]) / 7.0
        self.step_up[0] = -self.step_right[Y]
        self.step_up[1] = self.step_right[X]

        self.down_orientation = [(h8[RX] + a1[RX]) / 2, (h8[RY] + a1[RY]) / 2, (h8[RZ] + a1[RZ]) / 2]
        self.floor_height = (h8[Z] + a1[Z]) / 2
        self.sky_height = self.floor_height + 0.3

        tmp_pos = [a1[X], a1[Y]]
        for row in range(1, 9):
            for col in "abcdefgh":
                square = f"{col}{row}"
                self.positions[square] = tmp_pos + [self.floor_height] + self.down_orientation
                tmp_pos = self.move_on_chessboard(tmp_pos, right=4, up=0)
            tmp_pos = self.move_on_chessboard(tmp_pos, right=-32, up=4)

        self.start_position = self.move_on_chessboard(self.positions['d5'], right = 2, up = -2)
        self.start_position[Z] = self.sky_height

        self.grip_height["queen"] = self.floor_height + 0.04
        self.grip_height["pawn"] = self.floor_height + 0.025 
        self.grip_height["king"] = self.floor_height + 0.04
        self.grip_height["rook"] = self.floor_height + 0.025
        self.grip_height["knight"] = self.floor_height + 0.03
        self.grip_height["bishop"] = self.floor_height + 0.03
        
        self.release_lying_height["queen"] = self.floor_height + 0.065
        self.release_lying_height["pawn"] = self.floor_height + 0.03
        self.release_lying_height["king"] = self.floor_height + 0.06
        self.release_lying_height["rook"] = self.floor_height + 0.040
        self.release_lying_height["knight"] = self.floor_height + 0.045
        self.release_lying_height["bishop"] = self.floor_height + 0.028

        self.safe_height = 0.15 + self.floor_height
        self.free_platform = self.move_on_chessboard(self.positions['a8'], right=-8.5, up=2)[0:2] + [self.floor_height + 0.042] + self.down_orientation
        self.table_height = self.floor_height - 0.02

        #global cube_pose
        #cube_pose = ChessBot.modify_pose_relative(self.positions["a8"], dx=-0.02, dy=-0.09, dz=0.09)

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
    def pose(self):
        return self.rtde_r.getActualTCPPose()

    # return a rotated version vector of curent position
    def get_rotated_tcp_orientation(self, base_orientation = None, Rx=0, Ry=0, Rz=0):
        if base_orientation is None:
            base_orientation = self.pose
        base_orientation = base_orientation[-3:] 
        rot_base = Rotation.from_rotvec(base_orientation)
        rot_local = Rotation.from_euler('xyz', [Rx, Ry, Rz], degrees=True)
        new_rot = rot_base * rot_local
        return  new_rot.as_rotvec().tolist()
    

    def calculate_target_pose(self, pose=None, x=None, y=None, z=None, rx=None, ry=None, rz=None, 
                              orientation = None, dx=None, dy=None, dz=None, drx=None, dry=None, drz=None):
        if pose is None:
            pose = self.pose

        abs_params = any(v is not None for v in (x, y, z, rx, ry, rz))
        rel_params = any(v is not None for v in (dx, dy, dz, drx, dry, drz))
        ver_ori = orientation is not None
        if sum([abs_params, rel_params, ver_ori]) > 1: # pick only one of them
            raise ValueError("Cannot mix absolute (x,y,z,rx,ry,rz) and relative (dx,dy,dz,drx,dry,drz) parameters and rotations")

        if abs_params:
            target_pose = self.modify_pose(pose, x=x, y=y, z=z, rx=rx, ry=ry, rz=rz)
        elif rel_params:
            target_pose = self.modify_pose_relative(pose, dx=dx, dy=dy, dz=dz, drx=drx, dry=dry, drz=drz)
        elif ver_ori:
            target_pose = pose[0:3] + orientation
        else:
            target_pose = pose.copy()

        return target_pose

    def move_to(self, pose=None, x=None, y=None, z=None, rx=None, ry=None, rz=None, orientation = None,
                dx=None, dy=None, dz=None, drx=None, dry=None, drz=None, speed = None, acceleration = None):
        
        if speed is None:
            speed = self.speed
        if acceleration is None:
            acceleration = self.acceleration
        target_pose = self.calculate_target_pose(pose=pose, x=x, y=y, z=z, rx=rx, ry=ry, rz=rz, orientation = orientation,
                                                dx=dx, dy=dy, dz=dz, drx=drx, dry=dry, drz=drz)
        self.rtde_c.moveL(target_pose, speed, acceleration)
        return target_pose

    def set_gripper(self, position, speed=120, force=0, wait = True):
        if wait == True:
            self.gripper.move_and_wait_for_pos(position, speed, force)
        else:
            self.gripper.move(position, speed, force)

    def get_gripper(self):
        return self.gripper.get_current_position()
    @staticmethod
    def modify_pose(pose, x=None, y=None, z=None, rx=None, ry=None, rz=None):
        modified = pose.copy()
        if x is not None:
            modified[X] = x
        if y is not None:
            modified[Y] = y
        if z is not None:
            modified[Z] = z
        if rx is not None:
            modified[RX] = rx
        if ry is not None:
            modified[RY] = ry
        if rz is not None:
            modified[RZ] = rz
        return modified

    @staticmethod
    def modify_pose_relative(pose, dx=None, dy=None, dz=None, drx=None, dry=None, drz=None):
        modified = pose.copy()
        if dx is not None:
            modified[X] += dx
        if dy is not None:
            modified[Y] += dy
        if dz is not None:
            modified[Z] += dz
        if drx is not None:
            modified[RX] += drx
        if dry is not None:
            modified[RY] += dry
        if drz is not None:
            modified[RZ] += drz
        return modified

    def mov_chess_piece(self, type=None, start_pos=None, end_pos=None, speed=None, acceleration=None, rz_rotation=None):
        if speed is None:
            speed = self.speed
        if acceleration is None:
            acceleration = self.acceleration
        if self.pose[Z] < self.safe_height:
            self.move_to(z=self.safe_height)
        start_pos = self.positions[start_pos] # update chess board location
        end_pos = self.positions[end_pos] #  update chess board location
        if rz_rotation is not None:
            start_pos[3:6] = self.get_rotated_tcp_orientation(start_pos,Rz=rz_rotation)
            end_pos[3:6] = self.get_rotated_tcp_orientation(end_pos,Rz=rz_rotation)

        self.set_gripper(grip_size[type] - GRIP_RELEASE_OFFSET,wait=False) #  open the gripper

        self.move_to(start_pos, z=self.safe_height, speed=speed, acceleration=acceleration) # move to first spot
        self.move_to(z=self.grip_height[type])

        self.set_gripper(grip_size[type]) # grip the piece

        self.move_to(start_pos, z=self.safe_height)
        self.move_to(end_pos, z=self.safe_height, speed=speed, acceleration=acceleration)
        self.move_to(z=self.grip_height[type] + GRIP_RELEASE_HEIGHT)
        
        self.set_gripper(grip_size[type] - GRIP_RELEASE_OFFSET) # release the piece
        
        self.move_to(z=self.safe_height)
        self.move_to(self.start_position, speed=speed, acceleration=acceleration)

    def mov_chess_piece_grip_modify(self, type=None, start_pos=None, end_pos=None, speed=None, acceleration=None, rz_rotation=None):
        if speed is None:
            speed = self.speed
        if acceleration is None:
            acceleration = self.acceleration
        if self.pose[Z] < self.safe_height:
            self.move_to(z=self.safe_height)
        start_pos = self.positions[start_pos] # update chess board location
        end_pos = self.positions[end_pos] #  update chess board location
        if rz_rotation is not None:
            start_pos[3:6] = self.get_rotated_tcp_orientation(start_pos,Rz=rz_rotation)
            end_pos[3:6] = self.get_rotated_tcp_orientation(end_pos,Rz=rz_rotation)

        self.set_gripper(grip_size[type] - GRIP_RELEASE_OFFSET,wait=False) #  open the gripper

        self.move_to(start_pos, z=self.safe_height, speed=speed, acceleration=acceleration) # move to first spot
        self.move_to(z=self.grip_height[type])

        self.set_gripper(255) # grip the piece

        self.move_to(start_pos, z=self.safe_height)
        self.move_to(end_pos, z=self.safe_height, speed=speed, acceleration=acceleration)
        self.move_to(z=self.grip_height[type] + GRIP_RELEASE_HEIGHT)
        
        
        self.set_gripper(self.get_gripper() - GRIP_RELEASE_OFFSET) # release the piece
        
        self.move_to(z=self.safe_height)
        self.move_to(self.start_position, speed=speed, acceleration=acceleration)

    def move_smooth_path(self, steps, blend_radius=0.03, speed=None, acceleration=None):
        
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

    def mov_chess_piece_rotated3(self, type=None, start_pos=None, end_pos=None, blend_radius = 0.05):
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
    
    def align_piece(self, type=None, pos=None):
        cur_pos = pos.copy()
        

        self.set_gripper(grip_size[type+"_alignment"] - GRIP_RELEASE_OFFSET, wait=False)

        self.move_to(cur_pos, z = self.safe_height)
        self.move_to(z=self.floor_height+0.002)

        self.set_gripper(grip_size[type+"_alignment"])

        self.move_to(z=self.safe_height)

        # release slowly
        self.set_gripper(grip_size[type+"_alignment"] - int(GRIP_REALIGNMENT_OFFSET*0.5))
        time.sleep(0.5)
        self.set_gripper(grip_size[type+"_alignment"] - int(GRIP_REALIGNMENT_OFFSET*0.75))
        time.sleep(0.75)
        self.set_gripper(grip_size[type+"_alignment"] - GRIP_REALIGNMENT_OFFSET)
        time.sleep(1)
        if type == "queen":
            time.sleep(1)
        self.set_gripper(grip_size[type+"_alignment"]) # get good grip again

        self.move_to(z=self.release_lying_height[type])

        self.set_gripper(grip_size[type+"_alignment"] - GRIP_RELEASE_OFFSET)

        self.move_to(z=self.safe_height)

    def align_piece_rotaion(self, type=None, pos=None):
        cur_pos = pos.copy()
        
        self.set_gripper(grip_size[type+"_alignment"] - GRIP_RELEASE_OFFSET, wait=False)

        self.move_to(cur_pos, z = self.safe_height)
        self.move_to(z=self.floor_height+0.002)

        self.set_gripper(grip_size[type+"_alignment"])

        self.move_to(z=self.safe_height)

        # rotate slowly
        self.move_to(orientation = self.get_rotated_tcp_orientation(Rx=-90))

        self.move_to(z=self.release_lying_height[type])

        self.set_gripper(grip_size[type+"_alignment"] - GRIP_RELEASE_OFFSET)

        self.move_to(z=self.safe_height)

    def align_piece_rotaion3(self, type=None, start_pos=None, end_pos=None, lying = True, orientation=None):
        if start_pos[Z] < self.safe_height:
            self.move_to(z=self.safe_height)

        #self.set_gripper(grip_size[type] - GRIP_RELEASE_OFFSET, wait=False)
        self.set_gripper(140,wait=False)
        if orientation is not None:
            start_pos[3:6] = orientation
        #mov and rotate partially
        if lying:
            
            self.move_to(start_pos, z=self.safe_height)
            self.move_to(start_pos, z=self.table_height+0.0015)
            
            
            
        else: #standing
            cur_pos = [start_pos[X], start_pos[Y], self.grip_height[type]] + self.up_orientation
            # later
        
        self.set_gripper(grip_size[type]-3) # grip the piece
         

        self.move_to(z=self.safe_height)

        robot.move_to(cube_pose, z=self.safe_height)

        # rotate slowly
        #self.move_to(x=self.positions['c1'][X],y=self.positions['c1'][Y], z=self.safe_height)
        self.move_to(orientation = self.get_rotated_tcp_orientation(Rx=-85))
        

        #self.move_to(x=self.free_platform[X], y=self.free_platform[Y], z=self.free_platform[Z] + 0.01)


        #self.move_to(x=self.positions['a1'][X], y=self.positions['a1'][Y], z=self.safe_height)

        #self.set_gripper(grip_size[type] - GRIP_RELEASE_OFFSET) # release

        #self.move_to(z=self.safe_height)

    def camera_vector_to_robot_vector(self, camera_vector):
        R, t = estimate_transform(camera_points, robot_points)
        return list(map(float, R @ camera_vector + t)) + self.down_orientation

    def get_dead_chess_piece(self):
        base_point, head_point = get_base_and_head_camera_points()
        print([float(base_point[0]), float(base_point[1]), float(base_point[2])])
        print([float(head_point[0]), float(head_point[1]), float(head_point[2])])
        

        
        R, t = estimate_transform(camera_points, robot_points)
        base_robot =  R @ base_point + t
        head_robot = R @ head_point + t

        # fix alignment
        base_robot[Y]-=0.01
        head_robot[Y]-=0.01

        # calculate middle position
        dx = head_robot[0] - base_robot[0]
        dy = head_robot[1] - base_robot[1]
        dz = math.degrees(math.atan2(dx, dy))

        XYZ = [0.5*(head_robot[0] + base_robot[0]), 0.5*(head_robot[1] + base_robot[1]), 0]
        robot.align_piece_rotaion2(type='pawn', start_pos=XYZ + robot.down_orientation, 
                                    end_pos=robot.positions['a2'], orientation = robot.get_rotated_tcp_orientation(Rz=dz+90),
                                    lying = True)

    def get_dead_chess_piece3(self, type):
        base_point, head_point = get_base_and_head_camera_points()
        #print([float(base_point[0]), float(base_point[1]), float(base_point[2])])
        #print([float(head_point[0]), float(head_point[1]), float(head_point[2])])
        

        
        R, t = estimate_transform(camera_points, robot_points)
        base_robot =  R @ base_point + t
        head_robot = R @ head_point + t

        # fix alignment
        base_robot[Y]-=0.01
        head_robot[Y]-=0.01
        base_robot[X]+=0.01
        base_robot[X]+=0.01

        # calculate middle position
        dx = head_robot[0] - base_robot[0]
        dy = head_robot[1] - base_robot[1]
        dz = math.degrees(math.atan2(dx, dy))

        XYZ = [0.5*(head_robot[0] + base_robot[0]), 0.5*(head_robot[1] + base_robot[1]), 0]
        
        orientation = robot.get_rotated_tcp_orientation(Rz=dz+90)
        lying = True

        if XYZ[Z] < self.safe_height:
            self.move_to(z=self.safe_height)

        #self.set_gripper(grip_size[type] - GRIP_RELEASE_OFFSET, wait=False)
        self.set_gripper(140,wait=False)
        if orientation is not None:
            XYZ[3:6] = orientation
        #mov and rotate partially
        if lying:
            
            self.move_to(XYZ, z=self.safe_height)
            self.move_to(XYZ, z=self.table_height+0.0015)
            
            
            
        else: #standing
            cur_pos = [XYZ[X], XYZ[Y], self.grip_height[type]] + self.up_orientation
            # later
        
        self.set_gripper(grip_size[type]) # grip the piece
         

        self.move_to(z=self.safe_height)

        robot.move_to(cube_pose, z=self.safe_height)

        # rotate slowly
        self.move_to(orientation = self.get_rotated_tcp_orientation(Rx=-85))
        
        self.move_to(z=cube_pose[Z] - self.floor_height + self.grip_height[type] + 0.01)
        self.set_gripper(grip_size[type] - GRIP_RELEASE_OFFSET)
        
        self.move_to(cube_pose, z=cube_pose[Z] - self.floor_height + self.grip_height[type]- 0.01)
        self.move_to(dx=0.01)
        self.set_gripper(grip_size[type])
        self.move_to(dz=0.05)
        self.move_to(self.positions["a1"], z=self.safe_height)
        self.move_to(z=self.grip_height[type])
        self.set_gripper(grip_size[type] - GRIP_RELEASE_OFFSET)
        self.move_to(z=self.safe_height)
        
       


########################calibration#########################
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




if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == "reset":
        reset_gripper()

    with ChessBot(robot_ip=ROBOT_IP, base_tcp_port=BASE_TCP_PORT, A1=A1, H8=H8) as robot:
       # מלך, מלכה, רץ, פרש, צריח, רגלי = king, queen, bishop, knight, rook, pawn
        print("starting session")
        
        robot.move_to(robot.start_position, z=robot.safe_height)
        
        #base, head = get_base_and_head_camera_points()
        #robot.move_to(robot.camera_vector_to_robot_vector(base), dz=0.01)
        

        
        #robot.mov_chess_piece_grip_modify('pawn', 'b1', 'b3', speed=0.5)
        
        # base_point, head_point = get_base_and_head_camera_points()        
        # R, t = estimate_transform(camera_points, robot_points)
        # base_robot =  R @ base_point + t
        # head_robot = R @ head_point + t
        # # fix alignment
        # #base_robot[Y]-=0.01
        # #head_robot[Y]-=0.01
        # # calculate middle position
        # dx = head_robot[0] - base_robot[0]
        # dy = head_robot[1] - base_robot[1]
        # dz = math.degrees(math.atan2(dx, dy))
        # XYZ = [0.5*(head_robot[0] + base_robot[0]), 0.5*(head_robot[1] + base_robot[1]), 0]
        # robot.align_piece_rotaion3(type='queen', start_pos=XYZ + robot.down_orientation, 
        #                             end_pos=robot.positions['a2'], orientation = robot.get_rotated_tcp_orientation(Rz=dz+90),
        #                             lying = True)
        robot.get_dead_chess_piece3("queen")
        
        
        print(robot.positions['a1'][0:3])
        print(robot.positions['c2'][0:3])
        print(robot.positions['e3'][0:3])
        print(robot.positions['f6'][0:3])
        print(robot.positions['h7'][0:3])
        print(robot.positions['h3'][0:3])
        print(robot.positions['b7'][0:3])
        print(robot.positions['c6'][0:3])

        # with open("output", "a") as f:
        #     for i in range(0, 8 + 11 + 1, 2):
        #         base, head = get_base_and_head_camera_points()
        #         print(f"point {i}:", list(map(float, base)))
        #         print(f"point {i + 1}:", list(map(float, head)))
        #         print(f"point {i}:", list(map(float, base)), file=f)
        #         print(f"point {i + 1}:", list(map(float, head)), file=f)
        #         f.flush()
        

        #[0.08205673493996721, -0.6753187762204925, 0.025300681966506575], #a1
        #[0.04006300568110827, -0.5963315088823268, 0.025300681966506575], #c2
        #[-0.001930723577750662, -0.517344241544161, 0.025300681966506575], #e3
        #[-0.12291172017477514, -0.48035070346485403, 0.025300681966506575], #f6
        #[-0.16490544943363408, -0.4013634361266884, 0.025300681966506575], #h7
        #[-0.0049308382854820615, -0.3973632831830471, 0.025300681966506575], #h3
        #[-0.15890522001817128, -0.6413253528489165, 0.025300681966506575], #b7
        #[-0.11991160546704374, -0.6003316618259681, 0.025300681966506575] #c6
        
        




        robot.move_to(robot.start_position, z=robot.safe_height)

        print("end of session")




        '''
[0.07165449155305594, -0.8689120342824104, 0.00761849382290658], #1
[0.0746530566617607, -0.7953362242005896, 0.004351846959708611], #2
[0.07251428629002046, -0.7563871277745808, 0.004090195582639206], #3
[0.0297674262951436, -0.7946321237172691, 0.004359263137356434], #4
[0.002640284170454068, -0.8300784899379653, 0.005978647005982551], #5
[-0.03088749462845628, -0.8305381263150142, 0.006450310317636543], #6
[-0.07661470188311771, -0.7625228718765196, 0.005115601503159012], #7
[-0.10240466056378457, -0.8607379650664497, 0.005362619851522338], #8
[-0.10241297195056764, -0.7979398917752542, 0.0042431200006042835], #9
[-0.13430503939697003, -0.8594993130056128, 0.004450275407329174], #10
[-0.1462758604281513, -0.8000864040037845, 0.00473211183153302], #11
        '''











        #robot.align_piece('king', robot.positions['a1'])
        ##robot.align_piece('queen', robot.positions['b1']) not working
        #robot.align_piece_rotaion('queen', robot.positions['b1'])
        #robot.align_piece('bishop', robot.positions['c1'])
        #robot.align_piece('knight', robot.positions['d1'])
        #robot.align_piece('rook', robot.positions['e1'])
        #robot.align_piece('pawn', robot.positions['f1'])
        
        #robot.mov_chess_piece('king', 'a1', 'a3', speed=0.5)
        #robot.mov_chess_piece('queen', 'b1', 'b3', speed=0.5)
        #robot.mov_chess_piece('bishop', 'c1', 'c3', speed=0.5)
        #robot.mov_chess_piece('knight', 'd1', 'd3', speed=0.5)
        #robot.mov_chess_piece('rook', 'e1', 'e3', speed=0.5)
        #robot.mov_chess_piece('pawn', 'f1', 'f3', speed=0.5)
        
        #print(robot.pose)
        
        '''
        d1 = [0.031, 0.055, 0.912 ]
        d1_ = [0.022, 0.046, 0.913]
        a1_ = [-0.096, 0.053, 0.909]
        h8_ = [0.188,-0.126, 1.116 ]
        tmp = [-0.203, 0.008, 0.994]
        base_point, head_point = get_base_and_head_camera_points()
        
        R, t = estimate_transform(camera_points, robot_points)
        base_robot =  R @ base_point + t
        head_robot = R @ head_point + t

        # fix alignment
        base_robot[Y]-=0.01
        head_robot[Y]-=0.01

        dx = head_robot[0] - base_robot[0]
        dy = head_robot[1] - base_robot[1]
        dz = math.degrees(math.atan2(dx, dy))
        
        tmp_pos = robot.pose
        tmp_pos[RZ] = 0

        print(dx, dy, dz)
        print(base_robot)
        print(head_robot)
        #robot.move_to(orientation = robot.get_rotated_tcp_orientation(Rz=dz + 90))
        

        XY = [0.5*(head_robot[0] + base_robot[0]), 0.5*(head_robot[1] + base_robot[1])]
        #robot.move_to(robot.pose[0:3] + tmp_pos)


        XYZ = R @ tmp + t
        
        position = [XY[0], XY[1], 0]
        
        

        pose = [float(base_robot[0]), float(base_robot[1])-0.01, float(robot.table_height)] + robot.down_orientation
        
        #robot.move_to(pose)
        
        robot.align_piece_rotaion2(type='pawn', start_pos=position + robot.down_orientation, 
                                    end_pos=robot.positions['a2'], orientation = robot.get_rotated_tcp_orientation(Rz=dz+90) ,lying = True)
        
       
        
        


        '''
        
        



