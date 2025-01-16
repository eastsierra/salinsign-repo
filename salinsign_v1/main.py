from landmarks import mediapipe_detection, draw_styled_landmarks
from extraction import extract_keypoints, save_keypoints, load_keypoints
import cv2
import mediapipe as mp
import numpy as np

mp_holistic = mp.solutions.holistic

cap = cv2.VideoCapture(0)
with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
    while cap.isOpened():
        ret, frame = cap.read()
        image, results = mediapipe_detection(frame, holistic)
        draw_styled_landmarks(image, results)

        # Extract and save keypoints
        keypoints = extract_keypoints(results)
        save_keypoints('keypoints', keypoints)

        # Load keypoints (just for demonstration)
        loaded_keypoints = load_keypoints('keypoints.npy')
        print(loaded_keypoints)

        cv2.imshow('OpenCV Feed', image)
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
