"""Figures and terminal captures for page ⑥ (recording, LeRobotDataset). Output: docs/lecture/l06_*.png

  python3 dev/capture_window.py OUT 0.5 110 -- .venv/bin/python dev/fake_leader.py record --hold-s 2 --auto-enter \
      -- --dataset lecture_record --num-episodes 3 --fixed-cube        # viewer frames l06_view_*.png
  .venv/bin/python docs/lecture/inspect_dataset.py lecture_record --save-plot docs/lecture/l06_episode.json
  python3 docs/lecture/draw_lesson06_figures.py
"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figstyle import BLUE, GREY, INK, OUT, RED, C, arrow, chain, fig_ax, image, label, note, rbox, save  # noqa: E402
from render_terminal import render  # noqa: E402


def vs_teleop():
    fig, ax = fig_ax(16, 4.0)
    rbox(ax, 0.3, 0.7, 7.3, 2.9, "teleop.py (⑤)", ["리더 → MuJoCo 팔, 10 Hz", "성공 판정 · SUCCESS 배너", "아무것도 저장하지 않음"],
         fc=C["grey"], align="left", dy=0.5)
    rbox(ax, 8.4, 0.7, 7.3, 2.9, "record.py (이 페이지)", ["teleop 과 같은 화면 · 같은 10 Hz",
                                                        "매 스텝 (관측, 행동) 한 쌍을 기록", "성공하면 자동 저장 → data/<dataset>"],
         fc=C["teal"], align="left", dy=0.5)
    arrow(ax, (7.6, 2.15), (8.4, 2.15))
    note(ax, 0.3, 0.3, "성공한 시연만 남습니다. 실패 · 취소 · 60 s 초과 에피소드는 버립니다.")
    save(fig, "l06_vs_teleop.png")


def states():
    fig, ax = fig_ax(16, 5.4)
    y = 2.9
    boxes = [("대기", 0.3, C["grey"]), ("REC  (빨강)", 3.5, C["red"]), ("REC  OK  (초록)", 6.7, C["green"]),
             ("SAVING → SAVED", 9.9, C["teal"]), ("DONE", 13.1, C["blue"])]
    for t, x, fc in boxes:
        rbox(ax, x, y, 2.6, 1.0, t, fc=fc, tfs=11)
    for (a, b, txt) in [(2.9, 3.5, "ENTER"), (6.1, 6.7, "성공 판정"), (9.3, 9.9, "0.5 s 뒤"), (12.5, 13.1, "목표 개수")]:
        arrow(ax, (a, y + 0.5), (b, y + 0.5))
        label(ax, (a + b) / 2, y + 1.3, txt, fs=9.5)
    # SAVED returns to idle
    ax.plot([11.2, 11.2], [y, y - 0.7], color="#7a4b00", lw=1.3); ax.plot([11.2, 1.6], [y - 0.7, y - 0.7], color="#7a4b00", lw=1.3)
    arrow(ax, (1.6, y - 0.7), (1.6, y), color="#7a4b00", lw=1.3)
    label(ax, 6.4, y - 0.7, "저장 끝 → 다음 ENTER 를 기다림", color="#7a4b00", fs=9.5)
    rows = [("녹화 중 ENTER", "취소 (DISCARDED cancelled)"), ("녹화 중 BACKSPACE", "버림 (뷰어도 시뮬레이션을 리셋)"),
            ("60 s 넘음", "버림 (DISCARDED time limit)"), ("대기 중 BACKSPACE", "이번 실행에서 마지막으로 저장한 에피소드 삭제 (1번)")]
    for i, (k, v) in enumerate(rows):
        yy = 1.35 - i * 0.42
        note(ax, 0.4, yy, k, bold=True, color=INK, fs=10)
        note(ax, 3.6, yy, v, fs=10)
    note(ax, 0.3, 4.95, "record.py 의 상태와 배너", bold=True, color=INK, fs=11)
    save(fig, "l06_states.png")


def frame():
    fig, ax = fig_ax(16, 4.4)
    hg = image(ax, OUT / "l06_frame_global_000.png", 0.3, 1.0, 2.9)
    image(ax, OUT / "l06_frame_wrist_000.png", 3.4, 1.0, 2.9)
    note(ax, 1.75, 1.0 + hg + 0.2, "observation.images.global", ha="center", fs=9.5)
    note(ax, 4.85, 1.0 + hg + 0.2, "observation.images.wrist", ha="center", fs=9.5)
    rbox(ax, 6.7, 2.2, 4.2, 1.6, "observation.state", ["관절 6개 현재 각도 (rad)", "Joint1~5, Gripper"], fc=C["yellow"])
    rbox(ax, 11.4, 2.2, 4.3, 1.6, "action", ["이 순간 보낸 관절 목표 6개", "= 리더 값을 매핑한 것"], fc=C["purple"])
    rbox(ax, 6.7, 0.5, 9.0, 1.2, "timestamp · frame_index · episode_index · index · task", fc=C["grey"], tfs=10.5)
    note(ax, 0.3, 0.45, "한 프레임 = 시각 t 의 관측 + 시각 t 에 보낸 행동 (10 Hz 이므로 0.1 s 마다 1 프레임)", fs=9.5)
    save(fig, "l06_frame.png")


def sequence():
    fig, ax = fig_ax(16, 4.1)
    for i, (n, t) in enumerate([("rec", "REC 4.4 s"), ("ok", "성공 → REC OK"), ("saved", "SAVED episode 1"),
                                ("done", "3 / 3 → DONE")]):
        x = 0.3 + i * 3.9
        hh = image(ax, OUT / f"l06_view_{n}.png", x, 0.3, 3.7)
        note(ax, x + 1.85, 0.3 + hh + 0.25, t, ha="center", fs=10.5, bold=True, color=INK)
    save(fig, "l06_sequence.png")


def layout():
    fig, ax = fig_ax(16, 5.6)
    rbox(ax, 0.3, 0.4, 4.6, 4.8, "data/lecture_record/", ["meta/info.json", "meta/stats.json", "meta/tasks.parquet",
                                                         "meta/episodes/...parquet", "data/chunk-000/*.parquet",
                                                         "videos/<카메라>/chunk-000/*.mp4"],
         fc=C["teal"], align="left", dy=0.55, fs=9.8)
    items = [("meta/info.json", ["fps 10 · 에피소드 수 · 프레임 수", "features (모양 · 자료형)"], C["grey"]),
             ("meta/stats.json", ["값마다 평균 · 표준편차 · 최소 · 최대", "학습 때 정규화에 사용"], C["grey"]),
             ("data/*.parquet", ["프레임마다 한 줄: state · action", "timestamp · episode_index ..."], C["yellow"]),
             ("videos/*.mp4", ["카메라 영상 (AV1, 320×240, 10 fps)", "에피소드마다 파일 1개 (이 저장소 설정)"], C["blue"])]
    for i, (t, l, fc) in enumerate(items):
        r, c = divmod(i, 2)
        rbox(ax, 5.4 + c * 5.25, 2.9 - r * 2.5, 5.0, 2.2, t, l, fc=fc, align="left", dy=0.45, fs=9.5)
    save(fig, "l06_layout.png")


def episode_plot():
    d = json.loads((OUT / "l06_episode.json").read_text())
    s, a = np.rad2deg(np.array(d["state"])), np.rad2deg(np.array(d["action"]))
    t = np.arange(len(s)) / d["fps"]
    names = ["Joint1", "Joint2", "Joint3", "Joint4", "Joint5", "Gripper"]
    fig, axes = plt.subplots(2, 3, figsize=(16, 6.2), dpi=150, sharex=True)
    for i, axx in enumerate(axes.flat):
        axx.plot(t, a[:, i], color=RED, lw=1.6, label="action (목표)")
        axx.plot(t, s[:, i], color=BLUE, lw=1.6, ls="--", label="observation.state (실제)")
        axx.set_title(names[i], fontsize=11); axx.grid(color="#EEEEEE"); axx.tick_params(labelsize=9)
        for sp in ("top", "right"):
            axx.spines[sp].set_visible(False)
    for axx in axes[1]:
        axx.set_xlabel("시간 (s)", fontsize=10)
    for axx in axes[:, 0]:
        axx.set_ylabel("각도 (°)", fontsize=10)
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, fontsize=10, frameon=False, loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.04))
    fig.suptitle("data/lecture_record 에피소드 0 (89 프레임, 8.9 s): 목표를 실제 각도가 조금 늦게 따라감", fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT / "l06_episode_plot.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
    print("saved l06_episode_plot.png")


def episode_frames():
    fig, ax = fig_ax(16, 5.6)
    idx = [0, 29, 59, 88]
    for k, i in enumerate(idx):
        x = 0.3 + k * 3.9
        hg = image(ax, OUT / f"l06_frame_global_{i:03d}.png", x, 2.9, 3.7)
        image(ax, OUT / f"l06_frame_wrist_{i:03d}.png", x, 0.1, 3.7)
        note(ax, x + 1.85, 2.9 + hg + 0.2, f"frame {i}  (t = {i / 10:.1f} s)", ha="center", fs=10, bold=True, color=INK)
    save(fig, "l06_episode_frames.png")


def terminals():
    render([("prompt", ".venv/bin/python dev/fake_leader.py record --auto-enter -- --dataset lecture_record --num-episodes 3 --fixed-cube"),
            ("out", "dataset: /home/pw/il_omx_mujoco/data/lecture_record  (0 episodes already)"),
            ("out", "cube: fixed at x 0.21, y -0.06, yaw 0 deg"),
            ("out", "saved (success), 89 frames"),
            ("out", "saved (success), 89 frames"),
            ("out", "saved (success), 89 frames"),
            ("out", "^C"),
            ("out", "dataset: /home/pw/il_omx_mujoco/data/lecture_record  (3 episodes)")],
           "l06_t_record.png", highlight=("saved (success)",))
    lines = (OUT / "l06_inspect.txt").read_text().splitlines()
    lines = [s for s in lines if not s.startswith("saved ")]
    render([("prompt", ".venv/bin/python docs/lecture/inspect_dataset.py lecture_record")] + [("out", s) for s in lines],
           "l06_t_inspect.png", highlight=("episode lengths", "size on disk"))
    render([("prompt", "du -sh data/lecture_record data/omx_cube_fixed5 data/omx_cube_random50"),
            ("out", "1.9M\tdata/lecture_record"), ("out", "2.8M\tdata/omx_cube_fixed5"), ("out", "28M\tdata/omx_cube_random50")],
           "l06_t_size.png")


if __name__ == "__main__":
    for f in (vs_teleop, states, frame, sequence, layout, episode_plot, episode_frames, terminals):
        f()
