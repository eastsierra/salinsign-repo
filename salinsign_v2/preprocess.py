import os
import numpy as np
from sklearn.model_selection import train_test_split
from tensorflow.keras.utils import to_categorical

# Define constants (should align with your project settings)
DATA_PATH = os.path.join('MP_Data')
actions = np.array(['hello', 'thanks', 'iloveyou'])
no_sequences = 30
sequence_length = 30

# Map actions to numerical labels
label_map = {label: num for num, label in enumerate(actions)}

def load_data(data_path, actions, no_sequences, sequence_length):
    """
    Loads and organizes data into features (X) and labels (y).

    Parameters:
    - data_path: Path to the dataset directory.
    - actions: List of action labels.
    - no_sequences: Number of sequences per action.
    - sequence_length: Number of frames per sequence.

    Returns:
    - X: Numpy array of sequences (features).
    - y: Numpy array of one-hot encoded labels.
    """
    sequences, labels = [], []
    for action in actions:
        for sequence in range(no_sequences):
            window = []
            for frame_num in range(sequence_length):
                npy_path = os.path.join(data_path, action, str(sequence), f"{frame_num}.npy")
                res = np.load(npy_path)
                window.append(res)
            sequences.append(window)
            labels.append(label_map[action])

    X = np.array(sequences)
    y = to_categorical(labels).astype(int)
    return X, y

# Load data
X, y = load_data(DATA_PATH, actions, no_sequences, sequence_length)

# Split into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.05, random_state=42)

# Save the data to disk
np.save('X_train.npy', X_train)
np.save('X_test.npy', X_test)
np.save('y_train.npy', y_train)
np.save('y_test.npy', y_test)
