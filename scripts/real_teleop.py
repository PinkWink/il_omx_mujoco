"""Teleoperate the real OMX follower with the OMX leader, watching both cameras (nothing is recorded).

At start the follower glides to the leader's pose in --start-s seconds (hold the leader still),
then it follows the leader. Close the window or press ESC to quit; the follower's torque turns
off then, so put the leader (and with it the follower) in its rest pose first.

An orange HIGH LOAD banner means a joint is pushing hard (against the table, the strawberry or its own
stop): ease off the leader. A red MOTOR ERROR means a servo shut down (red LED on the servo):
quit, unplug the follower's power and USB, plug both back in and start again.

  python scripts/real_teleop.py [--fps 30] [--zoom 2] [--front-fps 30]
"""
import argparse
import csv
import sys
import time

import numpy as np

from il_omx.leader import DEFAULT_PORT, connect_leader
from il_omx.real import (FOLLOWER_PORT, MOTORS, REAL_CAMERAS, Cameras, Follower, add_camera_fps_args, camera_fps,
                         close_all, to_vector)
from il_omx.real_ui import ESCAPE_KEY, GRAY, ORANGE, RED, CameraWindow


def status_line(leader: np.ndarray, follower: np.ndarray, load: np.ndarray) -> str:
    """Leader -> follower per joint (J1..J5 = shoulder_pan..wrist_roll, G = gripper), normalized units,
    then the highest arm load."""
    labels = [f"J{i + 1}" for i in range(len(MOTORS) - 1)] + ["G"]
    joints = "  ".join(f"{n} {a:+6.1f}->{b:+6.1f}" for n, a, b in zip(labels, leader, follower))
    return f"{joints}  load J{np.argmax(load) + 1} {load.max():3.0f}%"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", default=DEFAULT_PORT, help="leader port")
    p.add_argument("--follower-port", default=FOLLOWER_PORT)
    p.add_argument("--fps", type=int, default=30, help="control rate")
    p.add_argument("--start-s", type=float, default=3.0, help="time to glide to the leader's pose at start")
    p.add_argument("--zoom", type=float, default=2.0, help="window size (camera images are 320x240)")
    add_camera_fps_args(p)
    p.add_argument("--log", help="CSV file: leader, sent target, follower position and arm load every frame")
    args = p.parse_args()

    cams = Cameras(fps=camera_fps(args))
    leader = connect_leader(args.port)
    follower = Follower(args.follower_port)
    window = CameraWindow("OMX teleop", REAL_CAMERAS, zoom=args.zoom)
    dt = 1.0 / args.fps

    def show_start():
        window.poll_keys()
        window.show(cams.read(), "MOVING TO LEADER POSE ...", GRAY)

    error = None
    log = None
    if args.log:
        log_file = open(args.log, "w", newline="")  # noqa: SIM115 - closed in finally
        log = csv.writer(log_file)
        log.writerow(["t"] + [f"{k}_{m}" for k in ("leader", "sent", "pos") for m in MOTORS]
                     + [f"load_{m}" for m in MOTORS[:-1]])
    t_start = time.perf_counter()
    try:
        follower.glide(to_vector(leader.get_action()), args.start_s, args.fps, on_step=show_start)
        last_print = time.perf_counter()
        while window.is_running() and ESCAPE_KEY not in window.poll_keys():
            t0 = time.perf_counter()
            if error is None:
                error, warning = follower.check()
            if error is not None:  # a servo is off: stop commanding, keep showing what to do
                window.show(cams.read(), error.split(":")[0], RED, error.split(": ")[1] + "    ESC: quit")
                time.sleep(dt)
                continue
            action = leader.get_action()
            sent = follower.send(action)
            if log:
                log.writerow([f"{t0 - t_start:.3f}", *to_vector(action).round(2), *sent.round(2),
                              *follower.state().round(2), *follower.load.round(1)])
            images = cams.read()
            banner = (cams.lost_text(), RED) if cams.lost else (warning, ORANGE) if warning else ("", GRAY)
            window.show(images, *banner, hint="ESC: quit (rest pose first)")

            loop_ms = (time.perf_counter() - t0) * 1e3
            if t0 - last_print > 0.5:
                slow = "  SLOW" if loop_ms > dt * 1e3 else ""
                sys.stdout.write("\r" + status_line(to_vector(action), sent, follower.load)
                                 + f"  [{loop_ms:4.1f} ms]{slow}   ")
                sys.stdout.flush()
                last_print = t0
            time.sleep(max(0.0, dt - (time.perf_counter() - t0)))
    except KeyboardInterrupt:
        pass
    finally:
        print()
        if error is not None:
            print(error)
        if log:
            log_file.close()
        close_all(window.close, follower.disconnect, leader.disconnect, cams.close)


if __name__ == "__main__":
    main()
