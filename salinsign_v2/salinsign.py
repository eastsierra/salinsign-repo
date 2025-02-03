import cv2
import numpy as np
from landmarks import mediapipe_detection, draw_styled_landmarks
from extraction import extract_keypoints
from tensorflow.keras.models import load_model
import mediapipe as mp
from threading import Thread

# Colors for visualization
colors = [(245, 117, 16), (117, 245, 16), (16, 117, 245)]

def prob_viz(res, actions, input_frame, colors):
    output_frame = input_frame.copy()
    for num, prob in enumerate(res[:len(actions)]):
        # Cycle through colors if there are more classes than colors
        color = colors[num % len(colors)]
        cv2.rectangle(output_frame, (0, 60 + num * 40),
                      (int(prob * 100), 90 + num * 40), color, -1)
        cv2.putText(output_frame, actions[num], (0, 85 + num * 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    return output_frame

# Threaded video stream class
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

# Actions to detect
actions = np.array(['strong', 'backpain', 'cold',
    'breathingdifficulty', 'sorethroat', 'cough',
    'diarrhea', 'dizzy', 'headache', 'heartache',
    'pain', 'sick', 'vomit'])

# Load the trained model
model = load_model('action.h5')

# New detection variables
sequence = []
sentence = []
threshold = 0.8

# Variables for delaying the gesture output
last_predicted = None
gesture_counter = 0
required_frames = 10  # Number of consecutive frames required before updating the output

# Initialize threaded video capture
stream = VideoStream(src=0).start()

mp_holistic = mp.solutions.holistic

with mp_holistic.Holistic(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    # Optionally disable face-related processing:
    # enable_segmentation=False,
    # refine_face_landmarks=False
) as holistic:
    while True:
        frame = stream.read()
        if frame is None:
            continue

        # Resize frame for faster processing
        frame = cv2.resize(frame, (640, 480))
        image, results = mediapipe_detection(frame, holistic)
        draw_styled_landmarks(image, results)

        # Append keypoints and keep a fixed-length sequence
        keypoints = extract_keypoints(results)
        sequence.append(keypoints)
        sequence = sequence[-30:]

        if len(sequence) == 30:
            res = model.predict(np.expand_dims(sequence, axis=0))[0]
            predicted_idx = np.argmax(res)
            predicted_gesture = actions[predicted_idx]

            # Only consider the prediction if its probability exceeds the threshold
            if res[predicted_idx] > threshold:
                # If the same gesture is being predicted, increment the counter; otherwise, reset it.
                if predicted_gesture == last_predicted:
                    gesture_counter += 1
                else:
                    gesture_counter = 1
                    last_predicted = predicted_gesture

                # If the same gesture has been detected for enough consecutive frames, update sentence.
                if gesture_counter >= required_frames:
                    # Only add if it's not already the last gesture in sentence
                    if len(sentence) == 0 or predicted_gesture != sentence[-1]:
                        sentence.append(predicted_gesture)
                    # Optionally, clear the counter after updating
                    gesture_counter = 0
            else:
                # Reset if the confidence is below threshold
                gesture_counter = 0
                last_predicted = None

            # Keep sentence limited to the last 5 gestures
            if len(sentence) > 5:
                sentence = sentence[-5:]

            # Visualize probabilities on the frame
            image = prob_viz(res, actions, image, colors)

        # Display the sentence on the frame
        cv2.rectangle(image, (0, 0), (640, 40), (245, 117, 16), -1)
        cv2.putText(image, ' '.join(sentence), (3, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        cv2.imshow('OpenCV Feed', image)
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    stream.stop()
    cv2.destroyAllWindows()
