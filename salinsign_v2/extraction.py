import numpy as np

def extract_keypoints(results):
    # Extract pose landmarks
    pose = np.array([[res.x, res.y, res.z, res.visibility] for res in
                     results.pose_landmarks.landmark]).flatten() if results.pose_landmarks else np.zeros(33 * 4)
    # Extract left hand landmarks
    lh = np.array([[res.x, res.y, res.z] for res in
                   results.left_hand_landmarks.landmark]).flatten() if results.left_hand_landmarks else np.zeros(21 * 3)
    # Extract right hand landmarks
    rh = np.array([[res.x, res.y, res.z] for res in
                   results.right_hand_landmarks.landmark]).flatten() if results.right_hand_landmarks else np.zeros(21 * 3)

    # Concatenate all keypoints (excluding face)
    return np.concatenate([pose, lh, rh])

def save_keypoints(filename, keypoints):
    np.save(filename, keypoints)

def load_keypoints(filename):
    return np.load(filename)
