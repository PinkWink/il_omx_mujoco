"""Stream the OMX leader joint readings (hardware check).

Prints LeRobot's normalized values (arm -100..100, gripper 0..100). Arm joints also show degrees.

  python scripts/leader_read.py [--port /dev/ttyACM0] [--hz 10]
"""
import argparse
import sys
import time

from il_omx.leader import DEFAULT_PORT, connect_leader
from il_omx.leader_mapping import DEG_PER_UNIT


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", default=DEFAULT_PORT)
    p.add_argument("--hz", type=float, default=10.0)
    args = p.parse_args()

    leader = connect_leader(args.port)
    print("connected. Ctrl+C to stop.")
    try:
        while True:
            t0 = time.perf_counter()
            action = leader.get_action()
            read_ms = (time.perf_counter() - t0) * 1e3
            cols = []
            for k, v in action.items():
                name = k.removesuffix(".pos")
                deg = "" if name == "gripper" else f"({v * DEG_PER_UNIT:+7.1f}°)"
                cols.append(f"{name}={v:+7.2f}{deg}")
            sys.stdout.write("\r" + "  ".join(cols) + f"  [{read_ms:.1f} ms]  ")
            sys.stdout.flush()
            time.sleep(max(0.0, 1.0 / args.hz - (time.perf_counter() - t0)))
    except KeyboardInterrupt:
        print()
    finally:
        leader.disconnect()


if __name__ == "__main__":
    main()
