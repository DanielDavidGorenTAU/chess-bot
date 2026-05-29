import sys
import time
from rtde_control import RTDEControlInterface
from rtde_receive import RTDEReceiveInterface
#from rtde_io import RTDEIOInterface 
from robotiq_gripper import RobotiqGripper



ROBOT_IP = "192.168.56.101"
BASE_TCP_PORT = 63352
X, Y, Z, RX, RY, RZ = 0,1,2,3,4,5
SAFE_HEIGHT= 0.15

POSITION_START = [0,0,0,0,0,0]
DOWN_ORIENTATION = [2.0107452890463056, -2.3743186369030598, -0.0762631964824858]
positions = {} # with floor height and down orientation

FLOOR_HEIGHT, SKY_HEIGHT = 0, 0 # tmp
###################################################################################### fill
KING_GRIP_HEIGHT ,UEEN_GRIP_HEIGHT, ROOK_GRIP_HEIGHT = 0, 0, 0 # מלך, מלכה, צריח
BISHOP_GRIP_HEIGHT, KNIGHT_GRIP_HEIGHT, PAWN_GRIP_HEIGHT = 0, 0, 0.025 # חץ, פרש, חייל
###################################################################################### fill
KING_GRIP_SIZE, QUEEN_GRIP_SIZE, ROOK_GRIP_SIZE = 0, 0, 0
BISHOP_GRIP_SIZE, KNIGHT_GRIP_SIZE, PAWN_GRIP_SIZE = 0, 0, 190



tmp  = [-0.336678047173925, 0.18697748211123463, -0.2170342321916081, 2.0107452890463056, -2.3743186369030598, -0.0762631964824858] # tmp
A1 = [-0.1994344966132951, -0.693638575673329, 0.026182646610849847, 0.0350689165769008, -3.1131421845178666, 0.020230491110566802]
H8 = [0.06654803495138017, -0.39829560870099523, 0.026648711861183172, 0.03507144665327432, -3.1131925402916614, 0.020182850783539992]

step_right = [0,0]
step_up = [0,0]

# make sure to call calibrate_board_positions once before use
# return a new postion with right * blocks added and up * blocks added
def mov_blocks(current_pos, right, up):
    position = current_pos.copy()
    position[X] = position[X] + step_right[X] * right + step_up[X] * up
    position[Y] = position[Y] + step_right[Y] * right + step_up[Y] * up
    return position



def calibrate_board_positions(a1 = tmp, h8 = tmp):
    global step_right, step_up, DOWN_ORIENTATION, FLOOR_HEIGHT, SKY_HEIGHT, POSITION_START, positions

    # calculate h1 based on a1, h8
    dx = h8[X] - a1[X]
    dy = h8[Y] - a1[Y]
    h1 = [a1[X] + (dx + dy) / 2.0, a1[Y] + (dy - dx) / 2.0]
    
    step_right = [(h1[X] - a1[X]) / 7.0, (h1[Y] - a1[Y]) / 7.0]
    step_up = [-step_right[Y], step_right[X]] 

    DOWN_ORIENTATION = [(h8[RX] + a1[RX]) /2, (h8[RY] + a1[RY]) /2, (h8[RZ] + a1[RZ]) /2] # avg
    FLOOR_HEIGHT = (h8[Z] + a1[Z]) / 2 # avg
    SKY_HEIGHT = FLOOR_HEIGHT + 0.3

    tmp_pos = [a1[X], a1[Y]]
    for row in range(1, 9):
        for col in "abcdefgh":
            square = f"{col}{row}"
            positions[square] = tmp_pos  + [FLOOR_HEIGHT] + DOWN_ORIENTATION
            tmp_pos = mov_blocks(tmp_pos, right = 1, up = 0)  # step 1 block right
        tmp_pos = mov_blocks(tmp_pos, right = -8, up = 1) # step 8 block left and 1 up

    POSITION_START = positions['d5'].copy()
    POSITION_START[Z] = SKY_HEIGHT

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

def modify_pose_relative(pose, x=None, y=None, z=None, rx=None, ry=None, rz=None):
    modified = pose.copy()
    if x is not None:
        modified[X] += x
    if y is not None:
        modified[Y] += y
    if z is not None:
        modified[Z] += z
    if rx is not None:
        modified[RX] += rx
    if ry is not None:
        modified[RY] += ry
    if rz is not None:
        modified[RZ] += rz
    return modified

def main(action=None):
    def up_move_down(dest, vertical=0.10, speed=0.05, acceleration=0.1):
        current_pose = rtde_r.getActualTCPPose()
        if current_pose[Z] < dest[Z] + vertical:
            pose1 = modify_pose_relative(current_pose, z=vertical)
            rtde_c.moveL(pose1, speed, acceleration)
        pose2 = modify_pose_relative(dest, z=vertical)
        rtde_c.moveL(pose2, speed, acceleration)
        rtde_c.moveL(dest, speed, acceleration)

    rtde_c = RTDEControlInterface(ROBOT_IP)
    rtde_r = RTDEReceiveInterface(ROBOT_IP)
    #rtde_io = RTDEIOInterface(ROBOT_IP)
    gripper = RobotiqGripper()
    calibrate_board_positions(A1, H8)
    rtde_c.moveL(POSITION_START, 0.1, 0.1)
    gripper.connect(ROBOT_IP, BASE_TCP_PORT)
    gripper.activate()
    time.sleep(0.1)


    try:
        

        #up_move_down(positions['d4'])
        #current_pose = rtde_r.getActualTCPPose()
        #print(current_pose)
        #rtde_c.moveL(POSITION_START, 0.05, 0.1)
        gripper.move_and_wait_for_pos(PAWN_GRIP_SIZE - 20,255,255)
        rtde_c.moveL(modify_pose_relative(positions["g7"], z=SAFE_HEIGHT), 0.1, 0.1)
        rtde_c.moveL(modify_pose_relative(positions["g7"], z=PAWN_GRIP_HEIGHT), 0.1, 0.1)



        gripper.move_and_wait_for_pos(PAWN_GRIP_SIZE,255,255)
        rtde_c.moveL(modify_pose_relative(positions["g7"], z=SAFE_HEIGHT), 0.1, 0.1)
        rtde_c.moveL(POSITION_START, 0.1, 0.1)
        gripper.move_and_wait_for_pos(0,255,255)
        
        











        #rtde_c.moveL(tmp, 0.05, 0.1)
        #current_pose = rtde_r.getActualTCPPose()
        #new_pose = current_pose.copy()
        #new_pose[2] -= 0.2
        #rtde_c.moveL(new_pose, 0.05, 0.1)
        
        # get down
        #current_pose = rtde_r.getActualTCPPose()
        
        #new_pose = big_arm_base.copy()
        #new_pose[2] -= 0.1
        #rtde_c.moveL(new_pose, 0.05, 0.1)
        # grip soldier
        #gripper.move_and_wait_for_pos(190,255,255) # soldier size
        #move up
        #current_pose = rtde_r.getActualTCPPose()
        #new_pose = current_pose.copy()
        #new_pose[2] += 0.1
        #rtde_c.moveL(new_pose, 0.05, 0.1)

        #print("11")
        #time.sleep(1.0)
        #gripper.move_and_wait_for_pos(0,255,255)
        #print("11")
        #time.sleep(1.0)
        #print("22")
        
        

    finally:
        rtde_c.stopScript()
        gripper.disconnect()
        rtde_c.disconnect()
        rtde_r.disconnect()
        


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    main(arg)
