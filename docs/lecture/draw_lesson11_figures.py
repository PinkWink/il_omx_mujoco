"""Figures for page ⑪ (real follower + two USB cameras).

  python3 docs/lecture/draw_lesson11_figures.py

Measured values (2026-10-18, follower serial C707EF98…, 12 V supply 11.6 V):
- folded rest: leader J2 -67.5, follower stops at -63.3 -> J2 load 49.5 %; with the -62 soft limit 3 %
- cable caught on J2: leader -62 -> -29 slowly, follower J2 did not move, load 100 % for ~4 s -> overload 0x20
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figstyle import BLUE, C, GREEN, GREY, INK, RED, arrow, chain, fig_ax, label, note, plt, rbox, save  # noqa: E402


def hardware():
    fig, ax = fig_ax(16, 5.6)
    rbox(ax, 6.3, 0.6, 3.4, 4.4, "PC", ["udev 가 이름을 붙임", "/dev/omx_* · /dev/cam_*", "", "/etc/udev/rules.d/", "99-omx-leader.rules (②)", "99-omx-follower.rules", "99-omx-cameras.rules"], fc=C["grey"], dy=0.45)
    devs = [
        (0.3, 3.7, "OMX 리더 (OMX-L)", ["OpenRB-150 · serial 2FD8BC…", "→ /dev/omx_leader (②)"], C["teal"]),
        (0.3, 0.6, "OMX 팔로워 (OMX-F)", ["OpenRB-150 · serial C707EF…", "→ /dev/omx_follower · 12 V 전원"], C["yellow"]),
        (11.7, 3.7, "정면 카메라", ["Lenovo FHD · USB id 17ef:4831", "→ /dev/cam_front"], C["blue"]),
        (11.7, 0.6, "손목 카메라", ["Innomaker U20CAM · 0c45:6367", "→ /dev/cam_wrist"], C["green"]),
    ]
    for x, y, title, lines, fc in devs:
        rbox(ax, x, y, 4.0, 1.3, title, lines, fc=fc, align="left", fs=9.2)
    arrow(ax, (4.3, 4.35), (6.3, 4.35))
    arrow(ax, (6.3, 1.25), (4.3, 1.25))
    arrow(ax, (11.7, 4.35), (9.7, 4.35))
    arrow(ax, (11.7, 1.25), (9.7, 1.25))
    label(ax, 5.3, 4.65, "위치 읽기")
    label(ax, 5.3, 1.55, "명령 · 상태")
    label(ax, 10.7, 4.65, "영상")
    label(ax, 10.7, 1.55, "영상")
    note(ax, 0.3, 5.35, "USB 장치 네 개: 이름은 꽂는 순서가 아니라 udev 규칙으로 정한다", bold=True, color=INK, fs=11)
    save(fig, "l11_hardware.png")


def follower_udev():
    fig, ax = fig_ax(16, 2.3)
    chain(ax, [("(1) 팔로워만 연결", ["리더 USB 뽑기"]), ("(2) udevadm info", ["ID_SERIAL_SHORT 확인"]),
               ("(3) 규칙 파일", ["99-omx-follower.rules"]), ("(4) 적용 · 확인", ["ls -l /dev/omx_follower"]),
               ("(5) 리더 다시 연결", ["두 이름이 따로"])], 0.35, 1.45,
          colors=[C["red"], C["grey"], C["yellow"], C["teal"], C["purple"]], tfs=11, fs=9.2)
    save(fig, "l11_follower_udev.png")


def camera_rule():
    fig, ax = fig_ax(16, 5.0)
    note(ax, 0.3, 4.75, "카메라는 시리얼로 구분할 수 없다", bold=True, color=INK, fs=11)
    rbox(ax, 0.3, 2.55, 4.9, 1.8, "udevadm info 로 본 두 카메라",
         ["ID_SERIAL_SHORT = SN0001 (둘 다 같음)", "카메라 하나에 video 노드 두 개", "index 0 = 영상, index 1 = 메타데이터"],
         fc=C["red"], align="left", dy=0.4)
    note(ax, 5.8, 4.75, "다른 모델이면: USB 제조사 · 제품 번호", bold=True, color=INK, fs=11)
    rbox(ax, 5.8, 2.55, 4.7, 1.8, "ATTRS{idVendor} · ATTRS{idProduct}",
         ["17ef:4831 (Lenovo) → cam_front", "0c45:6367 (Innomaker) → cam_wrist", "어느 USB 포트에 꽂아도 같음"],
         fc=C["green"], align="left", dy=0.4)
    note(ax, 11.1, 4.75, "같은 모델 두 대면: USB 포트", bold=True, color=INK, fs=11)
    rbox(ax, 11.1, 2.55, 4.6, 1.8, "ENV{ID_PATH}",
         ["pci-…-usb-0:1:1.0 → cam_wrist", "pci-…-usb-0:2:1.0 → cam_front", "늘 같은 포트에 꽂아야 함"],
         fc=C["yellow"], align="left", dy=0.4)
    chain(ax, [("(1) 카메라 찾기", ["real_cameras.py --find"]), ("(2) 번호 확인", ["그리퍼가 보이면 손목"]),
               ("(3) 규칙 만들기", ["camera_udev_rule.py"]), ("(4) 적용 · 확인", ["ls -l /dev/cam_*"]),
               ("(5) 이름으로 보기", ["real_cameras.py"])], 0.35, 1.45,
          colors=[C["grey"], C["blue"], C["yellow"], C["teal"], C["purple"]], tfs=11, fs=9.2)
    save(fig, "l11_camera_rule.png")


def teleop_loop():
    fig, ax = fig_ax(16, 3.4)
    chain(ax, [("check()", ["오류 비트 · 부하 읽기", "약 2.6 ms"]), ("leader.get_action()", ["리더 관절 6개", "정규화 값"]),
               ("follower.send()", ["소프트 한계로 자르기", "Goal_Position 쓰기"]), ("cams.read()", ["두 카메라 최신 영상", "320x240 으로 줄임"]),
               ("window.show()", ["영상 · 배너 · 키 안내", "ESC 로 끝"])], 0.9, 2.1,
          colors=[C["red"], C["teal"], C["yellow"], C["blue"], C["purple"]], tfs=11, fs=9.2)
    note(ax, 0.3, 3.2, "30 Hz 한 주기 (33 ms) 안에서 차례로: 측정 6 ms", bold=True, color=INK, fs=11)
    note(ax, 0.3, 0.45, "MuJoCo 페이지와 다른 점: 단위 변환(LeaderToSim)이 없다. 리더와 팔로워가 같은 정규화 값(-100 ~ 100)을 쓴다.",
         fs=9.8)
    save(fig, "l11_teleop_loop.png")


def safeguards():
    fig, ax = fig_ax(16, 4.6)
    note(ax, 0.3, 4.35, "막힌 관절은 계속 밀다가 스스로 꺼진다 (overload)", bold=True, color=INK, fs=11)
    chain(ax, [("목표에 못 감", ["케이블 걸림 · 책상 · 기구 끝"]), ("부하 100 %", ["모터가 최대 힘으로 밂"]),
               ("overload", ["빨간 LED · 토크 꺼짐", "Hardware_Error 0x20"]), ("복구", ["12 V 전원 + USB 뽑기", "다시 꽂기"])],
          2.55, 1.45, x1=15.7, colors=[C["grey"], C["orange"], C["red"], C["teal"]], tfs=11, fs=9.2)
    note(ax, 0.3, 2.05, "Follower 클래스의 세 가지 안전장치", bold=True, color=INK, fs=11)
    chain(ax, [("소프트 한계", ["configs/follower_limits.json", "J2 ≥ -62 (기구 끝 -63.3)"]),
               ("HIGH LOAD (주황)", ["팔 관절 부하 60 % 이상 0.5 s", "→ 리더를 풀어 준다"]),
               ("MOTOR ERROR (빨강)", ["오류 비트가 서면 명령 중지", "→ 전원 + USB 다시"])],
          0.2, 1.55, arrows=False, colors=[C["yellow"], C["orange"], C["red"]], tfs=11, fs=9.2)
    save(fig, "l11_safeguards.png")


def load_plot():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 3.8), dpi=150, gridspec_kw={"width_ratios": [1, 1.5]})
    a1.bar(["한계 없음\n(목표 -67.5)", "한계 -62"], [49.5, 3.0], color=[RED, GREEN], width=0.55)
    for x, v in enumerate([49.5, 3.0]):
        a1.text(x, v + 2, f"{v:g} %", ha="center", fontsize=11, color=INK)
    a1.set_ylim(0, 100); a1.set_ylabel("J2 부하 (%)")
    a1.set_title("접어 둔 자세에서 J2 부하", fontsize=11.5)
    # real_teleop.py status lines, one every 0.5 s, while a cable held J2 (load = highest arm joint)
    t = [0.5 * i for i in range(11)]
    target = [-66.7, -59.3, -50.3, -39.6, -32.2, -30.3, -29.9, -29.9, -29.4, -29.4, -29.0]
    load = [20, 23, 30, 88, 100, 100, 100, 100, 100, 100, 100]
    a2.plot(t, load, color=RED, marker="o", lw=2, label="가장 큰 팔 관절 부하 (%)")
    a2.axhline(60, color=GREY, ls="--", lw=1); a2.text(2.6, 63, "HIGH LOAD 기준 60 %", color="#666666", fontsize=9.5)
    a2.annotate("overload\n빨간 LED", xy=(5.0, 100), xytext=(5.25, 70), fontsize=10, color=RED,
                arrowprops=dict(arrowstyle="-|>", color=RED))
    a2.set_ylim(0, 115); a2.set_xlim(-0.2, 6.2); a2.set_xlabel("시간 (s)"); a2.set_ylabel("부하 (%)")
    b2 = a2.twinx()
    b2.plot(t, target, color=BLUE, marker="s", lw=1.6, label="J2 목표 (리더)")
    b2.axhline(-62, color=BLUE, ls=":", lw=1.2)
    b2.text(2.3, -60.5, "팔로워 J2: 걸려서 그대로 (약 -62)", color=BLUE, fontsize=9.5)
    b2.set_ylim(-75, -20); b2.set_ylabel("J2 (정규화 값)", color=BLUE)
    b2.spines[["top"]].set_visible(False)
    a2.set_title("케이블에 걸린 J2: 리더만 천천히 -67 → -29", fontsize=11.5)
    h1, l1 = a2.get_legend_handles_labels(); h2, l2 = b2.get_legend_handles_labels()
    a2.legend(h1 + h2, l1 + l2, loc="lower right", fontsize=9, frameon=False)
    a1.spines[["top", "right"]].set_visible(False)
    a2.spines[["top"]].set_visible(False)
    fig.tight_layout()
    save(fig, "l11_load.png")


if __name__ == "__main__":
    for f in (hardware, follower_udev, camera_rule, teleop_loop, safeguards, load_plot):
        f()
