"""A plain window for the real-robot scripts: both camera views, a banner and key hints.

The venv's OpenCV has no GUI (opencv-python-headless), so the frame is drawn with GLFW and
OpenGL, which MuJoCo already installed. Text is drawn into the image with cv2.putText.
"""
import cv2
import glfw
import numpy as np
from OpenGL import GL

ENTER_KEYS = {glfw.KEY_ENTER, glfw.KEY_KP_ENTER}
BACKSPACE_KEY = glfw.KEY_BACKSPACE
ESCAPE_KEY = glfw.KEY_ESCAPE

RED, GREEN, GRAY, ORANGE, WHITE = (230, 60, 60), (60, 200, 90), (150, 150, 150), (235, 140, 20), (255, 255, 255)
BAR_H = 56
FONT = cv2.FONT_HERSHEY_SIMPLEX


class CameraWindow:
    """Shows camera images side by side (scaled by zoom) with a banner on top and hints below."""

    def __init__(self, title: str, names: list, image_width: int = 320, image_height: int = 240,
                 zoom: float = 2.0):
        self.names = names
        self.view = (round(image_width * zoom), round(image_height * zoom))
        self.size = (self.view[0] * len(names), self.view[1] + 2 * BAR_H)
        if not glfw.init():
            raise SystemExit("cannot open a window (no display?)")
        glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)
        self.window = glfw.create_window(*self.size, title, None, None)
        glfw.make_context_current(self.window)
        glfw.swap_interval(0)  # never wait for the screen refresh; the control loop sets the pace
        self.keys = []
        glfw.set_key_callback(self.window, self._on_key)

    def _on_key(self, window, key, scancode, action, mods):
        if action == glfw.PRESS:
            self.keys.append(key)

    def poll_keys(self) -> list:
        """Keys pressed since the last call."""
        glfw.poll_events()
        keys, self.keys = self.keys, []
        return keys

    def is_running(self) -> bool:
        return not glfw.window_should_close(self.window)

    def show(self, images: dict, banner: str = "", banner_color=GRAY, hint: str = "", info: str = ""):
        w, h = self.size
        frame = np.full((h, w, 3), 30, np.uint8)
        for i, name in enumerate(self.names):
            x = i * self.view[0]
            frame[BAR_H:BAR_H + self.view[1], x:x + self.view[0]] = cv2.resize(images[name], self.view)
            cv2.putText(frame, name, (x + 10, BAR_H + 30), FONT, 0.8, WHITE, 2, cv2.LINE_AA)
        if banner:
            frame[:BAR_H] = banner_color
            cv2.putText(frame, banner, (16, 39), FONT, 1.1, WHITE, 2, cv2.LINE_AA)
        cv2.putText(frame, info, (w - 16 - cv2.getTextSize(info, FONT, 0.8, 2)[0][0], 37), FONT, 0.8, WHITE, 2,
                    cv2.LINE_AA)
        cv2.putText(frame, hint, (16, h - 20), FONT, 0.8, WHITE, 2, cv2.LINE_AA)

        fb_w, fb_h = glfw.get_framebuffer_size(self.window)  # differs from the window size on HiDPI screens
        GL.glViewport(0, 0, fb_w, fb_h)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        GL.glPixelZoom(fb_w / w, fb_h / h)
        GL.glRasterPos2f(-1, -1)
        GL.glDrawPixels(w, h, GL.GL_RGB, GL.GL_UNSIGNED_BYTE, np.ascontiguousarray(frame[::-1]))
        glfw.swap_buffers(self.window)

    def close(self):
        glfw.destroy_window(self.window)
        glfw.terminate()
