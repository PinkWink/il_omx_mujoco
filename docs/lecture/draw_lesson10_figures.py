"""Figures and terminal captures for page ⑩ (scripted IK demos). Output: docs/lecture/l10_*.png

  MUJOCO_GL=egl .venv/bin/python docs/lecture/render_lesson10_sim.py
  .venv/bin/python scripts/scripted_pick_place.py --episodes 5 --video outputs/lecture/scripted5.mp4 | tee outputs/lecture/scripted5.log
  python3 docs/lecture/draw_lesson10_figures.py
"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figstyle import BLUE, GREEN, INK, OUT, RED, C, arrow, chain, fig_ax, image, note, rbox, save  # noqa: E402
from render_terminal import render  # noqa: E402

ROOT = OUT.parents[1]
DATA = json.loads((OUT / "l10_data.json").read_text())
NAMES = [("큐브 8 cm 위", "1.3 s · 그리퍼 열림"), ("큐브 높이로 내림", "1.0 s"), ("쥠", "0.7 s · 그리퍼 0°"), ("10 cm 들어 올림", "1.0 s"),
         ("트레이 10 cm 위", "1.3 s"), ("5 cm 로 내림", "0.7 s"), ("놓음", "0.5 s · 그리퍼 열림"), ("12 cm 로 올림", "0.7 s")]


def why():
    fig, ax = fig_ax(16, 4.0)
    rbox(ax, 0.3, 0.5, 7.5, 3.1, "좋은 점", ["리더 · 사람 없이 시연 50개를 몇 분 만에", "큐브 자리를 seed 로 정확히 재현",
                                         "파이프라인 점검 · 기준 결과 (⑧ ⑨ 의 수치)"], fc=C["green"], align="left", dy=0.55)
    rbox(ax, 8.2, 0.5, 7.5, 3.1, "사람 시연과 다른 점", ["매번 같은 방식 · 같은 속도로 움직임", "실패했다가 다시 잡는 장면이 없음",
                                                   "→ 정책도 놓치면 다시 잡지 못함 (⑨ 의 실패)"], fc=C["red"], align="left", dy=0.55)
    save(fig, "l10_why.png")


def waypoints():
    fig, ax = fig_ax(16, 6.6)
    for i, (t, s) in enumerate(NAMES):
        r, c = divmod(i, 4)
        x, y = 0.3 + c * 3.9, 3.45 - r * 3.25
        h = image(ax, OUT / f"l10_wp_{i}.png", x, y, 3.7)
        note(ax, x + 1.85, y + h + 0.22, f"{i + 1}. {t}", ha="center", fs=10.5, bold=True, color=INK)
        note(ax, x + 0.12, y + 0.2, s, fs=9, color=INK)
    save(fig, "l10_waypoints.png")


def ik():
    conv = DATA["ik_conv_mm"]
    fig = plt.figure(figsize=(16, 5.0), dpi=150)
    ax = fig.add_axes([0, 0, 0.55, 1]); ax.set_xlim(0, 8.8); ax.set_ylim(0, 5); ax.axis("off")
    rbox(ax, 0.3, 3.4, 8.2, 1.2, "목표: tcp 위치 + 손 방향 (아래를 보고, 손가락은 yaw 방향)", fc=C["yellow"], tfs=10.5)
    rbox(ax, 0.3, 1.9, 8.2, 1.2, "오차 e = [위치 차이, 0.3 × 방향 차이]  ·  야코비안 J (6 × 5)", fc=C["blue"], tfs=10.5)
    rbox(ax, 0.3, 0.4, 8.2, 1.2, "Δq = J^T (J J^T + 0.001 I)^-1 e  →  q ← clip(q + Δq, 관절 범위)", fc=C["purple"], tfs=10.5)
    arrow(ax, (4.4, 3.4), (4.4, 3.1)); arrow(ax, (4.4, 1.9), (4.4, 1.6))
    ax.text(0.3, 4.85, "Damped least squares (최대 200번 반복, 위치 0.1 mm 이내면 멈춤)", fontsize=11, fontweight="bold", color=INK)
    a2 = fig.add_axes([0.62, 0.15, 0.36, 0.72])
    a2.semilogy(range(1, len(conv) + 1), conv, "o-", color=BLUE, ms=4)
    a2.set_xlabel("반복 횟수", fontsize=10); a2.set_ylabel("tcp 위치 오차 (mm)", fontsize=10)
    a2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}")); a2.yaxis.set_minor_formatter(plt.NullFormatter())
    a2.grid(color="#EEEEEE", which="both"); a2.set_title("첫 경유점 (큐브 8 cm 위) 의 수렴", fontsize=11)
    for sp in ("top", "right"):
        a2.spines[sp].set_visible(False)
    fig.savefig(OUT / "l10_ik.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
    print("saved l10_ik.png")


def grasp_yaw():
    fig, ax = fig_ax(16, 3.8)
    ex = DATA["grasp_yaw_examples"]
    w = (15.4 - 0.3 * 4) / 5
    for i, (c, g) in enumerate(ex):
        x = 0.3 + i * (w + 0.3)
        rbox(ax, x, 1.0, w, 2.2, f"큐브 {c:+.0f}°", [f"손가락 방향 {g:.0f}°", f"(= 큐브 {c:+.0f}° + 90°)"], fc=C["teal"], tfs=11.5, fs=9.5)
    note(ax, 0.3, 0.45, "큐브는 90° 마다 같은 모양이므로, 마주 보는 면 한 쌍 중 팔의 옆 방향(Joint1 각 + 90°)에 가장 가까운 쌍을 고릅니다 (Joint1 = 0° 일 때 예).")
    save(fig, "l10_grasp_yaw.png")


def interp():
    wps = DATA["waypoints"]
    q = [np.array([0, -17.2, 5.7, 74.5, 0, 45.8])]             # home keyframe (deg)
    for w in wps:                                                # straight lines in joint space, 10 Hz
        start, goal = q[-1], np.array(w["q_deg"] + [w["grip_deg"]])
        q += [start + (goal - start) * (i + 1) / w["steps"] for i in range(w["steps"])]
    q = np.array(q); t = np.arange(len(q)) / 10
    fig, ax = plt.subplots(figsize=(15, 4.6), dpi=150)
    cols = [RED, "#EF6C00", "#F9A825", GREEN, BLUE, "#6A1B9A"]
    for j, n in enumerate(["Joint1", "Joint2", "Joint3", "Joint4", "Joint5", "Gripper"]):
        ax.plot(t, q[:, j], color=cols[j], lw=1.8, label=n)
    edges = np.cumsum([0] + [w["steps"] for w in wps]) / 10
    for i, e in enumerate(edges[1:]):
        ax.axvline(e, color="#CCCCCC", lw=1, ls=":")
        ax.text(e - 0.05, 112, str(i + 1), ha="right", fontsize=9, color="#777777")
    ax.set_xlabel("시간 (s)", fontsize=10); ax.set_ylabel("관절 목표 (°)", fontsize=10); ax.set_ylim(-60, 120)
    ax.legend(frameon=False, ncol=6, fontsize=9.5, loc="lower center", bbox_to_anchor=(0.5, -0.32))
    ax.grid(color="#EEEEEE")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.set_title("seed 0 의 행동: 경유점(1~8) 사이를 관절 공간에서 직선으로 이음 (10 Hz)", fontsize=11.5)
    fig.savefig(OUT / "l10_interp.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
    print("saved l10_interp.png")


def video_frames():
    """Frames 0/25/45/80 of outputs/lecture/scripted5.mp4, extracted with the venv (imageio) to l10_video_*.png."""
    fig, ax = fig_ax(16, 2.6)
    for k, i in enumerate((0, 25, 45, 80)):
        x = 0.3 + k * 3.9
        image(ax, OUT / f"l10_video_{i:03d}.png", x, 0.3, 3.7)
        note(ax, x + 0.1, 0.5, f"t = {i / 10:.1f} s", fs=9, color="white")
    save(fig, "l10_video.png")


def terminals():
    lines = (ROOT / "outputs/lecture/scripted5.log").read_text().splitlines()
    render([("prompt", ".venv/bin/python scripts/scripted_pick_place.py --episodes 5 --video outputs/lecture/scripted5.mp4")]
           + [("out", s) for s in lines], "l10_t_scripted.png", highlight=("success rate", "IK error"))


if __name__ == "__main__":
    for f in (why, waypoints, ik, grasp_yaw, interp, video_frames, terminals):
        f()
