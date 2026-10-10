"""Run scripts/teleop.py or scripts/record.py with a fake leader that replays the scripted IK demo.

  python dev/fake_leader.py teleop [--hold-s 2] -- --fixed-cube --duration 20
  python dev/fake_leader.py record [--hold-s 2] [--auto-enter] -- --dataset _try --num-episodes 2

The real viewer opens; nothing is sent to any window. --auto-enter presses ENTER through the
viewer's key callback whenever record.py is idle (start of the run and after each saved episode).
Each episode the fake leader holds still for --hold-s seconds, then follows the IK plan.
"""
import argparse
import importlib.util
import os
import sys
import threading
import time
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("SVT_LOG", "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np  # noqa: E402

import il_omx.env as envmod  # noqa: E402
from il_omx.ik import OmxIK  # noqa: E402
from il_omx.leader_mapping import ARM_MOTORS, DEG_PER_UNIT, GRIPPER_DEG_PER_UNIT  # noqa: E402
from il_omx.teleop_ui import ENTER_KEYS  # noqa: E402
from scripted_pick_place import plan  # noqa: E402

ENVS, RESETS = [], [0]
_init, _reset = envmod.OmxCubeEnv.__init__, envmod.OmxCubeEnv.reset


def _patched_init(self, *a, **k):
    _init(self, *a, **k)
    ENVS.append(self)


def _patched_reset(self, *a, **k):
    RESETS[0] += 1
    return _reset(self, *a, **k)


envmod.OmxCubeEnv.__init__ = _patched_init
envmod.OmxCubeEnv.reset = _patched_reset


class FakeLeader:
    """Reports leader-style readings (LeRobot units) that follow the IK plan of the current episode."""

    def __init__(self, hold_s, fps):
        self.q = np.array([0, -0.3, 0.1, 1.3, 0, 0.6])
        self.traj, self.episode, self.hold = [], None, round(hold_s * fps)
        self.finished, self.finished_at = None, 0.0

    def get_action(self):
        env = ENVS[0] if ENVS else None
        if env is not None and RESETS[0] and RESETS[0] != self.episode:   # a new episode began
            self.episode = RESETS[0]
            a = env.cube_qpos_adr
            yaw = 2 * np.arctan2(env.data.qpos[a + 6], env.data.qpos[a + 3])
            start = env.data.qpos[env.qpos_ids].copy()
            self.traj = [start] * self.hold
            for q, g, n in plan(env, OmxIK(env.model), yaw):
                goal = np.append(q, g)
                self.traj += [start + (goal - start) * (i + 1) / n for i in range(n)]
                start = goal
        if self.traj:
            self.q = self.traj.pop(0)
            if not self.traj:
                self.finished, self.finished_at = self.episode, time.time()
        act = {f"{m}.pos": float(np.rad2deg(self.q[i]) / DEG_PER_UNIT) for i, m in enumerate(ARM_MOTORS)}
        act["gripper.pos"] = 50 + np.rad2deg(self.q[5]) / GRIPPER_DEG_PER_UNIT
        return act

    def disconnect(self):
        pass


def main():
    p = argparse.ArgumentParser()
    p.add_argument("script", choices=["teleop", "record"])
    p.add_argument("--hold-s", type=float, default=2.0)
    p.add_argument("--auto-enter", action="store_true")
    args, rest = p.parse_known_args()
    rest = [a for a in rest if a != "--"]

    spec = importlib.util.spec_from_file_location(args.script, ROOT / "scripts" / f"{args.script}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    leader = FakeLeader(args.hold_s, envmod.TaskConfig.fps)
    mod.connect_leader = lambda port: leader

    if args.auto_enter:
        open_viewer = mod.open_viewer

        def open_viewer_with_enter(env, key_callback=None):
            viewer, overlay = open_viewer(env, key_callback=key_callback)

            def press_when_done():
                time.sleep(1.5)
                key_callback(next(iter(ENTER_KEYS)))          # start the first recording
                pressed_for = None
                while viewer.is_running():
                    ep = RESETS[0]
                    if leader.finished == ep and pressed_for != ep and time.time() - leader.finished_at > 2.0:
                        pressed_for = ep                      # episode replayed and saved: start the next
                        key_callback(next(iter(ENTER_KEYS)))
                    time.sleep(0.2)

            threading.Thread(target=press_when_done, daemon=True).start()
            return viewer, overlay

        mod.open_viewer = open_viewer_with_enter

    sys.argv = [f"{args.script}.py"] + rest
    mod.main()


if __name__ == "__main__":
    main()
