"""Train an ACT policy on a recorded dataset (data/<dataset>) with LeRobot, fully offline.

  python scripts/train.py [--dataset omx_cube_to_tray] [--steps 30000] [--batch-size 8]
  python scripts/train.py --resume            # continue an interrupted run (Ctrl+C is fine)
  python scripts/train.py --resume --steps 50000   # or train an existing run for longer

Output: outputs/train/<dataset>_act/checkpoints/<step>/pretrained_model (a checkpoint every
--save-freq steps; checkpoints/last points at the newest). Progress, loss and the remaining time
are printed by LeRobot. A GPU is strongly recommended: on CPU training is 25x slower.
"""
import argparse
import json
import os
import subprocess
import sys

import torch

from il_omx.dataset import DATA_DIR, ROOT

TRAIN_DIR = ROOT / "outputs" / "train"
MIN_EPISODES = 5


def pick_device(requested: str) -> str:
    if requested != "auto":
        return requested
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", default="omx_cube_to_tray", help=f"folder name under {DATA_DIR}")
    p.add_argument("--name", help="run name (default: <dataset>_act)")
    p.add_argument("--steps", type=int, default=30_000, help="total training steps")
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--save-freq", type=int, default=5_000, help="checkpoint every N steps")
    p.add_argument("--chunk-s", type=float, default=2.0,
                   help="ACT action chunk length in seconds (converted to steps with the dataset fps)")
    p.add_argument("--device", default="auto", choices=["auto", "cuda", "mps", "cpu"])
    p.add_argument("--num-workers", type=int, default=min(4, max(1, (os.cpu_count() or 2) // 2)),
                   help="data loading processes")
    p.add_argument("--resume", action="store_true", help="continue the run from its last checkpoint")
    p.add_argument("--min-episodes", type=int, default=MIN_EPISODES, help="refuse smaller datasets")
    args = p.parse_args()

    run_dir = TRAIN_DIR / (args.name or f"{args.dataset}_act")
    device = pick_device(args.device)
    # LeRobot's train loop; AMP (mixed precision) is ~25% faster on a GPU and changes nothing else.
    cmd = [sys.executable, "-m", "lerobot.scripts.lerobot_train"]
    common = [
        f"--steps={args.steps}",
        f"--batch_size={args.batch_size}",
        f"--save_freq={args.save_freq}",
        f"--num_workers={args.num_workers}",
        f"--policy.device={device}",
        f"--policy.use_amp={str(device == 'cuda').lower()}",
    ]

    if args.resume:
        config = run_dir / "checkpoints" / "last" / "pretrained_model" / "train_config.json"
        if not config.exists():
            raise SystemExit(f"No checkpoint to resume in {run_dir}. Train without --resume first.")
        cmd += [f"--config_path={config}", "--resume=true", *common]
    else:
        root = DATA_DIR / args.dataset
        info = root / "meta" / "info.json"
        if not info.exists():
            raise SystemExit(f"No dataset at {root}. Record one with scripts/record.py --dataset {args.dataset}")
        meta = json.loads(info.read_text())
        episodes, fps = meta["total_episodes"], meta["fps"]
        # ACT's default chunk is 100 steps (2 s at 50 Hz). Keep the chunk a fixed time instead, so a
        # 10 fps dataset gets 20 steps rather than a 10 s chunk longer than a whole demo.
        chunk = max(1, round(args.chunk_s * fps))
        if episodes < args.min_episodes:
            raise SystemExit(f"{root} has only {episodes} episodes; record at least {args.min_episodes} "
                             "(about 50 works well) before training.")
        if run_dir.exists():
            raise SystemExit(f"{run_dir} already exists. Continue it with --resume, pick another --name, "
                             "or delete the folder to start over.")
        print(f"dataset: {root}  ({episodes} episodes, {fps} fps, ACT chunk {chunk} steps)")
        cmd += [
            f"--dataset.repo_id=local/{args.dataset}",
            f"--dataset.root={root}",
            "--policy.type=act",
            f"--policy.chunk_size={chunk}",
            f"--policy.n_action_steps={chunk}",
            "--policy.push_to_hub=false",
            "--wandb.enable=false",
            f"--output_dir={run_dir}",
            f"--job_name={run_dir.name}",
            "--log_freq=100",
            *common,
        ]

    print(f"run: {run_dir}  device: {device}")
    if device == "cpu":
        print(f"WARNING: no GPU found. On CPU a step takes ~5 s, so {args.steps} steps take about "
              f"{args.steps * 5 / 3600:.0f} h. Train on a PC with an NVIDIA GPU if you can.")

    env = dict(os.environ, SVT_LOG="1", HF_HUB_OFFLINE="1")  # quiet video encoder, never touch the Hub
    try:
        result = subprocess.run(cmd, env=env, cwd=ROOT)
    except KeyboardInterrupt:
        result = None
    if result is None or result.returncode != 0:
        if (run_dir / "checkpoints" / "last").exists():
            print("\nstopped. Continue with: python scripts/train.py --resume"
                  + (f" --name {args.name}" if args.name else f" --dataset {args.dataset}"))
        sys.exit(1)
    print(f"\ndone. Policy: {run_dir / 'checkpoints' / 'last' / 'pretrained_model'}")


if __name__ == "__main__":
    main()
