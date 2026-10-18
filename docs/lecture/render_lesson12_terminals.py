"""Terminal captures for page ⑫ (outputs copied from the real runs on 2026-10-18, long lines cut).

  python3 docs/lecture/render_lesson12_terminals.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_terminal import render  # noqa: E402

render([("prompt", ".venv/bin/python scripts/real_record.py"),
        ("out", "dataset: /home/pw/il_omx_mujoco/data/real_strawberry_lift  (0 episodes already)"),
        ("out", "saved (done), 388 frames"),
        ("out", "saved (done), 338 frames"),
        ("out", "..."),
        ("out", "saved (done), 270 frames"),
        ("out", "saved 10/10, this session 10  [ 8.3 ms]"),
        ("out", "dataset: /home/pw/il_omx_mujoco/data/real_strawberry_lift  (10 episodes)")],
       "l12_t_record.png", highlight=("(10 episodes)",))

render([("prompt", ".venv/bin/python docs/lecture/inspect_dataset.py real_strawberry_lift"),
        ("out", "/home/pw/il_omx_mujoco/data/real_strawberry_lift: 10 episodes, 3062 frames, 30 fps, robot omx_follower"),
        ("out", "features:"),
        ("out", "  observation.state            float32  (6,)"),
        ("out", "  action                       float32  (6,)"),
        ("out", "  observation.images.front     video    (240, 320, 3)"),
        ("out", "  observation.images.wrist     video    (240, 320, 3)"),
        ("out", "  ..."),
        ("out", "  task                         'Pick up the strawberry and lift it.'"),
        ("out", "  state : [  0.855 -56.581  54.774  32.601  -0.611  49.915]"),
        ("out", "  action: [  0.855 -56.532  54.628  29.963  -0.757  47.228]"),
        ("out", "episode lengths (frames): [388, 338, 411, 240, 318, 293, 264, 293, 247, 270]  -> 10.2 s on average"),
        ("out", "size on disk: 23.3 MB")],
       "l12_t_inspect.png", highlight=("10 episodes, 3062 frames", "task "))

render([("prompt", ".venv/bin/python scripts/train.py --dataset real_strawberry_lift --steps 20000 --save-freq 5000"),
        ("out", "dataset: /home/pw/il_omx_mujoco/data/real_strawberry_lift  (10 episodes, 30 fps, ACT chunk 60 steps)"),
        ("out", "run: /home/pw/il_omx_mujoco/outputs/train/real_strawberry_lift_act  device: cuda"),
        ("out", "... dataset.num_frames=3062 (3K)"),
        ("out", "... num_learnable_params=51576710 (52M)"),
        ("out", "... step:1K smpl:8K ep:26 epch:2.61 loss:1.867 ... l1_loss:0.223"),
        ("out", "... Checkpoint policy after step 5000"),
        ("out", "..."),
        ("out", "... step:20K smpl:160K ep:523 epch:52.25 loss:0.071 ... l1_loss:0.059"),
        ("out", "... Checkpoint policy after step 20000"),
        ("out", "Training: 100%| 20000/20000 [15:50<00:00, 21.42step/s]")],
       "l12_t_train.png", highlight=("ACT chunk 60 steps", "loss:0.071"))

render([("prompt", ".venv/bin/python scripts/real_run.py --max-step 8"),
        ("out", "policy: /home/pw/il_omx_mujoco/outputs/train/real_strawberry_lift_act/checkpoints/020000/pretrained_model"),
        ("out", "30 fps, 320x240, cameras ['front', 'wrist'], device cuda"),
        ("out", "WARNING:root:Relative goal position magnitude had to be clamped to be safe."),
        ("out", "{   'shoulder_lift': {   'original goal_pos': -30.787704467773438,"),
        ("out", "                         'safe goal_pos': -24.58119658119658}}"),
        ("out", "run 1: time limit 30 s after 30.0 s"),
        ("out", "run 2: stopped after 9.3 s"),
        ("out", "run 3: stopped after 14.5 s")],
       "l12_t_run.png", highlight=("run 2:", "had to be clamped"))

render([("prompt", ".venv/bin/pip install matplotlib          # 처음 한 번"),
        ("prompt", ".venv/bin/python scripts/plot_dataset.py --dataset real_strawberry_lift"),
        ("out", "/home/pw/il_omx_mujoco/data/real_strawberry_lift: 10 episodes, 3062 frames, 30 fps"),
        ("out", "saved /home/pw/il_omx_mujoco/outputs/plots/real_strawberry_lift_joints.png"),
        ("out", "saved /home/pw/il_omx_mujoco/outputs/plots/real_strawberry_lift_lengths.png")],
       "l12_t_plot.png", highlight=("saved",))
