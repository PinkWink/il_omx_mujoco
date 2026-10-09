"""Teleoperate the simulated OMX follower with the real OMX leader arm (practice, no recording).

The follower's position actuators track the leader at the recording rate (10 Hz), so practice
feels the same as recording, and the arm can grasp the cube.
The global and wrist camera images (what the policy will see) are shown on the right.
Press ENTER in the viewer for a new episode (new cube position). SUCCESS shows once the cube
rests in the tray and the gripper has let go. BACKSPACE (the viewer's own simulation reset) also
starts a new episode, with the arm placed at the leader's pose.

  python scripts/teleop.py [--port /dev/ttyACM0] [--camera-fps 10]

Lower --camera-fps on slow PCs (0 turns the camera views off); control stays at 10 Hz.
"""
import argparse
import os
import sys
import threading
import time

# Offscreen camera rendering uses EGL so it does not clash with the viewer's GLFW window.
os.environ.setdefault("MUJOCO_GL", "egl")

import mujoco

from il_omx.env import CAMERA_NAMES, OmxCubeEnv, TaskConfig
from il_omx.leader import DEFAULT_PORT, connect_leader
from il_omx.leader_mapping import LeaderToSim
from il_omx.teleop_ui import ENTER_KEYS, open_viewer, status_line


class Episodes:
    """Episode counter, timer and latched success for the on-screen overlay."""

    def __init__(self):
        self.index = 0
        self.successes = 0
        self.start = time.perf_counter()
        self.success_time = None

    def new(self):
        self.index += 1
        self.start = time.perf_counter()
        self.success_time = None

    def update(self, success: bool):
        if success and self.success_time is None:
            self.success_time = time.perf_counter() - self.start
            self.successes += 1

    def texts(self) -> list:
        done = self.success_time is not None
        elapsed = self.success_time if done else time.perf_counter() - self.start
        font, grid = mujoco.mjtFontScale, mujoco.mjtGridPos
        texts = [
            (font.mjFONTSCALE_150, grid.mjGRID_TOPLEFT,
             "Episode\nTime\nSuccess",
             f"{self.index + 1}\n{elapsed:.1f} s\n{self.successes} / {self.index + done}"),
            (font.mjFONTSCALE_150, grid.mjGRID_BOTTOMLEFT, "ENTER / BACKSPACE: new episode", None),
        ]
        return texts

    def banner(self) -> str | None:
        return None if self.success_time is None else f"SUCCESS  {self.success_time:.1f} s"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", default=DEFAULT_PORT)
    p.add_argument("--camera-fps", type=float, default=float(TaskConfig.fps),
                   help="camera view refresh rate; lower it on slow PCs, 0 = off")
    p.add_argument("--headless", action="store_true", help="no viewer (for testing)")
    p.add_argument("--duration", type=float, default=0.0, help="stop after N seconds (0 = forever)")
    args = p.parse_args()

    leader = connect_leader(args.port)
    mapper = LeaderToSim()
    cameras_on = args.camera_fps > 0
    env = OmxCubeEnv(TaskConfig(), render=cameras_on)
    env.reset(arm_q=mapper(leader.get_action()), render=False)
    dt = 1.0 / env.cfg.fps
    camera_dt = 1.0 / args.camera_fps if cameras_on else float("inf")

    episodes = Episodes()
    reset_event = threading.Event()

    def on_key(keycode):
        if keycode in ENTER_KEYS:
            reset_event.set()

    viewer = overlay = None
    if not args.headless:
        viewer, overlay = open_viewer(env, key_callback=on_key)

    t_start = last_print = time.perf_counter()
    last_camera = -float("inf")
    sim_time = env.data.time
    camera_frames = 0
    try:
        while viewer is None or viewer.is_running():
            t0 = time.perf_counter()
            if args.duration and t0 - t_start > args.duration:
                break
            action = leader.get_action()
            target = mapper(action)
            render = t0 - last_camera >= camera_dt - 0.5 * dt  # tolerate loop jitter

            if viewer is not None:
                with viewer.lock():
                    # BACKSPACE makes the viewer reset the simulation (at the next sync); turn that
                    # into a proper new episode so the arm does not snap away from the leader.
                    if reset_event.is_set() or env.data.time < sim_time:
                        reset_event.clear()
                        episodes.new()
                        obs = env.reset(arm_q=target, render=render)
                    else:
                        obs = env.step(target, render=render)
                    sim_time = env.data.time
                    episodes.update(env.is_success())
                if render:
                    overlay.set_cameras({cam: obs[cam] for cam in CAMERA_NAMES})
                overlay.set_banner(episodes.banner())
                overlay.flush()
                viewer.set_texts(episodes.texts())
                viewer.sync()
            else:
                env.step(target, render=render)
            if render:
                last_camera = t0
                camera_frames += 1
            loop_ms = (time.perf_counter() - t0) * 1e3

            if t0 - last_print > 0.5:
                camera_fps = camera_frames / (t0 - last_print)
                sys.stdout.write("\r" + status_line(action, target, env)
                                 + f"  [{loop_ms:4.1f} ms, camera {camera_fps:4.1f} fps]  ")
                sys.stdout.flush()
                last_print = t0
                camera_frames = 0
            time.sleep(max(0.0, dt - (time.perf_counter() - t0)))
    except KeyboardInterrupt:
        pass
    finally:
        print()
        if viewer is not None:
            viewer.close()
        leader.disconnect()
        env.close()


if __name__ == "__main__":
    main()
