"""Look inside a recorded dataset (page ⑥): meta, one frame, episode lengths, files.

  .venv/bin/python docs/lecture/inspect_dataset.py lecture_record
  .venv/bin/python docs/lecture/inspect_dataset.py lecture_record --save-plot docs/lecture/l06_episode.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np  # noqa: E402
from lerobot.datasets.lerobot_dataset import LeRobotDataset  # noqa: E402

from il_omx.dataset import DATA_DIR  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("dataset")
p.add_argument("--save-plot", help="write episode 0 state/action arrays to this json (for the lecture figures)")
args = p.parse_args()

root = DATA_DIR / args.dataset
ds = LeRobotDataset(f"local/{args.dataset}", root=root)
m = ds.meta
print(f"{root}: {m.total_episodes} episodes, {m.total_frames} frames, {m.fps} fps, robot {m.robot_type}")
print("features:")
for k, f in m.features.items():
    print(f"  {k:28s} {f['dtype']:8s} {tuple(f['shape'])}")

frame = ds[0]
print("\nds[0] (episode 0, frame 0):")
for k, v in frame.items():
    if hasattr(v, "shape"):
        print(f"  {k:28s} {str(tuple(v.shape)):16s} {v.dtype}")
    else:
        print(f"  {k:28s} {v!r}")
np.set_printoptions(precision=3, suppress=True)
print("  state :", frame["observation.state"].numpy())
print("  action:", frame["action"].numpy())

lengths = [int(e["length"]) for e in m.episodes]
print(f"\nepisode lengths (frames): {lengths}  -> {np.mean(lengths) / m.fps:.1f} s on average")
size = sum(f.stat().st_size for f in root.rglob("*") if f.is_file())
print(f"size on disk: {size / 1e6:.1f} MB")

if args.save_plot:
    ep = [ds[i] for i in range(lengths[0])]
    out = {"fps": m.fps, "state": np.stack([f["observation.state"].numpy() for f in ep]).tolist(),
           "action": np.stack([f["action"].numpy() for f in ep]).tolist()}
    for cam in ("global", "wrist"):
        for i in (0, lengths[0] // 3, 2 * lengths[0] // 3, lengths[0] - 1):
            img = (ep[i][f"observation.images.{cam}"].permute(1, 2, 0).numpy() * 255).astype(np.uint8)
            from PIL import Image
            Image.fromarray(img).save(Path(args.save_plot).with_name(f"l06_frame_{cam}_{i:03d}.png"))
    Path(args.save_plot).write_text(json.dumps(out))
    print("saved", args.save_plot)
