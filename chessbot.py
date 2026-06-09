import time
import sys
from rtde_control import RTDEControlInterface
from rtde_receive import RTDEReceiveInterface
from robotiq_gripper import RobotiqGripper
import numpy as np
from scipy.spatial.transform import Rotation

ROBOT_IP = "192.168.56.101"
BASE_TCP_PORT = 63352
X, Y, Z, RX, RY, RZ = 0,1,2,3,4,5
GRIP_RELEASE_OFFSET = 24
GRIP_REALIGNMENT_OFFSET = 4
GRIP_RELEASE_HEIGHT = 0.005

grip_offset = 0
grip_size = {
    "queen": 180 +grip_offset, # מלכה
    "pawn": 190+grip_offset,   # רגלי
    "king": 180+grip_offset,   # מלך
    "rook": 178+grip_offset,   # צריח
    "knight": 198+grip_offset, # פרש
    "bishop": 178+grip_offset, # רץ

    "king_alignment": 179+grip_offset,
    "queen_alignment": 181 +grip_offset,
    "pawn_alignment": 195+grip_offset,
    "rook_alignment": 179+grip_offset,
    "knight_alignment": 167+grip_offset,
    "bishop_alignment": 177+grip_offset, 
}


A1 = [0.08318963239490007, -0.6729068646629713, 0.028260349774598126, 2.2085534413590167, 2.2125017895387313, -0.0006430518002744046]
H8 = [-0.20806546653597902, -0.40398542992701425, 0.02470172121064082, 2.2085529406690534, 2.2124634903015785, -0.0007412473852994461]


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

    def __enter__(self):
        self.rtde_c = RTDEControlInterface(self.robot_ip)
        self.rtde_r = RTDEReceiveInterface(self.robot_ip)
        self.gripper = RobotiqGripper()
        self.gripper.connect(self.robot_ip, self.base_tcp_port)
        time.sleep(0.1)
        self.calibrate_board_positions(self.A1, self.H8)
        self.rtde_c.moveL(self.start_position, self.speed, self.acceleration)
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

        self.grip_height["queen"] = self.floor_height + 0.045
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
        start_pos = self.positions[start_pos]
        end_pos = self.positions[end_pos]
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

        
    



if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == "reset":
        reset_gripper()

    with ChessBot(robot_ip=ROBOT_IP, base_tcp_port=BASE_TCP_PORT, A1=A1, H8=H8) as robot:
       # מלך, מלכה, רץ, פרש, צריח, רגלי = king, queen, bishop, knight, rook, pawn
        #robot.align_piece('king', robot.positions['a1'])
        ##robot.align_piece('queen', robot.positions['b1']) not working
        #robot.align_piece_rotaion('queen', robot.positions['b1'])
        #robot.align_piece('bishop', robot.positions['c1'])
        #robot.align_piece('knight', robot.positions['d1'])
        #robot.align_piece('rook', robot.positions['e1'])
        #robot.align_piece('pawn', robot.positions['f1'])

        #robot.mov_chess_piece('king', 'a1', 'a3')
        #robot.mov_chess_piece('queen', 'b1', 'b3')
        #robot.mov_chess_piece('bishop', 'c1', 'c3')
        #robot.mov_chess_piece('knight', 'd1', 'd3')
        #robot.mov_chess_piece('rook', 'e1', 'e3')
        #robot.mov_chess_piece('pawn', 'f1', 'f3')
        
        
        #robot.move_to(orientation = robot.get_rotated_tcp_orientation(Ry=45))


        

        #robot.move_to(robot.start_position)
        print("end of session")



