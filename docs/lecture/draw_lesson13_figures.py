"""Figures for page ⑬ (the LeRobot commands under the class scripts).

  python3 docs/lecture/draw_lesson13_figures.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figstyle import C, INK, chain, fig_ax, note, save  # noqa: E402


def steps():
    fig, ax = fig_ax(16, 4.7)
    note(ax, 0.3, 4.45, "준비: 한 번만", bold=True, color=INK, fs=11)
    chain(ax, [("lerobot-info", ["버전 · GPU 확인"]), ("lerobot-find-port", ["보드 포트 찾기"]),
               ("lerobot-find-cameras", ["카메라 번호 · 해상도"]), ("lerobot-calibrate", ["보정 파일 만들기"])],
          2.6, 1.45, colors=[C["grey"], C["teal"], C["blue"], C["yellow"]], tfs=10.5, fs=9.2)
    note(ax, 0.3, 2.0, "모방학습: 매번", bold=True, color=INK, fs=11)
    chain(ax, [("lerobot-teleoperate", ["리더로 조작 연습"]), ("lerobot-record", ["시연 녹화 → 데이터셋"]),
               ("lerobot-dataset-viz", ["데이터 확인 · replay"]), ("lerobot-train", ["ACT 학습"]),
               ("lerobot-rollout", ["정책 실행"])],
          0.15, 1.45, colors=[C["teal"], C["red"], C["purple"], C["yellow"], C["green"]], tfs=10.5, fs=9.2)
    save(fig, "l13_steps.png")


def cli_shape():
    fig, ax = fig_ax(16, 2.6)
    chain(ax, [("lerobot-record", ["어떤 일을 할지", "(명령 이름)"]),
               ("--robot.type=omx_follower", ["그룹.필드=값", "type 을 고르면 그 설정이 열림"]),
               ("--robot.port=/dev/omx_follower", ["로봇 설정의 필드", "--robot.type=... --help 로 목록"]),
               ("--dataset.repo_id=local/x", ["데이터셋 설정의 필드", "기본값은 --help 에"])], 0.6, 1.6,
          arrows=False, colors=[C["grey"], C["blue"], C["blue"], C["yellow"]], tfs=10.5, fs=9.2)
    note(ax, 0.3, 2.4, "LeRobot 명령의 모양: 설정(dataclass)을 --그룹.필드=값 으로 채운다 (draccus)", bold=True, color=INK, fs=11)
    save(fig, "l13_cli.png")


if __name__ == "__main__":
    for f in (steps, cli_shape):
        f()
