"""OMX leader arm connection through LeRobot."""
from pathlib import Path

from lerobot.teleoperators.omx_leader import OmxLeader, OmxLeaderConfig

ROOT = Path(__file__).resolve().parents[1]
CALIBRATION_DIR = ROOT / "calibration"
DEFAULT_PORT = "/dev/ttyACM0"


def connect_leader(port: str = DEFAULT_PORT) -> OmxLeader:
    """Connect using the project's calibration file (calibration/omx_leader.json)."""
    leader = OmxLeader(OmxLeaderConfig(port=port, id="omx_leader", calibration_dir=CALIBRATION_DIR))
    leader.connect()
    return leader
