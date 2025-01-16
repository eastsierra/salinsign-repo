import os
import numpy as np

# Path for exported data, numpy arrays
DATA_PATH = os.path.join('MP_Data')

# Actions that we try to detect
actions = np.array(['hello', 'thanks', 'iloveyou'])

# Number of sequences (videos) to collect per action
no_sequences = 30

# Videos are going to be 30 frames in length
sequence_length = 30

def setup_data_folders(data_path, actions, no_sequences):
    """
    Sets up the folder structure for data collection.

    Parameters:
    - data_path: Base directory where data will be stored.
    - actions: List of action labels.
    - no_sequences: Number of sequences per action.

    Creates directories in the form:
    data_path/action_label/sequence_index
    """
    for action in actions:
        for sequence in range(no_sequences):
            folder_path = os.path.join(data_path, action, str(sequence))
            os.makedirs(folder_path, exist_ok=True)
    print(f"Folder structure created under '{data_path}'.")

# Run the folder setup
setup_data_folders(DATA_PATH, actions, no_sequences)
