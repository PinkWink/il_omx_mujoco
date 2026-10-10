"""Scripted IK pick-and-place: checks the task is solvable, and can record demos without a leader.

  python scripts/scripted_pick_place.py --episodes 10 [--video outputs/scripted.mp4]
  python scripts/scripted_pick_place.py --episodes 30 --dataset scripted_demos

Every episode gets a new random cube position and yaw (seeded by --seed + episode number),
unless --cube-pose X Y YAW_DEG fixes it.
With --dataset, successful episodes are recorded like scripts/record.py does (same fps, image
size and frame layout) into data/<dataset>; failed ones are skipped.
"""
import argparse
import os
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("SVT_LOG", "1")

import numpy as np

from il_omx.env import (
    OmxCubeEnv,
    TaskConfig,
    add_cube_args,
    cube_pose_from_args,
    describe_cube,
)
from il_omx.ik import OmxIK, top_down_rotation

GRIP_OPEN = 0.6
GRIP_CLOSED = 0.0
POST_ROLL_S = 0.5  # same as scripts/record.py
SETTLE_MAX_S = 2.0  # wait this long at most for the cube to come to rest in the tray


def grasp_yaw(cube_yaw: float, joint1_yaw: float) -> float:
    """Pick the cube face pair whose normal is closest to the arm's sideways direction."""
    base = joint1_yaw + np.pi / 2
    k = np.round((base - cube_yaw) / (np.pi / 2))
    return cube_yaw + k * np.pi / 2


def plan(env: OmxCubeEnv, ik: OmxIK, cube_yaw: float):
    """Return a list of (arm_q, gripper, n_steps) segments; n_steps follow the env fps."""
    cube = env.cube_pos
    tray = env.data.xpos[env.tray_body].copy()
    yaw_c = grasp_yaw(cube_yaw, np.arctan2(cube[1], cube[0]))
    yaw_t = grasp_yaw(cube_yaw, np.arctan2(tray[1], tray[0]))
    waypoints = [
        (cube + [0, 0, 0.08], yaw_c, GRIP_OPEN, 1.3),   # duration in seconds
        (cube + [0, 0, 0.005], yaw_c, GRIP_OPEN, 1.0),
        (cube + [0, 0, 0.005], yaw_c, GRIP_CLOSED, 0.7),
        (cube + [0, 0, 0.10], yaw_c, GRIP_CLOSED, 1.0),
        (tray + [0, 0, 0.10], yaw_t, GRIP_CLOSED, 1.3),
        (tray + [0, 0, 0.05], yaw_t, GRIP_CLOSED, 0.7),
        (tray + [0, 0, 0.05], yaw_t, GRIP_OPEN, 0.5),
        (tray + [0, 0, 0.12], yaw_t, GRIP_OPEN, 0.7),
    ]
    q = env.data.qpos[:5].copy()
    segments = []
    for pos, yaw, grip, seconds in waypoints:
        q, err = ik.solve(q, pos, top_down_rotation(yaw))
        if err > 5e-3:
            print(f"  IK error {err * 1000:.1f} mm at {np.round(pos, 3)}")
        segments.append((q.copy(), grip, max(1, round(seconds * env.cfg.fps))))
    return segments


def run_episode(env, ik, seed, frames=None, recorder=None, cube_pose=None):
    """One scripted episode. frames collects video frames, recorder (EpisodeRecorder) the demo."""
    obs = env.reset(seed=seed, cube_pose=cube_pose)
    a = env.cube_qpos_adr
    w, z = env.data.qpos[a + 3], env.data.qpos[a + 6]
    cube_yaw = 2 * np.arctan2(z, w)
    action = env.data.ctrl[env.actuator_ids].copy()

    def step(action):
        nonlocal obs
        if recorder is not None:
            recorder.add(obs, action)  # observation at t + action applied at t
        obs = env.step(action)
        if frames is not None:
            frames.append(np.concatenate([obs["global"], obs["wrist"]], axis=1))

    for q_goal, grip, n in plan(env, ik, cube_yaw):
        start = action.copy()
        goal = np.append(q_goal, grip)
        for i in range(n):
            action = start + (goal - start) * (i + 1) / n
            step(action)
    # Hold still until the cube rests in the tray, then a short post-roll like record.py.
    fps = env.cfg.fps
    for _ in range(round(SETTLE_MAX_S * fps)):
        if env.is_success():
            break
        step(action)
    success = env.is_success()
    if success:
        for _ in range(round(POST_ROLL_S * fps)):
            step(action)
    return success


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--episodes", type=int, default=10)
    p.add_argument("--seed", type=int, default=0, help="episode i uses cube seed (seed + i)")
    add_cube_args(p)
    p.add_argument("--video", default=None)
    p.add_argument("--dataset", default=None, help="record successful episodes into data/<dataset>")
    args = p.parse_args()

    cfg = TaskConfig()
    env = OmxCubeEnv(cfg, render=args.video is not None or args.dataset is not None)
    ik = OmxIK(env.model)
    frames = [] if args.video else None
    recorder = None
    if args.dataset:
        from il_omx.dataset import EpisodeRecorder
        recorder = EpisodeRecorder(args.dataset, cfg.fps, cfg.image_height, cfg.image_width)
        print(f"dataset: {recorder.root}  ({recorder.num_episodes} episodes already)")
    cube_pose = cube_pose_from_args(args)
    print(f"cube: {describe_cube(cube_pose)}")
    successes = 0
    for ep in range(args.episodes):
        ok = run_episode(env, ik, seed=args.seed + ep, frames=frames, recorder=recorder, cube_pose=cube_pose)
        successes += ok
        if recorder is not None:
            n = recorder.frames
            recorder.save() if ok else recorder.discard()
            print(f"episode {ep}: {'saved' if ok else 'FAILED, discarded'} ({n} frames)  "
                  f"cube={np.round(env.cube_pos, 3)}")
        else:
            print(f"episode {ep}: {'success' if ok else 'fail'}  cube={np.round(env.cube_pos, 3)}")
    print(f"success rate: {successes}/{args.episodes}")
    if recorder is not None:
        recorder.close()
        print(f"dataset: {recorder.root}  ({recorder.num_episodes} episodes)")

    if frames:
        import imageio.v2 as imageio
        Path(args.video).parent.mkdir(parents=True, exist_ok=True)
        imageio.mimsave(args.video, frames, fps=env.cfg.fps)
        print("video saved to", args.video)
    env.close()


if __name__ == "__main__":
    main()
