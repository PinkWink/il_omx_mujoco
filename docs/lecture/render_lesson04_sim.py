"""MuJoCo renders for page ④: leader readings mapped onto the sim arm (needs the project venv).

  MUJOCO_GL=egl .venv/bin/python docs/lecture/render_lesson04_sim.py
"""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")
import mujoco
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from il_omx.env import FIXED_CUBE_POSE, OmxCubeEnv, TaskConfig  # noqa: E402
from il_omx.leader_mapping import ARM_MOTORS, LeaderToSim  # noqa: E402

OUT = Path(__file__).resolve().parent

# leader_read.py output on 2026-10-10 (leader resting folded on the desk, trigger released).
REST = {"shoulder_pan": 3.10, "shoulder_lift": -66.54, "elbow_flex": 54.48, "wrist_flex": 46.62,
        "wrist_roll": 0.85, "gripper": 59.85}
ZERO = {m: 0.0 for m in ARM_MOTORS} | {"gripper": 50.0}
SQUEEZED = REST | {"gripper": 47.0}


def pose(env, values):
    action = {f"{k}.pos": v for k, v in values.items()}
    raw = LeaderToSim()(action)
    q = np.clip(raw, env.ctrl_low, env.ctrl_high)
    env.reset(cube_pose=FIXED_CUBE_POSE, arm_q=q, render=False)
    return raw, q


def shot(env, name):
    m, d = env.model, env.data
    m.vis.global_.offwidth, m.vis.global_.offheight = 1200, 800
    r = mujoco.Renderer(m, 800, 1200)
    cam = mujoco.MjvCamera()
    cam.lookat[:] = (0.08, 0, 0.1)
    cam.distance, cam.azimuth, cam.elevation = 0.6, 270, -8
    r.update_scene(d, cam)
    Image.fromarray(r.render()).save(OUT / name)
    r.close()
    print("saved", name)


def main():
    env = OmxCubeEnv(TaskConfig(), render=False)
    out = {}
    for name, values in (("zero", ZERO), ("rest", REST), ("squeezed", SQUEEZED)):
        raw, q = pose(env, values)
        out[name] = {"leader": values, "sim_deg": np.rad2deg(raw).round(1).tolist(),
                     "sim_clipped_deg": np.rad2deg(q).round(1).tolist()}
        if name != "squeezed":
            shot(env, f"l04_sim_{name}.png")
    (OUT / "l04_data.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
