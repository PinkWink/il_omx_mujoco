"""Read-only backup of the OMX leader's servo settings (no writes to the motors).

Run this once before connecting through LeRobot, which rewrites some EEPROM fields
(e.g. the gripper Homing_Offset) in configure().
"""
import argparse
import json
import time
from pathlib import Path

from dynamixel_sdk import COMM_SUCCESS, PacketHandler, PortHandler

ROOT = Path(__file__).resolve().parents[1]

# XL330 control table: name -> (address, size in bytes)
FIELDS = {
    "Model_Number": (0, 2),
    "Firmware_Version": (6, 1),
    "ID": (7, 1),
    "Baud_Rate": (8, 1),
    "Drive_Mode": (10, 1),
    "Operating_Mode": (11, 1),
    "Homing_Offset": (20, 4),
    "Current_Limit": (38, 2),
    "Max_Position_Limit": (48, 4),
    "Min_Position_Limit": (52, 4),
    "Present_Position": (132, 4),
}
SIGNED = {"Homing_Offset", "Present_Position"}


def read(packet, port, dxl_id, addr, size):
    fn = {1: packet.read1ByteTxRx, 2: packet.read2ByteTxRx, 4: packet.read4ByteTxRx}[size]
    value, comm, err = fn(port, dxl_id, addr)
    if comm != COMM_SUCCESS:
        raise IOError(packet.getTxRxResult(comm))
    return value


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", default="/dev/ttyACM0")
    p.add_argument("--baudrate", type=int, default=1_000_000)
    p.add_argument("--ids", type=int, nargs="+", default=[1, 2, 3, 4, 5, 6])
    args = p.parse_args()

    port = PortHandler(args.port)
    packet = PacketHandler(2.0)
    if not port.openPort() or not port.setBaudRate(args.baudrate):
        raise SystemExit(f"cannot open {args.port} at {args.baudrate}")

    backup = {"port": args.port, "baudrate": args.baudrate, "time": time.strftime("%Y-%m-%d %H:%M:%S"), "motors": {}}
    for dxl_id in args.ids:
        entry = {}
        for name, (addr, size) in FIELDS.items():
            v = read(packet, port, dxl_id, addr, size)
            if name in SIGNED and v >= 2 ** 31:
                v -= 2 ** 32
            entry[name] = v
        backup["motors"][str(dxl_id)] = entry
        print(dxl_id, entry)
    port.closePort()

    out = ROOT / "calibration" / f"leader_eeprom_backup_{time.strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(backup, indent=2))
    print("saved", out)


if __name__ == "__main__":
    main()
