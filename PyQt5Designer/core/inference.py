"""
Sign-language inference thread.

Runs MediaPipe hand detection and the trained RandomForest classifier in a
background QThread, emitting recognised signs and annotated video frames.
"""

import logging
import os
import pickle
import threading

import cv2
import mediapipe as mp
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage

import config
from core.features import extract_features

log = logging.getLogger(__name__)


def load_model(path: str = config.MODEL_PATH):
    """Load the pickled model dict and return the estimator.

    Raises FileNotFoundError if the model file is missing, and
    ValueError if the file does not contain the expected structure.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Model file not found: {path}")

    with open(path, "rb") as f:
        model_dict = pickle.load(f)  # noqa: S301

    if not isinstance(model_dict, dict) or "model" not in model_dict:
        raise ValueError("Invalid model file: expected a dict with a 'model' key")

    return model_dict["model"]


class SignLanguageThread(QThread):
    """Performs real-time sign-language recognition from a camera feed."""

    update_frame = pyqtSignal(QImage)
    update_text = pyqtSignal(str)

    def __init__(self, camera_id: int = 0) -> None:
        super().__init__()
        self.camera_id = camera_id
        self.running = True
        self.cap: cv2.VideoCapture | None = None
        self._lock = threading.Lock()

        self.last_prediction: int | None = None
        self.prediction_count = 0

        try:
            self.model = load_model()
        except Exception:
            log.exception("Failed to load sign-language model")
            self.model = None
            self.running = False

    def run(self) -> None:
        if self.model is None:
            return

        try:
            with self._lock:
                self.cap = cv2.VideoCapture(self.camera_id)
                w, h = config.CAMERA_RESOLUTION
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

            mp_hands = mp.solutions.hands
            hands = mp_hands.Hands(
                static_image_mode=True,
                min_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
            )

            while self.running:
                try:
                    with self._lock:
                        if self.cap is None or not self.cap.isOpened():
                            break
                        ret, frame = self.cap.read()

                    if not ret:
                        self.msleep(100)
                        continue

                    H, W, _ = frame.shape
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = hands.process(frame_rgb)

                    if results.multi_hand_landmarks:
                        for hand_lm in results.multi_hand_landmarks:
                            features = extract_features(hand_lm)
                            if features is None:
                                continue

                            xs = [p.x for p in hand_lm.landmark]
                            ys = [p.y for p in hand_lm.landmark]
                            x1 = int(min(xs) * W) - 10
                            y1 = int(min(ys) * H) - 10
                            x2 = int(max(xs) * W) + 10
                            y2 = int(max(ys) * H) + 10

                            try:
                                input_data = np.asarray(features).reshape(1, -1)
                                prediction = int(self.model.predict(input_data)[0])

                                if prediction == self.last_prediction:
                                    self.prediction_count += 1
                                else:
                                    self.prediction_count = 1
                                    self.last_prediction = prediction

                                if self.prediction_count >= config.STABLE_PREDICTIONS_REQUIRED:
                                    label = config.LABELS.get(prediction, "?")
                                else:
                                    label = "Sign language not recognized"

                                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 4)
                                cv2.putText(
                                    frame, label, (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 0), 3,
                                    cv2.LINE_AA,
                                )

                                if label != "Sign language not recognized":
                                    self.update_text.emit(label)
                            except Exception:
                                log.exception("Error during prediction")

                    rgb_out = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    rows, cols, ch = rgb_out.shape
                    bpl = ch * cols
                    qt_image = QImage(rgb_out.data, cols, rows, bpl, QImage.Format_RGB888)
                    self.update_frame.emit(qt_image)
                    self.msleep(10)

                except Exception:
                    log.exception("Error in SignLanguageThread loop")
                    self.msleep(500)

        except Exception:
            log.exception("Critical error in SignLanguageThread")
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
            log.warning("SignLanguageThread did not stop in time")

    def _release_camera(self) -> None:
        with self._lock:
            if self.cap is not None and self.cap.isOpened():
                try:
                    self.cap.release()
                except Exception:
                    log.exception("Error releasing camera")
            self.cap = None
