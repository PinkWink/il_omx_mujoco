"""MuJoCo renders and data for page ③ (needs the project venv).

  MUJOCO_GL=egl .venv/bin/python docs/lecture/render_lesson03_sim.py
Writes docs/lecture/l03_sim_*.png and l03_data.json (projected joint positions, finger outlines,
condition timeline of one scripted episode), which draw_lesson03_figures.py turns into figures.
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
sys.path.insert(0, str(ROOT / "scripts"))
from il_omx.env import FIXED_CUBE_POSE, JOINT_NAMES, OmxCubeEnv, TaskConfig  # noqa: E402
from il_omx.ik import OmxIK  # noqa: E402
from scripted_pick_place import plan  # noqa: E402

OUT = Path(__file__).resolve().parent
W, H = 1600, 1000


def free_cam(lookat, distance, azimuth, elevation):
    cam = mujoco.MjvCamera()
    cam.lookat[:] = lookat
    cam.distance, cam.azimuth, cam.elevation = distance, azimuth, elevation
    return cam


def project(model, cam, points, w, h):
    """Pixel (u, v) of world points seen from a free camera (pinhole, the viewer's fovy)."""
    az, el = np.deg2rad(cam.azimuth), np.deg2rad(cam.elevation)
    fwd = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
    pos = np.array(cam.lookat) - cam.distance * fwd
    right = np.cross(fwd, [0, 0, 1]); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    f = (h / 2) / np.tan(np.deg2rad(model.vis.global_.fovy) / 2)
    out = []
    for p in np.atleast_2d(points):
        d = p - pos
        out.append([w / 2 + f * d @ right / (d @ fwd), h / 2 - f * d @ up / (d @ fwd)])
    return out


def render(model, data, cam, w=W, h=H, opt=None):
    r = mujoco.Renderer(model, h, w)
    r.update_scene(data, cam, opt) if opt is not None else r.update_scene(data, cam)
    img = r.render()
    r.close()
    return img


def save(img, name):
    Image.fromarray(img).save(OUT / name)
    print("saved", name)


def finger_outlines(env):
    """Finger mesh vertices and pad box corners in the wrist (link5) frame, x-y plane, mm."""
    m, d = env.model, env.data
    b5 = m.body("link5").id
    R5, p5 = d.xmat[b5].reshape(3, 3), d.xpos[b5]
    to5 = lambda pts: ((pts - p5) @ R5)[:, :2] * 1000  # noqa: E731
    out = {"meshes": [], "pads": []}
    for gid in range(m.ngeom):
        if m.geom_bodyid[gid] not in (m.body("link6").id, m.body("link7").id):
            continue
        R, p = d.geom_xmat[gid].reshape(3, 3), d.geom_xpos[gid]
        if m.geom_type[gid] == mujoco.mjtGeom.mjGEOM_MESH:
            mid = m.geom_dataid[gid]
            v = m.mesh_vert[m.mesh_vertadr[mid]:m.mesh_vertadr[mid] + m.mesh_vertnum[mid]]
            out["meshes"].append(to5(v @ R.T + p).round(2).tolist())
        elif m.geom_type[gid] == mujoco.mjtGeom.mjGEOM_BOX:
            s = m.geom_size[gid]
            corners = np.array([[-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0]]) * s
            out["pads"].append(to5(corners @ R.T + p).round(2).tolist())
    out["tcp"] = to5(d.site("tcp").xpos[None])[0].round(2).tolist()
    return out


def main():
    env = OmxCubeEnv(TaskConfig())
    m, d = env.model, env.data
    m.vis.global_.offwidth, m.vis.global_.offheight = W, H
    data = {}

    # Arm at the home keyframe, seen from the robot's right side, with joint anchors projected.
    env.reset(cube_pose=FIXED_CUBE_POSE)
    cam = free_cam((0.12, 0, 0.11), 0.55, 90 + 180, -8)
    save(render(m, d, cam), "l03_sim_arm.png")
    anchors = {n: d.xanchor[m.joint(n).id] for n in JOINT_NAMES}
    anchors["tcp"] = d.site("tcp").xpos
    anchors["wrist_cam"] = d.cam_xpos[m.camera("wrist").id]
    data["arm"] = {k: project(m, cam, v, W, H)[0] for k, v in anchors.items()}

    # Collision view: finger pads (group 3) over the visual meshes.
    tcp = d.site("tcp").xpos.copy()
    opt = mujoco.MjvOption()
    opt.geomgroup[:] = 0
    opt.geomgroup[2] = opt.geomgroup[3] = 1
    save(render(m, d, free_cam(tcp - [0.03, 0, 0], 0.16, 90, -60), 1200, 900, opt), "l03_sim_pads.png")
    data["fingers"] = finger_outlines(env)

    # Camera placement overview: the two camera frames are drawn by the viewer flag.
    opt = mujoco.MjvOption()
    opt.flags[mujoco.mjtVisFlag.mjVIS_CAMERA] = 1
    cam = free_cam((0.15, 0, 0.12), 0.95, 235, -25)
    save(render(m, d, cam, opt=opt), "l03_sim_cameras.png")
    data["cameras"] = {n: project(m, cam, d.cam_xpos[m.camera(n).id], W, H)[0] for n in ("global", "wrist")}

    # Four random resets: what the global camera sees at the start of an episode.
    for s in range(4):
        obs = env.reset(seed=s)
        a = env.cube_qpos_adr
        yaw = np.rad2deg(2 * np.arctan2(d.qpos[a + 6], d.qpos[a + 3]))
        data[f"seed{s}"] = [round(float(d.qpos[a]), 3), round(float(d.qpos[a + 1]), 3), round(float(yaw), 1)]
        save(obs["global"], f"l03_sim_seed{s}.png")

    # One scripted episode at the fixed pose: success conditions at every control step.
    env.reset(cube_pose=FIXED_CUBE_POSE)
    ik = OmxIK(m)
    action = d.ctrl[env.actuator_ids].copy()
    steps, keyframes = [], {}
    limit = env.TRAY_INNER_HALF - env.CUBE_HALF - env.cfg.tray_margin

    def log(t):
        rel = env.cube_pos - d.xpos[env.tray_body]
        steps.append({"t": round(t, 2), "inside": bool(abs(rel[0]) < limit and abs(rel[1]) < limit),
                      "resting": bool(rel[2] < env.CUBE_HALF + 0.008), "touching": env.cube_touching_gripper(),
                      "success": env.is_success(), "cube_z": round(float(env.cube_pos[2]), 4),
                      "gripper": round(float(np.rad2deg(d.qpos[env.qpos_ids[-1]])), 1)})

    k = 0
    log(0.0)
    for q_goal, grip, n in plan(env, ik, 0.0):
        start, goal = action.copy(), np.append(q_goal, grip)
        for i in range(n):
            action = start + (goal - start) * (i + 1) / n
            env.step(action, render=False)
            k += 1
            log(k / env.cfg.fps)
    for _ in range(10):
        env.step(action, render=False)
        k += 1
        log(k / env.cfg.fps)
    data["timeline"] = steps

    # Key moments of the same episode, replayed for pictures.
    env.reset(cube_pose=FIXED_CUBE_POSE)
    action = d.ctrl[env.actuator_ids].copy()
    want = {"grasp": None, "carry": None, "release": None, "success": None}
    first_success = next(s["t"] for s in steps if s["success"])
    times = {"grasp": 3.0, "carry": 4.3, "release": first_success - 0.2, "success": first_success + 0.5}
    k = 0
    cam = free_cam((0.15, 0.03, 0.09), 0.62, 200, -30)
    for q_goal, grip, n in plan(env, ik, 0.0) + [(None, None, 10)]:
        start = action.copy()
        goal = start if q_goal is None else np.append(q_goal, grip)
        for i in range(n):
            action = start + (goal - start) * (i + 1) / n
            env.step(action, render=False)
            k += 1
            for name, t in times.items():
                if want[name] is None and abs(k / env.cfg.fps - t) < 1e-6 + 0.05:
                    want[name] = True
                    save(render(m, d, cam, 800, 560), f"l03_sim_{name}.png")
    data["key_times"] = times

    (OUT / "l03_data.json").write_text(json.dumps(data, indent=1))
    print("saved l03_data.json")


if __name__ == "__main__":
    main()
