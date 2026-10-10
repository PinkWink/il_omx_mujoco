"""Renders and data for page ⑩ (scripted IK demos). Needs the project venv.

  MUJOCO_GL=egl .venv/bin/python docs/lecture/render_lesson10_sim.py
Writes l10_wp_<i>.png (arm at each waypoint of the plan for seed 0) and l10_data.json
(waypoints, IK error per iteration count, grasp yaw examples).
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
from scripted_pick_place import grasp_yaw, plan  # noqa: E402

from il_omx.env import OmxCubeEnv, TaskConfig  # noqa: E402
from il_omx.ik import OmxIK, top_down_rotation  # noqa: E402

OUT = Path(__file__).resolve().parent


def main():
    env = OmxCubeEnv(TaskConfig(), render=False)
    m, d = env.model, env.data
    m.vis.global_.offwidth, m.vis.global_.offheight = 640, 480
    env.reset(seed=0)
    a = env.cube_qpos_adr
    cube_yaw = 2 * np.arctan2(d.qpos[a + 6], d.qpos[a + 3])
    cube, tray = env.cube_pos.copy(), d.xpos[env.tray_body].copy()
    ik = OmxIK(m)
    segs = plan(env, ik, cube_yaw)
    r = mujoco.Renderer(m, 480, 640)
    cam = mujoco.MjvCamera()
    cam.lookat[:] = (0.17, 0.03, 0.06); cam.distance, cam.azimuth, cam.elevation = 0.55, 200, -30
    qpos0 = d.qpos.copy()
    wps = []
    for i, (q, g, n) in enumerate(segs):
        d.qpos[:] = qpos0
        d.qpos[env.qpos_ids[:5]] = q
        d.qpos[env.qpos_ids[5]] = g
        d.qpos[env.qpos_ids[5] + 1] = -g
        mujoco.mj_forward(m, d)
        r.update_scene(d, cam)
        Image.fromarray(r.render()).save(OUT / f"l10_wp_{i}.png")
        wps.append({"q_deg": np.rad2deg(q).round(1).tolist(), "grip_deg": round(float(np.rad2deg(g)), 1), "steps": n,
                    "tcp": d.site("tcp").xpos.round(3).tolist()})
    r.close()

    # IK convergence: error after k iterations for the first waypoint (8 cm above the cube).
    target = cube + [0, 0, 0.08]
    yaw_c = grasp_yaw(cube_yaw, np.arctan2(cube[1], cube[0]))
    q0 = m.key_qpos[env.home_key][:5]
    conv = []
    for k in range(1, 31):
        _, err = OmxIK(m).solve(q0, target, top_down_rotation(yaw_c), iters=k)
        conv.append(round(float(err) * 1000, 3))

    yaws = [[c, round(float(np.rad2deg(grasp_yaw(np.deg2rad(c), 0.0))), 1)]
            for c in (-40, -20, 0, 20, 40)]
    out = {"cube": cube.round(3).tolist(), "cube_yaw_deg": round(float(np.rad2deg(cube_yaw)), 1),
           "tray": tray.round(3).tolist(), "waypoints": wps, "ik_conv_mm": conv, "grasp_yaw_examples": yaws}
    (OUT / "l10_data.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "waypoints"}))
    for w in wps:
        print(w)


if __name__ == "__main__":
    main()
