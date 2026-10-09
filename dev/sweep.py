"""Generalization sweep around the fixed training pose. Usage: sweep.py <pretrained_model> <out.json>"""
import os, sys, json
os.environ.setdefault("MUJOCO_GL", "egl")
sys.path.insert(0, "scripts")
import numpy as np
from pathlib import Path
from eval import load_policy, task_config
from il_omx.env import OmxCubeEnv

X0, Y0 = 0.21, -0.06
path = Path(sys.argv[1]).resolve()
cfg = task_config(path); env = OmxCubeEnv(cfg); policy, act = load_policy(path, "cuda")
def run(x, y, yaw_deg, max_s=20):
    obs = env.reset(cube_pose=(x, y, np.deg2rad(yaw_deg))); policy.reset()
    for t in range(round(max_s * cfg.fps)):
        obs = env.step(act(obs))
        if env.is_success(): return True
    return False
out = {"pos": {}, "yaw": {}}
for d in (0, 1, 2, 3, 4, 6):
    dirs = [0] if d == 0 else range(0, 360, 45)
    r = [run(X0 + d / 100 * np.cos(np.deg2rad(a)), Y0 + d / 100 * np.sin(np.deg2rad(a)), 0) for a in dirs]
    out["pos"][d] = [int(v) for v in r]; print(f"offset {d} cm: {sum(r)}/{len(r)}", flush=True)
for yaw in (5, 10, 20, 30, 45):
    r = [run(X0, Y0, s * yaw) for s in (1, -1)]
    out["yaw"][yaw] = [int(v) for v in r]; print(f"yaw ±{yaw}: {sum(r)}/{len(r)}", flush=True)
json.dump(out, open(sys.argv[2], "w"), indent=1)
