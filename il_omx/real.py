"""Real OMX follower and its two USB cameras through LeRobot.

The leader's values go to the follower as they are (only clipped to configs/follower_limits.json):
both arms use LeRobot's normalized units (arm -100..100 = one full turn, gripper 0..100), as in
LeRobot's own omx_leader -> omx_follower teleop.
"""
import json
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np
from lerobot.cameras.opencv import OpenCVCamera, OpenCVCameraConfig
from lerobot.robots.omx_follower import OmxFollower, OmxFollowerConfig

from il_omx.leader import CALIBRATION_DIR, ROOT

# /dev/omx_follower, /dev/cam_front and /dev/cam_wrist come from the udev rules on page ⑪
FOLLOWER_PORT = "/dev/omx_follower"
CAMERA_PATHS = {"front": "/dev/cam_front", "wrist": "/dev/cam_wrist"}
REAL_CAMERAS = list(CAMERA_PATHS)
MOTORS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
ROBOT_TYPE = "omx_follower"
LIMITS_FILE = ROOT / "configs" / "follower_limits.json"

# Servo load warning: a joint above HIGH_LOAD_PCT for HIGH_LOAD_S. Pushing hard for long trips the
# servo's overload protection (red LED, torque off) until the follower is powered off and on.
HIGH_LOAD_PCT, HIGH_LOAD_S = 60.0, 0.5

# Cameras deliver 640x480; frames are shrunk to the dataset size (320x240 like the MuJoCo pages).
# CAPTURE_FPS is the default camera rate; a camera that cannot run at it takes --front-fps / --wrist-fps
# (0 = the camera's own rate). The recording rate (--fps) is separate: a slower camera repeats frames.
CAPTURE_WIDTH, CAPTURE_HEIGHT, CAPTURE_FPS = 640, 480, 30


def add_camera_fps_args(parser):
    """--front-fps and --wrist-fps for every script that opens the cameras."""
    for name in REAL_CAMERAS:
        parser.add_argument(f"--{name}-fps", type=float, default=CAPTURE_FPS,
                            help=f"{name} camera frame rate (0 = the camera's own rate; see real_cameras.py --find)")


def camera_fps(args) -> dict:
    return {name: getattr(args, f"{name}_fps") for name in REAL_CAMERAS}


def require_device(path: str, what: str):
    if not Path(path).exists():
        raise SystemExit(f"{path} not found. Plug in the {what} and check the udev rule (page ⑪).")


def to_vector(values: dict) -> np.ndarray:
    """{'shoulder_pan.pos': ..} (leader action or follower observation) -> 6 values in MOTORS order."""
    return np.array([values[f"{m}.pos"] for m in MOTORS], dtype=np.float32)


def to_action(vector) -> dict:
    return {f"{m}.pos": float(v) for m, v in zip(MOTORS, vector)}


def load_limits(path: Path = LIMITS_FILE) -> tuple[np.ndarray, np.ndarray]:
    """(low, high) 6-vectors from configs/follower_limits.json; joints not listed are unlimited."""
    cfg = json.loads(path.read_text())
    low = np.array([cfg.get(m, {}).get("min", -np.inf) for m in MOTORS], dtype=np.float32)
    high = np.array([cfg.get(m, {}).get("max", np.inf) for m in MOTORS], dtype=np.float32)
    return low, high


class Follower:
    """The real follower (LeRobot OmxFollower, calibration/omx_follower.json) with three safeguards:
    commands are clipped to configs/follower_limits.json, glide() moves slowly instead of jumping,
    and check() watches the servos' load and error flags."""

    def __init__(self, port: str = FOLLOWER_PORT, max_step: float | None = None):
        """max_step limits how far one command may move a joint from where it is now
        (normalized units, 1 = 1.8 deg); None = no limit."""
        require_device(port, "follower (OMX-F)")
        self.robot = OmxFollower(OmxFollowerConfig(port=port, id="omx_follower", calibration_dir=CALIBRATION_DIR,
                                                   max_relative_target=max_step))
        self.robot.connect()
        self.bus = self.robot.bus
        self.low, self.high = load_limits()
        self.load = np.zeros(len(MOTORS) - 1)  # arm joints, percent of the servo's maximum
        self._high_since = {}  # joint -> time its load went above HIGH_LOAD_PCT

    def state(self) -> np.ndarray:
        """Joint positions (what get_observation reports, without the camera images)."""
        return np.array(list(self.bus.sync_read("Present_Position").values()), dtype=np.float32)

    def send(self, target) -> np.ndarray:
        """Send a 6-vector or a leader action dict; returns the clipped target actually sent."""
        if isinstance(target, dict):
            target = to_vector(target)
        target = np.clip(target, self.low, self.high)
        self.robot.send_action(to_action(target))
        return target

    def glide(self, target, seconds: float = 3.0, fps: int = 30, on_step=None):
        """Move from the present pose to target in a straight line instead of at full servo speed."""
        start, target = self.state(), np.clip(np.asarray(target, dtype=np.float32), self.low, self.high)
        steps = max(1, round(seconds * fps))
        for i in range(1, steps + 1):
            t0 = time.perf_counter()
            self.send(start + (target - start) * i / steps)
            if on_step is not None:
                on_step()
            time.sleep(max(0.0, 1 / fps - (time.perf_counter() - t0)))

    def check(self) -> tuple[str | None, str | None]:
        """(error, warning) texts for the window. An error means a servo shut down (red LED)."""
        errors = [m for m, v in self.bus.sync_read("Hardware_Error_Status", normalize=False).items() if v]
        if errors:
            ids = ", ".join(f"{m} (ID {self.bus.motors[m].id})" for m in errors)
            return f"MOTOR ERROR {ids}: turn the follower off (power + USB) and on", None
        raw = self.bus.sync_read("Present_Current", normalize=False)
        now, warning = time.perf_counter(), None
        for i, m in enumerate(MOTORS[:-1]):  # the gripper squeezes at its current limit on purpose
            # XL430: Present_Load in 0.1 %. XL330: Present_Current in mA, against its Current_Limit 1750 mA.
            self.load[i] = abs(raw[m]) / (10 if self.bus.motors[m].model.startswith("xl430") else 17.5)
            if self.load[i] < HIGH_LOAD_PCT:
                self._high_since.pop(m, None)
            elif now - self._high_since.setdefault(m, now) > HIGH_LOAD_S:
                warning = f"HIGH LOAD J{i + 1} {self.load[i]:.0f}% - ease off the leader"
        return None, warning

    def disconnect(self):
        """Torque off: the arm goes limp, so leave it in its rest pose first."""
        self.robot.disconnect()


def close_all(*closers):
    """Call every close/disconnect even if one fails (e.g. a USB cable came loose mid-run)."""
    for close in closers:
        try:
            close()
        except Exception as e:  # noqa: BLE001 - report and keep closing the rest
            print(f"while closing: {type(e).__name__}: {e}")


def udev_properties(dev: str) -> dict:
    out = subprocess.run(["udevadm", "info", "-q", "property", "-n", dev], capture_output=True, text=True,
                         check=False).stdout
    return dict(line.split("=", 1) for line in out.splitlines() if "=" in line)


def video_devices() -> list:
    """Capture nodes of the connected USB cameras (each camera also has a metadata node, skipped)."""
    devices = []
    for dev in sorted(Path("/dev").glob("video*"), key=lambda d: int(d.name[5:])):
        props = udev_properties(str(dev))
        if ":capture:" in props.get("ID_V4L_CAPABILITIES", ""):
            devices.append({"dev": str(dev), "model": props.get("ID_MODEL", "?"),
                            "vendor": props.get("ID_VENDOR_ID", ""), "product": props.get("ID_MODEL_ID", ""),
                            "usb_path": props.get("ID_PATH", "")})
    return devices


class Cameras:
    """The front and wrist USB cameras, read in background threads (LeRobot OpenCVCamera).

    A camera whose USB connection drops (a loose or strained cable) shows black and is listed in
    `lost` instead of stopping the script; it is reconnected once its /dev/cam_* link is back."""

    RETRY_S = 2.0

    def __init__(self, image_width: int = 320, image_height: int = 240, paths: dict = CAMERA_PATHS,
                 fps: dict | None = None):
        """fps: {name: frames per second}, CAPTURE_FPS for names not given, 0 = the camera's own rate."""
        self.size = (image_width, image_height)
        self.paths = paths
        self.fps = {name: (fps or {}).get(name, CAPTURE_FPS) or None for name in paths}
        self.cams = {}
        self.lost = {}  # name -> time of the last (re)connect attempt
        for name, path in paths.items():
            require_device(path, f"{name} camera")
            try:
                self.cams[name] = self._connect(name)
            except RuntimeError as e:
                if "failed to set fps" not in str(e):
                    raise
                close_all(self.close)
                actual = str(e).split("actual_fps=")[-1].rstrip(").")
                raise SystemExit(f"The {name} camera ({path}) cannot run at {self.fps[name]:g} fps (it offers "
                                 f"{actual}). Run again with --{name}-fps {float(actual):g}, or --{name}-fps 0 "
                                 f"for the camera's own rate.") from None

    def _connect(self, name: str) -> OpenCVCamera:
        cam = OpenCVCamera(OpenCVCameraConfig(index_or_path=Path(self.paths[name]), fps=self.fps[name],
                                              width=CAPTURE_WIDTH, height=CAPTURE_HEIGHT, fourcc="MJPG"))
        cam.connect()
        return cam

    def _retry(self, name: str):
        if time.perf_counter() - self.lost[name] < self.RETRY_S:
            return
        self.lost[name] = time.perf_counter()
        if not Path(self.paths[name]).exists():
            return
        try:
            self.cams[name] = self._connect(name)
            del self.lost[name]
            print(f"\n{name} camera reconnected")
        except Exception:  # noqa: BLE001, S110 - still coming back; try again later
            pass

    def read(self) -> dict:
        """Newest RGB frame of each camera at the dataset size (black while a camera is lost)."""
        frames = {}
        for name in self.paths:
            if name in self.lost:
                self._retry(name)
            if name not in self.lost:
                try:
                    frames[name] = cv2.resize(self.cams[name].read_latest(), self.size,
                                              interpolation=cv2.INTER_AREA)
                    continue
                except Exception as e:  # noqa: BLE001 - USB dropped: keep going without this camera
                    print(f"\n{name} camera lost: {e}")
                    close_all(self.cams.pop(name).disconnect)
                    self.lost[name] = time.perf_counter()
            frames[name] = np.zeros((self.size[1], self.size[0], 3), np.uint8)
        return frames

    def lost_text(self) -> str | None:
        """Banner text while a camera is lost."""
        if self.lost:
            return f"CAMERA LOST {', '.join(self.lost)}: check its USB cable"
        return None

    def close(self):
        close_all(*(cam.disconnect for cam in self.cams.values()))
