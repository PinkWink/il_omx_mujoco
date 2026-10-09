"""Render the global and wrist cameras at the home keyframe and save PNGs."""
import argparse
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image

from il_omx.env import SCENE_XML

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=str(ROOT / "outputs"))
    args = p.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    m = mujoco.MjModel.from_xml_path(str(SCENE_XML))
    d = mujoco.MjData(m)
    mujoco.mj_resetDataKeyframe(m, d, m.key("home").id)
    mujoco.mj_forward(m, d)

    with mujoco.Renderer(m, 480, 640) as r:
        frames = []
        for cam in ["global", "wrist"]:
            r.update_scene(d, camera=cam)
            img = r.render()
            Image.fromarray(img).save(out / f"{cam}.png")
            frames.append(img)
        Image.fromarray(np.concatenate(frames, axis=1)).save(out / "cameras.png")
    print("saved to", out)


if __name__ == "__main__":
    main()
