"""Launch a command and screenshot its MuJoCo viewer window at a fixed interval (no input is sent).

  python3 dev/capture_window.py OUT_DIR INTERVAL_S COUNT -- .venv/bin/python dev/fake_leader.py teleop -- --duration 20

The window is the one whose WM_CLASS is MuJoCo AND whose _NET_WM_PID is the launched process,
so no other window (browser, terminal) can be picked. Frames: OUT_DIR/frame_000.png ...
The command's stdout/stderr go to OUT_DIR/stdout.log. A command still running after the last
frame gets SIGINT (Ctrl+C).
"""
import signal
import subprocess
import sys
import time
from pathlib import Path


def find_window(pid, timeout=30.0):
    end = time.time() + timeout
    while time.time() < end:
        out = subprocess.run(["xdotool", "search", "--onlyvisible", "--class", "^MuJoCo$"],
                             capture_output=True, text=True).stdout.split()
        for wid in out:
            wpid = subprocess.run(["xdotool", "getwindowpid", wid], capture_output=True, text=True).stdout.strip()
            if wpid == str(pid):
                return wid
        time.sleep(0.3)
    return None


def main():
    sep = sys.argv.index("--")
    out_dir, interval, count = Path(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3])
    cmd = sys.argv[sep + 1:]
    out_dir.mkdir(parents=True, exist_ok=True)
    log = open(out_dir / "stdout.log", "w")
    # Restore default SIGINT in the child (a background shell starts it ignored), so Ctrl+C works.
    proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT,
                            preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_DFL))
    wid = find_window(proc.pid)
    if wid is None:
        print("no MuJoCo window of pid", proc.pid)
        proc.terminate()
        return
    print("window", wid, "pid", proc.pid)
    # A window that is not drawn yet shows whatever is behind it on screen; wait before the first shot.
    time.sleep(3.0)
    t0 = time.time()
    for i in range(count):
        if proc.poll() is not None:
            break
        try:   # a window that is closing can block import forever
            subprocess.run(["import", "-window", wid, str(out_dir / f"frame_{i:03d}.png")], capture_output=True,
                           timeout=5)
        except subprocess.TimeoutExpired:
            break
        time.sleep(max(0.0, t0 + (i + 1) * interval - time.time()))
    if proc.poll() is None:              # still running after the last frame: stop it like Ctrl+C
        proc.send_signal(signal.SIGINT)
    try:
        proc.wait(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
    print("done, exit", proc.returncode)


if __name__ == "__main__":
    main()
