import cv2
import os
import numpy as np
from matplotlib import pyplot as plt
import time
from landmarks import mediapipe_detection, draw_landmarks, draw_styled_landmarks
import mediapipe as mp

mp_holistic = mp.solutions.holistic  # Holistic model

cap = cv2.VideoCapture(0)
with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
    while cap.isOpened():
        ret, frame = cap.read()
        image, results = mediapipe_detection(frame, holistic)
        print(results)
        draw_styled_landmarks(image, results)

        cv2.imshow('OpenCV Feed', image)
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

