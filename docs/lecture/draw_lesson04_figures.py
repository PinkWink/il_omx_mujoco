"""Figures and terminal captures for page ④ (OMX leader). Output: docs/lecture/l04_*.png

  MUJOCO_GL=egl .venv/bin/python docs/lecture/render_lesson04_sim.py      # sim renders + l04_data.json
  python3 docs/lecture/draw_lesson04_figures.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figstyle import INK, OUT, RED, C, arrow, chain, fig_ax, image, note, rbox, save  # noqa: E402
from render_terminal import render  # noqa: E402

DATA = json.loads((OUT / "l04_data.json").read_text())


def hardware():
    fig, ax = fig_ax(16, 4.4)
    rbox(ax, 0.3, 0.6, 5.0, 3.4, "OMX 리더 (실물)", ["Dynamixel XL330 6개 (ID 1~6)", "팔 1~5: 모델 1200 (XL330-M288)",
                                                   "그리퍼 트리거 6: 모델 1190 (XL330-M077)", "통신 1 Mbps, Protocol 2.0"],
         fc=C["yellow"], align="left", dy=0.5)
    arrow(ax, (5.3, 2.3), (6.1, 2.3))
    rbox(ax, 6.1, 0.6, 3.6, 3.4, "USB", ["/dev/ttyACM0", "dialout 그룹 권한 (②)"], fc=C["grey"], align="left", dy=0.5)
    arrow(ax, (9.7, 2.3), (10.5, 2.3))
    rbox(ax, 10.5, 0.6, 5.2, 3.4, "PC: LeRobot OmxLeader", ["connect(): 설정 쓰기 (2절)", "get_action(): 6개 위치 읽기",
                                                          "읽기 1회 1.4 ~ 1.6 ms (실측)"], fc=C["purple"], align="left", dy=0.5)
    save(fig, "l04_hardware.png")


def pipeline():
    fig, ax = fig_ax(16, 3.6)
    chain(ax, [("Present_Position", ["모터 원시값 0 ~ 4095", "= 한 바퀴"]),
               ("LeRobot 정규화", ["팔: -100 ~ 100", "그리퍼: 0 ~ 100"]),
               ("LeaderToSim", ["팔: 1.8°/단위", "그리퍼: (값-50) × 3.6°"]),
               ("MuJoCo 목표 (rad)", ["Joint1~5, Gripper", "범위 밖이면 잘림"])],
          1.0, 2.1, colors=[C["grey"], C["purple"], C["yellow"], C["blue"]], tfs=11.5, fs=9.5)
    note(ax, 0.3, 0.45, "예: shoulder_pan 원시값 2111 → 2111/4095 × 200 - 100 = +3.10 → × 1.8° = +5.6° → Joint1 목표 5.6°")
    save(fig, "l04_pipeline.png")


def arm_mapping():
    fig, ax = fig_ax(16, 5.0)
    rows = [("리더 모터", "LeRobot 이름", "MuJoCo 관절", "변환"),
            ("ID 1", "shoulder_pan", "Joint1", "1.8° × 값"),
            ("ID 2", "shoulder_lift", "Joint2", "1.8° × 값"),
            ("ID 3", "elbow_flex", "Joint3", "1.8° × 값"),
            ("ID 4", "wrist_flex", "Joint4", "1.8° × 값"),
            ("ID 5", "wrist_roll", "Joint5", "1.8° × 값"),
            ("ID 6", "gripper", "Gripper", "(값 - 50) × 3.6°")]
    xs, ws = (0.3, 2.6, 6.2, 9.4), (2.1, 3.4, 3.0, 6.3)
    for i, r in enumerate(rows):
        y = 4.35 - i * 0.62
        for j, t in enumerate(r):
            fc = C["grey"] if i == 0 else ([C["yellow"], "white", C["blue"], "white"][j])
            rbox(ax, xs[j], y, ws[j], 0.5, t, fc=fc, tfs=10.5 if i == 0 else 10, lw=0.9)
    note(ax, 0.3, 0.1, "팔 관절은 리더 각도를 그대로 (sign +1, offset 0). ROBOTIS 설명서대로 조립한 리더와 menagerie 모델의 0° 자세가 같습니다.")
    save(fig, "l04_arm_mapping.png")


def zero_pose():
    fig, ax = fig_ax(16, 5.3)
    h = image(ax, OUT / "l04_sim_zero.png", 0.3, 0.3, 7.4)
    note(ax, 4.0, 0.3 + h + 0.25, "리더 값이 모두 0 (그리퍼 50) → MuJoCo 0° 자세", ha="center", fs=10.5, bold=True, color=INK)
    h2 = image(ax, OUT / "l04_sim_rest.png", 8.3, 0.3, 7.4)
    d = DATA["rest"]
    note(ax, 12.0, 0.3 + h2 + 0.25, "실측: 책상에 접어 둔 리더 → MuJoCo", ha="center", fs=10.5, bold=True, color=INK)
    save(fig, "l04_poses.png")


def clip_example():
    fig, ax = fig_ax(16, 3.4)
    d = DATA["rest"]
    names = ["Joint1", "Joint2", "Joint3", "Joint4", "Joint5", "Gripper"]
    w = (15.4 - 0.25 * 5) / 6
    for i, n in enumerate(names):
        x = 0.3 + i * (w + 0.25)
        raw, clip = d["sim_deg"][i], d["sim_clipped_deg"][i]
        fc = C["red"] if raw != clip else C["blue"]
        lines = [f"리더 → {raw:+.1f}°"] + ([f"범위 밖 → {clip:+.1f}°"] if raw != clip else ["범위 안"])
        rbox(ax, x, 1.1, w, 1.5, n, lines, fc=fc, tfs=11.5, fs=9.5)
    note(ax, 0.3, 0.4, "접어 둔 자세에서 Joint3 는 +98.1° 로 MuJoCo 범위(-120 ~ 90°)를 넘어 90° 로 잘립니다. teleop 출력에는 '!' 로 표시됩니다.")
    save(fig, "l04_clip.png")


def gripper():
    fig, ax = fig_ax(16, 4.4)
    rbox(ax, 0.3, 0.7, 4.9, 3.2, "트리거를 놓음", ["리더 값 약 60 (열린 위치)", "(60 - 50) × 3.6° = 36°",
                                               "→ MuJoCo 그리퍼 36° 열림", "실측 59.85 → 35.5°"], fc=C["green"], align="left", dy=0.48)
    rbox(ax, 5.55, 0.7, 4.9, 3.2, "트리거를 쥠", ["리더 값 약 47", "(47 - 50) × 3.6° = -10.8°",
                                              "→ 0° (닫힘) 아래로 잘림", "액추에이터가 계속 조임"], fc=C["red"], align="left", dy=0.48)
    rbox(ax, 10.8, 0.7, 4.9, 3.2, "리더 트리거의 원리", ["그리퍼 서보 = 전류 기반 위치 모드", "목표 = 열린 위치 60, 전류 제한 100",
                                                     "손가락으로 누르면 밀리고", "놓으면 60 으로 돌아옴"], fc=C["purple"], align="left", dy=0.48)
    note(ax, 0.3, 0.3, "실물 팔로워로 LeRobot 이 리더 값을 그대로 보내는 것과 같은 방식입니다. 큐브를 쥐면 힘 제한(±3.5 N·m) 때문에 손가락이 큐브에서 멈춥니다.")
    save(fig, "l04_gripper.png")


def connect_writes():
    fig, ax = fig_ax(16, 5.6)
    rows = [("connect() 가 쓰는 값", "대상", "값", "원래 (10/09 백업)"),
            ("Operating_Mode", "팔 1~5", "4 (확장 위치)", "4"),
            ("Drive_Mode", "팔 1~5 / 그리퍼", "0 / 1 (반전)", "0 / 1"),
            ("Operating_Mode", "그리퍼", "5 (전류 기반 위치)", "5"),
            ("Current_Limit · Homing_Offset", "그리퍼", "100 · 100", "100 · 100"),
            ("Return_Delay_Time", "모두", "0", "기록 없음"),
            ("Goal_Current · 토크 · Goal_Position", "그리퍼", "100 · 켬 · 60", "RAM (전원 끄면 초기화)")]
    xs, ws = (0.3, 5.5, 8.4, 12.0), (5.0, 2.7, 3.4, 3.7)
    for i, r in enumerate(rows):
        y = 4.85 - i * 0.66
        for j, t in enumerate(r):
            fc = C["grey"] if i == 0 else (C["yellow"] if j == 0 else "white")
            rbox(ax, xs[j], y, ws[j], 0.54, t, fc=fc, tfs=10.5 if i == 0 else 9.8, lw=0.9)
    note(ax, 0.3, 0.2, "OMX 리더는 처음부터 LeRobot 설정으로 되어 있어, 연결할 때 쓰는 값이 원래 값과 같았습니다 (전후 백업 비교, 2절).", fs=9.8)
    save(fig, "l04_connect_writes.png")


def terminals():
    motor = "'Model_Number': {m}, 'Firmware_Version': 53, 'ID': {i}, 'Baud_Rate': 3, 'Return_Delay_Time': 0, 'Drive_Mode': {d}, ..."
    render([("prompt", ".venv/bin/python scripts/leader_backup_eeprom.py")]
           + [("out", f"{i} {{" + motor.format(m=1200, i=i, d=0)) for i in range(1, 6)]
           + [("out", "6 {" + motor.format(m=1190, i=6, d=1)),
              ("out", "saved /home/pw/il_omx_mujoco/calibration/leader_eeprom_backup_20261010_095133.json")],
           "l04_t_backup.png", highlight=("saved",))
    line = ("shoulder_pan=  +3.10(   +5.6°)  shoulder_lift= -66.54( -119.8°)  elbow_flex= +54.48(  +98.1°)  "
            "wrist_flex= +46.62(  +83.9°)")
    render([("prompt", ".venv/bin/python scripts/leader_read.py"),
            ("out", "connected. Ctrl+C to stop."),
            ("out", line),
            ("out", "    wrist_roll=  +0.85(   +1.5°)  gripper= +59.85  [1.6 ms]"),
            ("out", "^C")],
           "l04_t_read.png", highlight=("gripper=",))
    render([("prompt", "python3 docs/lecture/compare_backups.py calibration/leader_eeprom_backup_20261009_121708.json \\"),
            ("out", "      calibration/leader_eeprom_backup_20261010_095133.json calibration/leader_eeprom_backup_20261010_095140.json"),
            ("out", "any diff: False"),
            ("out", "Return_Delay_Time now: {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0, '6': 0}")],
           "l04_t_compare.png", highlight=("any diff: False",))


if __name__ == "__main__":
    for f in (hardware, pipeline, arm_mapping, zero_pose, clip_example, gripper, connect_writes, terminals):
        f()
