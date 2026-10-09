"""Run scripts/record.py with a fake leader that replays the scripted IK demo."""
import os; os.environ["MUJOCO_GL"] = "egl"; os.environ["SVT_LOG"] = "1"
import sys, numpy as np, importlib.util
sys.path.insert(0, "scripts")
import il_omx.env as envmod
from il_omx.ik import OmxIK
from il_omx.leader_mapping import ARM_MOTORS, DEG_PER_UNIT, GRIPPER_DEG_PER_UNIT
from scripted_pick_place import plan
spec = importlib.util.spec_from_file_location("record", "scripts/record.py"); rec = importlib.util.module_from_spec(spec); spec.loader.exec_module(rec)

ENVS = []
orig_init = envmod.OmxCubeEnv.__init__
def init(self, *a, **k): orig_init(self, *a, **k); ENVS.append(self)
rec.OmxCubeEnv.__init__ = init
RESETS = []
orig_reset = envmod.OmxCubeEnv.reset
def reset(self, *a, **k): RESETS.append(1); return orig_reset(self, *a, **k)
rec.OmxCubeEnv.reset = reset

class FakeLeader:
    def __init__(self): self.q = np.array([0, -0.3, 0.1, 1.3, 0, 0.6]); self.traj = []; self.cube = None
    def get_action(self):
        env = ENVS[0] if ENVS else None
        if env is not None:
            if len(RESETS) != self.cube:   # new episode
                self.cube = len(RESETS)
                a = env.cube_qpos_adr; yaw = 2*np.arctan2(env.data.qpos[a+6], env.data.qpos[a+3])
                start = env.data.qpos[env.qpos_ids].copy(); self.traj = []
                for q, g, n in plan(env, OmxIK(env.model), yaw):
                    goal = np.append(q, g)
                    self.traj += [start + (goal - start) * (i + 1) / n for i in range(n)]; start = goal
            if self.traj: self.q = self.traj.pop(0)
        act = {f"{m}.pos": float(np.rad2deg(self.q[i]) / DEG_PER_UNIT) for i, m in enumerate(ARM_MOTORS)}
        act["gripper.pos"] = 50 + np.rad2deg(self.q[5]) / GRIPPER_DEG_PER_UNIT
        return act
    def disconnect(self): pass

rec.connect_leader = lambda port: FakeLeader()
sys.argv = ["record.py", "--dataset", "_e2e", "--num-episodes", "2"]
rec.main()
