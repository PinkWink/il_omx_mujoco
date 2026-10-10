"""Compare OMX leader EEPROM backups (scripts/leader_backup_eeprom.py), ignoring Present_Position.

  python3 docs/lecture/compare_backups.py calibration/leader_eeprom_backup_A.json calibration/leader_eeprom_backup_B.json ...
"""
import json
import sys

backups = [json.load(open(p))["motors"] for p in sys.argv[1:]]
diff = False
for mid in backups[-1]:
    for key in backups[-1][mid]:
        if key == "Present_Position":
            continue
        values = [b[mid].get(key, "-") for b in backups]
        known = [v for v in values if v != "-"]   # older backups may lack a field
        if len(set(known)) > 1:
            diff = True
            print("DIFF motor", mid, key, values)
print("any diff:", diff)
print("Return_Delay_Time now:", {m: backups[-1][m].get("Return_Delay_Time") for m in backups[-1]})
