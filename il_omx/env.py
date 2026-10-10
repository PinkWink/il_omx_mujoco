"""MuJoCo task: the OMX follower picks the blue cube and places it in the green tray.

Action = 6 joint position targets (Joint1..5, Gripper) in radians, the same layout
the OMX leader arm reports. Observation state = the follower's current joint positions.
"""
from dataclasses import dataclass
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCENE_XML = ROOT / "models" / "scene_cube.xml"

JOINT_NAMES = ["Joint1", "Joint2", "Joint3", "Joint4", "Joint5", "Gripper"]
CAMERA_NAMES = ["global", "wrist"]

# The cube pose for --fixed-cube: the center of the random spawn region, not rotated (x, y, yaw rad).
FIXED_CUBE_POSE = (0.21, -0.06, 0.0)


def add_cube_args(parser):
    """--fixed-cube / --cube-pose, shared by teleop, record, scripted demos and eval."""
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--fixed-cube", action="store_true",
                   help=f"same cube pose every episode (x {FIXED_CUBE_POSE[0]}, y {FIXED_CUBE_POSE[1]}, yaw 0); "
                        "default: a new random pose each episode")
    g.add_argument("--cube-pose", type=float, nargs=3, metavar=("X", "Y", "YAW_DEG"),
                   help="same cube pose every episode, given explicitly")


def cube_pose_from_args(args) -> tuple | None:
    """(x, y, yaw rad) for a fixed cube, or None for a random pose each episode."""
    if args.fixed_cube:
        return FIXED_CUBE_POSE
    if args.cube_pose:
        x, y, yaw_deg = args.cube_pose
        return (x, y, np.deg2rad(yaw_deg))
    return None


def describe_cube(cube_pose: tuple | None) -> str:
    if cube_pose is None:
        return "random pose each episode"
    x, y, yaw = cube_pose
    return f"fixed at x {x:g}, y {y:g}, yaw {np.rad2deg(yaw):g} deg"


@dataclass
class TaskConfig:
    # 10 Hz and 320x240 keep recording and training light enough for ordinary classroom PCs.
    fps: int = 10
    image_height: int = 240
    image_width: int = 320
    # Cube spawn region (world xy, meters) and yaw range (radians).
    cube_x_range: tuple = (0.17, 0.25)
    cube_y_range: tuple = (-0.10, -0.02)
    cube_yaw_range: tuple = (-np.pi / 4, np.pi / 4)
    # Cube center must be inside the tray by this margin from the inner walls.
    tray_margin: float = 0.005


class OmxCubeEnv:
    CUBE_HALF = 0.015
    TRAY_INNER_HALF = 0.040

    def __init__(self, config: TaskConfig | None = None, render: bool = True):
        self.cfg = config or TaskConfig()
        self.model = mujoco.MjModel.from_xml_path(str(SCENE_XML))
        # Integer number of physics steps per control step at the requested fps.
        self.n_substeps = max(1, round(1.0 / (self.cfg.fps * self.model.opt.timestep)))
        self.model.opt.timestep = 1.0 / (self.cfg.fps * self.n_substeps)
        self.data = mujoco.MjData(self.model)

        m = self.model
        self.qpos_ids = np.array([m.jnt_qposadr[m.joint(n).id] for n in JOINT_NAMES])
        self.actuator_ids = np.array([m.actuator(n).id for n in JOINT_NAMES])
        self.ctrl_low = m.actuator_ctrlrange[self.actuator_ids, 0]
        self.ctrl_high = m.actuator_ctrlrange[self.actuator_ids, 1]
        self.cube_qpos_adr = m.jnt_qposadr[m.joint("cube_joint").id]
        self.cube_body = m.body("cube").id
        self.cube_geom = m.geom("cube").id
        self.tray_body = m.body("tray").id
        self.finger_geoms = {m.geom(n).id for n in (
            "finger_l_base", "finger_l_mid", "finger_l_tip",
            "finger_r_base", "finger_r_mid", "finger_r_tip")}
        self.home_key = m.key("home").id

        self.renderer = (
            mujoco.Renderer(m, self.cfg.image_height, self.cfg.image_width) if render else None
        )
        self.rng = np.random.default_rng()

    # ------------------------------------------------------------------ core API
    def reset(self, seed: int | None = None, cube_pose: tuple | None = None,
              arm_q: np.ndarray | None = None, render: bool = True) -> dict:
        """Reset with a new cube. cube_pose = (x, y, yaw) or None to randomize.

        arm_q = 6 joint positions to start from (e.g. the leader's current pose, so the arm
        does not jump); None uses the home keyframe."""
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        mujoco.mj_resetDataKeyframe(self.model, self.data, self.home_key)
        if arm_q is not None:
            q = np.clip(arm_q, self.ctrl_low, self.ctrl_high)
            self.data.qpos[self.qpos_ids] = q
            self.data.qpos[self.qpos_ids[-1] + 1] = -q[-1]  # gripper mimic joint
            self.data.ctrl[self.actuator_ids] = q
        if cube_pose is None:
            c = self.cfg
            cube_pose = (
                self.rng.uniform(*c.cube_x_range),
                self.rng.uniform(*c.cube_y_range),
                self.rng.uniform(*c.cube_yaw_range),
            )
        x, y, yaw = cube_pose
        a = self.cube_qpos_adr
        self.data.qpos[a:a + 3] = [x, y, self.CUBE_HALF]
        self.data.qpos[a + 3:a + 7] = [np.cos(yaw / 2), 0, 0, np.sin(yaw / 2)]
        mujoco.mj_forward(self.model, self.data)
        return self.get_observation(render)

    def step(self, action: np.ndarray, render: bool = True) -> dict:
        """Apply 6 joint position targets and advance one control period.

        render=False skips the camera images (they cost far more than the physics)."""
        action = np.clip(np.asarray(action, dtype=float), self.ctrl_low, self.ctrl_high)
        self.data.ctrl[self.actuator_ids] = action
        mujoco.mj_step(self.model, self.data, nstep=self.n_substeps)
        return self.get_observation(render)

    def get_observation(self, render: bool = True) -> dict:
        obs = {"state": self.data.qpos[self.qpos_ids].copy()}
        if render and self.renderer is not None:
            for cam in CAMERA_NAMES:
                obs[cam] = self.render(cam)
        return obs

    def render(self, camera: str) -> np.ndarray:
        self.renderer.update_scene(self.data, camera=camera)
        return self.renderer.render()

    # ------------------------------------------------------------------ task
    @property
    def cube_pos(self) -> np.ndarray:
        return self.data.xpos[self.cube_body].copy()

    def cube_touching_gripper(self) -> bool:
        for i in range(self.data.ncon):
            c = self.data.contact[i]
            pair = {c.geom1, c.geom2}
            if self.cube_geom in pair and pair & self.finger_geoms:
                return True
        return False

    def is_success(self) -> bool:
        """Cube rests inside the tray and the gripper has let go of it."""
        rel = self.cube_pos - self.data.xpos[self.tray_body]
        limit = self.TRAY_INNER_HALF - self.CUBE_HALF - self.cfg.tray_margin
        inside = abs(rel[0]) < limit and abs(rel[1]) < limit
        resting = rel[2] < self.CUBE_HALF + 0.008
        return bool(inside and resting and not self.cube_touching_gripper())

    def close(self):
        if self.renderer is not None:
            self.renderer.close()
            self.renderer = None
