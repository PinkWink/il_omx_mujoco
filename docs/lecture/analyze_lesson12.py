"""Numbers and frames for page ⑫ (real follower: record, train, run) -> docs/lecture/l12_data.json + l12_frame_*.png.

  .venv/bin/python docs/lecture/analyze_lesson12.py

Inputs: data/real_strawberry_lift (10 demos), outputs/train/real_strawberry_lift_act (20000 steps),
outputs/lecture/real_strawberry_lift_train.log (the training terminal output).
The policy is run offline on one recorded episode: for every frame it predicts a fresh 60-step chunk
from that frame's images and state, so the plot shows what the model learned, not a robot run.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402
from lerobot.datasets.lerobot_dataset import LeRobotDataset  # noqa: E402
from PIL import Image  # noqa: E402

from il_omx.dataset import DATA_DIR  # noqa: E402
from il_omx.leader import ROOT  # noqa: E402

DATASET = "real_strawberry_lift"
RUN = ROOT / "outputs" / "train" / "real_strawberry_lift_act"
TRAIN_LOG = ROOT / "outputs" / "lecture" / "real_strawberry_lift_train.log"
OUT = Path(__file__).resolve().parent
EPISODE = 9            # the episode shown frame by frame on the page
CHUNK_AT = (0, 90, 180)  # frames of EPISODE whose whole predicted chunk is plotted
FRONT_CROP = 230       # front images: keep x < 230 (the operator sits on the right)


def episodes() -> list:
    data = pd.concat(pd.read_parquet(f) for f in sorted((DATA_DIR / DATASET / "data").glob("*/*.parquet")))
    return [{"state": np.stack(g["observation.state"]).round(2).tolist(),
             "action": np.stack(g["action"]).round(2).tolist()}
            for _, g in data.sort_values("index").groupby("episode_index")]


def loss_curve() -> list:
    """[step, loss, l1_loss, kld_loss] every log_freq (100) steps."""
    txt = TRAIN_LOG.read_text().replace("\r", "\n")
    rows = re.findall(r"loss:(\S+) grdn.*?l1_loss:(\S+) kld_loss:(\S+)", txt)
    return [[100 * (i + 1), float(a), float(b), float(c)] for i, (a, b, c) in enumerate(rows)]


def to_uint8(img: torch.Tensor) -> np.ndarray:
    return (img.permute(1, 2, 0).numpy() * 255).round().astype(np.uint8)


def offline_predictions(ds: LeRobotDataset, frames: range) -> dict:
    from lerobot.policies.act.modeling_act import ACTPolicy
    from lerobot.policies.factory import make_pre_post_processors
    from lerobot.policies.utils import prepare_observation_for_inference

    path = RUN / "checkpoints" / "last" / "pretrained_model"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    policy = ACTPolicy.from_pretrained(path).to(device).eval()
    pre, post = make_pre_post_processors(policy.config, pretrained_path=str(path),
                                         preprocessor_overrides={"device_processor": {"device": device}})
    first, chunks = [], {}
    for i in frames:
        item = ds[i]
        obs = {"observation.state": item["observation.state"].numpy(),
               **{k: to_uint8(item[k]) for k in ("observation.images.front", "observation.images.wrist")}}
        with torch.inference_mode():
            batch = pre(prepare_observation_for_inference(obs, torch.device(device), item["task"], None))
            chunk = post(policy.predict_action_chunk(batch))[0].cpu().numpy()     # (60, 6)
        first.append(chunk[0].round(2).tolist())
        k = i - frames.start
        if k in CHUNK_AT:
            chunks[k] = chunk.round(2).tolist()
    return {"first": first, "chunks": chunks}


def save_frames(ds: LeRobotDataset, frames: range, picks: list):
    for k in picks:
        item = ds[frames.start + k]
        front = to_uint8(item["observation.images.front"])[:, :FRONT_CROP]
        Image.fromarray(front).save(OUT / f"l12_frame_front_{k:03d}.png")
        Image.fromarray(to_uint8(item["observation.images.wrist"])).save(OUT / f"l12_frame_wrist_{k:03d}.png")


def main():
    ds = LeRobotDataset(f"local/{DATASET}", root=DATA_DIR / DATASET)
    eps = episodes()
    start = sum(len(e["state"]) for e in eps[:EPISODE])
    frames = range(start, start + len(eps[EPISODE]["state"]))
    picks = [0, 60, 120, 180, 240, len(frames) - 1]
    save_frames(ds, frames, picks)
    out = {"fps": ds.meta.fps, "episodes": eps, "loss": loss_curve(), "episode": EPISODE, "frame_picks": picks,
           "chunk_at": list(CHUNK_AT), "pred": offline_predictions(ds, frames)}
    (OUT / "l12_data.json").write_text(json.dumps(out))
    print(f"saved l12_data.json: {len(eps)} episodes, {len(out['loss'])} loss rows, "
          f"{len(out['pred']['first'])} predictions; frames {picks}")


if __name__ == "__main__":
    main()
