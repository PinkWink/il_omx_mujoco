"""A short tour of OmxCubeEnv (page ③): reset, observation, step, success check.

  MUJOCO_GL=egl .venv/bin/python docs/lecture/env_tour.py
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np  # noqa: E402

from il_omx.env import FIXED_CUBE_POSE, JOINT_NAMES, OmxCubeEnv  # noqa: E402

np.set_printoptions(precision=3, suppress=True)
env = OmxCubeEnv()
m = env.model
print(f"physics dt {m.opt.timestep} s x {env.n_substeps} substeps = control {1 / env.cfg.fps:.1f} s ({env.cfg.fps} Hz)")
print("joints:", JOINT_NAMES)
print("ctrl range (deg):", np.rad2deg(env.ctrl_low).round(), "~", np.rad2deg(env.ctrl_high).round())

obs = env.reset(cube_pose=FIXED_CUBE_POSE)
print("\nreset(cube_pose=FIXED_CUBE_POSE)")
for k, v in obs.items():
    print(f"  obs[{k!r}]: shape {v.shape}, dtype {v.dtype}")
print("  state (rad):", obs["state"])
print("  cube position (m):", env.cube_pos, " success:", env.is_success())

target = obs["state"].copy()
target[0] += np.deg2rad(30)             # turn Joint1 by 30 deg
for _ in range(10):                     # 10 control steps = 1 s
    obs = env.step(target)
print("\nstep() x 10 with Joint1 +30 deg")
print("  state (deg):", np.rad2deg(obs["state"]).round(1), " sim time", round(env.data.time, 2), "s")

for name, offset in [("tray center", (0, 0)), ("tray, 22 mm off center", (0.022, 0))]:
    tray = env.data.xpos[env.tray_body]
    obs = env.reset(cube_pose=(tray[0] + offset[0], tray[1] + offset[1], 0.0))
    env.data.qpos[env.cube_qpos_adr + 2] += 0.002   # start above the 2 mm tray floor, then settle
    for _ in range(5):
        env.step(obs["state"])
    print(f"\ncube placed at {name}: cube {env.cube_pos}  success: {env.is_success()}")
env.close()
