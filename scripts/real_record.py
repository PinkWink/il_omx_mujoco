"""Record teleoperated demos on the real OMX follower into a local LeRobotDataset (data/<dataset>).

Window controls (click the camera window first so it has keyboard focus):
  ENTER      idle      -> start recording (place the strawberry and hold the leader at its start pose first)
  ENTER      recording -> the demo is done: save the episode
  BACKSPACE  recording -> discard the episode
  BACKSPACE  idle      -> delete the episode saved last in this session (once, e.g. a sloppy demo)
  ESC                  -> quit (put the leader in its rest pose first; the follower's torque turns off)
Between episodes the follower keeps following the leader, so you can reset the scene with it.
Episodes longer than --max-episode-s are discarded. An orange HIGH LOAD banner means a joint is
pushing hard: ease off the leader. A red MOTOR ERROR (red LED on a servo) discards the episode in
progress; quit, unplug the follower's power and USB, plug both back in and run again (it appends).
A red CAMERA LOST (a camera's USB dropped) also discards the episode in progress; recording can
start again once the camera is back (it reconnects by itself; check its cable).

  python scripts/real_record.py [--dataset real_strawberry_lift] [--num-episodes 10] [--fps 30]

Each frame holds the follower's joint positions and both camera images (observation) and the
leader's values sent to the follower, after the soft limits (action), in LeRobot's normalized units.
Running again with the same --dataset appends episodes.
"""
import argparse
import os
import sys
import time

os.environ.setdefault("SVT_LOG", "1")  # keep the AV1 encoder's info logs out of the terminal

from il_omx.dataset import DATA_DIR, EpisodeRecorder
from il_omx.leader import DEFAULT_PORT, connect_leader
from il_omx.real import (FOLLOWER_PORT, MOTORS, REAL_CAMERAS, ROBOT_TYPE, Cameras, Follower, add_camera_fps_args,
                         camera_fps, close_all, to_vector)
from il_omx.real_ui import BACKSPACE_KEY, ENTER_KEYS, ESCAPE_KEY, GRAY, GREEN, ORANGE, RED, CameraWindow

NOTICE_S = 2.0  # how long "SAVED" / "DISCARDED" notices stay on screen


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", default=DEFAULT_PORT, help="leader port")
    p.add_argument("--follower-port", default=FOLLOWER_PORT)
    p.add_argument("--dataset", default="real_strawberry_lift", help=f"folder name under {DATA_DIR}")
    p.add_argument("--task", default="Pick up the strawberry and lift it.",
                   help="task text stored with every frame")
    p.add_argument("--num-episodes", type=int, default=10, help="stop accepting new episodes after this many")
    p.add_argument("--fps", type=int, default=30, help="control and recording rate")
    p.add_argument("--image-height", type=int, default=240)
    p.add_argument("--image-width", type=int, default=320)
    p.add_argument("--max-episode-s", type=float, default=60.0)
    p.add_argument("--start-s", type=float, default=3.0, help="time to glide to the leader's pose at start")
    p.add_argument("--zoom", type=float, default=2.0, help="window size")
    add_camera_fps_args(p)
    args = p.parse_args()

    recorder = EpisodeRecorder(args.dataset, args.fps, args.image_height, args.image_width,
                               joint_names=[f"{m}.pos" for m in MOTORS], cameras=REAL_CAMERAS,
                               robot_type=ROBOT_TYPE, task=args.task)
    print(f"dataset: {recorder.root}  ({recorder.num_episodes} episodes already)")

    cams = Cameras(args.image_width, args.image_height, fps=camera_fps(args))
    leader = connect_leader(args.port)
    follower = Follower(args.follower_port)
    window = CameraWindow("OMX record", REAL_CAMERAS, args.image_width, args.image_height, args.zoom)
    dt = 1.0 / args.fps

    recording = False
    notice, notice_until = None, 0.0
    saved_this_session = 0
    can_delete = False  # the newest episode was saved in this session and not deleted yet
    error = None

    def set_notice(text, color):
        nonlocal notice, notice_until
        notice, notice_until = (text, color), time.perf_counter() + NOTICE_S

    def show_busy(text):
        window.show(cams.read(), text, GRAY)

    try:
        follower.glide(to_vector(leader.get_action()), args.start_s, args.fps,
                       on_step=lambda: (window.poll_keys(), show_busy("MOVING TO LEADER POSE ...")))
        last_print = time.perf_counter()
        while window.is_running():
            t0 = time.perf_counter()
            keys = window.poll_keys()
            if ESCAPE_KEY in keys:
                break
            if error is None:
                error, warning = follower.check()
                if error is not None:
                    print(f"\n{error}")
                    if recording:
                        recording = False
                        recorder.discard()
            if error is not None:  # a servo is off: stop commanding, keep showing what to do
                window.show(cams.read(), error.split(":")[0], RED, error.split(": ")[1] + "    ESC: quit")
                time.sleep(dt)
                continue
            state = follower.state()
            images = cams.read()
            lost = cams.lost_text()
            if lost and recording:
                recording = False
                recorder.discard()
                print("\ndiscarded (camera lost)")
            sent = follower.send(leader.get_action())
            if recording:
                recorder.add({"state": state, **images}, sent)  # observation at t + action sent at t

            finish = None  # (save, reason) once the episode ends this frame
            if any(k in ENTER_KEYS for k in keys):
                if recording:
                    finish = (True, "done")
                elif recorder.num_episodes < args.num_episodes and not lost:
                    recording = True
            elif BACKSPACE_KEY in keys:
                if recording:
                    finish = (False, "backspace")
                elif can_delete:
                    show_busy("DELETING ...")
                    deleted = recorder.num_episodes
                    recorder.delete_last()
                    saved_this_session -= 1
                    can_delete = False
                    set_notice(f"DELETED  episode {deleted}", RED)
                    print(f"\ndeleted episode {deleted}")
            if recording and finish is None and recorder.frames >= args.max_episode_s * args.fps:
                finish = (False, "time limit")

            # Saving takes a moment (video encoding); the follower holds its last target meanwhile.
            if finish is not None:
                save, reason = finish
                recording = False
                n_frames = recorder.frames
                if save:
                    show_busy("SAVING ...")
                    recorder.save()
                    saved_this_session += 1
                    can_delete = True
                    set_notice(f"SAVED  episode {recorder.num_episodes}", GREEN)
                else:
                    recorder.discard()
                    set_notice(f"DISCARDED  ({reason})", GRAY)
                print(f"\n{'saved' if save else 'discarded'} ({reason}), {n_frames} frames")

            if recording:
                rec = f"REC  {recorder.frames / args.fps:4.1f} s"
                banner = (f"{rec}   {warning}", ORANGE) if warning else (rec, RED)
                hint = "ENTER: save episode    BACKSPACE: discard"
            else:
                if lost:
                    banner = (lost, RED)
                elif time.perf_counter() < notice_until:
                    banner = notice
                elif recorder.num_episodes >= args.num_episodes:
                    banner = ("DONE  -  ESC to quit", GREEN)
                elif warning:
                    banner = (warning, ORANGE)
                else:
                    banner = ("", GRAY)
                hint = "ENTER: start recording" + (f"    BACKSPACE: delete episode {recorder.num_episodes}"
                                                   if can_delete else "") + "    ESC: quit"
            window.show(images, *banner, hint=hint,
                        info=f"{args.dataset}  {recorder.num_episodes} / {args.num_episodes}")

            loop_ms = (time.perf_counter() - t0) * 1e3
            if t0 - last_print > 0.5:
                slow = "  SLOW: lower --fps" if loop_ms > dt * 1e3 else ""
                sys.stdout.write(f"\rsaved {recorder.num_episodes}/{args.num_episodes}, this session "
                                 f"{saved_this_session}  [{loop_ms:4.1f} ms]{slow}   ")
                sys.stdout.flush()
                last_print = t0
            time.sleep(max(0.0, dt - (time.perf_counter() - t0)))
    except KeyboardInterrupt:
        pass
    finally:
        print()
        recorder.close()
        print(f"dataset: {recorder.root}  ({recorder.num_episodes} episodes)")
        close_all(window.close, follower.disconnect, leader.disconnect, cams.close)


if __name__ == "__main__":
    main()
