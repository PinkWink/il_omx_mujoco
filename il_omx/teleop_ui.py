"""Shared pieces of the teleop and recording front ends."""
import mujoco
import mujoco.viewer
import numpy as np

from il_omx.env import OmxCubeEnv
from il_omx.leader_mapping import LeaderToSim
from il_omx.viewer_overlay import ViewerOverlay, set_workspace_camera

ENTER_KEYS = {257, 335}  # GLFW Enter, keypad Enter (every letter key is already bound by the viewer)
BACKSPACE_KEY = 259  # the viewer also resets the simulation on it; callers must restore their state


def open_viewer(env: OmxCubeEnv, key_callback=None):
    """Passive viewer looking at the workspace from behind the robot, plus its image overlay."""
    # The image overlays are only drawn while a UI panel is shown, so keep the slim right one.
    viewer = mujoco.viewer.launch_passive(env.model, env.data, key_callback=key_callback,
                                          show_left_ui=False, show_right_ui=True)
    set_workspace_camera(viewer)
    return viewer, ViewerOverlay(viewer)


def status_line(action: dict, target: np.ndarray, env: OmxCubeEnv) -> str:
    """Leader deg -> sim target deg per joint; '!' marks targets clipped by the sim joint range."""
    leader = LeaderToSim.leader_deg(action)
    sim = np.rad2deg(target)
    low, high = np.rad2deg(env.ctrl_low), np.rad2deg(env.ctrl_high)
    cols = []
    for i in range(5):
        clip = "!" if not low[i] <= sim[i] <= high[i] else " "
        cols.append(f"J{i + 1} {leader[i]:+6.1f}->{sim[i]:+6.1f}{clip}")
    cols.append(f"G {action['gripper.pos']:5.1f}->{sim[5]:+5.1f}")
    return "  ".join(cols)
