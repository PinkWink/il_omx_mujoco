"""Open the interactive MuJoCo viewer on the task scene.

Use the Control panel sliders to move joints. Press ] / [ to cycle cameras (global, wrist).
"""

import mujoco
import mujoco.viewer

from il_omx.env import SCENE_XML

m = mujoco.MjModel.from_xml_path(str(SCENE_XML))
d = mujoco.MjData(m)
mujoco.mj_resetDataKeyframe(m, d, m.key("home").id)
mujoco.viewer.launch(m, d)
