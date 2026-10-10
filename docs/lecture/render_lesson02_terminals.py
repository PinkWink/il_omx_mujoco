"""Terminal captures for page ② from a fresh clone + install (outputs copied from the real run, long lines cut).

  python3 docs/lecture/render_lesson02_terminals.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_terminal import render  # noqa: E402

HOME_PROMPT = "pw@laptop:~$ "
HOME_TITLE = "pw@laptop: ~ — bash"

render([("prompt", "git clone https://github.com/PinkWink/il_omx_mujoco.git"),
        ("out", "Cloning into 'il_omx_mujoco'..."),
        ("prompt", "cd il_omx_mujoco")],
       "l02_t_clone.png", title=HOME_TITLE, prompt=HOME_PROMPT)

render([("prompt", "python3 -m venv .venv"),
        ("prompt", ".venv/bin/pip install -e ."),
        ("out", "Obtaining file:///home/pw/il_omx_mujoco"),
        ("out", "  Installing build dependencies: started"),
        ("out", "  ..."),
        ("out", "Successfully built il-omx"),
        ("out", "Installing collected packages: pytz, pyserial, pyopengl, nvidia-cusparselt-cu13, mpmath, glfw, ..."),
        ("out", "Successfully installed MarkupSafe-3.0.4 absl-py-2.5.1 accelerate-1.15.0 ... (111 packages)")],
       "l02_t_pip.png", highlight=("Successfully installed",))

render([("prompt", "git clone --depth 1 https://github.com/ROBOTIS-GIT/robotis_mujoco_menagerie.git \\"),
        ("out", "      third_party/robotis_mujoco_menagerie"),
        ("out", "Cloning into 'third_party/robotis_mujoco_menagerie'..."),
        ("prompt", "du -sh .venv third_party"),
        ("out", "5.7G\t.venv"),
        ("out", "236M\tthird_party")],
       "l02_t_menagerie.png")

render([("prompt", "sudo usermod -aG dialout $USER"),
        ("out", "(로그아웃 → 다시 로그인)"),
        ("prompt", "groups"),
        ("out", "pw adm dialout cdrom sudo dip plugdev users lpadmin"),
        ("prompt", "ls -l /dev/ttyACM0"),
        ("out", "crw-rw---- 1 root dialout 166, 0 Oct 10 09:03 /dev/ttyACM0")],
       "l02_t_dialout.png", highlight=("dialout cdrom",))

render([("prompt", ".venv/bin/python -c \"import mujoco, lerobot, torch; ...\""),
        ("out", "mujoco 3.15.0"),
        ("out", "lerobot 0.6.1"),
        ("out", "torch 2.11.0+cu130 cuda True NVIDIA GeForce RTX 5060 Ti"),
        ("prompt", "nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv"),
        ("out", "name, driver_version, memory.total [MiB]"),
        ("out", "NVIDIA GeForce RTX 5060 Ti, 580.126.16, 16311 MiB")],
       "l02_t_check.png", highlight=("mujoco 3.15.0", "cuda True"))

render([("prompt", "MUJOCO_GL=egl .venv/bin/python scripts/render_cameras.py"),
        ("out", "saved to /home/pw/il_omx_mujoco/outputs"),
        ("prompt", "ls outputs"),
        ("out", "cameras.png  global.png  wrist.png")],
       "l02_t_render.png")

render([("prompt", "MUJOCO_GL=egl .venv/bin/python scripts/render_cameras.py      # third_party/ 없이"),
        ("out", "Traceback (most recent call last):"),
        ("out", "  ..."),
        ("out", "    m = mujoco.MjModel.from_xml_path(str(SCENE_XML))"),
        ("out", "ValueError: Error: Error opening file '/home/pw/il_omx_mujoco/models/follower_01_base.stl'")],
       "l02_t_missing.png", highlight=("ValueError",))
