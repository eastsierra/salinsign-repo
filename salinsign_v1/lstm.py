import os
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import TensorBoard
from tensorflow.keras.models import load_model

# Load the data
X_train = np.load('X_train.npy')
X_test = np.load('X_test.npy')
y_train = np.load('y_train.npy')
y_test = np.load('y_test.npy')

# Constants (should align with other scripts)
actions = np.array(['hello', 'thanks', 'iloveyou'])
log_dir = os.path.join('Logs')
tb_callback = TensorBoard(log_dir=log_dir)

# Build LSTM Model
model = Sequential([
    LSTM(64, return_sequences=True, activation='relu', input_shape=(30, 1662)),
    LSTM(128, return_sequences=True, activation='relu'),
    LSTM(64, return_sequences=False, activation='relu'),
    Dense(64, activation='relu'),
    Dense(32, activation='relu'),
    Dense(actions.shape[0], activation='softmax')
])

# Test Prediction Example
res = [0.7, 0.2, 0.1]
print(f"Predicted Action: {actions[np.argmax(res)]}")

# Compile Model
model.compile(optimizer='Adam', loss='categorical_crossentropy', metrics=['categorical_accuracy'])

# Train Model
history = model.fit(X_train, y_train, epochs=600, callbacks=[tb_callback])

# Model Summary
model.summary()

# Save the model to a file
model.save('action.h5')

del model

model = load_model('action.h5')