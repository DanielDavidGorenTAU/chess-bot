import time
from rtde_control import RTDEControlInterface
from rtde_receive import RTDEReceiveInterface
from robotiq_gripper import RobotiqGripper
# test dd
ROBOT_IP = "192.168.56.101"
BASE_TCP_PORT = 63352
X, Y, Z, RX, RY, RZ = 0,1,2,3,4,5
SAFE_HEIGHT= 0.15

POSITION_START = [0,0,0,0,0,0]
DOWN_ORIENTATION = [2.0107452890463056, -2.3743186369030598, -0.0762631964824858]
positions = {} # with floor height and down orientation

FLOOR_HEIGHT, SKY_HEIGHT = 0, 0 # tmp
"""
מלך, מלכה, רץ, פרש, צריח, רגלי = king, queen, bishop, knight, rook, pawn
"""

grip_height = {}

grip_size = {
    "queen": 180,
    "pawn": 190,
    "king": 180,
    "rook": 180,
    "bishop": 190,
    "knight": 190,
}

A1 = [-0.1994344966132951, -0.693638575673329, 0.026182646610849847, 0.0350689165769008, -3.1131421845178666, 0.020230491110566802]
H8 = [0.06654803495138017, -0.39829560870099523, 0.026648711861183172, 0.03507144665327432, -3.1131925402916614, 0.020182850783539992]

step_right = [0,0]
step_up = [0,0]

# make sure to call calibrate_board_positions once before use
# return a new position with right * blocks added and up * blocks added

def mov_blocks(current_pos, right, up):
    position = current_pos.copy()
    position[X] = position[X] + step_right[X] * right + step_up[X] * up
    position[Y] = position[Y] + step_right[Y] * right + step_up[Y] * up
    return position


def calibrate_board_positions(a1=A1, h8=H8):
    global SAFE_HEIGHT, grip_height,step_right, step_up, DOWN_ORIENTATION, FLOOR_HEIGHT, SKY_HEIGHT, POSITION_START, positions

    dx = h8[X] - a1[X]
    dy = h8[Y] - a1[Y]
    h1 = [a1[X] + (dx + dy) / 2.0, a1[Y] + (dy - dx) / 2.0]

    step_right[0] = (h1[X] - a1[X]) / 7.0
    step_right[1] = (h1[Y] - a1[Y]) / 7.0
    step_up[0] = -step_right[Y]
    step_up[1] = step_right[X]

    DOWN_ORIENTATION = [(h8[RX] + a1[RX]) / 2, (h8[RY] + a1[RY]) / 2, (h8[RZ] + a1[RZ]) / 2]
    FLOOR_HEIGHT = (h8[Z] + a1[Z]) / 2
    SKY_HEIGHT = FLOOR_HEIGHT + 0.3

    tmp_pos = [a1[X], a1[Y]]
    for row in range(1, 9):
        for col in "abcdefgh":
            square = f"{col}{row}"
            positions[square] = tmp_pos + [FLOOR_HEIGHT] + DOWN_ORIENTATION
            tmp_pos = mov_blocks(tmp_pos, right=1, up=0)
        tmp_pos = mov_blocks(tmp_pos, right=-8, up=1)

    POSITION_START = positions['d5'].copy()
    POSITION_START[Z] = SKY_HEIGHT

    grip_height["queen"] = FLOOR_HEIGHT + 0.04
    grip_height["pawn"] = FLOOR_HEIGHT + 0.025 
    grip_height["king"] = FLOOR_HEIGHT + 0.04
    grip_height["rook"] = FLOOR_HEIGHT + 0.025
    grip_height["knight"] = FLOOR_HEIGHT + 0
    grip_height["bishop"] = FLOOR_HEIGHT + 0
    
    SAFE_HEIGHT = 0.15 + FLOOR_HEIGHT



class ChessBot:
    def __init__(self, robot_ip="192.168.56.101", base_tcp_port=63352, speed=0.1, acceleration=0.1):
        self.robot_ip = robot_ip
        self.base_tcp_port = base_tcp_port
        self.speed = speed
        self.acceleration = acceleration
        self.rtde_c = None
        self.rtde_r = None
        self.gripper = None

    def __enter__(self):
        self.rtde_c = RTDEControlInterface(self.robot_ip)
        self.rtde_r = RTDEReceiveInterface(self.robot_ip)
        self.gripper = RobotiqGripper()
        self.gripper.connect(self.robot_ip, self.base_tcp_port)
        time.sleep(0.1)
        calibrate_board_positions(A1, H8)
        self.rtde_c.moveL(POSITION_START, self.speed, self.acceleration)
        return self

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

    def move_to(self, pose=None,
                x=None, y=None, z=None, rx=None, ry=None, rz=None,
                dx=None, dy=None, dz=None, drx=None, dry=None, drz=None):
        # Resolve base pose
        if pose is None:
            pose = self.pose

        # It's an error to mix absolute (x,y,...) and relative (dx,dy,...) params
        abs_params = any(v is not None for v in (x, y, z, rx, ry, rz))
        rel_params = any(v is not None for v in (dx, dy, dz, drx, dry, drz))
        if abs_params and rel_params:
            raise ValueError("Cannot mix absolute (x,y,z,rx,ry,rz) and relative (dx,dy,dz,drx,dry,drz) parameters")

        if abs_params:
            target_pose = self.modify_pose(pose, x=x, y=y, z=z, rx=rx, ry=ry, rz=rz)
        elif rel_params:
            target_pose = self.modify_pose_relative(pose, dx=dx, dy=dy, dz=dz, drx=drx, dry=dry, drz=drz)
        else:
            target_pose = pose.copy()

        self.rtde_c.moveL(target_pose, self.speed, self.acceleration)
        return target_pose

    def set_gripper(self, position, speed=255, force=0):
        self.gripper.move_and_wait_for_pos(position, speed, force)

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

    
    def mov_chess_piece(self, type=None, start_pos=None, end_pos=None):
        if self.pose[Z] < SAFE_HEIGHT:
            self.move_to(z=SAFE_HEIGHT)

        self.set_gripper(grip_size[type] - 20) #  release the piece

        self.move_to(start_pos, z=SAFE_HEIGHT)
        self.move_to(z=grip_height[type])

        self.set_gripper(grip_size[type]) # grip the piece

        self.move_to(start_pos, z=SAFE_HEIGHT)
        self.move_to(end_pos, z=SAFE_HEIGHT)
        self.move_to(z=grip_height[type] + 0.005)

        
        self.set_gripper(grip_size[type] - 20) # release the piece
        
        self.move_to(z=SAFE_HEIGHT)
        self.move_to(POSITION_START)

if __name__ == "__main__":
    with ChessBot() as bot:
        
        
        ''' bot.set_gripper(PAWN_GRIP_SIZE - 20)
        bot.move_to(positions["g7"], dz=SAFE_HEIGHT)
        bot.move_to(positions["g7"], dz=PAWN_GRIP_HEIGHT)

        bot.set_gripper(PAWN_GRIP_SIZE)
        bot.move_to(positions["g7"], dz=SAFE_HEIGHT)
        bot.move_to(POSITION_START)
        bot.set_gripper(0)'''

        #bot.mov_chess_piece('rook', positions["c8"], positions["c2"])
        bot.set_gripper(255)

