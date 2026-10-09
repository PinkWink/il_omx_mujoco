"""Image overlays for the MuJoCo passive viewer: camera insets and a status banner."""
import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont

MARGIN = 8
MIN_INSET_WIDTH = 240
BANNER_HEIGHT = 90
GREEN = (30, 160, 70)
RED = (200, 40, 40)
GRAY = (90, 90, 90)


def _label(img: np.ndarray, text: str) -> np.ndarray:
    pil = Image.fromarray(img)
    draw = ImageDraw.Draw(pil)
    draw.rectangle([0, 0, 8 * len(text) + 10, 18], fill=(0, 0, 0))
    draw.text((5, 3), text, fill=(255, 255, 255))
    return np.asarray(pil)


def _banner(text: str, color: tuple) -> np.ndarray:
    font = ImageFont.load_default(size=44)
    box = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), text, font=font)
    w, h = box[2] - box[0] + 60, BANNER_HEIGHT
    pil = Image.new("RGB", (w, h), color)
    ImageDraw.Draw(pil).text(((w - (box[2] - box[0])) / 2 - box[0], (h - (box[3] - box[1])) / 2 - box[1]),
                             text, fill=(255, 255, 255), font=font)
    return np.asarray(pil)


class ViewerOverlay:
    """Camera insets stacked down the right edge plus an optional banner at the top center.

    The viewer's set_images replaces every image at once, so both live here and are pushed
    together only when something changed. Note: the viewer draws images only while a UI panel
    is shown.
    """

    def __init__(self, viewer):
        self.viewer = viewer
        self.cameras = {}
        self.banner = None  # (text, color)
        self.dirty = False

    def set_cameras(self, images: dict):
        self.cameras = images
        self.dirty = True

    def set_banner(self, text: str | None, color: tuple = GREEN):
        banner = (text, color) if text else None
        if banner != self.banner:
            self.banner = banner
            self.dirty = True

    def flush(self):
        if not self.dirty:
            return
        vp = self.viewer.viewport
        if vp is None:
            return
        self.dirty = False
        items = []
        inset_width = 0
        if self.cameras:
            aspect = [img.shape[0] / img.shape[1] for img in self.cameras.values()]  # h / w
            width = int(min(vp.width / 3, (vp.height - (len(aspect) + 1) * MARGIN) / sum(aspect)))
            if width >= MIN_INSET_WIDTH:
                inset_width = width + MARGIN
                top = vp.height - MARGIN
                for (name, img), a in zip(self.cameras.items(), aspect):
                    h = round(width * a)
                    small = np.asarray(Image.fromarray(img).resize((width, h), Image.BILINEAR))
                    items.append((mujoco.MjrRect(vp.width - width - MARGIN, top - h, width, h),
                                  _label(small, name)))
                    top -= h + MARGIN
        if self.banner:
            img = _banner(*self.banner)
            h, w = img.shape[:2]
            left = max(0, ((vp.width - inset_width) - w) // 2)
            items.append((mujoco.MjrRect(left, vp.height - h - 3 * MARGIN, w, h), img))
        if items:
            self.viewer.set_images(items)
        else:
            self.viewer.clear_images()


def set_workspace_camera(viewer):
    """Free camera behind the robot, so left/right match the operator sitting behind the leader."""
    viewer.cam.lookat[:] = [0.2, 0.03, 0.03]
    viewer.cam.distance = 0.7
    viewer.cam.azimuth = 0
    viewer.cam.elevation = -40
