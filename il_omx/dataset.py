"""LeRobotDataset layout for the cube-to-tray task. Datasets live only on the local disk."""
import shutil
from pathlib import Path

import numpy as np
from lerobot.datasets.dataset_tools import delete_episodes
from lerobot.datasets.lerobot_dataset import LeRobotDataset

from il_omx.env import CAMERA_NAMES, JOINT_NAMES

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"  # git-ignored
TASK = "Pick up the blue cube and place it in the green tray."
ROBOT_TYPE = "omx_follower_mujoco"
IMAGE_WRITER_THREADS_PER_CAMERA = 4


def dataset_features(image_height: int, image_width: int) -> dict:
    joints = {"dtype": "float32", "shape": (len(JOINT_NAMES),), "names": list(JOINT_NAMES)}
    features = {"observation.state": dict(joints), "action": dict(joints)}
    for cam in CAMERA_NAMES:
        features[f"observation.images.{cam}"] = {
            "dtype": "video",
            "shape": (image_height, image_width, 3),
            "names": ["height", "width", "channels"],
        }
    return features


def open_dataset(name: str, fps: int, image_height: int, image_width: int,
                 streaming_encoding: bool = False) -> LeRobotDataset:
    """Create data/<name>, or append to it if it already exists (settings must match)."""
    root = DATA_DIR / name
    repo_id = f"local/{name}"
    threads = IMAGE_WRITER_THREADS_PER_CAMERA * len(CAMERA_NAMES)
    features = dataset_features(image_height, image_width)
    if not (root / "meta" / "info.json").exists():
        return LeRobotDataset.create(
            repo_id=repo_id, fps=fps, features=features, root=root, robot_type=ROBOT_TYPE,
            use_videos=True, image_writer_threads=threads, streaming_encoding=streaming_encoding,
        )

    ds = LeRobotDataset.resume(repo_id=repo_id, root=root, image_writer_threads=threads,
                               streaming_encoding=streaming_encoding)
    mismatch = []
    if ds.meta.fps != fps:
        mismatch.append(f"fps {ds.meta.fps} (requested {fps})")
    for key, ft in features.items():
        if tuple(ds.meta.features[key]["shape"]) != tuple(ft["shape"]):
            mismatch.append(f"{key} shape {tuple(ds.meta.features[key]['shape'])} (requested {ft['shape']})")
    if mismatch:
        ds.finalize()
        raise SystemExit(f"{root} was recorded with different settings: " + ", ".join(mismatch)
                         + ". Use the same settings or a new --dataset name.")
    return ds


class EpisodeRecorder:
    """Records episodes into data/<name>, finalizing after every saved episode.

    LeRobot only writes the parquet footers in finalize(), so a dataset that is never finalized
    (killed terminal, crash) is unreadable. Finalizing and reopening after each episode costs
    ~0.1 s and means a crash loses at most the episode in progress.
    """

    def __init__(self, name: str, fps: int, image_height: int, image_width: int,
                 streaming_encoding: bool = False):
        self._open_args = (name, fps, image_height, image_width, streaming_encoding)
        self.dataset = open_dataset(*self._open_args)
        self.frames = 0

    @property
    def root(self) -> Path:
        return self.dataset.root

    @property
    def num_episodes(self) -> int:
        return self.dataset.meta.total_episodes

    def add(self, obs: dict, action: np.ndarray):
        self.dataset.add_frame(make_frame(obs, action))
        self.frames += 1

    def save(self):
        self.dataset.save_episode()
        self.dataset.finalize()
        self.dataset = open_dataset(*self._open_args)
        self.frames = 0

    def discard(self):
        if self.dataset.has_pending_frames():
            self.dataset.clear_episode_buffer()
        self.frames = 0

    def delete_last(self):
        """Remove the newest saved episode. Each episode has its own files, so this is a quick copy."""
        self.discard()
        self.dataset.finalize()
        root, name = self.root, self._open_args[0]
        if self.num_episodes > 1:
            tmp, old = root.with_name(f".{name}_tmp"), root.with_name(f".{name}_old")
            shutil.rmtree(tmp, ignore_errors=True)
            shutil.rmtree(old, ignore_errors=True)
            src = LeRobotDataset(self.dataset.repo_id, root=root)
            delete_episodes(src, [self.num_episodes - 1], output_dir=tmp, repo_id=self.dataset.repo_id)
            root.rename(old)
            tmp.rename(root)
            shutil.rmtree(old)
        else:
            shutil.rmtree(root)
        self.dataset = open_dataset(*self._open_args)

    def close(self):
        self.discard()
        self.dataset.finalize()


def make_frame(obs: dict, action: np.ndarray) -> dict:
    """One dataset frame: the observation at time t and the action applied at time t."""
    frame = {
        "observation.state": obs["state"].astype(np.float32),
        "action": np.asarray(action, dtype=np.float32),
        "task": TASK,
    }
    for cam in CAMERA_NAMES:
        frame[f"observation.images.{cam}"] = obs[cam]
    return frame
