from tensorflow.keras.models import load_model

# Save the model to a file
model.save('action.h5')

# Delete the model to demonstrate reloading
del model

# Load the model from the file
model = load_model('action.h5')

print("Model successfully saved and reloaded from 'action.h5'")
