"""Figures and terminal captures for pages ⑧ (5 fixed demos) and ⑨ (50 random demos). Output: l08_*.png, l09_*.png

  MUJOCO_GL=egl .venv/bin/python docs/lecture/render_lesson08_sim.py     # rollout frames + l08_rollouts.json
  python3 docs/lecture/draw_lesson08_figures.py
Inputs: eval json files under outputs/train/*/checkpoints/*/eval, logs under outputs/lecture, dev sweep json files.
"""
import json
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figstyle import BLUE, GREEN, GREY, INK, OUT, RED, C, arrow, chain, fig_ax, image, note, rbox, save  # noqa: E402
from render_terminal import render  # noqa: E402

ROOT = OUT.parents[1]
LOGS = ROOT / "outputs" / "lecture"
TRAIN = ROOT / "outputs" / "train"
STEPS = ["005000", "010000", "015000", "020000", "025000", "030000"]
X_RANGE, Y_RANGE, YAW_RANGE = (0.17, 0.25), (-0.10, -0.02), (-np.pi / 4, np.pi / 4)
FIXED = (0.21, -0.06)


def rate_from_log(path):
    m = re.search(r"success rate: (\d+)/(\d+)", Path(path).read_text())
    return 100 * int(m[1]) / int(m[2])


def eval_rate(run, step, tag):
    return 100 * json.loads((TRAIN / run / "checkpoints" / step / "eval" / f"{tag}.json").read_text())["success_rate"]


def curves():
    """Success per checkpoint, both policies, both conditions (early 1k-4k from the extra short runs)."""
    def early(ds, cond):
        out = []
        for s in ("001000", "002000", "003000", "004000"):
            p = LOGS / f"eval_early_{ds}_{s}_{cond}.log"
            out.append(rate_from_log(p) if p.exists() else np.nan)
        return out
    k = np.array([1, 2, 3, 4, 5, 10, 15, 20, 25, 30])
    f_fix = early("omx_cube_fixed5", "fixed") + [eval_rate("omx_cube_fixed5_act", s, "pose0.21_-0.06_0_n5") for s in STEPS]
    f_rnd = early("omx_cube_fixed5", "rand") + [eval_rate("omx_cube_fixed5_act", "005000", "seed1000_n50")] + \
        [rate_from_log(LOGS / f"eval_fixed5_{s}.log") for s in STEPS[1:]]
    r_fix = early("omx_cube_random50", "fixed") + [rate_from_log(LOGS / f"eval_random50_fixed_{s}.log") for s in STEPS[:-1]] + \
        [rate_from_log(LOGS / "eval_random50_fixed.log")]
    r_rnd = early("omx_cube_random50", "rand") + [rate_from_log(LOGS / f"eval_random50_{s}.log") for s in STEPS]
    data = {"steps_k": k.tolist(), "fixed5_fixed": f_fix, "fixed5_random": f_rnd, "random50_fixed": r_fix,
            "random50_random": r_rnd}
    (OUT / "l08_curves.json").write_text(json.dumps(data))
    for name, series, title in (
            ("l08_curve.png", [("추론 A: 같은 자리", f_fix, GREEN), ("추론 B: 자리 · 각도 변경", f_rnd, RED)],
             "실습 1 정책 (시연 5회, 고정): 체크포인트별 성공률"),
            ("l09_curve.png", [("추론 A: 같은 자리", r_fix, GREEN), ("추론 B: 자리 · 각도 변경", r_rnd, BLUE)],
             "실습 2 정책 (시연 50회, 무작위): 체크포인트별 성공률")):
        fig, ax = plt.subplots(figsize=(14, 4.8), dpi=150)
        for lab, v, col in series:
            ax.plot(k, v, "o-", color=col, lw=2, ms=6, label=lab)
            for x, y in zip(k, v):
                if not np.isnan(y):
                    ax.text(x, y + 4, f"{y:.0f}", ha="center", fontsize=8.5, color=col)
        ax.axvspan(0.5, 4.5, color="#F4F4F4", zorder=0)
        ax.text(2.5, 112, "1k ~ 4k: 5,000 스텝 짧은 학습 (평가 A 3회 · B 20회)", ha="center", fontsize=9, color="#777777")
        ax.text(17.5, 112, "5k ~ 30k: 30,000 스텝 학습 (평가 A 5~10회 · B 50회)", ha="center", fontsize=9, color="#777777")
        ax.set_xticks(k, [f"{v}k" for v in k]); ax.set_ylim(-5, 120); ax.set_ylabel("성공률 (%)", fontsize=10.5)
        ax.set_xlabel("학습 스텝", fontsize=10.5); ax.grid(color="#EEEEEE"); ax.legend(frameon=False, fontsize=10, loc="center right")
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.set_title(title, fontsize=12)
        fig.savefig(OUT / name, bbox_inches="tight", facecolor="white"); plt.close(fig)
        print("saved", name)


def cube_pose(seed):
    rng = np.random.default_rng(seed)
    return rng.uniform(*X_RANGE), rng.uniform(*Y_RANGE), rng.uniform(*YAW_RANGE)


def placement_map():
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.4), dpi=150)
    for ax, (run, title) in zip(axes, (("omx_cube_fixed5_act", "실습 1 정책 (시연 5회, 고정): 9 / 50"),
                                       ("omx_cube_random50_act", "실습 2 정책 (시연 50회, 무작위): 49 / 50"))):
        res = json.loads((TRAIN / run / "checkpoints/030000/eval/seed1000_n50.json").read_text())["results"]
        ax.add_patch(Rectangle((Y_RANGE[0] * 100, X_RANGE[0] * 100), 8, 8, fc="#F6F8FB", ec=GREY, ls="--"))
        for r in res:
            x, y, yaw = cube_pose(r["seed"])
            ax.plot(y * 100, x * 100, "o" if r["success"] else "x", color=GREEN if r["success"] else RED,
                    ms=8 if r["success"] else 9, mew=2)
        ax.plot(FIXED[1] * 100, FIXED[0] * 100, "s", ms=14, mfc="none", mec=INK, mew=1.8)
        ax.text(FIXED[1] * 100, FIXED[0] * 100 - 0.9, "학습 자리 (고정)", ha="center", va="top", fontsize=9)
        ax.set_xlim(-1, -11); ax.set_ylim(16, 26); ax.set_aspect("equal")
        ax.set_xlabel("y (cm)", fontsize=10); ax.set_ylabel("x (cm)", fontsize=10); ax.grid(color="#EEEEEE")
        ax.set_title(title, fontsize=12)
    fig.text(0.5, 0.0, "평가 50회 (seed 1000~1049) 의 큐브 자리. 초록 o = 성공, 빨강 x = 실패. 점선 = 무작위 범위 (회전은 ±45° 무작위)",
             ha="center", fontsize=10, color="#555555")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUT / "l08_map.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
    print("saved l08_map.png")


def sweep():
    s5 = json.loads((ROOT / "dev/report_fixed5/sweep_fixed5_30k.json").read_text())
    s50 = json.loads((LOGS / "sweep_random50_30k.json").read_text())
    fig, axes = plt.subplots(1, 2, figsize=(15, 4.8), dpi=150, gridspec_kw={"width_ratios": [3, 2]})
    d = ["0", "1", "2", "3", "4", "6"]
    for i, (s, col, lab) in enumerate(((s5, RED, "시연 5회 (고정)"), (s50, BLUE, "시연 50회 (무작위)"))):
        v = [100 * np.mean(s["pos"][k]) for k in d]
        axes[0].bar(np.arange(6) + (i - 0.5) * 0.38, v, 0.36, color=col, label=lab)
        yk = ["5", "10", "20", "30", "45"]
        w = [100 * np.mean(s["yaw"][k]) for k in yk]
        axes[1].bar(np.arange(5) + (i - 0.5) * 0.38, w, 0.36, color=col, label=lab)
    axes[0].set_xticks(range(6), [f"{k} cm" for k in d]); axes[0].set_title("큐브를 학습 자리에서 옮긴 거리 (8 방향, 회전 0°)", fontsize=11)
    axes[1].set_xticks(range(5), [f"±{k}°" for k in ["5", "10", "20", "30", "45"]]); axes[1].set_title("학습 자리에서 회전만 (±, 2회)", fontsize=11)
    for ax in axes:
        ax.set_ylim(0, 110); ax.set_ylabel("성공률 (%)", fontsize=10); ax.grid(axis="y", color="#EEEEEE"); ax.set_axisbelow(True)
        ax.legend(frameon=False, fontsize=9.5, loc="lower left")
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    fig.suptitle("학습 자리 주변에서 조금씩 바꿔 본 결과 (30,000 스텝 정책)", fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT / "l08_sweep.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
    print("saved l08_sweep.png")


def rollout_rows(rows, name, times=(0, 25, 45, 80)):
    fig, ax = fig_ax(16, 3.3 * len(rows) + 0.2)
    for i, (key, case, title) in enumerate(rows):
        y = 0.2 + (len(rows) - 1 - i) * 3.3
        note(ax, 0.3, y + 3.0, title, bold=True, color=INK, fs=11)
        for j, t in enumerate(times):
            x = 0.3 + j * 3.9
            image(ax, OUT / f"l08_{key}_{case}_{t:03d}.png", x, y, 3.7)
            note(ax, x + 0.1, y + 0.2, f"t = {t / 10:.1f} s", fs=9, color="white")
    save(fig, name)


def paths():
    d = json.loads((OUT / "l08_rollouts.json").read_text())
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.0), dpi=150)
    for ax, key, title in ((axes[0], "fixed5", "실습 1 정책"), (axes[1], "random50", "실습 2 정책")):
        for case, col, lab in (("fixed", GREEN, "학습 자리"), ("seed1001", RED, "seed 1001 (4 cm 옆, -28°)")):
            r = d[f"{key}_{case}"]
            t = np.array(r["tcp"]) * 100; c = np.array(r["cube"]) * 100
            ax.plot(t[:, 1], t[:, 0], color=col, lw=1.8, label=f"손끝 경로: {lab}")
            ax.plot(c[0, 1], c[0, 0], "s", color=col, ms=11, mfc="none", mew=2)
        ax.add_patch(Rectangle((13 - 4.4, 18 - 4.4), 8.8, 8.8, fc="#E6F7E6", ec=GREEN))
        ax.text(13, 18, "트레이", ha="center", va="center", color=GREEN, fontsize=10)
        ax.set_xlim(17, -13); ax.set_ylim(8, 28); ax.set_aspect("equal"); ax.grid(color="#EEEEEE")
        ax.set_xlabel("y (cm)", fontsize=10); ax.set_ylabel("x (cm)", fontsize=10); ax.legend(frameon=False, fontsize=9, loc="lower left")
        ax.set_title(f"{title}: 위에서 본 손끝(tcp) 경로, □ = 큐브 시작 자리", fontsize=11)
    fig.tight_layout()
    fig.savefig(OUT / "l08_paths.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
    print("saved l08_paths.png")


def purpose():
    fig, ax = fig_ax(16, 4.2)
    rbox(ax, 0.3, 0.6, 7.5, 3.2, "보이고 싶은 것 1: 간단한 데이터로 먼저 학습된다", ["같은 자리 · 같은 동작 5번이면 충분", "짧은 학습에도 학습 자리에서 성공",
                                                                     "→ 파이프라인이 동작함을 빠르게 확인"], fc=C["green"], align="left", dy=0.55)
    rbox(ax, 8.2, 0.6, 7.5, 3.2, "보이고 싶은 것 2: 데이터는 다양해야 한다", ["같은 정책이 큐브를 몇 cm 옮기면 실패", "큐브 대신 '외운 자리'로 손을 뻗음",
                                                                "→ 실습 2 (시연 50회, 무작위) 의 이유"], fc=C["red"], align="left", dy=0.55)
    save(fig, "l08_purpose.png")


def compare_table():
    c = json.loads((OUT / "l08_curves.json").read_text())
    s5 = json.loads((ROOT / "dev/report_fixed5/sweep_fixed5_30k.json").read_text())
    s50 = json.loads((LOGS / "sweep_random50_30k.json").read_text())
    def frac(s, k):
        return f"{sum(s['pos'][k])} / {len(s['pos'][k])}"
    rows = [("", "실습 1: 시연 5회 (고정)", "실습 2: 시연 50회 (무작위)"),
            ("시연 데이터", "5 에피소드 · 385 프레임 · 2.8 MB", "50 에피소드 · 3,850 프레임 · 28 MB"),
            ("학습 30k 마지막 L1 loss", "0.024", "0.042"),
            ("추론 A 같은 자리 (30k)", f"{c['fixed5_fixed'][-1]:.0f}%", f"{c['random50_fixed'][-1]:.0f}%"),
            ("추론 B 자리 · 각도 변경 50회 (30k)", f"{c['fixed5_random'][-1]:.0f}%", f"{c['random50_random'][-1]:.0f}%"),
            ("3 cm 옮김 (8방향)", frac(s5, "3"), frac(s50, "3")),
            ("6 cm 옮김 (8방향)", frac(s5, "6"), frac(s50, "6"))]
    fig, ax = fig_ax(16, 5.4)
    xs, ws = (0.3, 5.6, 10.7), (5.0, 4.8, 5.0)
    for i, r in enumerate(rows):
        y = 4.6 - i * 0.68
        for j, t in enumerate(r):
            fc = C["grey"] if i == 0 or j == 0 else ([None, C["red"], C["blue"]][j] if i >= 3 else "white")
            if t or i:
                rbox(ax, xs[j], y, ws[j], 0.56, t, fc=fc, tfs=10.5 if i == 0 else 10, lw=0.9)
    save(fig, "l09_compare.png")


def terminals():
    def pick(path, n_ep=5):
        lines = Path(path).read_text().splitlines()
        keep = [s for s in lines if s.startswith(("policy:", "cube:"))]
        keep += [s for s in lines if s.startswith("episode")][:n_ep] + ["..."]
        keep += [s for s in lines if s.startswith(("success rate", "results:"))]
        return keep
    for cmd, log, name in (
            (".venv/bin/python scripts/eval.py --run omx_cube_fixed5_act --fixed-cube --episodes 10", "eval_fixed5_fixed.log", "l08_t_eval_a.png"),
            (".venv/bin/python scripts/eval.py --run omx_cube_fixed5_act --episodes 50", "eval_fixed5_030000.log", "l08_t_eval_b.png"),
            (".venv/bin/python scripts/eval.py --run omx_cube_random50_act --fixed-cube --episodes 10", "eval_random50_fixed.log", "l09_t_eval_a.png"),
            (".venv/bin/python scripts/eval.py --run omx_cube_random50_act --episodes 50", "eval_random50_030000.log", "l09_t_eval_b.png")):
        render([("prompt", cmd)] + [("out", s) for s in pick(LOGS / log)], name, highlight=("success rate",))
    render([("prompt", ".venv/bin/python scripts/scripted_pick_place.py --episodes 50 --dataset omx_cube_random50")]
           + [("out", s) for s in [l for l in (LOGS / "collect_random50.log").read_text().replace("\r", "\n").splitlines()
                                   if l.startswith(("dataset:", "cube:", "episode 0:", "episode 1:", "episode 49:", "success rate"))]],
           "l09_t_collect.png", highlight=("success rate",))


if __name__ == "__main__":
    for f in (purpose, curves, placement_map, sweep, paths, compare_table, terminals):
        f()
    rollout_rows([("fixed5", "fixed", "학습 자리 (x 21, y -6 cm, 0°): 성공 6.3 s"),
                  ("fixed5", "seed1001", "seed 1001 (x 21.9, y -9.9 cm, -28°): 학습 자리로 손을 뻗어 허공을 쥐고, 빈손으로 트레이로")],
                 "l08_rollouts.png")
    rollout_rows([("random50", "seed1001", "실습 2 정책, seed 1001: 큐브를 찾아가 잡고 성공 (6.2 s)"),
                  ("random50", "seed1035", "실습 2 정책의 유일한 실패, seed 1035: 큐브를 잡다가 놓치고 빈손으로 트레이로")],
                 "l09_rollouts.png")
