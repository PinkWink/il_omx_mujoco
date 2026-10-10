"""Figures for page ① (introduction and curriculum). Output: docs/lecture/l01_*.png

  MUJOCO_GL=egl .venv/bin/python docs/lecture/render_sim.py      # robot renders first
  python3 docs/lecture/draw_lesson01_figures.py
"""
import json
import sys
from pathlib import Path

import numpy as np
from matplotlib.patches import Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figstyle import BLUE, GREEN, GREY, INK, OUT, RED, C, arrow, chain, fig_ax, flow_rows, image, label, note, rbox, save, tiles  # noqa: E402

ROOT = OUT.parents[1]

# Same values as il_omx/env.py (TaskConfig and FIXED_CUBE_POSE) and models/scene_cube.xml.
X_RANGE, Y_RANGE, YAW_RANGE = (0.17, 0.25), (-0.10, -0.02), (-np.pi / 4, np.pi / 4)
FIXED = (0.21, -0.06, 0.0)
TRAY_XY, TRAY_HALF, CUBE_HALF = (0.18, 0.13), 0.044, 0.015


def cube_pose(seed):
    """The pose OmxCubeEnv.reset(seed=seed) draws."""
    rng = np.random.default_rng(seed)
    return rng.uniform(*X_RANGE), rng.uniform(*Y_RANGE), rng.uniform(*YAW_RANGE)


def overview():
    fig, ax = fig_ax(16, 3.6)
    items = [("① 실물 OMX 리더", ["사람이 손으로 조작", "USB · Dynamixel 5축 + 트리거"]),
             ("② MuJoCo OMX 팔", ["리더 관절각을 10 Hz로 추종", "카메라 2대 · 성공 자동 판정"]),
             ("③ 시연 데이터", ["LeRobotDataset", "관측(영상 2 · 관절 6) + 행동 6"]),
             ("④ ACT 학습", ["LeRobot ACT 정책", "GPU · 30,000 스텝"]),
             ("⑤ MuJoCo 평가", ["정책이 혼자 조작", "새 큐브 자리에서 성공률"])]
    chain(ax, items, 0.9, 2.1, colors=[C["yellow"], C["blue"], C["teal"], C["purple"], C["green"]], tfs=11.5, fs=9.2)
    note(ax, 0.3, 0.35, "실물 로봇은 리더 하나만 씁니다. 따라 움직이는 팔(follower)은 시뮬레이터 안에 있습니다.")
    save(fig, "l01_overview.png")


def imitation():
    fig, ax = fig_ax(16, 4.4)
    rbox(ax, 0.3, 1.0, 4.6, 2.9, "1. 시연 (사람)", ["사람이 과제를 직접 해 보인다", "매 순간의 (관측, 행동) 쌍을 기록",
                                                  "관측 = 카메라 영상 + 관절각", "행동 = 다음 관절 목표"],
         fc=C["yellow"], align="left", dy=0.42)
    rbox(ax, 5.7, 1.0, 4.6, 2.9, "2. 학습", ["정책 π(관측) → 행동", "시연과 같은 행동을 내도록", "신경망을 지도 학습",
                                          "보상 함수 · 시행착오 없음"], fc=C["purple"], align="left", dy=0.42)
    rbox(ax, 11.1, 1.0, 4.6, 2.9, "3. 실행 (정책)", ["사람 없이 정책이 조작", "관측 → 행동 → 관측 → ...",
                                                    "시연에서 본 상황과 비슷하면 성공", "처음 보는 상황에서는?"],
         fc=C["green"], align="left", dy=0.42)
    arrow(ax, (4.9, 2.45), (5.7, 2.45)); arrow(ax, (10.3, 2.45), (11.1, 2.45))
    note(ax, 0.3, 0.45, "모방학습(Imitation Learning) = 시연을 따라 하는 정책을 지도 학습으로 얻는 방법.  "
                        "이 과정의 질문: 시연이 얼마나 다양해야 하나?", bold=False)
    save(fig, "l01_imitation.png")


def why_sim():
    fig, ax = fig_ax(16, 5.0)
    rows = [("필요한 장비", "리더 + 팔로워 2대", "리더 1대 (팔로워는 시뮬레이터)"),
            ("에피소드 리셋", "사람이 큐브를 다시 놓는다", "ENTER 한 번, 큐브 자리 자동"),
            ("성공 판정", "사람이 눈으로", "트레이 안 · 바닥에 놓임 · 손 뗌을 자동 판정"),
            ("큐브 자리 재현", "어렵다 (손으로 놓기)", "같은 좌표를 정확히 (--fixed-cube)"),
            ("평가 50회", "수십 분 + 사람 필요", "자동, 수 분")]
    x = [0.3, 3.6, 9.4]; w = [3.1, 5.6, 6.3]; y0 = 4.2; h = 0.62
    for j, t in enumerate(["", "실물 팔로워", "MuJoCo 팔로워"]):
        if t:
            rbox(ax, x[j], y0, w[j], h, t, fc=[None, C["grey"], C["blue"]][j], tfs=11)
    for i, r in enumerate(rows):
        y = y0 - (i + 1) * (h + 0.12)
        for j, t in enumerate(r):
            fc = C["yellow"] if j == 0 else ("white" if j == 1 else C["green"])
            rbox(ax, x[j], y, w[j], h, t, fc=fc, tfs=10.5 if j == 0 else 10, lw=1.0)
    save(fig, "l01_why_sim.png")


def task():
    fig, ax = fig_ax(16, 6.9)
    h = image(ax, OUT / "sim_scene.png", 0.3, 0.3, 10.0)
    def tag(x, y, tx, ty, text, color):
        ax.plot([x, tx], [y, y], color=color, lw=1.4, zorder=4)
        ax.plot([tx, tx], [y, ty], color=color, lw=1.4, zorder=4) if ty != y else None
        label(ax, tx, ty, text, color=color, fs=10)
    # Callout positions are in figure units over the 10 x 6.25 image (1600 x 1000 px).
    tag(3.9, 3.0, 3.9, 0.75, "파란 큐브 30 mm", BLUE)
    tag(5.8, 2.2, 7.6, 2.2, "초록 트레이 (안쪽 80 mm)", GREEN)
    tag(5.4, 5.2, 7.6, 5.2, "OMX 팔: 관절 5 + 그리퍼", INK)
    rbox(ax, 10.8, 3.9, 4.9, 2.6, "과제", ["큐브를 집어 트레이에 놓기", "매 에피소드 큐브 자리가 바뀐다",
                                         "(또는 --fixed-cube 로 고정)"], fc=C["blue"], align="left", dy=0.42)
    rbox(ax, 10.8, 0.6, 4.9, 2.9, "성공 조건 (자동 판정)", ["큐브 중심이 트레이 안쪽", "큐브가 바닥에 놓임 (들려 있지 않음)",
                                                       "손가락이 큐브에서 떨어짐", "→ 녹화는 자동 저장 · 평가는 성공"],
         fc=C["green"], align="left", dy=0.42)
    save(fig, "l01_task.png")


def io():
    fig, ax = fig_ax(16, 5.4)
    hg = image(ax, OUT / "sim_cam_global.png", 0.3, 2.55, 3.2)
    image(ax, OUT / "sim_cam_wrist.png", 3.7, 2.55, 3.2)
    note(ax, 1.9, 2.55 + hg + 0.25, "global 카메라 320×240", ha="center", fs=9.5)
    note(ax, 5.3, 2.55 + hg + 0.25, "wrist 카메라 320×240", ha="center", fs=9.5)
    rbox(ax, 0.3, 0.65, 6.6, 1.2, "관절각 6", ["Joint1~5 · Gripper (rad)"], fc=C["yellow"])
    ax.plot([6.9, 7.5], [3.75, 3.75], color=INK, lw=1.6); ax.plot([6.9, 7.5], [1.25, 1.25], color=INK, lw=1.6)
    ax.plot([7.5, 7.5], [1.25, 3.75], color=INK, lw=1.6)
    arrow(ax, (7.5, 2.5), (8.3, 2.5))
    rbox(ax, 8.3, 1.75, 3.4, 1.5, "ACT 정책", ["영상 + 관절 → 행동 묶음", "2 s 분량 (20 스텝)"], fc=C["purple"])
    arrow(ax, (11.7, 2.5), (12.5, 2.5))
    rbox(ax, 12.5, 1.75, 3.2, 1.5, "행동 6", ["다음 관절 목표 (rad)", "10 Hz로 팔에 전달"], fc=C["green"])
    note(ax, 0.3, 0.1, "녹화 · 학습 · 평가 모두 10 Hz, 320×240 영상. 행동은 리더가 보내는 것과 같은 형식(관절 목표 6개)입니다.", fs=9.5)
    save(fig, "l01_io.png")


def exercise_flow():
    fig, ax = fig_ax(16, 6.2)
    rows = [("실습 1: 시연 5회, 큐브 고정", C["yellow"],
             [("녹화 5회", "--fixed-cube"), ("ACT 학습", "30,000 스텝"), ("추론 A", "같은 자리 (--fixed-cube)"),
              ("추론 B", "자리 · 각도 변경 (무작위)")]),
            ("실습 2: 시연 50회, 큐브 무작위", C["teal"],
             [("녹화 50회", "매번 다른 자리"), ("ACT 학습", "30,000 스텝"), ("추론 A", "같은 자리 (--fixed-cube)"),
              ("추론 B", "자리 · 각도 변경 (무작위)")])]
    for r, (title, fc, items) in enumerate(rows):
        y = 3.55 - r * 3.0
        note(ax, 0.3, y + 2.05, title, fs=12, bold=True, color=INK)
        chain(ax, [(t, [s]) for t, s in items], y, 1.6, colors=[fc, C["purple"], C["green"], C["red"]], tfs=11.5, fs=9.5)
    save(fig, "l01_exercise_flow.png")


def placements():
    """Top view: 5 identical fixed demos vs 50 random demos (seeds 0..49, as scripted_pick_place.py)."""
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(16, 7.2), dpi=150)
    panels = [("실습 1: 큐브 고정 (시연 5회 모두 같은 자리)", [FIXED] * 5, RED),
              ("실습 2: 큐브 무작위 (시연 50회)", [cube_pose(s) for s in range(50)], BLUE)]
    for ax, (title, poses, col) in zip(axes, panels):
        ax.add_patch(Rectangle((Y_RANGE[0] * 100, X_RANGE[0] * 100), (Y_RANGE[1] - Y_RANGE[0]) * 100,
                               (X_RANGE[1] - X_RANGE[0]) * 100, fc="#F3F6FB", ec=GREY, ls="--", lw=1.2, zorder=0))
        ty, tx = TRAY_XY[1] * 100, TRAY_XY[0] * 100
        ax.add_patch(Rectangle((ty - TRAY_HALF * 100, tx - TRAY_HALF * 100), 2 * TRAY_HALF * 100, 2 * TRAY_HALF * 100,
                               fc="#E6F7E6", ec=GREEN, lw=1.6))
        ax.text(ty, tx, "트레이", ha="center", va="center", color=GREEN, fontsize=11)
        ax.plot(0, 0, marker="o", ms=10, color=INK); ax.text(0, -1.6, "로봇 베이스 (원점)", ha="center", va="top", fontsize=10)
        for x, y, yaw in poses:
            c, s = np.cos(yaw), np.sin(yaw)
            corners = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]]) * CUBE_HALF
            pts = corners @ np.array([[c, s], [-s, c]]) + [x, y]
            if len(poses) > 5:   # outlines, so 50 overlapping cubes stay readable
                ax.plot(pts[:, 1] * 100, pts[:, 0] * 100, color=col, lw=0.9, alpha=0.7)
                ax.plot(y * 100, x * 100, marker="o", ms=2.5, color=col)
            else:
                ax.fill(pts[:, 1] * 100, pts[:, 0] * 100, fc=col, ec=col, lw=0.6)
        ax.text(-6, 13.2, "점선 = 무작위 범위\nx 17~25 cm, y -10~-2 cm\n회전 ±45° (큐브 30 mm)", ha="center", va="top",
                fontsize=9.5, color="#555555")
        ax.set_title(title, fontsize=13, pad=12)
        ax.set_xlim(20, -14); ax.set_ylim(-3, 28); ax.set_aspect("equal")
        ax.set_xlabel("y (cm)  ← 로봇 왼쪽", fontsize=10); ax.set_ylabel("x (cm)  로봇 앞쪽 →", fontsize=10)
        ax.grid(color="#EEEEEE", lw=0.8); ax.tick_params(labelsize=9)
        for sp in ax.spines.values():
            sp.set_color("#BBBBBB")
    fig.tight_layout()
    fig.savefig(OUT / "l01_placements.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
    print("saved l01_placements.png")


def preview():
    """Success rates of the two scripted-demo policies (filled from the eval json files)."""
    import matplotlib.pyplot as plt
    runs = ROOT / "outputs" / "train"
    def rate(run, tag):
        p = runs / run / "checkpoints" / "030000" / "eval" / f"{tag}.json"
        return 100 * json.loads(p.read_text())["success_rate"]
    vals = {"시연 5회 (고정)": [rate("omx_cube_fixed5_act", "pose0.21_-0.06_0_n10"), rate("omx_cube_fixed5_act", "seed1000_n50")],
            "시연 50회 (무작위)": [rate("omx_cube_random50_act", "pose0.21_-0.06_0_n10"),
                               rate("omx_cube_random50_act", "seed1000_n50")]}
    fig, ax = plt.subplots(figsize=(12, 5), dpi=150)
    xs = np.arange(2); w = 0.36
    for k, (name, v) in enumerate(vals.items()):
        bars = ax.bar(xs + (k - 0.5) * w, v, w * 0.92, color=[RED, BLUE][k], label=name)
        for b, val in zip(bars, v):
            ax.text(b.get_x() + b.get_width() / 2, val + 2, f"{val:.0f}%", ha="center", fontsize=12, fontweight="bold")
    ax.set_xticks(xs, ["추론 A: 같은 자리 (10회)", "추론 B: 자리 · 각도 변경 (50회)"], fontsize=11)
    ax.set_ylim(0, 112); ax.set_ylabel("성공률 (%)", fontsize=11); ax.legend(fontsize=11, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(axis="y", color="#EEEEEE"); ax.set_axisbelow(True)
    ax.set_title("스크립트 시연으로 학습한 두 정책의 성공률 (30,000 스텝)", fontsize=13, pad=12)
    fig.savefig(OUT / "l01_preview.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
    print("saved l01_preview.png", vals)


def curriculum():
    fig, ax = fig_ax(16, 5.0)
    items = [("① 소개 · 커리큘럼", "이 페이지"), ("② 환경 설정", "venv · MuJoCo 3.15.0"),
             ("③ MuJoCo 장면", "OMX 모델 · 과제 · 카메라"), ("④ Lead Device", "리더 연결 · 관절 매핑"),
             ("⑤ 텔레옵", "리더로 MuJoCo 팔 조작"), ("⑥ 시연 녹화", "LeRobotDataset"),
             ("⑦ ACT 학습", "action chunk · GPU"), ("⑧ 실습 1", "시연 5회 · 큐브 고정"),
             ("⑨ 실습 2", "시연 50회 · 큐브 무작위"), ("⑩ 부록", "IK 스크립트 시연")]
    colors = [C["grey"], C["grey"], C["blue"], C["yellow"], C["yellow"], C["teal"], C["purple"], C["red"], C["red"],
              C["grey"]]
    flow_rows(ax, items, 5, h=1.5, colors=colors, tfs=11, fs=9.2)
    save(fig, "l01_curriculum.png")


def page_cycle():
    fig, ax = fig_ax(16, 2.6)
    chain(ax, [("1. 개념", ["그림 한 장에 한 가지"]), ("2. 실행", ["명령 → 실제 출력 · 화면"]),
               ("3. 코드와 설정", ["핵심 함수 발췌"]), ("해 볼 것", ["바꿔 보고 비교"])], 0.4, 1.8,
          colors=[C["blue"], C["yellow"], C["purple"], C["green"]], tfs=11.5, fs=9.5)
    save(fig, "l01_page_cycle.png")


def stack():
    fig, ax = fig_ax(16, 4.6)
    tiles(ax, [("MuJoCo 3.15.0", ["물리 시뮬레이션 · 뷰어", "오프스크린 카메라 렌더 (EGL)"], C["blue"]),
               ("LeRobot 0.6.1", ["LeRobotDataset · ACT 정책", "OMX 리더 드라이버 (Dynamixel)"], C["purple"]),
               ("PyTorch + CUDA", ["ACT 학습 · 추론", "GPU 필수 (CPU는 약 25배 느림)"], C["red"]),
               ("ROBOTIS OMX", ["리더 팔 (실물)", "menagerie MJCF 모델"], C["yellow"]),
               ("Python venv", ["의존성은 pyproject.toml", "mujoco==3.15.0 고정"], C["grey"]),
               ("검증 환경", ["Ubuntu 24.04 · Python 3.12", "RTX 5060 Ti 16 GB"], C["green"])], 3, h=1.85)
    save(fig, "l01_stack.png")


def repo():
    fig, ax = fig_ax(16, 5.4)
    items = [("il_omx/", ["env.py  과제 · 카메라 · 성공 판정", "leader.py · leader_mapping.py  리더",
                          "dataset.py  녹화 · ik.py  IK"], C["blue"]),
             ("scripts/", ["teleop.py · record.py", "train.py · eval.py", "scripted_pick_place.py"], C["yellow"]),
             ("models/", ["omx_follower.xml  OMX 팔", "scene_cube.xml  책상 · 큐브 · 트레이"], C["teal"]),
             ("calibration/ · configs/", ["omx_leader.json  리더 보정값", "leader_to_sim.json  관절 매핑"], C["purple"]),
             ("data/ (git 제외)", ["녹화한 LeRobotDataset", "data/<dataset 이름>"], C["grey"]),
             ("outputs/train/ (git 제외)", ["학습 체크포인트 (5,000 스텝마다)", "eval/ 평가 결과 · 영상"], C["grey"])]
    tiles(ax, items, 3, h=2.2, fs=9.2)
    save(fig, "l01_repo.png")


if __name__ == "__main__":
    for f in (overview, imitation, why_sim, task, io, exercise_flow, placements, curriculum, page_cycle, stack, repo):
        f()
    if "--preview" in sys.argv:
        preview()
