"""Show the USB cameras (no robot needed).

  python scripts/real_cameras.py --find   # every camera under its /dev/videoN name: which one is which?
  python scripts/real_cameras.py          # /dev/cam_front and /dev/cam_wrist after the udev rule

ESC or closing the window quits. If front and wrist are swapped, fix the camera udev rule.
"""
import argparse
import time

from il_omx.real import REAL_CAMERAS, Cameras, close_all, video_devices
from il_omx.real_ui import ESCAPE_KEY, CameraWindow


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--find", action="store_true", help="show every connected camera by its /dev/videoN name")
    p.add_argument("--zoom", type=float, default=1.5, help="window size (camera images are 320x240)")
    args = p.parse_args()

    if args.find:
        devices = video_devices()
        if not devices:
            raise SystemExit("no USB camera found")
        for d in devices:
            print(f"{d['dev']}: {d['model']}  (USB id {d['vendor']}:{d['product']}, port {d['usb_path']})")
        cams = Cameras(paths={d["dev"]: d["dev"] for d in devices})
    else:
        cams = Cameras()
        for name, cam in cams.cams.items():
            print(f"{name}: {cam}  {cam.width}x{cam.height} @ {cam.fps} fps")
    names = list(cams.cams) if args.find else REAL_CAMERAS
    window = CameraWindow("OMX cameras", names, zoom=args.zoom)
    try:
        while window.is_running() and ESCAPE_KEY not in window.poll_keys():
            window.show(cams.read(), hint="ESC: quit")
            time.sleep(1 / 30)
    except KeyboardInterrupt:
        pass
    finally:
        close_all(window.close, cams.close)


if __name__ == "__main__":
    main()
