from landmarks import mediapipe_detection, draw_styled_landmarks
from extraction import extract_keypoints, save_keypoints, load_keypoints
import cv2
import mediapipe as mp
import numpy as np
from threading import Thread

# Threaded video stream for smoother capture
class VideoStream:
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src)
        self.ret, self.frame = self.cap.read()
        self.stopped = False

    def start(self):
        Thread(target=self.update, daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            self.ret, self.frame = self.cap.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.cap.release()

# Setup MediaPipe Holistic with face-related features disabled if not needed
mp_holistic = mp.solutions.holistic

# Optional: Toggle keypoint saving for debugging purposes
DEBUG_SAVE = False

# Initialize threaded video capture
stream = VideoStream(src=0).start()
frame_count = 0

with mp_holistic.Holistic(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    # If available in your MediaPipe version, disable unused modules:
    # enable_segmentation=False,
    # refine_face_landmarks=False
) as holistic:
    while True:
        frame = stream.read()
        if frame is None:
            continue

        # Resize for faster processing
        frame = cv2.resize(frame, (640, 480))
        frame_count += 1

        # Process every other frame to reduce load
        if frame_count % 2 != 0:
            cv2.imshow('OpenCV Feed', frame)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break
            continue

        # Detection and drawing
        image, results = mediapipe_detection(frame, holistic)
        draw_styled_landmarks(image, results)

        # Extract keypoints
        keypoints = extract_keypoints(results)
        if DEBUG_SAVE:
            save_keypoints('keypoints', keypoints)
            loaded_keypoints = load_keypoints('keypoints.npy')
            print("Loaded Keypoints:", loaded_keypoints)

        cv2.imshow('OpenCV Feed', image)
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    stream.stop()
    cv2.destroyAllWindows()
