"""Figures for page ⑫ (real follower: record 10 demos, train 20000 steps, run the policy).

  .venv/bin/python docs/lecture/analyze_lesson12.py      # first: l12_data.json + l12_frame_*.png
  python3 docs/lecture/draw_lesson12_figures.py

Inputs: l12_data.json, l12_frame_*.png, outputs/lecture/l12_video_*.png (stills of the phone video, 0.5 ~ 7.5 s).
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figstyle import BLUE, C, GREEN, GREY, INK, OUT, RED, chain, fig_ax, image, note, plt, save  # noqa: E402

D = json.loads((OUT / "l12_data.json").read_text())
FPS = D["fps"]
JOINTS = ["J1 shoulder_pan", "J2 shoulder_lift", "J3 elbow_flex", "J4 wrist_flex", "J5 wrist_roll", "G gripper"]
STILLS = Path(__file__).resolve().parents[2] / "outputs" / "lecture"


def flow():
    fig, ax = fig_ax(16, 2.3)
    chain(ax, [("real_record.py", ["리더로 시연 10회", "30 fps · 카메라 2대"]),
               ("data/real_strawberry_lift", ["3062 프레임 · 23 MB", "LeRobotDataset"]),
               ("train.py", ["ACT 20000 스텝", "RTX 5060 Ti 16 분"]),
               ("outputs/train/…_act", ["체크포인트 5000 마다", "last = 20000"]),
               ("real_run.py", ["리더 없이 정책만", "딸기를 들어 올림"])], 0.35, 1.45,
          colors=[C["teal"], C["yellow"], C["purple"], C["yellow"], C["green"]], tfs=10.5, fs=9.2)
    save(fig, "l12_flow.png")


def run_flow():
    fig, ax = fig_ax(16, 2.3)
    chain(ax, [("시작 자세로", ["시연 10회의 평균 시작 자세", "3 초 동안 천천히"]),
               ("ENTER", ["policy.reset()", "딸기를 놓은 뒤"]),
               ("정책 실행 (30 Hz)", ["두 카메라 + 관절 → ACT", "60 스텝 chunk 를 차례로"]),
               ("멈춤", ["ENTER · 30 s · HIGH LOAD", "CAMERA LOST · MOTOR ERROR"]),
               ("시작 자세로", ["다시 ENTER 로 다음 시도", "ESC 로 끝"])], 0.35, 1.45,
          colors=[C["grey"], C["teal"], C["green"], C["red"], C["grey"]], tfs=10.5, fs=9.2)
    save(fig, "l12_run_flow.png")


def demo_frames():
    picks = D["frame_picks"]
    fig, ax = fig_ax(16, 6.6)
    w = 2.45
    for c, k in enumerate(picks):
        x = 0.3 + c * (w + 0.18)
        h1 = image(ax, OUT / f"l12_frame_front_{k:03d}.png", x, 3.35, w)
        image(ax, OUT / f"l12_frame_wrist_{k:03d}.png", x, 1.0, w, w * 240 / 320)
        note(ax, x + w / 2, 3.35 + h1 + 0.25, f"{k / FPS:.1f} s", ha="center", bold=True, color=INK, fs=10.5)
    note(ax, 0.3, 3.15, "위: front (사람이 앉은 오른쪽은 잘라 냄)   아래: wrist", fs=9.8)
    save(fig, "l12_demo.png")


def episode_lengths():
    lengths = [len(e["state"]) / FPS for e in D["episodes"]]
    fig, ax = plt.subplots(figsize=(14, 3.2), dpi=150)
    ax.bar(range(len(lengths)), lengths, color=BLUE, width=0.6)
    for i, v in enumerate(lengths):
        ax.text(i, v + 0.2, f"{v:.1f}", ha="center", fontsize=10, color=INK)
    ax.axhline(np.mean(lengths), color=GREY, ls="--", lw=1)
    ax.text(len(lengths) - 0.5, np.mean(lengths) + 0.3, f"평균 {np.mean(lengths):.1f} s", ha="right", color="#666666")
    ax.set_xticks(range(len(lengths)), [f"ep {i}" for i in range(len(lengths))])
    ax.set_ylabel("길이 (s)"); ax.set_ylim(0, max(lengths) * 1.2)
    ax.set_title(f"시연 {len(lengths)} 회의 길이 (모두 {sum(len(e['state']) for e in D['episodes'])} 프레임)", fontsize=11.5)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    save(fig, "l12_lengths.png")


def joints():
    fig, axes = plt.subplots(2, 3, figsize=(15, 6.4), dpi=150, sharex=True)
    cmap = plt.get_cmap("viridis")
    n = len(D["episodes"])
    for e, ep in enumerate(D["episodes"]):
        s = np.array(ep["state"]); t = np.arange(len(s)) / FPS
        for j, ax in enumerate(axes.flat):
            ax.plot(t, s[:, j], color=cmap(e / (n - 1)), lw=1.3, label=f"ep {e}" if j == 0 else None)
    for j, ax in enumerate(axes.flat):
        ax.set_title(JOINTS[j], fontsize=11)
        ax.spines[["top", "right"]].set_visible(False)
        if j >= 3:
            ax.set_xlabel("시간 (s)")
    axes[0, 1].axhline(-62, color=RED, ls=":", lw=1.2)
    axes[0, 1].text(13.5, -59, "소프트 한계 -62", color=RED, fontsize=9, ha="right")
    fig.legend(*axes[0, 0].get_legend_handles_labels(), loc="lower center", ncol=10, fontsize=9, frameon=False,
               bbox_to_anchor=(0.5, -0.04))
    fig.suptitle("시연 10 회의 관절 위치 (observation.state, 정규화 단위)", fontsize=12)
    fig.tight_layout()
    save(fig, "l12_joints.png")


def loss():
    rows = np.array(D["loss"])
    fig, axes = plt.subplots(1, 3, figsize=(15, 3.6), dpi=150)
    for ax, col, title, color in zip(axes, (1, 2, 3), ("loss (= L1 + 10 x KLD)", "L1 (행동 예측 오차)", "KLD (CVAE)"),
                                     (INK, BLUE, GREEN)):
        ax.plot(rows[:, 0], rows[:, col], color=color, lw=1.6)
        ax.set_yscale("log"); ax.set_title(title, fontsize=11.5); ax.set_xlabel("학습 스텝")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.yaxis.set_minor_formatter(plt.NullFormatter())
        ax.text(rows[-1, 0] * 0.75, rows[-1, col] * 5, f"20000 스텝: {rows[-1, col]:.3f}", ha="center", fontsize=10,
                color=color)
        for s in (5000, 10000, 15000):
            ax.axvline(s, color=GREY, lw=0.8, ls=":")
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("20000 스텝 학습의 loss (100 스텝마다 기록, 세로축 로그). 점선 = 체크포인트", fontsize=12)
    fig.tight_layout()
    save(fig, "l12_loss.png")


def predictions():
    ep = D["episodes"][D["episode"]]
    demo, first = np.array(ep["action"]), np.array(D["pred"]["first"])
    t = np.arange(len(demo)) / FPS
    fig, axes = plt.subplots(2, 3, figsize=(15, 6.4), dpi=150, sharex=True)
    for j, ax in enumerate(axes.flat):
        ax.plot(t, demo[:, j], color=GREY, lw=3.2, label="시연 action (리더)")
        ax.plot(t, first[:, j], color=BLUE, lw=1.3, label="모델 예측 (각 프레임 chunk 의 첫 행동)")
        for k, chunk in D["pred"]["chunks"].items():
            k = int(k); c = np.array(chunk)
            tc = (k + np.arange(len(c))) / FPS
            ax.plot(tc, c[:, j], color=RED, lw=1.2, ls="--", label="한 번에 예측한 60 스텝 (2 s)" if k == 0 else None)
            ax.plot(tc[0], c[0, j], "o", color=RED, ms=4)
        err = np.abs(demo[:, j] - first[:, j]).mean()
        ax.set_title(f"{JOINTS[j]}   평균 차이 {err:.2f}", fontsize=11)
        ax.spines[["top", "right"]].set_visible(False)
        if j >= 3:
            ax.set_xlabel("시간 (s)")
    axes[0, 1].legend(fontsize=8.5, frameon=False, loc="lower right")
    fig.suptitle(f"학습한 모델에 시연 ep {D['episode']} 의 영상 · 관절을 넣어 본 예측 (로봇 없이, 학습에 쓴 시연)", fontsize=12)
    fig.tight_layout()
    save(fig, "l12_pred.png")


def success():
    stills = [(0.5, "005"), (2.5, "025"), (4.0, "040"), (5.5, "055"), (7.5, "075")]
    fig, ax = fig_ax(16, 2.75)
    w = 3.0
    for c, (t, tag) in enumerate(stills):
        x = 0.3 + c * (w + 0.12)
        h = image(ax, STILLS / f"l12_video_{tag}.png", x, 0.1, w)
        note(ax, x + w / 2, 0.1 + h + 0.18, f"{t:.1f} s", ha="center", bold=True, color=INK, fs=10.5)
    save(fig, "l12_success_seq.png")


if __name__ == "__main__":
    for f in (flow, run_flow, demo_frames, episode_lengths, joints, loss, predictions, success):
        f()
