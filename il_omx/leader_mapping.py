"""Map OMX leader readings (LeRobot normalized units) to sim joint targets (radians)."""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "leader_to_sim.json"

ARM_MOTORS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]
# RANGE_M100_100 over raw 0..4095 -> +/-100 spans one full turn.
DEG_PER_UNIT = 180.0 / 100.0
# The gripper uses RANGE_0_100 over raw 0..4095 -> 0..100 spans one full turn.
GRIPPER_DEG_PER_UNIT = 360.0 / 100.0


class LeaderToSim:
    """Arm: sim_rad = sign * (leader_deg + offset_deg). Gripper: the leader angle applied directly."""

    def __init__(self, config_path: Path = DEFAULT_CONFIG):
        cfg = json.loads(Path(config_path).read_text())
        joints = cfg["joints"]
        self.sign = np.array([joints[m]["sign"] for m in ARM_MOTORS], dtype=float)
        self.offset_deg = np.array([joints[m]["offset_deg"] for m in ARM_MOTORS], dtype=float)
        self.gripper_zero = float(cfg["gripper"]["zero"])

    @staticmethod
    def leader_deg(action: dict) -> np.ndarray:
        return np.array([action[f"{m}.pos"] for m in ARM_MOTORS]) * DEG_PER_UNIT

    def gripper_to_sim(self, value: float) -> float:
        """Rotate the sim gripper by the same angle as the leader trigger servo, as LeRobot does
        when it forwards the leader value straight to the real follower's gripper servo.
        Targets past closed (below zero) are clipped by the actuator range; the position actuator
        then keeps squeezing with its limited force, like the follower's current-limited mode."""
        return float(np.deg2rad((value - self.gripper_zero) * GRIPPER_DEG_PER_UNIT))

    def __call__(self, action: dict) -> np.ndarray:
        """Return the 6-dim sim action [Joint1..5, Gripper] in radians."""
        arm = np.deg2rad(self.sign * (self.leader_deg(action) + self.offset_deg))
        return np.append(arm, self.gripper_to_sim(action["gripper.pos"]))
