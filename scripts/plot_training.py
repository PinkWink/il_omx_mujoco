"""Plot what a training run learned (no robot needed): loss curves and the policy's predictions on one demo.

  python scripts/plot_training.py --run real_strawberry_lift_act
  python scripts/plot_training.py --run my_fixed5_act --episode 2 --checkpoint 005000

Saves to outputs/plots/:
  <run>_loss.png          loss, L1 and KLD every 100 steps, from outputs/train/logs/<run>.log (train.py writes it)
  <run>_pred_ep<N>.png    the demo's action (gray) and the policy's prediction (blue) for every frame of
                          episode N, plus three whole predicted chunks (red). The demo was used for training,
                          so this shows what the model learned, not how well it does on the robot.
"""
import argparse
import json
import re
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # files only, no window
import matplotlib.pyplot as plt
import numpy as np
import torch

from il_omx.leader import ROOT

TRAIN_DIR = ROOT / "outputs" / "train"
LOSS = r"ot_train\.py:\d+ step:\S+ .*?loss:(\S+) .*?l1_loss:(\S+) kld_loss:(\S+)"
WITH_STEP = re.compile(r"(\d+)/\d+ \[[^\]\n\r]*\][^\n\r]*?" + LOSS)  # progress bar "999/20000 [..]" + log line


def read_loss(log: Path) -> np.ndarray:
    """[step, loss, l1, kld] rows. The step comes from the progress bar printed just before each log line."""
    text = log.read_text(errors="replace")
    rows, offset, last = [], 0, 0
    for m in WITH_STEP.finditer(text):
        bar = int(m.group(1))
        if bar < last:  # a --resume run: its progress bar starts again from 0
            offset = rows[-1][0]
        last = bar
        rows.append([offset + round(bar / 100) * 100, *map(float, m.groups()[1:])])
    if not rows:  # no progress bar in the log: LeRobot logs every 100 steps (--log_freq=100)
        rows = [[100 * (i + 1), *map(float, m.groups())] for i, m in enumerate(re.finditer(LOSS, text))]
    return np.array(rows)


def plot_loss(rows: np.ndarray, run: str, out: Path):
    fig, axes = plt.subplots(1, 3, figsize=(15, 3.8), dpi=120)
    for ax, col, title in zip(axes, (1, 2, 3), ("loss (= L1 + 10 x KLD)", "L1: action error", "KLD (CVAE)")):
        ax.plot(rows[:, 0], rows[:, col], lw=1.5)
        ax.set_yscale("log")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.yaxis.set_minor_formatter(plt.NullFormatter())
        ax.set_title(f"{title}   last {rows[-1, col]:.3f}")
        ax.set_xlabel("training step")
        ax.grid(alpha=0.3, which="both")
    fig.suptitle(f"{run}: {len(rows)} log lines, up to step {int(rows[-1, 0])}")
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def load_policy(path: Path, device: str):
    from lerobot.policies.act.modeling_act import ACTPolicy
    from lerobot.policies.factory import make_pre_post_processors

    policy = ACTPolicy.from_pretrained(path).to(device).eval()
    pre, post = make_pre_post_processors(policy.config, pretrained_path=str(path),
                                         preprocessor_overrides={"device_processor": {"device": device}})
    return policy, pre, post


def predict_episode(path: Path, episode: int, device: str):
    """(demo actions, first predicted action per frame, {frame: whole chunk}, joint names, fps, unit)."""
    from lerobot.datasets.lerobot_dataset import LeRobotDataset
    from lerobot.policies.utils import prepare_observation_for_inference

    data_cfg = json.loads((path / "train_config.json").read_text())["dataset"]
    ds = LeRobotDataset(data_cfg["repo_id"], root=data_cfg["root"], episodes=[episode])
    meta = ds.meta
    cams = [k for k in meta.features if k.startswith("observation.images.")]
    policy, pre, post = load_policy(path, device)
    n = len(ds)
    chunk_at = {0, n // 3, 2 * n // 3}
    demo, first, chunks = [], [], {}
    for i in range(n):
        item = ds[i]
        obs = {"observation.state": item["observation.state"].numpy(),
               **{k: (item[k].permute(1, 2, 0).numpy() * 255).round().astype(np.uint8) for k in cams}}
        with torch.inference_mode():
            batch = pre(prepare_observation_for_inference(obs, torch.device(device), item["task"], None))
            chunk = post(policy.predict_action_chunk(batch))[0].float().cpu().numpy()
        demo.append(item["action"].numpy())
        first.append(chunk[0])
        if i in chunk_at:
            chunks[i] = chunk
    unit = "normalized" if meta.robot_type == "omx_follower" else "rad"
    return np.array(demo), np.array(first), chunks, meta.features["action"]["names"], meta.fps, unit


def plot_predictions(demo, first, chunks, names, fps, unit, title: str, out: Path):
    t = np.arange(len(demo)) / fps
    fig, axes = plt.subplots(2, 3, figsize=(15, 6.4), dpi=120, sharex=True)
    for j, ax in enumerate(axes.flat):
        ax.plot(t, demo[:, j], color="gray", lw=3, label="demo action")
        ax.plot(t, first[:, j], color="tab:blue", lw=1.2, label="prediction (first action of each chunk)")
        for k, (i, chunk) in enumerate(sorted(chunks.items())):
            tc = (i + np.arange(len(chunk))) / fps
            ax.plot(tc, chunk[:, j], color="tab:red", lw=1.1, ls="--",
                    label=f"one chunk ({len(chunk)} steps)" if k == 0 else None)
            ax.plot(tc[0], chunk[0, j], "o", color="tab:red", ms=3)
        ax.set_title(f"{names[j]} ({unit})   mean error {np.abs(demo[:, j] - first[:, j]).mean():.3g}")
        ax.grid(alpha=0.3)
        if j >= 3:
            ax.set_xlabel("time (s)")
    fig.legend(*axes[0, 0].get_legend_handles_labels(), loc="lower center", ncol=3, frameon=False,
               bbox_to_anchor=(0.5, -0.04))
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run", required=True, help=f"run folder under {TRAIN_DIR}")
    p.add_argument("--checkpoint", default="last", help="checkpoint folder: last, 005000, ...")
    p.add_argument("--episode", type=int, default=0, help="demo episode to predict")
    p.add_argument("--log", help=f"training log (default {TRAIN_DIR / 'logs'}/<run>.log)")
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--out", default=str(ROOT / "outputs" / "plots"))
    args = p.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    log = Path(args.log) if args.log else TRAIN_DIR / "logs" / f"{args.run}.log"
    rows = read_loss(log) if log.exists() else np.empty((0, 4))
    if len(rows):
        plot_loss(rows, args.run, out / f"{args.run}_loss.png")
        print(f"loss: {len(rows)} log lines, step {int(rows[0, 0])} -> {int(rows[-1, 0])}, "
              f"L1 {rows[0, 2]:.3f} -> {rows[-1, 2]:.3f}")
        print(f"saved {out / f'{args.run}_loss.png'}")
    else:
        print(f"no loss curve: {log} not found or empty (runs trained before train.py kept a log have none)")

    path = TRAIN_DIR / args.run / "checkpoints" / args.checkpoint / "pretrained_model"
    if not path.exists():
        raise SystemExit(f"{path} not found. Check --run and --checkpoint (ls {TRAIN_DIR / args.run / 'checkpoints'}).")
    t0 = time.perf_counter()
    demo, first, chunks, names, fps, unit = predict_episode(path, args.episode, args.device)
    name = out / f"{args.run}_pred_ep{args.episode}.png"
    plot_predictions(demo, first, chunks, names, fps, unit,
                     f"{args.run} ({args.checkpoint}) on demo episode {args.episode}", name)
    err = np.abs(demo - first).mean(axis=0)
    print(f"predictions: episode {args.episode}, {len(demo)} frames in {time.perf_counter() - t0:.0f} s on "
          f"{args.device}; mean error per joint {' '.join(f'{e:.2f}' for e in err)}")
    print(f"saved {name}")


if __name__ == "__main__":
    main()
