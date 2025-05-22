import cv2
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage

import config


def get_available_cameras(max_cameras: int = config.MAX_CAMERA_SCAN) -> list:
    """Detect available camera devices by probing each index."""
    cameras = []
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
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
            cap.release()

    if not cameras:
        cameras.append({"id": 0, "name": "Default Camera"})
    return cameras


class VideoStreamThread(QThread):
    """Captures frames from a camera and emits them as QImage signals."""

    update_frame = pyqtSignal(QImage)

    def __init__(self, camera_id: int = 0):
        super().__init__()
        self.camera_id = camera_id
        self.running = True
        self.cap = None

    def run(self):
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            w, h = config.CAMERA_RESOLUTION
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

            while self.running:
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
        except Exception as e:
            print(f"Error in VideoStreamThread: {e}")
        finally:
            if self.cap is not None and self.cap.isOpened():
                self.cap.release()

    def set_camera(self, camera_id: int):
        if self.camera_id == camera_id:
            return
        self.camera_id = camera_id
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        self.cap = cv2.VideoCapture(self.camera_id)
        w, h = config.CAMERA_RESOLUTION
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

    def stop(self):
        self.running = False
        try:
            if self.cap is not None and self.cap.isOpened():
                self.cap.release()
                self.cap = None
        except Exception as e:
            print(f"Error releasing camera during stop: {e}")
        if not self.wait(config.THREAD_STOP_TIMEOUT_MS):
            print("VideoStreamThread did not stop in time")
