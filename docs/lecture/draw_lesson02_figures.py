"""Figures for page ② (environment setup and usage). Output: docs/lecture/l02_*.png

  python3 docs/lecture/draw_lesson02_figures.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figstyle import INK, RED, C, arrow, chain, fig_ax, note, rbox, save, tiles  # noqa: E402


def requirements():
    fig, ax = fig_ax(16, 4.6)
    tiles(ax, [("운영체제", ["Ubuntu 24.04 (검증 환경)", "python3-venv · git"], C["blue"]),
               ("Python", ["3.10 이상 (검증 3.12)", "venv 하나에 모두 설치"], C["grey"]),
               ("NVIDIA GPU", ["학습 · 추론에 필요", "드라이버 580 이상 (CUDA 13 휠)"], C["red"]),
               ("디스크", ["venv 약 6 GB", "학습 1회 약 3.6 GB (체크포인트 6개)"], C["yellow"]),
               ("OMX 리더", ["USB 케이블 · /dev/ttyACM0", "④ 페이지부터 사용"], C["teal"]),
               ("인터넷", ["pip 다운로드 수 GB", "menagerie 모델 git clone"], C["green"])], 3, h=1.85)
    save(fig, "l02_requirements.png")


def install_flow():
    fig, ax = fig_ax(16, 2.9)
    chain(ax, [("① apt", ["python3-venv · git"]), ("② 저장소", ["git clone"]), ("③ venv", ["pip install -e ."]),
               ("④ menagerie", ["OMX 메시 · 모델"]), ("⑤ dialout", ["시리얼 권한"]), ("⑥ 확인", ["버전 · GPU · 렌더"])],
          0.5, 1.9, gap=0.3, colors=[C["grey"], C["blue"], C["purple"], C["teal"], C["yellow"], C["green"]],
          tfs=11.5, fs=9.5)
    save(fig, "l02_install_flow.png")


def deps():
    fig, ax = fig_ax(16, 5.0)
    rbox(ax, 6.3, 3.7, 3.4, 0.9, "il-omx (이 저장소)", fc=C["grey"], tfs=11.5)
    tops = [("mujoco 3.15.0", ["물리 · 뷰어 · 렌더"], C["blue"]),
            ("lerobot 0.6.1", ["dynamixel · dataset · training"], C["purple"]),
            ("numpy · pillow · imageio", ["배열 · 이미지 · 영상"], C["grey"])]
    xs = [0.3, 5.6, 10.9]
    for (t, l, fc), x in zip(tops, xs):
        rbox(ax, x, 2.0, 4.8, 1.1, t, l, fc=fc, tfs=11, fs=9)
        ax.plot([x + 2.4, x + 2.4], [3.1, 3.35], color=INK, lw=1.4)
    ax.plot([2.7, 13.3], [3.35, 3.35], color=INK, lw=1.4); ax.plot([8.0, 8.0], [3.35, 3.7], color=INK, lw=1.4)
    arrow(ax, (8.0, 2.0), (8.0, 1.55))
    subs = ["torch 2.11.0 (CUDA 13)", "torchvision 0.26.0", "datasets 4.8.5", "av 15.1.0 · torchcodec",
            "dynamixel-sdk 3.8.4", "accelerate · einops"]
    w = (15.4 - 0.3 * 5) / 6
    for i, t in enumerate(subs):
        rbox(ax, 0.3 + i * (w + 0.3), 0.6, w, 0.9, t, fc=C["yellow"], tfs=9.3, lw=1.0)
    note(ax, 0.3, 0.2, "lerobot 이 끌어오는 주요 패키지 (venv 전체 111개, 약 5.7 GB)", fs=9.5)
    save(fig, "l02_deps.png")


def venv_python():
    fig, ax = fig_ax(16, 4.2)
    rbox(ax, 0.3, 1.0, 7.4, 2.9, "방법 A: venv 파이썬을 직접 (이 강의의 표기)",
         [".venv/bin/python scripts/teleop.py", "activate 없이 어느 터미널에서나 같은 결과",
          "명령에 venv 경로가 보여 실수가 적다"], fc=C["blue"], align="left", dy=0.45)
    rbox(ax, 8.3, 1.0, 7.4, 2.9, "방법 B: 활성화 후 python",
         ["source .venv/bin/activate", "python scripts/teleop.py", "새 터미널마다 다시 activate 해야 한다"],
         fc=C["grey"], align="left", dy=0.45)
    note(ax, 0.3, 0.45, "두 방법은 같은 파이썬을 씁니다. 저장소 폴더(il_omx_mujoco)에서 실행하세요.")
    save(fig, "l02_venv_python.png")


def scripts_map():
    fig, ax = fig_ax(16, 5.6)
    rows = [("view_scene.py · render_cameras.py", "장면 확인 · 카메라 이미지 저장", "②③", C["blue"]),
            ("leader_read.py · leader_backup_eeprom.py", "리더 관절각 읽기 · 설정 백업", "④", C["yellow"]),
            ("teleop.py", "리더로 MuJoCo 팔 조작 (녹화 없음)", "⑤", C["yellow"]),
            ("record.py", "시연 녹화 → data/<dataset>", "⑥⑧⑨", C["teal"]),
            ("train.py", "ACT 학습 → outputs/train/<dataset>_act", "⑦⑧⑨", C["purple"]),
            ("eval.py", "정책 평가 · 성공률 · 영상", "⑧⑨", C["green"]),
            ("scripted_pick_place.py", "IK 스크립트 시연 (사람 없이)", "⑩", C["grey"])]
    for i, (name, what, page, fc) in enumerate(rows):
        y = 4.75 - i * 0.68
        rbox(ax, 0.3, y, 6.0, 0.56, name, fc=fc, tfs=10.5, lw=1.0)
        rbox(ax, 6.5, y, 7.4, 0.56, what, fc="white", tfs=10, lw=1.0)
        rbox(ax, 14.1, y, 1.6, 0.56, page, fc=C["grey"], tfs=10.5, lw=1.0)
    note(ax, 0.3, 5.55, "scripts/ 아래 스크립트", bold=True, color=INK, fs=11)
    note(ax, 6.5, 5.55, "하는 일", bold=True, color=INK, fs=11)
    note(ax, 14.1, 5.55, "페이지", bold=True, color=INK, fs=11)
    save(fig, "l02_scripts_map.png")


def folders():
    fig, ax = fig_ax(16, 4.8)
    rbox(ax, 0.3, 0.6, 5.0, 3.8, "data/<dataset>/", ["record.py가 만드는 LeRobotDataset", "meta/ · data/ · videos/",
                                                    "같은 이름으로 다시 녹화하면 이어 붙음", "git에 올라가지 않음"],
         fc=C["teal"], align="left", dy=0.45)
    arrow(ax, (5.3, 2.5), (6.0, 2.5))
    rbox(ax, 6.0, 0.6, 5.0, 3.8, "outputs/train/<dataset>_act/", ["train.py가 만드는 학습 폴더",
                                                                  "checkpoints/005000 ... 030000",
                                                                  "checkpoints/last → 마지막", "체크포인트 1개 약 0.6 GB"],
         fc=C["purple"], align="left", dy=0.45)
    arrow(ax, (11.0, 2.5), (11.7, 2.5))
    rbox(ax, 11.7, 0.6, 4.0, 3.8, ".../<step>/eval/", ["eval.py 결과", "seed1000_n50.json",
                                                       "pose0.21_-0.06_0_n10.json", "같은 이름의 .mp4 영상"],
         fc=C["green"], align="left", dy=0.45)
    save(fig, "l02_folders.png")


def version_pin():
    fig, ax = fig_ax(16, 4.8)
    rbox(ax, 0.3, 0.9, 4.9, 3.5, "venv A (이 강의)", ["mujoco==3.15.0", "자기 libmujoco.so 포함", "시연 · 정책을 이 버전으로"],
         fc=C["blue"], align="left", dy=0.45)
    rbox(ax, 5.55, 0.9, 4.9, 3.5, "venv B (다른 프로젝트)", ["mujoco==3.x (다른 버전)", "자기 libmujoco.so 포함",
                                                        "A와 서로 영향 없음"], fc=C["grey"], align="left", dy=0.45)
    rbox(ax, 10.8, 0.9, 4.9, 3.5, "버전을 고정하는 이유", ["MJCF 속성 · API가 바뀔 수 있다", "접촉 · 솔버 변경 → 궤적이 조금 달라짐",
                                                      "녹화 · 학습 · 평가를 같은 버전으로"],
         fc=C["red"], align="left", dy=0.45)
    note(ax, 0.3, 0.4, "pip 휠에 MuJoCo 엔진이 들어 있어 venv마다 다른 버전을 둘 수 있습니다. "
                       "GPU 드라이버 · OpenGL · MUJOCO_GL 환경 변수는 시스템 공통입니다.")
    save(fig, "l02_version_pin.png")


def troubleshoot():
    fig, ax = fig_ax(16, 4.6)
    rows = [("ensurepip is not available", "python3-venv 없음", "sudo apt install python3-venv"),
            ("Error opening file '.../models/follower_01_base.stl'", "menagerie를 받지 않음", "④ git clone 실행"),
            ("[Errno 13] Permission denied: '/dev/ttyACM0'", "dialout 그룹이 아님", "⑤ usermod 후 로그아웃 · 로그인"),
            ("WARNING: no GPU found. On CPU a step takes ~5 s", "GPU · 드라이버 없음", "nvidia-smi 확인, GPU PC에서 학습")]
    x = [0.3, 7.6, 11.0]; w = [7.1, 3.2, 4.7]
    for j, t in enumerate(["증상 (메시지)", "원인", "해결"]):
        rbox(ax, x[j], 3.75, w[j], 0.6, t, fc=[C["grey"], C["yellow"], C["green"]][j], tfs=11)
    for i, r in enumerate(rows):
        y = 2.95 - i * 0.78
        for j, t in enumerate(r):
            rbox(ax, x[j], y, w[j], 0.64, t, fc="white", tfs=9.5 if j == 0 else 10, lw=1.0)
    save(fig, "l02_troubleshoot.png")


if __name__ == "__main__":
    for f in (requirements, install_flow, deps, venv_python, scripts_map, folders, version_pin, troubleshoot):
        f()
