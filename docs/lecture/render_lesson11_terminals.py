"""Terminal captures for page ⑪ (outputs copied from the real runs on 2026-10-18, long lines split).

  python3 docs/lecture/render_lesson11_terminals.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_terminal import render  # noqa: E402

render([("prompt", "ls /dev/ttyACM*            # 팔로워만 연결"),
        ("out", "/dev/ttyACM1"),
        ("prompt", "PORT=$(ls /dev/ttyACM*)"),
        ("prompt", "udevadm info -q all -n $PORT | egrep 'DEVNAME=|ID_VENDOR=|ID_VENDOR_ID=|ID_MODEL=|ID_SERIAL_SHORT='"),
        ("out", "E: DEVNAME=/dev/ttyACM1"),
        ("out", "E: ID_MODEL=OpenRB-150"),
        ("out", "E: ID_SERIAL_SHORT=C707EF98503059384C2E3120FF081924"),
        ("out", "E: ID_VENDOR=ROBOTIS"),
        ("out", "E: ID_VENDOR_ID=2f5d")],
       "l11_t_udevinfo.png", highlight=("ID_SERIAL_SHORT",))

render([("prompt", "cat /etc/udev/rules.d/99-omx-follower.rules"),
        ("out", 'SUBSYSTEM=="tty", ATTRS{idVendor}=="2f5d", ATTRS{serial}=="C707EF98503059384C2E3120FF081924", '
                'SYMLINK+="omx_follower"'),
        ("prompt", "sudo udevadm control --reload-rules"),
        ("prompt", "sudo udevadm trigger"),
        ("out", "(팔로워 USB 를 뽑았다가 다시 꽂고, 리더 USB 도 다시 꽂음)"),
        ("prompt", "ls -l /dev/omx_*"),
        ("out", "lrwxrwxrwx 1 root root 7 Oct 18 10:49 /dev/omx_follower -> ttyACM1"),
        ("out", "lrwxrwxrwx 1 root root 7 Oct 18 10:36 /dev/omx_leader -> ttyACM0")],
       "l11_t_udev.png", highlight=("/dev/omx_follower ->", "/dev/omx_leader ->"))

render([("prompt", ".venv/bin/python scripts/real_cameras.py --find"),
        ("out", "/dev/video0: Innomaker-U20CAM-720P  (USB id 0c45:6367, port pci-0000:0b:00.4-usb-0:1:1.0, 30 fps)  <- likely wrist"),
        ("out", "/dev/video2: Lenovo_FHD_Webcam_Audio  (USB id 17ef:4831, port pci-0000:0b:00.4-usb-0:2:1.0, 30 fps)"),
        ("out", "(창에 두 카메라가 /dev/videoN 이름으로 나옴. 그리퍼 손가락이 보이는 쪽이 손목 카메라)")],
       "l11_t_find.png", highlight=("/dev/video0:", "/dev/video2:"))

render([("prompt", ".venv/bin/python scripts/camera_udev_rule.py --front /dev/video2 --wrist /dev/video0 \\"),
        ("out", "    | sudo tee /etc/udev/rules.d/99-omx-cameras.rules"),
        ("out", 'SUBSYSTEM=="video4linux", ATTRS{idVendor}=="17ef", ATTRS{idProduct}=="4831", ATTR{index}=="0", '
                'SYMLINK+="cam_front"'),
        ("out", 'SUBSYSTEM=="video4linux", ATTRS{idVendor}=="0c45", ATTRS{idProduct}=="6367", ATTR{index}=="0", '
                'SYMLINK+="cam_wrist"'),
        ("prompt", "sudo udevadm control --reload-rules && sudo udevadm trigger"),
        ("prompt", "ls -l /dev/cam_*"),
        ("out", "lrwxrwxrwx 1 root root 6 Oct 18 10:37 /dev/cam_front -> video2"),
        ("out", "lrwxrwxrwx 1 root root 6 Oct 18 10:37 /dev/cam_wrist -> video0")],
       "l11_t_camrule.png", highlight=("/dev/cam_front ->", "/dev/cam_wrist ->"))

render([("prompt", ".venv/bin/python scripts/real_cameras.py"),
        ("out", "front: OpenCVCamera(/dev/cam_front)  640x480 @ 30 fps"),
        ("out", "wrist: OpenCVCamera(/dev/cam_wrist)  640x480 @ 30 fps")],
       "l11_t_cams.png", highlight=("front:", "wrist:"))

render([("prompt", ".venv/bin/python scripts/real_cameras.py --front-fps 7"),
        ("out", "The front camera (/dev/cam_front) cannot run at 7 fps (it offers 10.0). Run again with "
                "--front-fps 10, or --front-fps 0 for the camera's own rate."),
        ("prompt", ".venv/bin/python scripts/real_cameras.py --front-fps 15"),
        ("out", "front: OpenCVCamera(/dev/cam_front)  640x480 @ 15 fps"),
        ("out", "wrist: OpenCVCamera(/dev/cam_wrist)  640x480 @ 30 fps")],
       "l11_t_fps.png", highlight=("cannot run at", "@ 15 fps"))

render([("prompt", ".venv/bin/python scripts/leader_backup_eeprom.py --port /dev/omx_follower \\"),
        ("out", "    --ids 11 12 13 14 15 16 --name follower"),
        ("out", "11 {'Model_Number': 1060, ..., 'Drive_Mode': 4, 'Operating_Mode': 4, 'Homing_Offset': 0, ...}"),
        ("out", "12 {'Model_Number': 1060, ..., 'Drive_Mode': 4, 'Operating_Mode': 4, 'Homing_Offset': 0, ...}"),
        ("out", "13 {'Model_Number': 1060, ..., 'Drive_Mode': 4, 'Operating_Mode': 4, 'Homing_Offset': 0, ...}"),
        ("out", "14 {'Model_Number': 1200, ..., 'Drive_Mode': 4, 'Operating_Mode': 4, 'Homing_Offset': 0, ...}"),
        ("out", "15 {'Model_Number': 1200, ..., 'Drive_Mode': 4, 'Operating_Mode': 4, 'Homing_Offset': 0, ...}"),
        ("out", "16 {'Model_Number': 1200, ..., 'Drive_Mode': 0, 'Operating_Mode': 5, 'Homing_Offset': 0, ...}"),
        ("out", "saved /home/pw/il_omx_mujoco/calibration/follower_eeprom_backup_20261018_145849.json"),
        ("prompt", "python3 docs/lecture/compare_backups.py calibration/follower_eeprom_backup_*.json"),
        ("out", "any diff: False")],
       "l11_t_backup.png", highlight=("saved", "any diff: False"))

render([("prompt", ".venv/bin/python scripts/real_teleop.py"),
        ("out", "J1   +0.7->  +0.7  J2  -63.3-> -62.0  J3  +54.3-> +54.3  J4  +37.6-> +37.6  J5   +0.9->  +0.9"),
        ("out", "                    G  +47.1-> +47.1  load J3   5%  [ 8.0 ms]          (쉬는 자세)"),
        ("out", "J1   -1.1->  -1.1  J2  -30.5-> -30.5  J3  +22.7-> +22.7  J4  +42.8-> +42.8  J5   +1.0->  +1.0"),
        ("out", "                    G  +49.2-> +49.2  load J3  14%  [ 8.0 ms]          (팔을 세움)"),
        ("out", "J1  -23.3-> -23.3  J2  -31.2-> -31.2  J3  +23.6-> +23.6  J4  +43.2-> +43.2  J5   +0.7->  +0.7"),
        ("out", "                    G  +52.2-> +52.2  load J2  10%  [ 8.0 ms]          (베이스를 돌림)"),
        ("out", "(ESC: 끝. 한 줄 출력을 두 줄로 나눔)")],
       "l11_t_teleop.png", highlight=("-63.3-> -62.0",))

render([("prompt", ".venv/bin/python scripts/real_teleop.py"),
        ("out", "J1   ...  J2  -39.6-> -39.6  ...  load J2  88%  [ 8.1 ms]"),
        ("out", "J1   ...  J2  -32.2-> -32.2  ...  load J2 100%  [ 8.0 ms]"),
        ("out", "(창: 주황 배너 HIGH LOAD J2 100% - ease off the leader)"),
        ("out", "MOTOR ERROR shoulder_lift (ID 12): turn the follower off (power + USB) and on")],
       "l11_t_error.png", highlight=("MOTOR ERROR",))
