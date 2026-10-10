"""Figures and terminal captures for page ⑤ (teleop). Output: docs/lecture/l05_*.png

The l05_view_*.png screenshots come from the real viewer, driven by dev/fake_leader.py:
  python3 dev/capture_window.py OUT 0.5 36 -- .venv/bin/python dev/fake_leader.py teleop --hold-s 3 -- --fixed-cube --duration 19
  python3 docs/lecture/draw_lesson05_figures.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figstyle import BLUE, GREEN, INK, OUT, RED, C, arrow, chain, fig_ax, image, label, note, rbox, save  # noqa: E402
from render_terminal import render  # noqa: E402


def loop():
    fig, ax = fig_ax(16, 3.9)
    chain(ax, [("리더 읽기", ["get_action()", "약 1.5 ms"]), ("매핑", ["LeaderToSim", "→ 관절 목표 6"]),
               ("물리", ["env.step(목표)", "0.002 s × 50"]), ("카메라", ["global · wrist", "320×240 렌더"]),
               ("화면", ["오버레이 · sync", "성공 판정"]), ("대기", ["0.1 s 채울 때까지", "sleep"])],
          1.3, 1.9, gap=0.3, colors=[C["yellow"], C["yellow"], C["blue"], C["teal"], C["green"], C["grey"]],
          tfs=11.5, fs=9.3)
    ax.plot([15.1, 15.1], [1.3, 0.85], color="#7a4b00", lw=1.3)
    ax.plot([15.1, 1.55], [0.85, 0.85], color="#7a4b00", lw=1.3)
    arrow(ax, (1.55, 0.85), (1.55, 1.3), color="#7a4b00", lw=1.3)
    label(ax, 8.3, 0.85, "10 Hz 반복 (한 바퀴 실측 8 ~ 16 ms, 나머지는 대기)", color="#7a4b00", fs=10)
    note(ax, 0.3, 3.6, "teleop.py 의 한 바퀴 = 0.1 s", bold=True, color=INK, fs=11)
    save(fig, "l05_loop.png")


def screen():
    fig, ax = fig_ax(16, 7.6)
    w = 15.4
    h = image(ax, OUT / "l05_view_success.png", 0.3, 0.3, w)
    s = w / 2293   # figure units per pixel of the 2293 x 960 screenshot

    def at(px, py):
        return 0.3 + px * s, 0.3 + h - py * s

    tags = [((60, 40), (2.6, 7.2), "① 에피소드 · 시간 · 성공 수", INK),
            ((700, 70), (8.0, 7.2), "② SUCCESS 배너 (성공 순간의 시간)", GREEN),
            ((1500, 30), (11.6, 7.2), "③ global 카메라", BLUE),
            ((1500, 500), (12.3, 0.05), "④ wrist 카메라", BLUE),
            ((130, 945), (3.4, 0.05), "⑤ 키 안내", INK)]
    for (px, py), (tx, ty), text, col in tags:
        x, y = at(px, py)
        ax.plot([x, x], [y, ty], color=col, lw=1.2, zorder=5)
        ax.plot([x, tx], [ty, ty], color=col, lw=1.2, zorder=5)
        label(ax, tx, ty, text, color=col, fs=10)
    ax.set_ylim(-0.3, 7.6)
    save(fig, "l05_screen.png")


def view_direction():
    fig, ax = fig_ax(16, 4.0)
    rbox(ax, 0.3, 0.6, 4.6, 2.9, "사람 + 리더", ["사람이 리더 뒤에 앉아 조작", "리더 앞쪽 = 사람 앞쪽"], fc=C["yellow"])
    arrow(ax, (4.9, 2.05), (5.7, 2.05))
    rbox(ax, 5.7, 0.6, 4.6, 2.9, "뷰어 카메라", ["로봇 뒤에서 앞쪽을 봄", "azimuth 0, elevation -40"], fc=C["blue"])
    arrow(ax, (10.3, 2.05), (11.1, 2.05))
    rbox(ax, 11.1, 0.6, 4.6, 2.9, "결과", ["리더를 왼쪽으로 돌리면", "화면의 팔도 왼쪽으로"], fc=C["green"])
    note(ax, 0.3, 0.2, "이 시점은 창을 열 때 set_workspace_camera() 가 한 번 정합니다. 마우스로 돌려 본 뒤에는 창을 다시 열면 처음 시점이 됩니다.")
    save(fig, "l05_view_dir.png")


def sequence():
    fig, ax = fig_ax(16, 4.1)
    names = [("start", "시작 (리더 정지)"), ("grasp", "잡기"), ("carry", "옮기기"), ("success", "놓기 → SUCCESS")]
    for i, (n, t) in enumerate(names):
        x = 0.3 + i * 3.9
        hh = image(ax, OUT / f"l05_view_{n}.png", x, 0.3, 3.7)
        note(ax, x + 1.85, 0.3 + hh + 0.25, t, ha="center", fs=10.5, bold=True, color=INK)
    save(fig, "l05_sequence.png")


def keys():
    fig, ax = fig_ax(16, 4.4)
    rows = [("입력", "동작"), ("ENTER", "새 에피소드: 큐브를 새 자리(--fixed-cube 면 같은 자리)에 놓고, 팔은 리더 자세에서 시작"),
            ("BACKSPACE", "뷰어 자체의 시뮬레이션 리셋 → teleop 이 알아채고 ENTER 와 같이 새 에피소드로 바꿈"),
            ("마우스", "왼쪽 드래그 회전 · 오른쪽 드래그 이동 · 휠 확대 (시점만 바뀜)"),
            ("Ctrl+C (터미널)", "끝내기. 창을 닫아도 끝남")]
    for i, (k, v) in enumerate(rows):
        y = 3.55 - i * 0.72
        rbox(ax, 0.3, y, 3.2, 0.58, k, fc=C["grey"] if i == 0 else C["yellow"], tfs=10.5, lw=0.9)
        rbox(ax, 3.7, y, 12.0, 0.58, v, fc=C["grey"] if i == 0 else "white", tfs=10, lw=0.9)
    note(ax, 0.3, 0.15, "뷰어 창을 한 번 클릭해 키보드 입력을 받게 한 뒤 누릅니다.")
    save(fig, "l05_keys.png")


def status():
    fig, ax = fig_ax(16, 3.6)
    cols = [("J1 +5.6->+5.6", "리더 각도 → MuJoCo 목표 (°)", C["yellow"]),
            ("J3 +98.1->+98.1!", "! = MuJoCo 범위 밖 (잘림)", C["red"]),
            ("G 59.9->+35.5", "트리거 값 → 그리퍼 목표 (°)", C["green"]),
            ("[14.6 ms, ...]", "한 바퀴 계산 시간", C["blue"]),
            ("camera 10.0 fps", "카메라 화면 갱신", C["teal"])]
    w = (15.4 - 0.25 * 4) / 5
    for i, (t, d, fc) in enumerate(cols):
        x = 0.3 + i * (w + 0.25)
        rbox(ax, x, 1.0, w, 2.0, t, [d], fc=fc, tfs=10.5, fs=9.3)
    note(ax, 0.3, 0.45, "터미널 상태 줄은 0.5 s 마다 같은 줄에 덮어 씁니다. ! 가 계속 보이면 리더 자세가 MuJoCo 관절 범위를 넘은 것입니다.")
    save(fig, "l05_status.png")


def tips():
    fig, ax = fig_ax(16, 4.6)
    steps = [("1. 위에서 접근", ["트리거를 놓아 그리퍼를 연 채", "큐브 위로 천천히"]),
             ("2. 손목 맞추기", ["wrist_roll 로 손가락을", "큐브 옆면과 나란히"]),
             ("3. 내려가 쥐기", ["바닥 가까이 내린 뒤", "트리거를 끝까지 쥠"]),
             ("4. 들어 옮기기", ["쥔 채로 들어 올려", "트레이 위로"]),
             ("5. 내려 놓기", ["트레이 안에서 낮춘 뒤", "트리거를 놓음 → SUCCESS"])]
    chain(ax, steps, 1.2, 2.4, gap=0.3, colors=[C["blue"], C["yellow"], C["purple"], C["teal"], C["green"]],
          tfs=11.5, fs=9.5)
    note(ax, 0.3, 0.55, "10 Hz 로 따라가므로 리더를 빠르게 휘두르면 화면의 팔이 늦게 따라옵니다. 천천히, 한 동작씩 하는 것이 녹화(⑥)에도 좋습니다.")
    save(fig, "l05_tips.png")


def terminals():
    render([("prompt", ".venv/bin/python dev/fake_leader.py teleop --hold-s 3 -- --fixed-cube --duration 19"),
            ("out", "cube: fixed at x 0.21, y -0.06, yaw 0 deg"),
            ("out", "J1   +0.0->  +0.0   J2  -17.2-> -17.2   J3   +5.7->  +5.7   J4  +74.5-> +74.5   J5   +0.0->  +0.0   G  59.5->+34.4  [ 8.1 ms, camera 12.0 fps]"),
            ("out", "J1  -12.5-> -12.5   J2   +9.0->  +9.0   J3  -14.0-> -14.0   J4  +90.9-> +90.9   J5  -12.5-> -12.5   G  59.5->+34.4  [10.8 ms, camera 10.0 fps]"),
            ("out", "J1  -14.8-> -14.8   J2  +19.1-> +19.1   J3   -1.9->  -1.9   J4  +72.6-> +72.6   J5  -14.8-> -14.8   G  50.0-> +0.0  [14.5 ms, camera 10.0 fps]"),
            ("out", "J1  +27.0-> +27.0   J2  +16.0-> +16.0   J3  -23.5-> -23.5   J4  +97.2-> +97.2   J5  +27.0-> +27.0   G  50.0-> +0.0  [14.7 ms, camera 10.0 fps]"),
            ("out", "J1  +34.6-> +34.6   J2  +18.1-> +18.1   J3  -29.3-> -29.3   J4  +97.1-> +97.1   J5  +34.6-> +34.6   G  59.5->+34.4  [14.0 ms, camera 10.0 fps]")],
           "l05_t_teleop.png", highlight=("G  50.0",))
    render([("prompt", ".venv/bin/python -c \"... status_line(리더 실측값) ...\"     # ④ 에서 읽은 접어 둔 자세"),
            ("out", "J1   +5.6->  +5.6   J2 -119.8->-119.8   J3  +98.1-> +98.1!  J4  +83.9-> +83.9   J5   +1.5->  +1.5   G  59.9->+35.5")],
           "l05_t_clip.png", highlight=("98.1!",))


if __name__ == "__main__":
    for f in (loop, screen, view_direction, sequence, keys, status, tips, terminals):
        f()
