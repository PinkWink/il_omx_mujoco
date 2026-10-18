"""Print the udev rule that names the two USB cameras /dev/cam_front and /dev/cam_wrist.

  python scripts/camera_udev_rule.py --front /dev/video2 --wrist /dev/video0 \
      | sudo tee /etc/udev/rules.d/99-omx-cameras.rules

Find the numbers first with `python scripts/real_cameras.py --find`. Two different camera models
are told apart by their USB vendor:product id, wherever they are plugged in. Two cameras of the
same model look identical (the serial is often a dummy like SN0001), so then the rule uses the
USB port instead: always plug each camera into the same port afterwards.
"""
import argparse
import sys

from il_omx.real import udev_properties

RULE = 'SUBSYSTEM=="video4linux", {match}, ATTR{{index}}=="0", SYMLINK+="{name}"'


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--front", required=True, help="/dev/videoN of the front camera")
    p.add_argument("--wrist", required=True, help="/dev/videoN of the wrist camera")
    args = p.parse_args()

    if args.front == args.wrist:
        raise SystemExit("--front and --wrist must be two different cameras")
    props = {name: udev_properties(dev) for name, dev in (("cam_front", args.front), ("cam_wrist", args.wrist))}
    ids = {name: (pr.get("ID_VENDOR_ID"), pr.get("ID_MODEL_ID")) for name, pr in props.items()}
    if None in ids["cam_front"] + ids["cam_wrist"]:
        raise SystemExit("not a USB camera; check the numbers with: python scripts/real_cameras.py --find")
    same_model = ids["cam_front"] == ids["cam_wrist"]
    if same_model:
        print("same camera model twice: matching by USB port, keep each camera in its port", file=sys.stderr)
    for name, pr in props.items():
        if same_model:
            match = f'ENV{{ID_PATH}}=="{pr["ID_PATH"]}"'
        else:
            match = f'ATTRS{{idVendor}}=="{pr["ID_VENDOR_ID"]}", ATTRS{{idProduct}}=="{pr["ID_MODEL_ID"]}"'
        print(RULE.format(match=match, name=name))


if __name__ == "__main__":
    main()
