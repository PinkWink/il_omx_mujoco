# OMX leader + MuJoCo imitation learning

Teleoperate a simulated OMX follower with a real OMX leader arm, to collect demos for
imitation learning. Task: pick up the blue 30 mm cube and place it in the green tray.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
git clone --depth 1 https://github.com/ROBOTIS-GIT/robotis_mujoco_menagerie.git third_party/robotis_mujoco_menagerie
sudo usermod -aG dialout $USER   # serial port access; log out and back in
```

MuJoCo is pinned to `mujoco==3.15.0` in `pyproject.toml`. Keep it pinned: MJCF attributes and
the Python API can change between minor versions, and contact/solver changes make rollouts
differ slightly, so recorded demos and trained policies are only reproducible on the same
version. The pip wheel bundles its own `libmujoco.so`, so each venv can hold a different
version without conflict. Check with:

```bash
.venv/bin/python -c "import mujoco; print(mujoco.__version__)"   # 3.15.0
```

## Usage

```bash
.venv/bin/python scripts/teleop.py                # practice teleop: ENTER = new episode, SUCCESS banner,
                                                  #   camera views on the right (--camera-fps N, 0 = off)
.venv/bin/python scripts/record.py --dataset omx_cube_to_tray --num-episodes 50
                                                  # record demos into data/<dataset> (see below)
.venv/bin/python scripts/train.py --dataset omx_cube_to_tray
                                                  # train ACT -> outputs/train/<dataset>_act (see below)
.venv/bin/python scripts/eval.py --run omx_cube_to_tray_act --episodes 50
                                                  # success rate of the trained policy in sim (--view to watch)
.venv/bin/python scripts/leader_read.py           # hardware check: print leader angles
.venv/bin/python scripts/view_scene.py            # scene only, no leader
MUJOCO_GL=egl .venv/bin/python scripts/render_cameras.py                  # outputs/cameras.png
.venv/bin/python scripts/scripted_pick_place.py --episodes 10   # IK demo, checks the task is solvable
.venv/bin/python scripts/scripted_pick_place.py --episodes 30 --dataset omx_cube_scripted
                                                  # record IK demos (new random cube pose each episode)
.venv/bin/python scripts/leader_backup_eeprom.py  # read-only backup of the leader servo settings
```

Defaults (`TaskConfig` in `il_omx/env.py`): 10 Hz control and recording, 320x240 camera images.
Practice, recording, training and evaluation all use the same rate.

## Recording

Click the viewer window once so it has keyboard focus.

| Key | Idle | Recording |
|---|---|---|
| ENTER | new cube position, start recording | cancel, discard the episode |
| BACKSPACE | delete the episode saved last in this session (once) | discard the episode |

The banner at the top shows `REC <time>`, `OK` once the task succeeded, then `SAVED episode N`.
An episode is saved automatically 0.5 s after success (cube resting in the tray, gripper open);
episodes over 60 s are discarded. Every saved episode is finalized on disk immediately, so a crash
loses at most the episode in progress. Running again with the same `--dataset` appends.
Datasets stay in `data/` (git-ignored) and are never uploaded.

## Training

`scripts/train.py` runs LeRobot's ACT training offline on `data/<dataset>` (at least 5 episodes).
Defaults: 30,000 steps, batch 8, a checkpoint every 5,000 steps (~0.6 GB each), ACT action chunk of
2 s (20 steps at 10 Hz), mixed precision on NVIDIA GPUs. Ctrl+C stops it; `--resume` continues from
the last checkpoint, and `--resume --steps N` trains longer.

Measured on an RTX 5060 Ti at 320x240 x 2 cameras: ~22 steps/s (30,000 steps in ~25 min), 1.3 GB GPU
memory. CPU training is about 25x slower, so train on a GPU machine.

## Evaluation

`scripts/eval.py` runs the policy on new cube placements (seeds 1000+, never used for demos) and
counts an episode as a success when the cube rests in the tray with the gripper open, within 20 s.
Results and a video go to `<checkpoint>/eval/`.

Reference run: 30 scripted demos (`omx_cube_scripted`), default training, 50 eval episodes.
The scripted IK demo itself solves all 50 placements.

| Checkpoint | 5k | 10k | 15k | 20k | 25k | 30k |
|---|---|---|---|---|---|---|
| Success rate | 10% | 24% | 44% | 48% | 60% | 86% |

All failures were missed or slipped grasps: the policy then carries on to the tray empty-handed,
because the demos never show a retry. Human demos that include recoveries help here.

Diversity experiment: 5 scripted demos with the cube always at the same pose (`--fixed-cube`, i.e. x 0.21, y -0.06, yaw 0;
the sim is deterministic, so the 5 demos are identical). Same training, 30k steps.

| Eval | 5 fixed demos | 30 random demos |
|---|---|---|
| Training pose | 100% (already at 5k steps) | 100% |
| Cube moved 1 / 2 / 3 / 4 / 6 cm (8 directions each) | 8 / 7 / 0 / 0 / 0 of 8 | 8 / 8 / 7 / 7 / 3 of 8 |
| 50 random placements | 18% (all within 1.7 cm of the training pose) | 86% |

The fixed-pose policy replays the memorized motion wherever the cube is, although its training loss is
lower (L1 0.024 vs 0.042).

## Class exercise: 5 fixed demos vs 50 varied demos

`--fixed-cube` puts the cube at the same pose every episode (x 0.21, y -0.06, yaw 0, the center of
the random region). Without it, every episode gets a new pose within x 0.17-0.25, y -0.10 to -0.02,
yaw +-45 deg. `teleop.py`, `record.py`, `scripted_pick_place.py` and `eval.py` all take it.

```bash
# 1. 5 demos, cube never moves
.venv/bin/python scripts/record.py --dataset my_fixed5 --num-episodes 5 --fixed-cube
.venv/bin/python scripts/train.py --dataset my_fixed5
.venv/bin/python scripts/eval.py --run my_fixed5_act --fixed-cube --episodes 10 --view   # same pose as the demos
.venv/bin/python scripts/eval.py --run my_fixed5_act --episodes 20 --view                # cube moved and rotated

# 2. 50 demos, new cube pose every episode
.venv/bin/python scripts/record.py --dataset my_random50 --num-episodes 50
.venv/bin/python scripts/train.py --dataset my_random50
.venv/bin/python scripts/eval.py --run my_random50_act --fixed-cube --episodes 10 --view
.venv/bin/python scripts/eval.py --run my_random50_act --episodes 20 --view
```

With scripted demos instead of human ones (Evaluation above), step 1 gave 100% at the training pose
and 18% on random poses, and 30 varied demos gave 86% on random poses.

## Layout

| Path | Contents |
|---|---|
| `models/omx_follower.xml` | ROBOTIS menagerie OMX, plus box finger pads (the curved finger meshes become fat convex hulls), a wrist camera and a `tcp` site |
| `models/scene_cube.xml` | Table, cube, tray, global camera, `home` keyframe |
| `il_omx/env.py` | `OmxCubeEnv`: `reset()` randomizes the cube, `step(action)` at 30 Hz, camera images, `is_success()` |
| `il_omx/leader.py` | `connect_leader()` using `calibration/omx_leader.json` |
| `il_omx/leader_mapping.py` | `LeaderToSim`: leader reading -> 6 sim joint targets (rad), from `configs/leader_to_sim.json` |
| `il_omx/ik.py` | Damped least-squares IK for the scripted demo |
| `il_omx/dataset.py` | LeRobotDataset features and `EpisodeRecorder` (save / discard / delete last) |
| `il_omx/teleop_ui.py` | Viewer setup and key codes shared by `teleop.py` and `record.py` |
| `il_omx/viewer_overlay.py` | `ViewerOverlay` (camera insets + banner) and the behind-the-robot view for the MuJoCo viewer |
| `calibration/` | LeRobot leader calibration and the EEPROM backup |

## Conventions

- **Action** = 6 joint position targets in radians: `Joint1..Joint5, Gripper`.
- **Arm joints**: leader degrees map 1:1 to sim joints (sign +1, offset 0) for arms assembled per the ROBOTIS manual.
- **Gripper**: the leader trigger angle is applied directly, as LeRobot forwards the leader value to the real
  follower: `sim_rad = (leader - 50) * 3.6 deg`. Sim gripper 0 = closed. Releasing the trigger (60) opens
  36 deg; squeezing (~47) targets past closed, so the actuator keeps gripping with its limited force.
- **Success**: cube rests inside the tray and the fingers no longer touch it.
