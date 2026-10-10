"""Evaluate a trained policy in the MuJoCo task: success rate over new random cube placements.

  python scripts/eval.py                                  # last checkpoint of outputs/train/omx_cube_to_tray_act
  python scripts/eval.py --run omx_cube_scripted_act --episodes 50
  python scripts/eval.py --policy outputs/train/<run>/checkpoints/010000/pretrained_model
  python scripts/eval.py --view                           # watch it in the MuJoCo viewer (real time)
  python scripts/eval.py --run my_fixed5_act --fixed-cube --episodes 10   # only the training pose

Cube placements come from --seed (default 1000), so they differ from scripted demos (seeds 0..)
and are the same for every policy you compare. --fixed-cube uses the fixed pose of
`record.py --fixed-cube` instead (--cube-pose X Y YAW_DEG for another one).
An episode succeeds when the cube rests in the tray with the gripper open, like in recording;
it fails after --max-s seconds.
A video of the first --video-episodes episodes is written next to the results.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")

import numpy as np
import torch

from il_omx.dataset import ROOT, TASK
from il_omx.env import (
    CAMERA_NAMES,
    OmxCubeEnv,
    TaskConfig,
    add_cube_args,
    cube_pose_from_args,
    describe_cube,
)

TRAIN_DIR = ROOT / "outputs" / "train"


def load_policy(path: Path, device: str):
    from lerobot.common.control_utils import predict_action
    from lerobot.policies.act.modeling_act import ACTPolicy
    from lerobot.policies.factory import make_pre_post_processors

    policy = ACTPolicy.from_pretrained(path)
    policy.config.device = device
    policy.to(device).eval()
    pre, post = make_pre_post_processors(policy.config, pretrained_path=str(path),
                                         preprocessor_overrides={"device_processor": {"device": device}})
    torch_device = torch.device(device)

    def act(obs: dict) -> np.ndarray:
        frame = {"observation.state": obs["state"].astype(np.float32)}
        for cam in CAMERA_NAMES:
            frame[f"observation.images.{cam}"] = obs[cam]
        action = predict_action(frame, policy, torch_device, pre, post, use_amp=False, task=TASK)
        return action.squeeze(0).cpu().numpy()

    return policy, act


def task_config(policy_path: Path) -> TaskConfig:
    """Same fps and image size as the training dataset."""
    train_cfg = json.loads((policy_path / "train_config.json").read_text())
    info = json.loads((Path(train_cfg["dataset"]["root"]) / "meta" / "info.json").read_text())
    h, w, _ = info["features"][f"observation.images.{CAMERA_NAMES[0]}"]["shape"]
    return TaskConfig(fps=info["fps"], image_height=h, image_width=w)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run", default="omx_cube_to_tray_act", help=f"run folder under {TRAIN_DIR}")
    p.add_argument("--policy", help="a pretrained_model folder (overrides --run)")
    p.add_argument("--episodes", type=int, default=20)
    p.add_argument("--seed", type=int, default=1000, help="episode i uses cube seed (seed + i)")
    add_cube_args(p)
    p.add_argument("--max-s", type=float, default=20.0, help="fail an episode after this many seconds")
    p.add_argument("--video-episodes", type=int, default=5, help="episodes to put in the video (0 = none)")
    p.add_argument("--view", action="store_true", help="show the rollouts in the MuJoCo viewer")
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = p.parse_args()

    path = Path(args.policy) if args.policy else TRAIN_DIR / args.run / "checkpoints" / "last" / "pretrained_model"
    if not (path / "model.safetensors").exists():
        raise SystemExit(f"No trained policy at {path}")
    path = path.resolve()  # checkpoints/last is a symlink; show which step is evaluated
    cfg = task_config(path)
    env = OmxCubeEnv(cfg)
    policy, act = load_policy(path, args.device)
    print(f"policy: {path}\n{cfg.fps} fps, {cfg.image_width}x{cfg.image_height}, device {args.device}")

    viewer = None
    if args.view:
        from il_omx.teleop_ui import open_viewer
        from il_omx.viewer_overlay import GRAY
        viewer, overlay = open_viewer(env)

    out_dir = path.parent / "eval"
    out_dir.mkdir(exist_ok=True)
    frames = []
    results = []
    max_steps = round(args.max_s * cfg.fps)
    cube_pose = cube_pose_from_args(args)
    print(f"cube: {describe_cube(cube_pose)}")
    pose_deg = None if cube_pose is None else [cube_pose[0], cube_pose[1], float(np.rad2deg(cube_pose[2]))]
    for ep in range(args.episodes):
        obs = env.reset(seed=args.seed + ep, cube_pose=cube_pose)
        policy.reset()  # drop the action chunk queued from the previous episode
        success_step = None
        for t in range(max_steps):
            t0 = time.perf_counter()
            obs = env.step(act(obs))
            if ep < args.video_episodes:
                frames.append(np.concatenate([obs[cam] for cam in CAMERA_NAMES], axis=1))
            if viewer is not None:
                if not viewer.is_running():
                    sys.exit(0)
                overlay.set_cameras({cam: obs[cam] for cam in CAMERA_NAMES})
                overlay.set_banner(f"EVAL  episode {ep + 1}  {t / cfg.fps:4.1f} s", GRAY)
                overlay.flush()
                viewer.sync()
                time.sleep(max(0.0, 1 / cfg.fps - (time.perf_counter() - t0)))
            if env.is_success():
                success_step = t + 1
                break
        ok = success_step is not None
        results.append({"episode": ep, "seed": args.seed + ep, "success": ok,
                        "time_s": success_step / cfg.fps if ok else None})
        print(f"episode {ep:3d} (seed {args.seed + ep}): "
              + (f"success in {success_step / cfg.fps:4.1f} s" if ok else "FAIL"), flush=True)

    n_ok = sum(r["success"] for r in results)
    times = [r["time_s"] for r in results if r["success"]]
    summary = {"policy": str(path), "episodes": args.episodes, "successes": n_ok,
               "success_rate": n_ok / args.episodes, "mean_time_s": float(np.mean(times)) if times else None,
               "seed": args.seed, "cube_pose": pose_deg, "max_s": args.max_s, "results": results}
    tag = (f"pose{'_'.join(f'{v:g}' for v in pose_deg)}" if pose_deg else f"seed{args.seed}") \
        + f"_n{args.episodes}"
    (out_dir / f"{tag}.json").write_text(json.dumps(summary, indent=2))
    print(f"\nsuccess rate: {n_ok}/{args.episodes} ({100 * n_ok / args.episodes:.0f}%)"
          + (f", mean time {np.mean(times):.1f} s" if times else ""))
    print(f"results: {out_dir / (tag + '.json')}")
    if frames:
        import imageio.v2 as imageio
        imageio.mimsave(out_dir / f"{tag}.mp4", frames, fps=cfg.fps)
        print(f"video:   {out_dir / (tag + '.mp4')}")
    if viewer is not None:
        viewer.close()
    env.close()


if __name__ == "__main__":
    main()
