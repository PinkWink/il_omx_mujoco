"""Policy rollouts rendered for pages ⑧ ⑨ (needs the project venv and the two 30k policies).

  MUJOCO_GL=egl .venv/bin/python docs/lecture/render_lesson08_sim.py
For each (policy, cube placement): free-view frames at a few times + tcp / cube xy paths -> l08_rollouts.json
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
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
from eval import load_policy, task_config  # noqa: E402

from il_omx.env import FIXED_CUBE_POSE, OmxCubeEnv  # noqa: E402

OUT = Path(__file__).resolve().parent
RUNS = {"fixed5": "omx_cube_fixed5_act", "random50": "omx_cube_random50_act"}
CASES = [("fixed", None), ("seed1001", 1001), ("seed1035", 1035)]
SHOTS = (0.0, 2.5, 4.5, 8.0)


def main():
    out = {}
    for key, run in RUNS.items():
        path = (ROOT / "outputs/train" / run / "checkpoints/030000/pretrained_model").resolve()
        cfg = task_config(path)
        env = OmxCubeEnv(cfg)
        policy, act = load_policy(path, "cuda")
        m, d = env.model, env.data
        m.vis.global_.offwidth, m.vis.global_.offheight = 800, 560
        r = mujoco.Renderer(m, 560, 800)
        cam = mujoco.MjvCamera()
        cam.lookat[:] = (0.15, 0.03, 0.09); cam.distance, cam.azimuth, cam.elevation = 0.62, 200, -30
        for name, seed in CASES:
            obs = env.reset(seed=seed, cube_pose=FIXED_CUBE_POSE if seed is None else None)
            policy.reset()
            a = env.cube_qpos_adr
            pose = [float(d.qpos[a]), float(d.qpos[a + 1]), float(np.rad2deg(2 * np.arctan2(d.qpos[a + 6], d.qpos[a + 3])))]
            tcp, cube, success_t = [], [], None
            for t in range(round(10 * cfg.fps)):
                time = t / cfg.fps
                if any(abs(time - s) < 1e-6 for s in SHOTS):
                    r.update_scene(d, cam)
                    Image.fromarray(r.render()).save(OUT / f"l08_{key}_{name}_{int(time * 10):03d}.png")
                tcp.append(d.site("tcp").xpos[:2].round(4).tolist())
                cube.append(env.cube_pos[:2].round(4).tolist())
                obs = env.step(act(obs))
                if success_t is None and env.is_success():
                    success_t = (t + 1) / cfg.fps
            out[f"{key}_{name}"] = {"pose": pose, "success_t": success_t, "tcp": tcp, "cube": cube}
            print(key, name, [round(v, 3) for v in pose], "success at", success_t)
        r.close(); env.close()
    (OUT / "l08_rollouts.json").write_text(json.dumps(out))


if __name__ == "__main__":
    main()
