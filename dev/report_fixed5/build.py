"""Inline the jpgs into template.html -> fixed5-report.html (the published page)."""
import base64
from pathlib import Path
d = Path(__file__).parent
s = (d / "template.html").read_text()
for k in ("fail_fixed", "ok_random", "start_fixed", "starts_random"):
    s = s.replace("{{%s}}" % k, "data:image/jpeg;base64," + base64.b64encode((d / f"{k}.jpg").read_bytes()).decode())
(d / "fixed5-report.html").write_text(s)
