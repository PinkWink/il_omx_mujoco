"""Offscreen MuJoCo renders for the lecture pages (needs the project venv, not the system python).

  MUJOCO_GL=egl .venv/bin/python docs/lecture/render_sim.py      # writes docs/lecture/sim_*.png
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")
import mujoco
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from il_omx.env import FIXED_CUBE_POSE, OmxCubeEnv, TaskConfig  # noqa: E402

OUT = Path(__file__).resolve().parent


def free_view(env, w, h, lookat, distance, azimuth, elevation):
    """Render the current state from a free camera."""
    r = mujoco.Renderer(env.model, h, w)
    cam = mujoco.MjvCamera()
    cam.lookat[:] = lookat
    cam.distance, cam.azimuth, cam.elevation = distance, azimuth, elevation
    r.update_scene(env.data, cam)
    img = r.render()
    r.close()
    return img


def save(img, name):
    Image.fromarray(img).save(OUT / name)
    print("saved", name)


def main():
    env = OmxCubeEnv(TaskConfig())
    obs = env.reset(cube_pose=FIXED_CUBE_POSE)
    env.model.vis.global_.offwidth, env.model.vis.global_.offheight = 1600, 1000
    save(free_view(env, 1600, 1000, (0.14, 0.03, 0.06), 0.62, 215, -32), "sim_scene.png")
    save(obs["global"], "sim_cam_global.png")   # what the policy sees, at the training size (320x240)
    save(obs["wrist"], "sim_cam_wrist.png")


if __name__ == "__main__":
    main()
