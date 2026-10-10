"""Record teleoperated demos into a local LeRobotDataset (data/<dataset>, git-ignored, never uploaded).

Viewer controls (click the viewer window first so it has keyboard focus):
  ENTER  idle      -> new cube position (same one with --fixed-cube), start recording
  ENTER      recording -> cancel and discard the episode
  BACKSPACE  idle      -> delete the episode saved last in this session (once, e.g. a sloppy demo)
  BACKSPACE  recording -> discard the episode (the viewer also resets the simulation on BACKSPACE)
A successful episode (cube resting in the tray, gripper released) is saved automatically after a
short post-roll. Episodes longer than --max-episode-s are discarded. Only successful demos are kept.

  python scripts/record.py [--dataset omx_cube_to_tray] [--num-episodes 50] [--fps 10]
  python scripts/record.py --dataset my_fixed5 --num-episodes 5 --fixed-cube   # cube never moves

The simulation advances exactly 1/fps per recorded frame, so the data stays consistent even if a
slow PC cannot keep up in real time (the teleop just feels slower). Lower --fps on slow PCs.
Running again with the same --dataset appends episodes. Each saved episode is finalized on disk
right away, so closing the terminal or a crash loses at most the episode being recorded.
"""
import argparse
import os
import sys
import threading
import time

# Offscreen camera rendering uses EGL so it does not clash with the viewer's GLFW window.
os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("SVT_LOG", "1")  # keep the AV1 encoder's info logs out of the terminal

import mujoco
import numpy as np

from il_omx.dataset import DATA_DIR, EpisodeRecorder
from il_omx.env import (
    CAMERA_NAMES,
    OmxCubeEnv,
    TaskConfig,
    add_cube_args,
    cube_pose_from_args,
    describe_cube,
)
from il_omx.leader import DEFAULT_PORT, connect_leader
from il_omx.leader_mapping import LeaderToSim
from il_omx.teleop_ui import BACKSPACE_KEY, ENTER_KEYS, open_viewer, status_line
from il_omx.viewer_overlay import GRAY, GREEN, RED

POST_ROLL_S = 0.5  # keep recording briefly after success so the release is in the demo
NOTICE_S = 2.0     # how long "SAVED" / "DISCARDED" notices stay on screen


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", default=DEFAULT_PORT)
    p.add_argument("--dataset", default="omx_cube_to_tray", help=f"folder name under {DATA_DIR}")
    p.add_argument("--num-episodes", type=int, default=50, help="stop accepting new episodes after this many")
    p.add_argument("--fps", type=int, default=TaskConfig.fps, help="control and recording rate")
    p.add_argument("--image-height", type=int, default=TaskConfig.image_height)
    p.add_argument("--image-width", type=int, default=TaskConfig.image_width)
    p.add_argument("--max-episode-s", type=float, default=60.0)
    add_cube_args(p)
    p.add_argument("--streaming-encoding", action="store_true",
                   help="encode video while recording (faster saving, needs a capable CPU)")
    args = p.parse_args()

    recorder = EpisodeRecorder(args.dataset, args.fps, args.image_height, args.image_width,
                               args.streaming_encoding)
    print(f"dataset: {recorder.root}  ({recorder.num_episodes} episodes already)")

    leader = connect_leader(args.port)
    mapper = LeaderToSim()
    env = OmxCubeEnv(TaskConfig(fps=args.fps, image_height=args.image_height, image_width=args.image_width))
    cube_pose = cube_pose_from_args(args)
    print(f"cube: {describe_cube(cube_pose)}")
    obs = env.reset(arm_q=mapper(leader.get_action()), cube_pose=cube_pose)
    dt = 1.0 / env.cfg.fps

    enter, backspace = threading.Event(), threading.Event()

    def on_key(key):
        if key in ENTER_KEYS:
            enter.set()
        elif key == BACKSPACE_KEY:
            backspace.set()

    viewer, overlay = open_viewer(env, key_callback=on_key)

    recording = False
    success_frame = None
    notice, notice_until = None, 0.0
    saved_this_session = 0
    can_delete = False  # the newest episode was saved in this session and not deleted yet
    sim_time = env.data.time
    font, grid = mujoco.mjtFontScale, mujoco.mjtGridPos
    last_print = time.perf_counter()

    def set_notice(text, color):
        nonlocal notice, notice_until
        notice, notice_until = (text, color), time.perf_counter() + NOTICE_S

    try:
        while viewer.is_running():
            t0 = time.perf_counter()
            action = leader.get_action()
            target = np.clip(mapper(action), env.ctrl_low, env.ctrl_high)

            finish = None  # (save, reason) once the episode ends this frame
            with viewer.lock():
                # The viewer resets the simulation on BACKSPACE (at the next sync). Restore a proper
                # episode start, and drop a recording in progress since its frames are now broken.
                if env.data.time < sim_time:
                    obs = env.reset(arm_q=target, cube_pose=cube_pose)
                    if recording:
                        backspace.clear()  # this press cancels the episode; it must not delete a saved one
                        finish = (False, "backspace")

                if enter.is_set() and finish is None:
                    enter.clear()
                    if recording:
                        finish = (False, "cancelled")
                    elif recorder.num_episodes < args.num_episodes:
                        obs = env.reset(arm_q=target, cube_pose=cube_pose)
                        recording, success_frame = True, None

                if recording and finish is None:
                    recorder.add(obs, target)  # observation at t + action applied at t
                obs = env.step(target)
                sim_time = env.data.time

                if recording and finish is None:
                    if success_frame is None and env.is_success():
                        success_frame = recorder.frames
                    if success_frame is not None and recorder.frames - success_frame >= POST_ROLL_S * args.fps:
                        finish = (True, "success")
                    elif recorder.frames >= args.max_episode_s * args.fps:
                        finish = (False, "time limit")

            if backspace.is_set():
                backspace.clear()
                if not recording and can_delete:
                    overlay.set_banner("DELETING ...", GRAY)
                    overlay.flush()
                    viewer.sync()
                    deleted = recorder.num_episodes
                    recorder.delete_last()
                    saved_this_session -= 1
                    can_delete = False
                    set_notice(f"DELETED  episode {deleted}", RED)
                    print(f"\ndeleted episode {deleted}")

            # Saving blocks for a moment, so it happens outside the viewer lock.
            if finish is not None:
                save, reason = finish
                recording = False
                n_frames = recorder.frames
                if save:
                    overlay.set_banner("SAVING ...", GRAY)
                    overlay.flush()
                    viewer.sync()
                    recorder.save()
                    saved_this_session += 1
                    can_delete = True
                    set_notice(f"SAVED  episode {recorder.num_episodes}", GREEN)
                else:
                    recorder.discard()
                    set_notice(f"DISCARDED  ({reason})", GRAY)
                print(f"\n{'saved' if save else 'discarded'} ({reason}), {n_frames} frames")

            if recording:
                banner = (f"REC  {recorder.frames / args.fps:4.1f} s" + ("  OK" if success_frame is not None else ""),
                          GREEN if success_frame is not None else RED)
            elif time.perf_counter() < notice_until:
                banner = notice
            elif recorder.num_episodes >= args.num_episodes:
                banner = ("DONE  -  close the window", GREEN)
            else:
                banner = (None, GREEN)
            overlay.set_banner(*banner)
            overlay.set_cameras({cam: obs[cam] for cam in CAMERA_NAMES})
            overlay.flush()
            if recording:
                hint = "ENTER: cancel episode"
            elif can_delete:
                hint = f"ENTER: start recording\nBACKSPACE: delete episode {recorder.num_episodes}"
            else:
                hint = "ENTER: start recording"
            viewer.set_texts([
                (font.mjFONTSCALE_150, grid.mjGRID_TOPLEFT, "Dataset\nSaved\nThis session",
                 f"{args.dataset}\n{recorder.num_episodes} / {args.num_episodes}\n{saved_this_session}"),
                (font.mjFONTSCALE_150, grid.mjGRID_BOTTOMLEFT, hint, None),
            ])
            viewer.sync()

            loop_ms = (time.perf_counter() - t0) * 1e3
            if t0 - last_print > 0.5:
                slow = "  SLOW: sim runs slower than real time" if loop_ms > dt * 1e3 else ""
                sys.stdout.write("\r" + status_line(action, target, env) + f"  [{loop_ms:4.1f} ms]{slow}   ")
                sys.stdout.flush()
                last_print = t0
            time.sleep(max(0.0, dt - (time.perf_counter() - t0)))
    except KeyboardInterrupt:
        pass
    finally:
        print()
        recorder.close()
        print(f"dataset: {recorder.root}  ({recorder.num_episodes} episodes)")
        viewer.close()
        leader.disconnect()
        env.close()


if __name__ == "__main__":
    main()
