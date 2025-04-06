# SalinSign: A Filipino Sign Language Recognition System for Doctor-Deaf Interaction

## About the Project

SalinSign is a Filipino Sign Language recognition system specializing for doctor-patient interaction, centering on creating a real-time application optimized for clinical environments. During consultations, it enables deaf patients to communicate with a general practitioner using medical-related FSL gestures, which will be translated into text. The general practitioner will respond by typing messages, which will be displayed as text for the patient to read. This setup eliminates the need for an interpreter—which may be limited or not available at all clinics—ensuring confidentiality and facilitating direct communication between the patient and the general practitioner.


## Features

- **Real-time Sign Language Detection**: Recognizes 53 signs including:
  - Medical signs (Pain, Sick, Headache, Fever, etc.)
  - Alphabet letters (A-Z)
- **Advanced Feature Extraction**: 84 hand features extracted for accurate recognition
- **Optimized Performance**: Configurable for different computer specifications

## Project Components

- **inference_classifier.py**: Main application for real-time sign language detection
- **create_dataset.py**: Processes collected images to extract hand features
- **train_classifier.py**: Trains the machine learning model
- **collect_imgs.py**: Tool for collecting training data

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/medical-sign-interpreter.git
   cd medical-sign-interpreter
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python inference_classifier.py
   ```

## Feature Extraction

This project uses MediaPipe Hands to extract 84 features from hand landmarks:

1. 42 features from 2D normalized coordinates (x,y) of 21 hand landmarks
2. 21 features from normalized z-coordinates
3. 5 features representing distances between fingertips and wrist
4. 4 features representing angles between adjacent fingers
5. 4 features representing distances between adjacent fingertips
6. 8 features representing curvature of each finger

## Dataset Collection

To collect your own dataset:
1. Run `collect_imgs.py`
2. Follow the on-screen instructions to capture images for each sign
3. Process the dataset with `create_dataset.py`
4. Train the model with `train_classifier.py`

## For Medical Staff

This tool is designed to facilitate communication between medical professionals and deaf patients by:

1. Providing real-time translation of medical sign language
2. Focusing on common medical terms and conditions
3. Enabling accurate symptom communication

## Performance Optimization

For computers with lower specifications:
- Reduced camera resolution settings (640x480)
- Frame rate controls
- Feature selection options

## Future Development

- GUI interface for easier interaction
- Text-to-sign language translation
- Expanded medical vocabulary
- Standalone executable application

## Requirements

- Python 3.7+
- OpenCV 4.7.0.68
- MediaPipe 0.9.0.1
- scikit-learn 1.2.0