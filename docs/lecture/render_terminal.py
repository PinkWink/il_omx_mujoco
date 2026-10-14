"""Render real terminal output as a terminal-styled PNG (dark window, green prompt).

    from render_terminal import render
    render([("prompt", ".venv/bin/python scripts/eval.py ..."), ("out", "episode 0 ..."), ...], "x.png")
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch

from figstyle import OUT

MONO = "NanumGothicCoding" if any(f.name == "NanumGothicCoding" for f in font_manager.fontManager.ttflist) \
    else "DejaVu Sans Mono"
SANS = "NanumGothic" if any(f.name == "NanumGothic" for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
PROMPT = "pw@laptop:~/il_omx_mujoco$ "
TITLE = "pw@laptop: ~/il_omx_mujoco — bash"


def render(lines, name, title=TITLE, highlight=(), prompt=PROMPT):
    """lines: ("prompt", command) or ("out", text). Lines containing a highlight string are yellow."""
    W, LH = 14.0, 0.36
    H = LH * len(lines) + 1.0
    fig, ax = plt.subplots(figsize=(W, H), dpi=150); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.1, 0.1), W - 0.2, H - 0.2, boxstyle="round,pad=0,rounding_size=0.15",
                                fc="#1E1E1E", ec="#444444", lw=1))
    ax.add_patch(FancyBboxPatch((0.1, H - 0.55), W - 0.2, 0.45, boxstyle="round,pad=0,rounding_size=0.15",
                                fc="#2D2D2D", ec="none"))
    for i, c in enumerate(("#FF5F56", "#FFBD2E", "#27C93F")):
        ax.add_patch(plt.Circle((0.4 + i * 0.28, H - 0.32), 0.08, fc=c, ec="none"))
    ax.text(W / 2, H - 0.32, title, ha="center", va="center", fontsize=9, color="#BBBBBB", family=SANS)
    y = H - 0.95
    for kind, text in lines:
        if kind == "prompt":
            t = ax.text(0.35, y, prompt, va="center", fontsize=9.6, color="#5FD75F", family=MONO)
            fig.canvas.draw()
            x1 = ax.transData.inverted().transform((t.get_window_extent().x1, 0))[0]
            ax.text(x1, y, text, va="center", fontsize=9.6, color="#FFFFFF", family=MONO)
        else:
            col = "#FFD75F" if any(h in text for h in highlight) else "#E0E0E0"
            # NanumGothicCoding draws box-drawing glyphs double-width, so tree output uses DejaVu
            fam = "DejaVu Sans Mono" if any(ch in text for ch in "├└│─") else MONO
            ax.text(0.35, y, text, va="center", fontsize=9.6, color=col, family=fam)
        y -= LH
    fig.savefig(OUT / name, bbox_inches="tight", facecolor="white", pad_inches=0.05)
    plt.close(fig)
    print("saved", name)
