"""Damped least-squares IK for the OMX tcp site (5 arm joints)."""
import mujoco
import numpy as np

ARM_DOFS = 5


def top_down_rotation(yaw: float) -> np.ndarray:
    """Tool frame pointing straight down; fingers close along (cos yaw, sin yaw, 0)."""
    x = np.array([0.0, 0.0, -1.0])
    y = np.array([np.cos(yaw), np.sin(yaw), 0.0])
    return np.column_stack([x, y, np.cross(x, y)])


class OmxIK:
    def __init__(self, model: mujoco.MjModel, site: str = "tcp"):
        self.model = model
        self.data = mujoco.MjData(model)
        self.site = model.site(site).id
        self.jnt_range = model.jnt_range[:ARM_DOFS]

    def solve(self, q0, target_pos, target_rot, iters=200, damping=1e-3, rot_weight=0.3):
        m, d = self.model, self.data
        q = np.array(q0[:ARM_DOFS], dtype=float)
        target_quat = np.zeros(4)
        mujoco.mju_mat2Quat(target_quat, np.asarray(target_rot).flatten())
        jacp = np.zeros((3, m.nv))
        jacr = np.zeros((3, m.nv))
        cur_quat = np.zeros(4)
        err = np.zeros(6)
        for _ in range(iters):
            d.qpos[:ARM_DOFS] = q
            mujoco.mj_kinematics(m, d)
            mujoco.mj_comPos(m, d)
            err[:3] = target_pos - d.site_xpos[self.site]
            mujoco.mju_mat2Quat(cur_quat, d.site_xmat[self.site])
            # subQuat gives the error in the current site frame; jacr is in world frame.
            mujoco.mju_subQuat(err[3:], target_quat, cur_quat)
            err[3:] = rot_weight * d.site_xmat[self.site].reshape(3, 3) @ err[3:]
            if np.linalg.norm(err[:3]) < 1e-4 and np.linalg.norm(err[3:]) < 1e-3:
                break
            mujoco.mj_jacSite(m, d, jacp, jacr, self.site)
            J = np.vstack([jacp[:, :ARM_DOFS], rot_weight * jacr[:, :ARM_DOFS]])
            dq = J.T @ np.linalg.solve(J @ J.T + damping * np.eye(6), err)
            q = np.clip(q + dq, self.jnt_range[:, 0], self.jnt_range[:, 1])
        pos_err = np.linalg.norm(target_pos - d.site_xpos[self.site])
        return q, pos_err
