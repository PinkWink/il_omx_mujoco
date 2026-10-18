"""Plot a recorded dataset: every episode's joint trajectories and the episode lengths (no robot needed).

  python scripts/plot_dataset.py --dataset real_strawberry_lift
  python scripts/plot_dataset.py --dataset my_fixed5 --signal action

Saves outputs/plots/<dataset>_joints.png and outputs/plots/<dataset>_lengths.png.
Works for the MuJoCo datasets (radians) and the real follower ones (LeRobot normalized units).
"""
import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # files only, no window
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from il_omx.dataset import DATA_DIR
from il_omx.leader import ROOT


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", required=True, help=f"folder name under {DATA_DIR}")
    p.add_argument("--signal", choices=["state", "action"], default="state",
                   help="observation.state (where the arm was) or action (the target sent)")
    p.add_argument("--out", default=str(ROOT / "outputs" / "plots"))
    args = p.parse_args()

    root = DATA_DIR / args.dataset
    if not (root / "meta" / "info.json").exists():
        raise SystemExit(f"{root} is not a dataset (no meta/info.json)")
    info = json.loads((root / "meta" / "info.json").read_text())
    key = "observation.state" if args.signal == "state" else "action"
    names = info["features"][key]["names"]
    unit = "normalized" if info.get("robot_type") == "omx_follower" else "rad"
    fps = info["fps"]
    data = pd.concat(pd.read_parquet(f, columns=["episode_index", "index", key])
                     for f in sorted((root / "data").glob("*/*.parquet")))
    episodes = [np.stack(g.sort_values("index")[key]) for _, g in data.groupby("episode_index")]

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 3, figsize=(15, 6.4), dpi=120, sharex=True)
    colors = plt.get_cmap("viridis")(np.linspace(0, 1, len(episodes)))
    for e, (values, color) in enumerate(zip(episodes, colors)):
        t = np.arange(len(values)) / fps
        for j, ax in enumerate(axes.flat):
            ax.plot(t, values[:, j], color=color, lw=1.2, label=f"ep {e}")
    for j, ax in enumerate(axes.flat):
        ax.set_title(f"{names[j]} ({unit})")
        ax.grid(alpha=0.3)
        if j >= 3:
            ax.set_xlabel("time (s)")
    if len(episodes) <= 20:
        fig.legend(*axes[0, 0].get_legend_handles_labels(), loc="lower center", ncol=10, frameon=False,
                   bbox_to_anchor=(0.5, -0.05))
    fig.suptitle(f"{args.dataset}: {key} of {len(episodes)} episodes ({fps} fps)")
    fig.tight_layout()
    joints_png = out / f"{args.dataset}_joints.png"
    fig.savefig(joints_png, bbox_inches="tight")
    plt.close(fig)

    lengths = [len(v) / fps for v in episodes]
    fig, ax = plt.subplots(figsize=(max(6, 0.5 * len(lengths) + 2), 3.2), dpi=120)
    ax.bar(range(len(lengths)), lengths, color="#1565C0")
    ax.axhline(np.mean(lengths), color="gray", ls="--", lw=1, label=f"mean {np.mean(lengths):.1f} s")
    ax.set_xlabel("episode"); ax.set_ylabel("length (s)"); ax.legend(frameon=False)
    ax.set_title(f"{args.dataset}: {len(lengths)} episodes, {sum(len(v) for v in episodes)} frames")
    fig.tight_layout()
    lengths_png = out / f"{args.dataset}_lengths.png"
    fig.savefig(lengths_png)
    plt.close(fig)

    print(f"{root}: {len(episodes)} episodes, {len(data)} frames, {fps} fps")
    print(f"saved {joints_png}")
    print(f"saved {lengths_png}")


if __name__ == "__main__":
    main()
