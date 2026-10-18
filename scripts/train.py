"""Train an ACT policy on a recorded dataset (data/<dataset>) with LeRobot, without the Hugging Face Hub.

The first run downloads the ResNet18 ImageNet weights (~45 MB, torchvision cache in ~/.cache/torch/hub);
after that no internet is needed.

  python scripts/train.py [--dataset omx_cube_to_tray] [--steps 30000] [--batch-size 8]
  python scripts/train.py --resume            # continue an interrupted run (Ctrl+C is fine)
  python scripts/train.py --resume --steps 50000   # or train an existing run for longer

Output: outputs/train/<dataset>_act/checkpoints/<step>/pretrained_model (a checkpoint every
--save-freq steps; checkpoints/last points at the newest). Progress, loss and the remaining time
are printed by LeRobot and also saved to outputs/train/logs/<run>.log (appended on --resume), which
scripts/plot_training.py turns into loss curves. A GPU is strongly recommended: on CPU training is
about 20x slower.
"""
import argparse
import json
import os
import subprocess
import sys

import torch

from il_omx.dataset import DATA_DIR, ROOT

TRAIN_DIR = ROOT / "outputs" / "train"
LOG_DIR = TRAIN_DIR / "logs"  # not inside the run folder: LeRobot refuses an existing output_dir
MIN_EPISODES = 5


def pick_device(requested: str) -> str:
    if requested != "auto":
        return requested
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def run_logged(cmd: list, env: dict, log_path) -> int:
    """Run cmd, showing its output as usual and appending it to log_path."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "ab") as log:
        proc = subprocess.Popen(cmd, env=env, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        try:
            while chunk := os.read(proc.stdout.fileno(), 4096):  # raw bytes: keeps tqdm's \r updates live
                sys.stdout.buffer.write(chunk)
                sys.stdout.flush()
                log.write(chunk)
        except KeyboardInterrupt:  # Ctrl+C also reaches LeRobot, which saves nothing more and exits
            pass
        return proc.wait()


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
        # Measured ~0.9 s per step on an 8-core desktop CPU (Ryzen 7 9700X); laptops are slower.
        print(f"WARNING: no GPU found. On CPU a step takes ~1 s or more, so {args.steps} steps take at least "
              f"{args.steps * 0.9 / 3600:.0f} h. Train on a PC with an NVIDIA GPU if you can.")

    env = dict(os.environ, SVT_LOG="1", HF_HUB_OFFLINE="1")  # quiet video encoder, never touch the Hub
    log_path = LOG_DIR / f"{run_dir.name}.log"
    print(f"log: {log_path}")
    try:
        returncode = run_logged(cmd, env, log_path)
    except KeyboardInterrupt:
        returncode = None
    if returncode != 0:
        if (run_dir / "checkpoints" / "last").exists():
            print("\nstopped. Continue with: python scripts/train.py --resume"
                  + (f" --name {args.name}" if args.name else f" --dataset {args.dataset}"))
        sys.exit(1)
    print(f"\ndone. Policy: {run_dir / 'checkpoints' / 'last' / 'pretrained_model'}")


if __name__ == "__main__":
    main()
