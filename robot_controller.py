"""
Simple RobotController using ur_rtde (RTDE) for Universal Robots.
This file provides a minimal, safe-to-read example. Adjust IPs and motions
for your robot and network setup before running on hardware.
"""

from rtde_control import RTDEControlInterface
from rtde_receive import RTDEReceiveInterface
import time


class RobotController:
    """Minimal controller wrapper around rtde_control / rtde_receive.

    Usage:
        rc = RobotController("192.168.0.1")
        rc.connect()
        q = rc.get_joint_positions()
        rc.move_joints([0, -1.57, 0, -1.57, 0, 0])
        rc.disconnect()
    """

    def __init__(self, host: str):
        self.host = host
        self.rc = None
        self.rr = None

    def connect(self, timeout: float = 5.0):
        """Open RTDE control and receive interfaces."""
        self.rc = RTDEControlInterface(self.host)
        self.rr = RTDEReceiveInterface(self.host)
        # small delay to ensure variables stream
        time.sleep(0.1)

    def disconnect(self):
        """Try to cleanly close interfaces."""
        try:
            if self.rc is not None:
                try:
                    self.rc.disconnect()
                except Exception:
                    pass
                self.rc = None
            if self.rr is not None:
                try:
                    self.rr.disconnect()
                except Exception:
                    pass
                self.rr = None
        except Exception:
            pass

    def get_joint_positions(self):
        """Return current joint positions (radians) as list of 6 floats."""
        if self.rr is None:
            raise RuntimeError("Not connected: call connect() first")
        return self.rr.getActualQ()

    def get_tcp_pose(self):
        """Return current TCP pose as [x,y,z,rx,ry,rz]."""
        if self.rr is None:
            raise RuntimeError("Not connected: call connect() first")
        return self.rr.getActualTCPPose()

    def move_joints(self, joints, speed=0.5, acceleration=0.5):
        """Move to target joint positions using moveJ.

        joints: iterable of 6 floats (radians)
        speed: joint speed fraction (0..1) or absolute speed depending on setup
        acceleration: acceleration value (robot units)
        """
        if self.rc is None:
            raise RuntimeError("Not connected: call connect() first")
        return self.rc.moveJ(joints, speed, acceleration)

    def move_pose(self, pose, speed=0.25, acceleration=0.25):
        """Linear move to TCP pose using moveL.

        pose: [x,y,z,rx,ry,rz]
        """
        if self.rc is None:
            raise RuntimeError("Not connected: call connect() first")
        return self.rc.moveL(pose, speed, acceleration)


if __name__ == "__main__":
    import os
    ip = os.environ.get("UR_RTDE_IP", "192.168.0.1")
    print(f"This module provides RobotController. Use examples/run_demo.py to demo (UR IP={ip}).")
