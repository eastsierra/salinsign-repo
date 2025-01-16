import cv2
import os
import numpy as np
from landmarks import mediapipe_detection, draw_styled_landmarks
from extraction import extract_keypoints
import mediapipe as mp

# MediaPipe Holistic model
mp_holistic = mp.solutions.holistic

# Path for exported data, numpy arrays
DATA_PATH = os.path.join('MP_Data')

# Actions to detect
actions = np.array(['hello', 'thanks', 'iloveyou'])

# Number of videos per action
no_sequences = 30

# Length of each video in frames
sequence_length = 30


def collect_data(data_path, actions, no_sequences, sequence_length):
    """
    Collects keypoint data for each action and saves it in the specified folder structure.

    Parameters:
    - data_path: Base directory for saving data.
    - actions: List of action labels.
    - no_sequences: Number of sequences per action.
    - sequence_length: Number of frames per sequence.
    """
    cap = cv2.VideoCapture(0)
    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:

        for action in actions:
            for sequence in range(no_sequences):
                for frame_num in range(sequence_length):
                    ret, frame = cap.read()
                    if not ret:
                        print("Failed to capture frame. Exiting.")
                        cap.release()
                        cv2.destroyAllWindows()
                        return

                    # Make detections and draw landmarks
                    image, results = mediapipe_detection(frame, holistic)
                    draw_styled_landmarks(image, results)

                    # Add text for frame collection status
                    if frame_num == 0:
                        cv2.putText(image, 'STARTING COLLECTION', (120, 200),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 4, cv2.LINE_AA)
                        cv2.putText(image, f'Collecting frames for {action} Video Number {sequence}', (15, 12),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                        cv2.imshow('OpenCV Feed', image)
                        cv2.waitKey(2000)  # Wait for 2 seconds before starting collection
                    else:
                        cv2.putText(image, f'Collecting frames for {action} Video Number {sequence}', (15, 12),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                        cv2.imshow('OpenCV Feed', image)

                    # Export keypoints
                    keypoints = extract_keypoints(results)
                    npy_path = os.path.join(data_path, action, str(sequence), str(frame_num))
                    np.save(npy_path, keypoints)

                    # Exit gracefully on 'q' key
                    if cv2.waitKey(10) & 0xFF == ord('q'):
                        print("Exiting gracefully...")
                        cap.release()
                        cv2.destroyAllWindows()
                        return

        cap.release()
        cv2.destroyAllWindows()


# Run the data collection
collect_data(DATA_PATH, actions, no_sequences, sequence_length)
