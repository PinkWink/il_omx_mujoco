"""Figures and terminal captures for page ⑦ (ACT training). Output: docs/lecture/l07_*.png

  python3 docs/lecture/draw_lesson07_figures.py
Inputs: l07_loss.json (parsed from the two 30k training logs), outputs/lecture/train_demo.log (300-step run).
"""
import json
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figstyle import BLUE, GREY, INK, OUT, RED, C, arrow, chain, fig_ax, label, note, rbox, save, tiles  # noqa: E402
from render_terminal import render  # noqa: E402

ROOT = OUT.parents[1]


def behavior_cloning():
    fig, ax = fig_ax(16, 4.2)
    rbox(ax, 0.3, 1.0, 4.4, 2.6, "시연 데이터의 한 순간 t", ["관측: 영상 2 + 관절 6", "정답: 시연 행동 t ~ t+19"],
         fc=C["teal"], align="left", dy=0.5)
    arrow(ax, (4.7, 2.3), (5.5, 2.3))
    rbox(ax, 5.5, 1.0, 4.4, 2.6, "ACT 정책", ["관측 → 행동 20개 예측", "(2 s 분량, 20 × 6)"], fc=C["purple"], align="left", dy=0.5)
    arrow(ax, (9.9, 2.3), (10.7, 2.3))
    rbox(ax, 10.7, 1.0, 5.0, 2.6, "손실 (loss)", ["L1: 예측과 시연 행동의 차이", "KLD: CVAE 잠재 변수 정리 (×10)",
                                                "줄어들도록 신경망 가중치 수정"], fc=C["red"], align="left", dy=0.5)
    note(ax, 0.3, 0.45, "배치 8개 (무작위로 뽑은 순간 8개) 마다 한 번 수정 = 1 스텝. 30,000 스텝이면 순간 24만 개를 봅니다.")
    save(fig, "l07_bc.png")


def chunking():
    fig, ax = fig_ax(16, 4.6)
    x0, x1, y = 0.8, 15.4, 3.2
    ax.plot([x0, x1], [y, y], color=INK, lw=1.3)
    span = (x1 - x0) / 3
    for k in range(4):
        xx = x0 + k * span
        ax.plot([xx, xx], [y - 0.15, y + 0.15], color=INK, lw=1.6)
        ax.text(xx, y + 0.35, f"{2 * k} s", ha="center", fontsize=10)
    for k in range(3):
        xs = x0 + k * span
        ax.plot(xs, y, "o", color=RED, ms=9, zorder=5)
        for i in range(20):
            ax.add_patch(plt.Rectangle((xs + i * span / 20, 1.9 - 0.12 * (k % 2)), span / 20 * 0.85, 0.5,
                                       fc=[C["purple"], C["teal"], C["yellow"]][k], ec=GREY, lw=0.5))
        label(ax, xs + span / 2, 1.3 - 0.12 * (k % 2), f"관측 1번 → 행동 20개 (0.1 s 마다 하나씩 실행)", fs=9.5)
    note(ax, 0.3, 0.45, "chunk_size = n_action_steps = 20: 2 s 마다 한 번 예측하고, 그 사이 20 스텝은 예측한 행동을 차례로 씁니다 (빨간 점 = 예측 시점).")
    note(ax, 0.3, 4.2, "Action chunking (10 Hz, chunk 2 s)", bold=True, color=INK, fs=11)
    save(fig, "l07_chunk.png")


def architecture():
    fig, ax = fig_ax(16, 6.2)
    rbox(ax, 0.3, 4.3, 2.8, 1.2, "global 영상", ["320×240"], fc=C["blue"], tfs=10.5, fs=9)
    rbox(ax, 0.3, 2.8, 2.8, 1.2, "wrist 영상", ["320×240"], fc=C["blue"], tfs=10.5, fs=9)
    rbox(ax, 0.3, 1.3, 2.8, 1.2, "관절 6", ["observation.state"], fc=C["yellow"], tfs=10.5, fs=9)
    rbox(ax, 3.8, 4.3, 2.6, 1.2, "ResNet18", ["영상 특징"], fc=C["grey"], tfs=10.5, fs=9)
    rbox(ax, 3.8, 2.8, 2.6, 1.2, "ResNet18", ["영상 특징"], fc=C["grey"], tfs=10.5, fs=9)
    rbox(ax, 3.8, 1.3, 2.6, 1.2, "선형층", ["→ 512"], fc=C["grey"], tfs=10.5, fs=9)
    for yy in (4.9, 3.4, 1.9):
        arrow(ax, (3.1, yy), (3.8, yy))
        ax.plot([6.4, 7.0], [yy, yy], color=INK, lw=1.4)
    ax.plot([7.0, 7.0], [1.9, 4.9], color=INK, lw=1.4)
    arrow(ax, (7.0, 3.4), (7.6, 3.4))
    rbox(ax, 7.6, 2.3, 3.0, 2.2, "Transformer", ["인코더 4층", "디코더 1층", "폭 512"], fc=C["purple"], tfs=11, fs=9.3)
    arrow(ax, (10.6, 3.4), (11.3, 3.4))
    rbox(ax, 11.3, 2.5, 4.4, 1.8, "행동 20 × 6", ["다음 2 s 의 관절 목표"], fc=C["green"], tfs=11.5, fs=9.5)
    rbox(ax, 7.6, 0.3, 3.0, 1.4, "CVAE 인코더", ["학습 때만: 시연 행동 → z", "추론 때: z = 0"], fc=C["red"], tfs=10, fs=8.8)
    arrow(ax, (9.1, 1.7), (9.1, 2.3))
    note(ax, 11.3, 1.4, "학습할 수 있는 값 5,156만 개 (52M)", fs=9.5)
    note(ax, 11.3, 0.95, "LeRobot ACT 기본 구조, chunk 만 20 으로", fs=9.5)
    note(ax, 0.3, 5.95, "ACT (Action Chunking with Transformers)", bold=True, color=INK, fs=11)
    save(fig, "l07_arch.png")


def settings():
    fig, ax = fig_ax(16, 4.4)
    tiles(ax, [("chunk 20 스텝", ["--chunk-s 2 × 10 fps", "LeRobot 기본 100 은 10 Hz 에서 10 s"], C["purple"]),
               ("batch 8 · lr 1e-5", ["LeRobot ACT 기본 학습률", "GPU 메모리 1.3 GB"], C["grey"]),
               ("30,000 스텝", ["5,000 스텝마다 체크포인트", "Ctrl+C → --resume 으로 이어서"], C["yellow"]),
               ("AMP (GPU)", ["혼합 정밀도 (float16 계산)", "CPU 에서는 끔"], C["blue"]),
               ("Hub 없이", ["HF_HUB_OFFLINE=1 · data/ 의 로컬 데이터", "첫 학습 때 ResNet18 가중치 47 MB 받음"], C["teal"]),
               ("실측 속도", ["RTX 5060 Ti: 약 21 스텝/s", "30,000 스텝 약 23 분"], C["green"])], 3, h=1.8)
    save(fig, "l07_settings.png")


def loss_curves():
    d = json.loads((OUT / "l07_loss.json").read_text())
    fig, axes = plt.subplots(1, 2, figsize=(16, 5.2), dpi=150)
    for name, col, lab in (("fixed5", RED, "시연 5회 (고정)"), ("random50", BLUE, "시연 50회 (무작위)")):
        a = np.array(d[name])
        axes[0].plot(a[:, 0], a[:, 1], color=col, lw=1.4, label=lab)
        axes[1].plot(a[:, 0], a[:, 2], color=col, lw=1.4, label=lab)
    axes[0].set_title("L1 loss (행동 예측 오차, 정규화 단위)", fontsize=11.5)
    axes[1].set_title("KLD loss (CVAE)", fontsize=11.5)
    for axx in axes:
        axx.set_yscale("log"); axx.grid(color="#EEEEEE", which="both")
        axx.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}"))
        axx.yaxis.set_minor_formatter(plt.NullFormatter()); axx.set_xlabel("학습 스텝", fontsize=10)
        axx.legend(frameon=False, fontsize=10); axx.tick_params(labelsize=9)
        for sp in ("top", "right"):
            axx.spines[sp].set_visible(False)
    f5, r50 = d["fixed5"][-1][1], d["random50"][-1][1]
    axes[0].annotate(f"30k: {f5:.3f}", (30000, f5), xytext=(22000, f5 * 0.55), color=RED, fontsize=10,
                     arrowprops=dict(arrowstyle="-", color=RED))
    axes[0].annotate(f"30k: {r50:.3f}", (30000, r50), xytext=(22000, r50 * 2.0), color=BLUE, fontsize=10,
                     arrowprops=dict(arrowstyle="-", color=BLUE))
    fig.suptitle("두 학습의 loss (100 스텝마다 기록). 시연 5회 쪽이 더 낮다 = 외우기 쉽다", fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT / "l07_loss.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
    print("saved l07_loss.png")


def checkpoints():
    fig, ax = fig_ax(16, 4.8)
    rbox(ax, 0.3, 0.4, 6.4, 4.0, "outputs/train/<dataset>_act/", ["checkpoints/005000/", "checkpoints/010000/ ... 030000/",
                                                                 "checkpoints/last → 030000", "(체크포인트 하나 약 0.6 GB)"],
         fc=C["purple"], align="left", dy=0.55)
    rbox(ax, 7.3, 2.5, 8.4, 1.9, "<step>/pretrained_model/  (평가 · 추론에 필요한 것)",
         ["model.safetensors (가중치) · config.json · train_config.json", "policy_preprocessor / postprocessor (정규화 통계)"],
         fc=C["green"], align="left", dy=0.45, tfs=10.5, fs=9.5)
    rbox(ax, 7.3, 0.4, 8.4, 1.7, "<step>/training_state/  (--resume 에 필요한 것)",
         ["optimizer_state · rng_state · training_step.json"], fc=C["grey"], align="left", dy=0.45, tfs=10.5, fs=9.5)
    save(fig, "l07_ckpt.png")


def gpu_cpu():
    fig, ax = plt.subplots(figsize=(12, 3.6), dpi=150)
    vals = [("GPU (RTX 5060 Ti, 30,000 스텝 실측)", 23 / 60, BLUE), ("CPU (Ryzen 7 9700X, 스텝당 0.9 s 실측)", 30000 * 0.9 / 3600, RED)]
    for i, (n, h, c) in enumerate(vals):
        ax.barh(i, h, color=c, height=0.5)
        ax.text(h + 0.12, i, f"{h:.1f} 시간" if h > 1 else f"{h * 60:.0f} 분", va="center", fontsize=11, fontweight="bold")
    ax.set_yticks(range(2), [v[0] for v in vals], fontsize=10.5); ax.invert_yaxis()
    ax.set_xlabel("30,000 스텝 학습 시간 (시간)", fontsize=10.5); ax.set_xlim(0, 9)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.set_title("GPU 와 CPU 학습 시간 비교 (CPU 는 40 스텝을 재서 30,000 스텝으로 환산)", fontsize=11.5)
    fig.savefig(OUT / "l07_gpu_cpu.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
    print("saved l07_gpu_cpu.png")


def terminals():
    txt = (ROOT / "outputs" / "lecture" / "train_demo.log").read_text().replace("\r", "\n")
    steps = re.findall(r"INFO \S+ (\S+) ot_train.py:641 (step:\S+ smpl:\S+ ep:\S+ epch:\S+ loss:\S+) .*?(mem_gb:\S+ l1_loss:\S+)", txt)
    render([("prompt", ".venv/bin/python scripts/train.py --dataset omx_cube_fixed5 --name lecture_demo_act --steps 300 --save-freq 300"),
            ("out", "dataset: /home/pw/il_omx_mujoco/data/omx_cube_fixed5  (5 episodes, 10 fps, ACT chunk 20 steps)"),
            ("out", "run: /home/pw/il_omx_mujoco/outputs/train/lecture_demo_act  device: cuda"),
            ("out", "INFO ... ot_train.py:441 cfg.steps=300 (300)"),
            ("out", "INFO ... ot_train.py:442 dataset.num_frames=385 (385)"),
            ("out", "INFO ... ot_train.py:443 dataset.num_episodes=5"),
            ("out", "INFO ... ot_train.py:447 num_learnable_params=51556230 (52M)")]
           + [("out", f"INFO {t} {a} ... {b}") for t, a, b in steps]
           + [("out", "Training: 100%|##########| 300/300 [00:24<00:00, 21.00step/s]"),
              ("out", "INFO ... ot_train.py:687 Checkpoint policy after step 300"),
              ("out", "done. Policy: /home/pw/il_omx_mujoco/outputs/train/lecture_demo_act/checkpoints/last/pretrained_model")],
           "l07_t_train.png", highlight=("step:", "done."))


if __name__ == "__main__":
    for f in (behavior_cloning, chunking, architecture, settings, loss_curves, checkpoints, gpu_cpu, terminals):
        f()
