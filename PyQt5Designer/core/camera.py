"""
Camera utilities: device discovery and video-streaming QThread.
"""

import logging
import threading

import cv2
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage

import config

log = logging.getLogger(__name__)


def get_available_cameras(max_cameras: int = config.MAX_CAMERA_SCAN) -> list[dict]:
    """Detect available camera devices by probing each index."""
    cameras: list[dict] = []
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
        try:
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    try:
                        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        name = f"Camera {i} ({w}x{h})"
                    except Exception:
                        name = f"Camera {i}"
                    cameras.append({"id": i, "name": name})
        finally:
            cap.release()

    if not cameras:
        cameras.append({"id": 0, "name": "Default Camera"})
    return cameras


class VideoStreamThread(QThread):
    """Captures frames from a camera and emits them as QImage signals."""

    update_frame = pyqtSignal(QImage)

    def __init__(self, camera_id: int = 0) -> None:
        super().__init__()
        self.camera_id = camera_id
        self.running = True
        self.cap: cv2.VideoCapture | None = None
        self._lock = threading.Lock()

    def run(self) -> None:
        try:
            with self._lock:
                self.cap = cv2.VideoCapture(self.camera_id)
                w, h = config.CAMERA_RESOLUTION
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

            while self.running:
                with self._lock:
                    if self.cap is None or not self.cap.isOpened():
                        break
                    ret, frame = self.cap.read()

                if not ret:
                    self.msleep(100)
                    continue

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rows, cols, ch = rgb.shape
                bytes_per_line = ch * cols
                qt_image = QImage(rgb.data, cols, rows, bytes_per_line, QImage.Format_RGB888)
                self.update_frame.emit(qt_image)
                self.msleep(30)
        except Exception:
            log.exception("Error in VideoStreamThread")
        finally:
            self._release_camera()

    def set_camera(self, camera_id: int) -> None:
        """Switch to a different camera (thread-safe)."""
        if self.camera_id == camera_id:
            return
        self.camera_id = camera_id
        with self._lock:
            if self.cap is not None and self.cap.isOpened():
                self.cap.release()
            self.cap = cv2.VideoCapture(self.camera_id)
            w, h = config.CAMERA_RESOLUTION
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

    def stop(self) -> None:
        self.running = False
        self._release_camera()
        if not self.wait(config.THREAD_STOP_TIMEOUT_MS):
            log.warning("VideoStreamThread did not stop in time")

    def _release_camera(self) -> None:
        with self._lock:
            if self.cap is not None and self.cap.isOpened():
                try:
                    self.cap.release()
                except Exception:
                    log.exception("Error releasing camera")
            self.cap = None
