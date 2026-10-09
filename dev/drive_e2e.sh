#!/bin/bash
# Run record.py with the fake leader and drive its viewer. Every key goes to a verified window id only.
set -u
S=$(dirname "$0"); cd /home/pw/il_omx_mujoco
w(){ perl -e "select(undef,undef,undef,$1)"; }
rm -rf data/_e2e
.venv/bin/python -u $S/e2e_record.py > $S/e2e.log 2>&1 &
PID=$!
wid=""
for i in $(seq 1 80); do for c in $(xdotool search --pid $PID 2>/dev/null); do xdotool getwindowname $c 2>/dev/null | grep -q "omx cube" && wid=$c; done; [ -n "$wid" ] && break; w 0.25; done
if [ -z "$wid" ]; then echo "NO WINDOW - aborting, no keys sent"; kill -9 $PID; exit 1; fi
echo wid=$wid
key(){ xdotool windowactivate --sync $wid 2>/dev/null; [ "$(xdotool getactivewindow)" = "$wid" ] || { echo "focus lost - aborting"; kill -9 $PID; exit 1; }; xdotool key --window $wid "$1"; }
w 2; key Return; w 3; import -window $wid $S/e1.png; w 4.5; import -window $wid $S/e2.png
w 2; key Return; w 9; import -window $wid $S/e3.png
python3 $S/wm_close.py $wid; w 8
kill -0 $PID 2>/dev/null && { echo STILL_RUNNING; kill -9 $PID; } || echo exited
tr '\r' '\n' < $S/e2e.log | grep -v "^J1" | grep -v "IK error" | grep -v "^\s*$" | tail -8
