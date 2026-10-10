"""Shared drawing helpers for the lecture figures (same look as the mujoco + ROS2 lecture pages).

Run the draw_*.py scripts with the system python3 (matplotlib) from the repository root.
All arrows are vertical or horizontal; Korean text uses NanumGothic.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

for name in ("NanumGothic", "Noto Sans CJK KR", "NanumBarunGothic"):
    if any(f.name == name for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = name
        break
plt.rcParams["axes.unicode_minus"] = False

OUT = Path(__file__).resolve().parent
INK = "#2b2b2b"
C = {"blue": "#E3EEFF", "yellow": "#FFF3D6", "green": "#E6F7E6", "red": "#FFE0E0", "purple": "#EDE7F6",
     "grey": "#F1F2F4", "orange": "#FFE9B8", "teal": "#DDF3F0"}
RED, GREEN, BLUE, GREY = "#C62828", "#2E7D32", "#1565C0", "#9E9E9E"


def fig_ax(w, h):
    fig, ax = plt.subplots(figsize=(w, h), dpi=150)
    ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis("off")
    return fig, ax


def rbox(ax, x0, y0, w, h, title, lines=(), fc="#EEF3FA", ec=INK, tfs=11.5, fs=9.2, lw=1.2, align="center", dy=0.3):
    ax.add_patch(FancyBboxPatch((x0, y0), w, h, boxstyle="round,pad=0,rounding_size=0.12", fc=fc, ec=ec, lw=lw, zorder=2))
    if lines:
        ax.text(x0 + w / 2, y0 + h - 0.22, title, ha="center", va="top", fontsize=tfs, fontweight="bold", color=INK, zorder=3)
        for i, t in enumerate(lines):
            x, ha = (x0 + 0.18, "left") if align == "left" else (x0 + w / 2, "center")
            ax.text(x, y0 + h - 0.22 - 0.42 - dy * i, t, ha=ha, va="top", fontsize=fs, color="#333333", zorder=3)
    else:
        ax.text(x0 + w / 2, y0 + h / 2, title, ha="center", va="center", fontsize=tfs, fontweight="bold", color=INK, zorder=3)


def arrow(ax, p, q, color=INK, lw=1.6, style="-|>"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=15, lw=lw, color=color, zorder=4,
                                 shrinkA=0, shrinkB=0))


def label(ax, x, y, text, color="#444444", fs=8.8, ha="center"):
    ax.text(x, y, text, ha=ha, va="center", fontsize=fs, color=color, zorder=5,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9))


def note(ax, x, y, text, color="#555555", fs=9.5, ha="left", bold=False):
    ax.text(x, y, text, ha=ha, va="center", fontsize=fs, color=color, fontweight="bold" if bold else "normal")


def chain(ax, items, y, h, x0=0.3, x1=None, gap=0.35, tfs=11, fs=9, colors=None, arrows=True):
    """Horizontal flow of boxes. items: title or (title, [lines]). Returns (x0, x1) per box."""
    x1 = x1 if x1 is not None else ax.get_xlim()[1] - 0.3
    n = len(items)
    w = (x1 - x0 - gap * (n - 1)) / n
    spans, x = [], x0
    for i, it in enumerate(items):
        title, lines = (it[0], it[1]) if isinstance(it, tuple) else (it, ())
        rbox(ax, x, y, w, h, title, lines, fc=colors[i % len(colors)] if colors else C["blue"], tfs=tfs, fs=fs)
        spans.append((x, x + w))
        if arrows and i < n - 1:
            arrow(ax, (x + w, y + h / 2), (x + w + gap, y + h / 2))
        x += w + gap
    return spans


def flow_rows(ax, items, per_row, y_top=None, h=1.35, gap=0.3, row_gap=0.75, colors=None, tfs=10.5, fs=8.8, x0=0.3):
    """Left-to-right flow split into rows; an orthogonal path links the end of a row to the next row."""
    W = ax.get_xlim()[1]
    y_top = y_top or ax.get_ylim()[1] - 0.3
    w = (W - 2 * x0 - gap * (per_row - 1)) / per_row
    rows = [items[i:i + per_row] for i in range(0, len(items), per_row)]
    for r, row in enumerate(rows):
        y = y_top - (r + 1) * h - r * row_gap
        for c, (title, sub) in enumerate(row):
            i = r * per_row + c
            x = x0 + c * (w + gap)
            rbox(ax, x, y, w, h, title, [sub] if sub else (), fc=colors[i % len(colors)] if colors else C["blue"],
                 tfs=tfs, fs=fs)
            if c < len(row) - 1:
                arrow(ax, (x + w, y + h / 2), (x + w + gap, y + h / 2))
        if r < len(rows) - 1:
            xr, xl, ym = x0 + (len(row) - 1) * (w + gap) + w / 2, x0 + w / 2, y - row_gap / 2
            ax.plot([xr, xr], [y, ym], color="#7a4b00", lw=1.3, zorder=4)
            ax.plot([xr, xl], [ym, ym], color="#7a4b00", lw=1.3, zorder=4)
            arrow(ax, (xl, ym), (xl, y - row_gap), color="#7a4b00", lw=1.3)


def tiles(ax, items, cols, x0=0.3, y_top=None, gap=0.3, h=1.9, tfs=11.5, fs=9):
    """Grid of cards. items: (title, [lines], color)."""
    W = ax.get_xlim()[1]
    y_top = y_top or ax.get_ylim()[1] - 0.3
    w = (W - 2 * x0 - gap * (cols - 1)) / cols
    for i, (title, lines, fc) in enumerate(items):
        r, c = divmod(i, cols)
        rbox(ax, x0 + c * (w + gap), y_top - (r + 1) * h - r * gap, w, h, title, lines, fc=fc, tfs=tfs, fs=fs,
             align="left")


def image(ax, path, x0, y0, w, h=None):
    """Place a PNG at (x0, y0) with width w (height from the aspect ratio unless given). Returns the height."""
    img = plt.imread(path)
    h = h or w * img.shape[0] / img.shape[1]
    ax.imshow(img, extent=(x0, x0 + w, y0, y0 + h), zorder=1)
    return h


def save(fig, name):
    fig.savefig(OUT / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", name)
