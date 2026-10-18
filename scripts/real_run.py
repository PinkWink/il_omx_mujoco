"""Run a trained policy on the real OMX follower (no leader needed), watching both cameras.

At start the follower glides to the demos' average start pose. Then, in the camera window:
  ENTER  idle    -> place the strawberry, then start the policy
  ENTER  running -> stop; the follower glides back to the start pose
  ESC            -> quit (the follower goes to the start pose first, then its torque turns off)
A run also stops after --max-s seconds, or when a joint pushes hard for a while (HIGH LOAD, e.g.
pressing into the table). A red MOTOR ERROR means a servo shut down: unplug the follower's power
and USB, plug both back in. A red CAMERA LOST (a camera's USB dropped) also stops the run; the
camera reconnects by itself. Keep a hand near the follower's power switch.

  python scripts/real_run.py --run real_strawberry_lift_act
  python scripts/real_run.py --policy outputs/train/<run>/checkpoints/002000/pretrained_model

The fps, image size and cameras come from the training dataset.
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from il_omx.dataset import ROOT, TASK
from il_omx.real import FOLLOWER_PORT, Cameras, Follower, close_all
from il_omx.real_ui import ENTER_KEYS, ESCAPE_KEY, GRAY, GREEN, RED, CameraWindow

TRAIN_DIR = ROOT / "outputs" / "train"


def load_policy(path: Path, cameras: list, device: str):
    from lerobot.common.control_utils import predict_action
    from lerobot.policies.act.modeling_act import ACTPolicy
    from lerobot.policies.factory import make_pre_post_processors

    policy = ACTPolicy.from_pretrained(path)
    policy.config.device = device
    policy.to(device).eval()
    pre, post = make_pre_post_processors(policy.config, pretrained_path=str(path),
                                         preprocessor_overrides={"device_processor": {"device": device}})

    def act(state: np.ndarray, images: dict) -> np.ndarray:
        frame = {"observation.state": state, **{f"observation.images.{c}": images[c] for c in cameras}}
        action = predict_action(frame, policy, torch.device(device), pre, post, use_amp=False, task=TASK)
        return action.squeeze(0).cpu().numpy()

    return policy, act


def dataset_settings(policy_path: Path):
    """fps, image size, camera names and the average first-frame state of the training dataset."""
    root = Path(json.loads((policy_path / "train_config.json").read_text())["dataset"]["root"])
    info = json.loads((root / "meta" / "info.json").read_text())
    cameras = [k.removeprefix("observation.images.") for k in info["features"] if k.startswith("observation.images.")]
    h, w, _ = info["features"][f"observation.images.{cameras[0]}"]["shape"]
    data = pd.concat(pd.read_parquet(f, columns=["frame_index", "observation.state"])
                     for f in sorted((root / "data").glob("*/*.parquet")))
    start = np.stack(data[data.frame_index == 0]["observation.state"]).mean(axis=0)
    return info["fps"], w, h, cameras, start


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run", default="real_strawberry_lift_act", help=f"run folder under {TRAIN_DIR}")
    p.add_argument("--policy", help="a pretrained_model folder (overrides --run)")
    p.add_argument("--follower-port", default=FOLLOWER_PORT)
    p.add_argument("--max-s", type=float, default=30.0, help="stop a run after this many seconds")
    p.add_argument("--max-step", type=float, default=5.0,
                   help="largest joint move per command, normalized units (5 = 9 deg)")
    p.add_argument("--zoom", type=float, default=2.0, help="window size")
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = p.parse_args()

    path = Path(args.policy) if args.policy else TRAIN_DIR / args.run / "checkpoints" / "last" / "pretrained_model"
    if not (path / "model.safetensors").exists():
        raise SystemExit(f"No trained policy at {path}")
    path = path.resolve()  # checkpoints/last is a symlink; show which step runs
    fps, w, h, cameras, start_pose = dataset_settings(path)
    policy, act = load_policy(path, cameras, args.device)
    print(f"policy: {path}\n{fps} fps, {w}x{h}, cameras {cameras}, device {args.device}")

    cams = Cameras(w, h)
    follower = Follower(args.follower_port, max_step=args.max_step)
    window = CameraWindow("OMX policy", cameras, w, h, args.zoom)
    dt = 1.0 / fps

    def glide_to_start():
        follower.glide(start_pose, 3.0, fps,
                       on_step=lambda: (window.poll_keys(), window.show(cams.read(), "MOVING TO START POSE ...", GRAY)))

    running, run_start, runs, error = False, 0.0, 0, None
    try:
        glide_to_start()
        while window.is_running():
            t0 = time.perf_counter()
            keys = window.poll_keys()
            if ESCAPE_KEY in keys:
                break
            images = cams.read()
            lost = cams.lost_text()
            if error is None:
                error, warning = follower.check()
                if error is not None:
                    running = False
                    print(error)
            if error is not None:  # a servo is off: stop commanding, keep showing what to do
                window.show(images, error.split(":")[0], RED, error.split(": ")[1] + "    ESC: quit")
                time.sleep(dt)
                continue
            stop = None  # why the run ends this frame
            if any(k in ENTER_KEYS for k in keys):
                if running:
                    stop = "stopped"
                elif not lost:
                    policy.reset()  # drop the action chunk left from the previous run
                    running, run_start, runs = True, t0, runs + 1
            if running and stop is None:
                if lost:
                    stop = lost.split(":")[0]  # the policy would see a black image
                elif warning:
                    stop = warning.split(" - ")[0]  # pushing hard (table, strawberry, own stop): do not keep at it
                elif t0 - run_start > args.max_s:
                    stop = f"time limit {args.max_s:g} s"
            if stop is not None:
                running = False
                print(f"run {runs}: {stop} after {t0 - run_start:.1f} s")
                glide_to_start()
                continue
            if running:
                follower.send(act(follower.state(), images))
                window.show(images, f"POLICY  run {runs}  {t0 - run_start:4.1f} s", GREEN,
                            "ENTER: stop    ESC: quit", path.parent.name)
            else:
                window.show(images, *((lost, RED) if lost else ("", GRAY)), hint="ENTER: start policy    ESC: quit",
                            info=path.parent.name)
            time.sleep(max(0.0, dt - (time.perf_counter() - t0)))
        if error is None:
            glide_to_start()
    except KeyboardInterrupt:
        pass
    finally:
        close_all(window.close, follower.disconnect, cams.close)


if __name__ == "__main__":
    main()
