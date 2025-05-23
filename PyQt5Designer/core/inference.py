"""
Sign-language inference thread.

Runs MediaPipe hand detection and the trained RandomForest classifier in a
background QThread, emitting recognised signs and annotated video frames.
"""

import pickle

import cv2
import mediapipe as mp
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage

import config
from core.features import extract_features


def load_model(path: str = config.MODEL_PATH):
    """Load the pickled model dict and return the estimator."""
    with open(path, "rb") as f:
        model_dict = pickle.load(f)
    return model_dict["model"]


class SignLanguageThread(QThread):
    """Performs real-time sign-language recognition from a camera feed."""

    update_frame = pyqtSignal(QImage)
    update_text = pyqtSignal(str)

    def __init__(self, camera_id: int = 0):
        super().__init__()
        self.camera_id = camera_id
        self.running = True
        self.cap = None

        self.last_prediction = None
        self.prediction_count = 0

        try:
            self.model = load_model()
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None
            self.running = False

    def run(self):
        if self.model is None:
            return

        try:
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
                            except Exception as e:
                                print(f"Error during prediction: {e}")

                    rgb_out = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    rows, cols, ch = rgb_out.shape
                    bpl = ch * cols
                    qt_image = QImage(rgb_out.data, cols, rows, bpl, QImage.Format_RGB888)
                    self.update_frame.emit(qt_image)
                    self.msleep(10)

                except Exception as e:
                    print(f"Error in SignLanguageThread: {e}")
                    self.msleep(500)

        except Exception as e:
            print(f"Critical error in SignLanguageThread: {e}")
        finally:
            try:
                if self.cap is not None and self.cap.isOpened():
                    self.cap.release()
            except Exception as e:
                print(f"Error releasing camera: {e}")

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
            print("SignLanguageThread did not stop in time")
