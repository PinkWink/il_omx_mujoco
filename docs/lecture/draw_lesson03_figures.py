"""Figures for page ③ (MuJoCo scene and task). Output: docs/lecture/l03_*.png

  MUJOCO_GL=egl .venv/bin/python docs/lecture/render_lesson03_sim.py     # renders + l03_data.json first
  python3 docs/lecture/draw_lesson03_figures.py
"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon, Rectangle
from scipy.spatial import ConvexHull

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figstyle import BLUE, GREEN, GREY, INK, OUT, RED, C, arrow, chain, fig_ax, image, label, note, rbox, save  # noqa: E402
from render_terminal import render  # noqa: E402

DATA = json.loads((OUT / "l03_data.json").read_text())


def xml_tree():
    fig, ax = fig_ax(16, 6.2)
    rbox(ax, 0.3, 0.4, 7.4, 5.4, "models/scene_cube.xml  (장면)",
         ["<include file=\"omx_follower.xml\"/>  ← 팔", "table: 책상 (윗면 z = 0, 로봇 베이스 = 원점)",
          "cube: 파란 큐브 30 mm, 25 g, freejoint", "tray: 초록 트레이, 안쪽 80 mm, 벽 12 mm",
          "camera global: 고정 3인칭 카메라", "light 2개 · 바닥 · 하늘", "keyframe home: 팔 · 큐브 시작 자세"],
         fc=C["teal"], align="left", dy=0.62, fs=10)
    rbox(ax, 8.3, 0.4, 7.4, 5.4, "models/omx_follower.xml  (팔)",
         ["menagerie robotis_omx/omx.xml 에서 출발", "link0 ~ link5: 관절 5 (Joint1 ~ Joint5)",
          "link6 · link7: 손가락 2 (Gripper · Gripper_mimic)", "actuator: position 6개 (Joint1~5, Gripper)",
          "추가: 손가락 박스 패드 · wrist 카메라 · tcp", "메시: third_party/.../robotis_omx/assets/*.stl"],
         fc=C["blue"], align="left", dy=0.62, fs=10)
    arrow(ax, (8.3, 4.65), (7.7, 4.65))
    save(fig, "l03_xml_tree.png")


def arm():
    fig, ax = fig_ax(16, 6.6)
    w = 10.0
    h = image(ax, OUT / "l03_sim_arm.png", 0.3, 0.3, w)
    sx = w / 1600
    names = {"Joint1": "Joint1 (z축 회전)", "Joint2": "Joint2", "Joint3": "Joint3", "Joint4": "Joint4",
             "Joint5": "Joint5 (손목 회전)", "Gripper": "Gripper", "tcp": "tcp", "wrist_cam": "wrist 카메라"}
    offsets = {"Joint1": (0.9, 0), "Joint2": (0.9, 0), "Joint3": (0.6, 0.35), "Joint4": (0.0, 0.55),
               "Joint5": (-1.6, 0.85), "Gripper": (-1.6, 0.25), "tcp": (-0.9, -0.55), "wrist_cam": (-1.1, -0.55)}
    for k, (u, v) in DATA["arm"].items():
        x, y = 0.3 + u * sx, 0.3 + h - v * sx
        col = RED if k in ("tcp", "wrist_cam") else INK
        ax.plot(x, y, "o", ms=7, color=col, mec="white", mew=1.2, zorder=6)
        dx, dy = offsets[k]
        ax.plot([x, x + dx], [y, y + dy], color=col, lw=1.0, zorder=5)
        label(ax, x + dx, y + dy, names[k], color=col, fs=9.5)
    rows = [("관절", "축", "범위 (deg)"), ("Joint1", "z", "-270 ~ 360"), ("Joint2", "y", "-120 ~ 90"),
            ("Joint3", "y", "-120 ~ 90"), ("Joint4", "y", "-100 ~ 100"), ("Joint5", "x", "-270 ~ 270"),
            ("Gripper", "z", "0 (닫힘) ~ 100")]
    for i, r in enumerate(rows):
        y = 5.6 - i * 0.62
        for j, (t, x0, ww) in enumerate(zip(r, (10.7, 12.4, 13.4), (1.6, 0.9, 2.3))):
            rbox(ax, x0, y, ww, 0.5, t, fc=C["grey"] if i == 0 else "white", tfs=10, lw=0.9)
    note(ax, 10.7, 1.05, "home 키프레임 자세 (deg)", fs=10, bold=True, color=INK)
    note(ax, 10.7, 0.6, "0, -17.2, 5.7, 74.5, 0, 그리퍼 45.8", fs=10)
    save(fig, "l03_arm.png")


def actuator():
    fig, ax = fig_ax(16, 3.4)
    chain(ax, [("목표 각도 (ctrl)", ["리더 · 정책이 주는 값 (rad)"]),
               ("position 액추에이터", ["kp = 50, dampratio = 1", "힘 제한 ±3.5 N·m"]),
               ("관절", ["frictionloss 0.1 · armature 0.1", "범위 밖 목표는 잘림 (clip)"])],
          0.9, 2.1, colors=[C["yellow"], C["purple"], C["blue"]], tfs=11.5, fs=9.5)
    note(ax, 0.3, 0.4, "실물 XL330 서보처럼 위치 목표를 따라갑니다. 힘 제한 때문에 큐브를 쥐면 손가락이 목표까지 닫히지 못하고 멈춥니다.")
    save(fig, "l03_actuator.png")


def gripper_mimic():
    fig, ax = fig_ax(16, 3.4)
    rbox(ax, 0.3, 0.9, 4.6, 2.1, "Gripper (link6)", ["액추에이터가 움직이는 손가락", "0 = 닫힘, 100° = 열림"], fc=C["purple"])
    rbox(ax, 11.1, 0.9, 4.6, 2.1, "Gripper_mimic (link7)", ["반대쪽 손가락", "-100° ~ 0 (반대 방향)"], fc=C["grey"])
    rbox(ax, 5.7, 1.2, 4.6, 1.5, "equality joint", ["Gripper_mimic = -1 × Gripper"], fc=C["yellow"])
    arrow(ax, (4.9, 1.95), (5.7, 1.95)); arrow(ax, (10.3, 1.95), (11.1, 1.95))
    note(ax, 0.3, 0.4, "액추에이터는 한쪽 손가락에만 있고, 다른 쪽은 등식 제약으로 같은 각도만큼 반대로 움직입니다.")
    save(fig, "l03_gripper_mimic.png")


def finger_hull():
    f = DATA["fingers"]
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.4), dpi=150)
    for ax, mode in zip(axes, ("hull", "pads")):
        for verts in f["meshes"]:
            v = np.array(verts)
            ax.plot(v[:, 0], v[:, 1], ".", ms=1.2, color="#555555", alpha=0.5)
            if mode == "hull":
                hull = ConvexHull(v)
                ax.add_patch(Polygon(v[hull.vertices], fc=RED, ec=RED, alpha=0.25, lw=1.5))
        if mode == "pads":
            for p in f["pads"]:
                ax.add_patch(Polygon(np.array(p), fc=RED, ec=RED, alpha=0.6, lw=1.2))
        tx, ty = f["tcp"]
        ax.add_patch(Rectangle((tx - 15, ty - 15), 30, 30, fc="none", ec=BLUE, lw=2, ls="--"))
        ax.text(tx, ty - 19, "30 mm 큐브 크기 (tcp 중심)", ha="center", va="top", color=BLUE, fontsize=10)
        ax.set_aspect("equal"); ax.grid(color="#EEEEEE"); ax.tick_params(labelsize=9)
        ax.set_xlabel("손목 앞쪽 (mm)", fontsize=10); ax.set_ylabel("좌우 (mm)", fontsize=10)
        ax.set_title({"hull": "원래 메시를 충돌에 쓰면: MuJoCo는 메시마다 볼록 껍질(빨강)로 계산",
                      "pads": "이 저장소: 손가락 안쪽을 따라 놓은 박스 패드 6개 (빨강)"}[mode], fontsize=11.5, pad=10)
    lo = np.min([np.min(np.array(v), axis=0) for v in f["meshes"]], axis=0) - 8
    hi = np.max([np.max(np.array(v), axis=0) for v in f["meshes"]], axis=0) + 8
    for ax in axes:
        ax.set_xlim(lo[0], hi[0] + 25); ax.set_ylim(lo[1] - 12, hi[1])
    fig.text(0.02, 0.0, "회색 점 = 손가락 메시 꼭짓점 (그리퍼를 home 자세 45.8°로 연 상태, 위에서 본 평면). "
             "껍질은 휜 손가락 안쪽의 빈 곳까지 채우므로, 실제로 재료가 없는 곳에서 접촉이 생깁니다.", fontsize=10, color="#555555")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUT / "l03_finger_hull.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
    print("saved l03_finger_hull.png")


def cameras():
    fig, ax = fig_ax(16, 6.0)
    w = 8.6
    h = image(ax, OUT / "l03_sim_cameras.png", 0.3, 0.3, w)
    sx = w / 1600
    for k, (u, v) in DATA["cameras"].items():
        x, y = 0.3 + u * sx, 0.3 + h - v * sx
        dx, dy = (0.9, 0.5) if k == "global" else (-1.2, 0.9)
        ax.plot([x, x + dx], [y, y + dy], color=RED, lw=1.2)
        label(ax, x + dx, y + dy, f"{k} 카메라", color=RED, fs=10)
    gh = image(ax, OUT / "sim_cam_global.png", 9.3, 3.1, 3.1)
    image(ax, OUT / "sim_cam_wrist.png", 12.6, 3.1, 3.1)
    note(ax, 10.85, 3.1 + gh + 0.2, "global (고정)", ha="center", fs=10)
    note(ax, 14.15, 3.1 + gh + 0.2, "wrist (link5, Joint5와 함께 회전)", ha="center", fs=10)
    rbox(ax, 9.3, 0.3, 6.4, 2.4, "두 카메라 (320×240, 10 Hz)",
         ["global: 책상 오른쪽 위, 작업 공간 중심을 바라봄 (fovy 50°)", "wrist: 손목 위, 손가락과 앞쪽 아래를 봄 (fovy 70°)",
          "정책은 두 영상과 관절각 6개를 함께 입력받음"], fc=C["blue"], align="left", dy=0.45, fs=9.5)
    save(fig, "l03_cameras.png")


def timing():
    fig, ax = fig_ax(16, 3.6)
    x0, x1, y = 0.6, 15.4, 1.9
    ax.plot([x0, x1], [y, y], color=INK, lw=1.4)
    span = (x1 - x0) / 2
    for i in range(3):
        xs = x0 + i * span
        ax.plot([xs, xs], [y - 0.35, y + 0.35], color=INK, lw=2)
        if i < 2:
            label(ax, xs + span / 2, y + 0.75, f"제어 1 스텝 = 0.1 s (10 Hz): step(action) 한 번", fs=10, color=INK)
            for k in range(1, 50):
                xx = xs + k * span / 50
                ax.plot([xx, xx], [y - 0.12, y + 0.12], color=GREY, lw=0.8)
    label(ax, x0 + span / 2, y - 0.75, "물리 0.002 s × 50 번 (mj_step nstep=50)", fs=10, color="#555555")
    note(ax, 0.3, 0.35, "녹화 · 학습 · 평가가 모두 같은 10 Hz 입니다. 한 스텝마다 행동 1개를 넣고 관측(영상 2 + 관절 6) 1개를 받습니다.")
    save(fig, "l03_timing.png")


def seeds():
    fig, ax = fig_ax(16, 3.9)
    for s in range(4):
        x = 0.3 + s * 3.9
        h = image(ax, OUT / f"l03_sim_seed{s}.png", x, 0.75, 3.6)
        cx, cy, yaw = DATA[f"seed{s}"]
        note(ax, x + 1.8, 0.4, f"seed {s}: x {cx * 100:.1f} cm, y {cy * 100:.1f} cm, {yaw:+.0f}°", ha="center", fs=9.5)
    save(fig, "l03_seeds.png")


def success_conditions():
    fig, ax = fig_ax(16, 5.2)
    # Top view of the tray (inner 80 mm) and the allowed region for the cube center (+-20 mm).
    s = 0.045  # figure units per mm
    cx, cy = 2.6, 2.6
    ax.add_patch(Rectangle((cx - 40 * s, cy - 40 * s), 80 * s, 80 * s, fc=C["green"], ec=GREEN, lw=2))
    ax.add_patch(Rectangle((cx - 20 * s, cy - 20 * s), 40 * s, 40 * s, fc="none", ec=RED, lw=1.8, ls="--"))
    ax.add_patch(Rectangle((cx - 7 * s, cy - 10 * s), 30 * s, 30 * s, fc=BLUE, alpha=0.35, ec=BLUE))
    ax.plot(cx + 8 * s, cy + 5 * s, "o", color=BLUE, ms=5)
    note(ax, cx + 8 * s, cy + 5 * s - 0.25, "큐브 예 (중심 8, 5 mm)", ha="center", fs=8.5, color=BLUE)
    note(ax, cx, cy + 40 * s + 0.3, "① 안쪽: 위에서 본 트레이 (안쪽 80 mm)", ha="center", fs=10.5, bold=True, color=INK)
    note(ax, cx, cy - 40 * s - 0.3, "큐브 중심이 빨간 점선 안 (중심에서 ±20 mm)", ha="center", fs=9.5)
    note(ax, cx, cy - 40 * s - 0.7, "= 40 - 15(큐브 반) - 5(여유) mm", ha="center", fs=9.5, color="#777777")
    rbox(ax, 5.6, 1.6, 4.8, 2.6, "② 놓임 (resting)", ["큐브 중심 높이가 트레이 기준", "15 + 8 = 23 mm 미만",
                                                     "= 들려 있지 않고 바닥에 놓임", "(속도는 보지 않음)"],
         fc=C["yellow"], align="left", dy=0.45)
    rbox(ax, 10.9, 1.6, 4.8, 2.6, "③ 손을 뗌", ["큐브와 손가락 패드 6개 사이", "접촉(contact)이 하나도 없음",
                                               "= 그리퍼를 열고 놓았음"], fc=C["purple"], align="left", dy=0.45)
    note(ax, 5.6, 4.7, "is_success() = ① and ② and ③", fs=12, bold=True, color=INK)
    save(fig, "l03_success_cond.png")


def timeline():
    tl = DATA["timeline"]
    t = np.array([s["t"] for s in tl])
    keys = [("inside", "① 트레이 안"), ("resting", "② 놓임 (23 mm 미만)"), ("touching", "손가락 접촉 (③의 반대)"),
            ("success", "is_success()")]
    fig = plt.figure(figsize=(16, 8.2), dpi=150)
    names = ["grasp", "carry", "release", "success"]
    titles = ["잡기", "옮기기", "놓기 직전", "성공"]
    for i, n in enumerate(names):
        a = fig.add_axes([0.06 + i * 0.235, 0.6, 0.22, 0.36])
        a.imshow(plt.imread(OUT / f"l03_sim_{n}.png")); a.axis("off")
        a.set_title(f"{titles[i]}  (t = {DATA['key_times'][n]:.1f} s)", fontsize=11)
    ax = fig.add_axes([0.06, 0.08, 0.9, 0.45])
    for r, (k, lab) in enumerate(keys):
        v = np.array([s[k] for s in tl])
        y = len(keys) - 1 - r
        col = GREEN if k != "touching" else RED
        for i in range(len(t) - 1):
            if v[i]:
                ax.add_patch(Rectangle((t[i], y - 0.35), t[i + 1] - t[i], 0.7, fc=col, alpha=0.8 if k == "success" else 0.55,
                                       ec="none"))
        ax.text(-0.15, y, lab, ha="right", va="center", fontsize=10.5)
    for n in names:
        ax.axvline(DATA["key_times"][n], color=GREY, lw=1, ls=":")
    ax.set_xlim(0, t[-1]); ax.set_ylim(-0.6, len(keys) - 0.4); ax.set_yticks([])
    ax.set_xlabel("시간 (s)  · 스크립트 시연 1회, 큐브 고정 자리 · 10 Hz 로 매 스텝 기록", fontsize=10.5)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    fig.savefig(OUT / "l03_timeline.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
    print("saved l03_timeline.png")


def terminals():
    out = (OUT / "l03_env_tour.txt").read_text().splitlines()
    render([("prompt", "MUJOCO_GL=egl .venv/bin/python docs/lecture/env_tour.py")] + [("out", s) for s in out],
           "l03_t_tour.png", highlight=("success: True", "shape (240, 320, 3)"))


if __name__ == "__main__":
    for f in (xml_tree, arm, actuator, gripper_mimic, finger_hull, cameras, timing, seeds, success_conditions,
              timeline, terminals):
        f()
