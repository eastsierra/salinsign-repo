from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit,
                           QScrollArea, QSizePolicy, QFrame, QCheckBox, QDialog, QComboBox,
                           QFormLayout, QDialogButtonBox, QGroupBox, QLayout, QCompleter)
from PyQt5.QtCore import Qt, QSize, QUrl, QThread, pyqtSignal, QByteArray, QTime, QTimer, QRect, QStringListModel
from PyQt5.QtGui import QPixmap, QCursor, QFont, QImage, QPainter, QColor
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import sys
import os
import pickle
import cv2
import mediapipe as mp
import numpy as np
import gc
import wordninja

def get_available_cameras(max_cameras=10):
    """Detect available camera devices by trying to open each index"""
    available_cameras = []
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            # Get camera name/description if possible
            # On most systems, this may just return a generic name
            ret, frame = cap.read()
            if ret:
                name = f"Camera {i}"
                # Try to get camera properties (may not work on all systems)
                try:
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    name = f"Camera {i} ({width}x{height})"
                except:
                    pass
                available_cameras.append({"id": i, "name": name})
            cap.release()

    # If no cameras found, add a dummy entry
    if not available_cameras:
        available_cameras.append({"id": 0, "name": "Default Camera"})

    return available_cameras

class VideoStreamThread(QThread):
    update_frame = pyqtSignal(QImage)

    def __init__(self, camera_id=0):
        super().__init__()
        self.camera_id = camera_id
        self.running = True
        self.cap = None

    def run(self):
        try:
            # Initialize camera with specified ID
            self.cap = cv2.VideoCapture(self.camera_id)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    print(f"Failed to get frame from camera {self.camera_id}")
                    self.msleep(100)  # Sleep to avoid CPU spinning
                    continue

                # Convert frame to QImage
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.update_frame.emit(qt_image)

                # Small delay to prevent CPU overuse
                self.msleep(30)
        except Exception as e:
            print(f"Error in VideoStreamThread: {e}")
        finally:
            if self.cap is not None and self.cap.isOpened():
                self.cap.release()

    def set_camera(self, camera_id):
        """Change the camera source"""
        if self.camera_id == camera_id:
            return  # No change needed

        self.camera_id = camera_id

        # Restart the camera capture
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()

        self.cap = cv2.VideoCapture(self.camera_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def stop(self):
        """Stop the thread safely and release resources"""
        print("VideoStreamThread stopping...")
        try:
            # Signal thread to stop
            self.running = False

            # Release camera resources if available
            try:
                if self.cap is not None and self.cap.isOpened():
                    print("Releasing camera in VideoStreamThread")
                    self.cap.release()
                    self.cap = None
            except Exception as e:
                print(f"Error releasing camera during stop: {e}")

            # Wait briefly to see if the thread exits naturally
            # but don't block indefinitely
            print("Waiting for VideoStreamThread to finish...")
            if not self.wait(300):  # 300ms timeout to give thread a chance to exit
                print("Thread did not stop quickly, continuing with cleanup")

        except Exception as e:
            print(f"Error during VideoStreamThread stop: {e}")

        print("VideoStreamThread stop completed")

class SignLanguageThread(QThread):
    update_frame = pyqtSignal(QImage)
    update_text = pyqtSignal(str)

    def __init__(self, camera_id=0):
        super().__init__()
        self.camera_id = camera_id
        self.running = True
        self.cap = None
        self.confidence_threshold = 0.4  # Lower threshold for testing
        self.last_prediction = None
        self.prediction_count = 0
        self.stable_predictions_required = 3  # Number of consistent predictions required

        # Load model in try-except block to catch any exceptions
        try:
            self.model_dict = pickle.load(open('./model.p', 'rb'))
            self.model = self.model_dict['model']
            self.labels_dict = {0: 'Pain', 1: 'Sick', 2: 'Headache', 3: 'Dizzy', 4: 'Vomit', 5: 'Diarrhea', 6: 'Cough', 7: 'Allergy', 
                           8: 'Strong', 9: 'Weak', 10: 'Stomachache', 11: 'Sore Throat', 12: 'Sore Throat', 13: 'Injury', 
                           14: 'Breathing Difficulty', 15: 'Food Poisoning', 16: 'Wound', 17: 'Stress',
                           18: 'Conditions', 19: 'Fever', 20: 'Diabetes', 21: 'Back Pain', 22: 'Back Pain', 23: 'Colds', 24: 'Stroke',
                           25: 'Blood Pressure', 26: 'Heartache', 27: 'A', 28: 'B', 29: 'C', 30: 'D', 31: 'E', 32: 'F', 33: 'G', 34: 'H', 35: 'I', 
                           36: 'J', 37: 'K', 38: 'L', 39: 'M', 40: 'N', 41: 'O', 42: 'P', 43: 'Q', 44: 'R', 45: 'S', 46: 'T', 
                           47: 'U', 48: 'V', 49: 'W', 50: 'X', 51: 'Y', 52: 'Z', 53: 'Hello', 54: 'Good Morning', 55: 'Good Afternooon',
                           56: 'Good Evening',  57: 'Thank You', 58: 'Good Bye', 59: '3', 60: '4', 61: '5', 62: '7', 63: '8', 64: '9', 65: '10'}
        except Exception as e:
            print(f"Error loading model: {e}")
            self.running = False

    def run(self):
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            mp_hands = mp.solutions.hands
            mp_drawing = mp.solutions.drawing_utils
            mp_drawing_styles = mp.solutions.drawing_styles

            hands = mp_hands.Hands(static_image_mode=True, min_detection_confidence=0.3)

            while self.running:
                try:
                    ret, frame = self.cap.read()
                    if not ret:
                        print("Failed to get frame from camera")
                        # Small delay to avoid CPU spinning
                        self.msleep(100)
                        continue

                    H, W, _ = frame.shape
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    results = hands.process(frame_rgb)

                    if results.multi_hand_landmarks:
                        for hand_landmarks in results.multi_hand_landmarks:
                            # Remove or comment out this section to make landmarks invisible
                            # mp_drawing.draw_landmarks(
                            #     frame,
                            #     hand_landmarks,
                            #     mp_hands.HAND_CONNECTIONS,
                            #     mp_drawing_styles.get_default_hand_landmarks_style(),
                            #     mp_drawing_styles.get_default_hand_connections_style())

                            data_aux = []
                            x_ = []
                            y_ = []
                            z_ = []

                            # Extract x, y, z coordinates
                            for i in range(len(hand_landmarks.landmark)):
                                x = hand_landmarks.landmark[i].x
                                y = hand_landmarks.landmark[i].y
                                z = hand_landmarks.landmark[i].z
                                x_.append(x)
                                y_.append(y)
                                z_.append(z)

                            # 1. Add normalized x and y coordinates (42 features)
                            for i in range(len(hand_landmarks.landmark)):
                                x = hand_landmarks.landmark[i].x
                                y = hand_landmarks.landmark[i].y
                                data_aux.append(x - min(x_))
                                data_aux.append(y - min(y_))

                            # 2. Add normalized z coordinates (21 features)
                            for i in range(len(hand_landmarks.landmark)):
                                z = hand_landmarks.landmark[i].z
                                data_aux.append(z - min(z_))

                            # 3. Add distances between fingertips and wrist (5 features)
                            wrist = hand_landmarks.landmark[0]  # Wrist landmark
                            fingertips = [4, 8, 12, 16, 20]  # Indices of fingertips
                            for fingertip_idx in fingertips:
                                fingertip = hand_landmarks.landmark[fingertip_idx]
                                distance = ((fingertip.x - wrist.x) ** 2 + 
                                          (fingertip.y - wrist.y) ** 2 + 
                                          (fingertip.z - wrist.z) ** 2) ** 0.5
                                data_aux.append(distance)

                            # 4. Add angles between adjacent fingers (4 features)
                            for i in range(4):
                                p1 = hand_landmarks.landmark[fingertips[i]]
                                p2 = hand_landmarks.landmark[fingertips[i+1]]
                                angle = np.arctan2(p2.y - p1.y, p2.x - p1.x)
                                data_aux.append(angle)

                            # 5. Add distances between adjacent fingertips (4 features)
                            for i in range(4):
                                p1 = hand_landmarks.landmark[fingertips[i]]
                                p2 = hand_landmarks.landmark[fingertips[i+1]]
                                distance = ((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2) ** 0.5
                                data_aux.append(distance)

                            # 6. Add finger curvature (8 features)
                            for i in range(4):  # For each finger (excluding thumb)
                                base = hand_landmarks.landmark[fingertips[i] - 3]
                                mid = hand_landmarks.landmark[fingertips[i] - 1]
                                tip = hand_landmarks.landmark[fingertips[i]]
                                # Calculate two angles for each finger
                                angle1 = np.arctan2(mid.y - base.y, mid.x - base.x)
                                angle2 = np.arctan2(tip.y - mid.y, tip.x - mid.x)
                                data_aux.append(angle1)
                                data_aux.append(angle2)

                            # Ensure we have exactly 84 features
                            if len(data_aux) != 84:
                                continue

                            x1 = int(min(x_) * W) - 10
                            y1 = int(min(y_) * H) - 10
                            x2 = int(max(x_) * W) - 10
                            y2 = int(max(y_) * H) - 10

                            try:
                                # Simple approach: get the prediction
                                input_data = np.asarray(data_aux).reshape(1, -1)  # Reshape for single sample
                                
                                # Basic prediction - this should work with most models
                                prediction = self.model.predict(input_data)[0]
                                
                                # Check if prediction is the same as last time
                                current_prediction = int(prediction)
                                
                                if current_prediction == self.last_prediction:
                                    self.prediction_count += 1
                                else:
                                    self.prediction_count = 1
                                    self.last_prediction = current_prediction
                                
                                # Only show a confident prediction if we've seen it consistently
                                if self.prediction_count >= self.stable_predictions_required:
                                    predicted_character = self.labels_dict[current_prediction]
                                else:
                                    predicted_character = "Sign language not recognized"
                                
                                # Draw rectangle around hand with green color
                                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 4)
                                
                                # Show prediction text above hand with green color
                                cv2.putText(frame, predicted_character, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 0), 3, cv2.LINE_AA)

                                # Emit the predicted character only if it's a recognized gesture
                                if predicted_character != "Sign language not recognized":
                                    self.update_text.emit(predicted_character)
                            except Exception as e:
                                print(f"Error during prediction: {e}")

                    # Convert frame to QImage
                    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb_image.shape
                    bytes_per_line = ch * w
                    qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                    self.update_frame.emit(qt_image)

                    # Small delay to prevent CPU overuse
                    self.msleep(10)

                except Exception as e:
                    print(f"Error in SignLanguageThread: {e}")
                    # Sleep to avoid rapid error logging
                    self.msleep(500)

        except Exception as e:
            print(f"Critical error in SignLanguageThread: {e}")
        finally:
            try:
                if self.cap is not None and self.cap.isOpened():
                    self.cap.release()
            except Exception as e:
                print(f"Error releasing camera: {e}")

    def set_camera(self, camera_id):
        """Change the camera source"""
        if self.camera_id == camera_id:
            return  # No change needed

        self.camera_id = camera_id

        # Restart the camera capture
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()

        self.cap = cv2.VideoCapture(self.camera_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def stop(self):
        """Stop the thread safely and release resources"""
        print("SignLanguageThread stopping...")
        try:
            # Signal thread to stop
            self.running = False

            # Release camera resources if available
            try:
                if self.cap is not None and self.cap.isOpened():
                    print("Releasing camera in SignLanguageThread")
                    self.cap.release()
                    self.cap = None
            except Exception as e:
                print(f"Error releasing camera during stop: {e}")

            # Wait briefly to see if the thread exits naturally
            # but don't block indefinitely
            print("Waiting for SignLanguageThread to finish...")
            if not self.wait(300):  # 300ms timeout to give thread a chance to exit
                print("Thread did not stop quickly, continuing with cleanup")

        except Exception as e:
            print(f"Error during SignLanguageThread stop: {e}")

        print("SignLanguageThread stop completed")

class PopupWindow(QDialog):
    def __init__(self, parent=None, content="", popup_type="first", image_path=None):
        super().__init__(parent)
        self.setWindowTitle("")  # Remove window title
        self.setFixedSize(800, 650)  # Make popup bigger (increased from 600x500)
        self.setStyleSheet("background-color: white;")

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for image to span the whole popup

        # Content - either image or text
        if image_path:
            content_label = QLabel()
            pixmap = QPixmap(image_path)
            content_label.setPixmap(pixmap.scaled(800, 550, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            content_label.setAlignment(Qt.AlignCenter)
            content_label.setStyleSheet("padding: 0px;")
        else:
            content_label = QLabel(content)
            content_label.setWordWrap(True)
            content_label.setStyleSheet("font-size: 18px; padding: 30px;")

        layout.addWidget(content_label)

        # Add spacer
        layout.addStretch()

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(20, 0, 20, 20)  # Add some padding around the button

        if popup_type == "first":
            next_button = QPushButton("Let's Get Started")
            next_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            next_button.clicked.connect(self.show_next_popup)
            button_layout.addWidget(next_button)
        elif popup_type == "second":
            # Create Patient button
            patient_button = QPushButton("Patient")
            patient_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: bold;
                    margin: 0 10px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            patient_button.clicked.connect(self.show_patient_popup1)
            button_layout.addWidget(patient_button)

            # Create Doctor button
            doctor_button = QPushButton("Doctor")
            doctor_button.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: bold;
                    margin: 0 10px;
                }
                QPushButton:hover {
                    background-color: #0b7dda;
                }
            """)
            doctor_button.clicked.connect(self.show_doctor_popup1)
            button_layout.addWidget(doctor_button)
        elif popup_type == "final_shared":
            # User Guide button
            guide_button = QPushButton("User Guide")
            guide_button.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: bold;
                    margin: 0 10px;
                }
                QPushButton:hover {
                    background-color: #0b7dda;
                }
            """)
            guide_button.clicked.connect(self.open_user_guide)
            button_layout.addWidget(guide_button)

            # Close button
            close_button = QPushButton("Close")
            close_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: bold;
                    margin: 0 10px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            close_button.clicked.connect(self.accept)
            button_layout.addWidget(close_button)
        else:
            # For all tutorial popups (patient1-5, doctor1-5)
            if "patient" in popup_type or "doctor" in popup_type:
                button_text = "Next"
                if popup_type.endswith("5"):  # Last popup in sequence
                    button_text = "Got it!"

                next_button = QPushButton(button_text)
                next_button.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        padding: 10px 20px;
                        font-size: 14px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)

                # Connect to the appropriate next function based on the popup type
                if popup_type == "patient1":
                    next_button.clicked.connect(self.show_patient_popup2)
                elif popup_type == "patient2":
                    next_button.clicked.connect(self.show_patient_popup3)
                elif popup_type == "patient3":
                    next_button.clicked.connect(self.show_patient_popup4)
                elif popup_type == "patient4":
                    next_button.clicked.connect(self.show_patient_popup5)
                elif popup_type == "patient5":
                    next_button.clicked.connect(self.show_final_shared_popup)
                elif popup_type == "doctor1":
                    next_button.clicked.connect(self.show_doctor_popup2)
                elif popup_type == "doctor2":
                    next_button.clicked.connect(self.show_doctor_popup3)
                elif popup_type == "doctor3":
                    next_button.clicked.connect(self.show_doctor_popup4)
                elif popup_type == "doctor4":
                    next_button.clicked.connect(self.show_doctor_popup5)
                elif popup_type == "doctor5":
                    next_button.clicked.connect(self.show_final_shared_popup)

                button_layout.addWidget(next_button)
            else:
                # For any other popups
                close_button = QPushButton("Got it!")
                close_button.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        padding: 10px 20px;
                        font-size: 14px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
                close_button.clicked.connect(self.accept)
                button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def open_user_guide(self):
        # Close the current popup
        self.accept()

        # Import and show the UserGuideModule
        from UserGuide import UserGuideModule

        # Find the parent TranslationModule window to close it
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, TranslationModule):
                # First create the user guide module
                user_guide = UserGuideModule()
                user_guide.showFullScreen()  # Show in full screen mode

                # Then close the translation module
                widget.close()
                return

        # Fallback if no parent window found
        user_guide = UserGuideModule()
        user_guide.showFullScreen()  # Show in full screen mode

    def show_final_shared_popup(self):
        self.accept()  # Close current popup
        final_popup = PopupWindow(
            self.parent(),
            "",  # No text content needed since we're using an image
            "final_shared",
            "images/helpassets/both/seemorepopup.png"  # Path to the final shared popup image
        )
        final_popup.exec_()

    def show_next_popup(self):
        self.accept()  # Close current popup
        second_popup = PopupWindow(
            self.parent(),
            "",  # No text content needed since we're using an image
            "second",
            "images/helpassets/both/beforepopup.png"  # Path to the image for role selection popup
        )
        second_popup.exec_()

    # Patient tutorial sequence
    def show_patient_popup1(self):
        self.accept()  # Close current popup
        popup = PopupWindow(
            self.parent(),
            "",  # No text needed since we're using images
            "patient1",
            "images/helpassets/patient/patientpopup1.png"
        )
        popup.exec_()

    def show_patient_popup2(self):
        self.accept()  # Close current popup
        popup = PopupWindow(
            self.parent(),
            "",  # No text needed since we're using images
            "patient2",
            "images/helpassets/patient/patientpopup2.png"
        )
        popup.exec_()

    def show_patient_popup3(self):
        self.accept()  # Close current popup
        popup = PopupWindow(
            self.parent(),
            "",  # No text needed since we're using images
            "patient3",
            "images/helpassets/patient/patientpopup3.png"
        )
        popup.exec_()

    def show_patient_popup4(self):
        self.accept()  # Close current popup
        popup = PopupWindow(
            self.parent(),
            "",  # No text needed since we're using images
            "patient4",
            "images/helpassets/patient/patientpopup4.png"
        )
        popup.exec_()

    def show_patient_popup5(self):
        self.accept()  # Close current popup
        popup = PopupWindow(
            self.parent(),
            "",  # No text needed since we're using images
            "patient5",
            "images/helpassets/patient/patientpopup5.png"
        )
        popup.exec_()

    # Doctor tutorial sequence
    def show_doctor_popup1(self):
        self.accept()  # Close current popup
        popup = PopupWindow(
            self.parent(),
            "",  # No text needed since we're using images
            "doctor1",
            "images/helpassets/doctor/doctorpopup1.png"
        )
        popup.exec_()

    def show_doctor_popup2(self):
        self.accept()  # Close current popup
        popup = PopupWindow(
            self.parent(),
            "",  # No text needed since we're using images
            "doctor2",
            "images/helpassets/doctor/doctorpopup2.png"
        )
        popup.exec_()

    def show_doctor_popup3(self):
        self.accept()  # Close current popup
        popup = PopupWindow(
            self.parent(),
            "",  # No text needed since we're using images
            "doctor3",
            "images/helpassets/doctor/doctorpopup3.png"
        )
        popup.exec_()

    def show_doctor_popup4(self):
        self.accept()  # Close current popup
        popup = PopupWindow(
            self.parent(),
            "",  # No text needed since we're using images
            "doctor4",
            "images/helpassets/doctor/doctorpopup4.png"
        )
        popup.exec_()

    def show_doctor_popup5(self):
        self.accept()  # Close current popup
        popup = PopupWindow(
            self.parent(),
            "",  # No text needed since we're using images
            "doctor5",
            "images/helpassets/doctor/doctorpopup5.png"
        )
        popup.exec_()

class MedicalSummaryTemplate(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Medical Summary Template")
        self.setMinimumSize(600, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333;
            }
            QTextEdit, QLineEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                background-color: #f9f9f9;
            }
            QPushButton {
                padding: 10px 20px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 20px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        # Create layout
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Medical Summary")
        header.setStyleSheet("font-size: 24px; color: #2a70a5; margin-bottom: 15px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        # Symptoms section
        symptoms_group = QGroupBox("Symptoms")
        symptoms_layout = QVBoxLayout()
        self.symptoms_edit = QTextEdit()
        self.symptoms_edit.setPlaceholderText("Enter patient symptoms here...")
        self.symptoms_edit.setMinimumHeight(100)
        symptoms_layout.addWidget(self.symptoms_edit)
        symptoms_group.setLayout(symptoms_layout)
        layout.addWidget(symptoms_group)

        # Diagnosis section
        diagnosis_group = QGroupBox("Diagnosis")
        diagnosis_layout = QVBoxLayout()
        self.diagnosis_edit = QTextEdit()
        self.diagnosis_edit.setPlaceholderText("Enter diagnosis here...")
        self.diagnosis_edit.setMinimumHeight(100)
        diagnosis_layout.addWidget(self.diagnosis_edit)
        diagnosis_group.setLayout(diagnosis_layout)
        layout.addWidget(diagnosis_group)

        # Prescription section
        prescription_group = QGroupBox("Prescription")
        prescription_layout = QVBoxLayout()
        self.prescription_edit = QTextEdit()
        self.prescription_edit.setPlaceholderText("Enter prescription details here...")
        self.prescription_edit.setMinimumHeight(100)
        prescription_layout.addWidget(self.prescription_edit)
        prescription_group.setLayout(prescription_layout)
        layout.addWidget(prescription_group)

        # Button layout
        button_layout = QHBoxLayout()

        # Generate Summary button
        self.generate_button = QPushButton("Generate Summary")
        self.generate_button.clicked.connect(self.generate_summary)
        button_layout.addWidget(self.generate_button)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def generate_summary(self):
        """Generate and display a summary of the medical information in a new popup window"""
        symptoms = self.symptoms_edit.toPlainText().strip()
        diagnosis = self.diagnosis_edit.toPlainText().strip()
        prescription = self.prescription_edit.toPlainText().strip()

        # Check if any field is empty
        if not symptoms or not diagnosis or not prescription:
            error_dialog = QDialog(self)
            error_dialog.setWindowTitle("Error")
            error_dialog.setFixedSize(300, 150)
            
            error_layout = QVBoxLayout(error_dialog)
            error_label = QLabel("Please fill in all fields to generate a summary.")
            error_label.setStyleSheet("color: red; font-size: 14px;")
            error_label.setWordWrap(True)
            error_label.setAlignment(Qt.AlignCenter)
            
            ok_button = QPushButton("OK")
            ok_button.clicked.connect(error_dialog.accept)
            
            error_layout.addWidget(error_label)
            error_layout.addWidget(ok_button, alignment=Qt.AlignCenter)
            
            error_dialog.exec_()
            return

        # Create formatted summary
        summary = f"""
        <div style='font-family: Arial, sans-serif; padding: 10px;'>
            <h2 style='color: #2a70a5; text-align: center;'>Medical Summary</h2>
            
            <div style='margin: 15px 0; padding: 10px; background-color: #f0f7ff; border-radius: 5px;'>
                <h3 style='color: #333;'>Symptoms:</h3>
                <p style='margin-left: 15px;'>{symptoms}</p>
            </div>
            
            <div style='margin: 15px 0; padding: 10px; background-color: #f0fff0; border-radius: 5px;'>
                <h3 style='color: #333;'>Diagnosis:</h3>
                <p style='margin-left: 15px;'>{diagnosis}</p>
            </div>
            
            <div style='margin: 15px 0; padding: 10px; background-color: #fff7f0; border-radius: 5px;'>
                <h3 style='color: #333;'>Prescription:</h3>
                <p style='margin-left: 15px;'>{prescription}</p>
            </div>
        </div>
        """

        # Store plain text summary for returning with improved spacing
        # Add 'Medical Summary' header at the top
        self.plain_summary = (
            "Medical Summary\n"
            "Symptoms:\n"
            f"{symptoms}\n\n"
            "Diagnosis:\n"
            f"{diagnosis}\n\n"
            "Prescription:\n"
            f"{prescription}"
        )

        # Create a new popup window to display the summary
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle("Medical Summary Preview")
        preview_dialog.setMinimumSize(600, 500)
        
        preview_layout = QVBoxLayout(preview_dialog)
        
        # Add the summary to a QTextEdit with HTML
        summary_display = QTextEdit()
        summary_display.setReadOnly(True)
        summary_display.setHtml(summary)
        preview_layout.addWidget(summary_display)
        
        # Button layout for the preview dialog
        preview_buttons = QHBoxLayout()
        
        # Add to Chat button
        add_to_chat_button = QPushButton("Add to Chat")
        add_to_chat_button.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        add_to_chat_button.clicked.connect(lambda: [preview_dialog.accept(), self.accept()])
        preview_buttons.addWidget(add_to_chat_button)
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        cancel_button.clicked.connect(preview_dialog.reject)
        preview_buttons.addWidget(cancel_button)
        
        preview_layout.addLayout(preview_buttons)
        
        # Show the preview dialog
        if preview_dialog.exec_() == QDialog.Accepted:
            # User clicked "Add to Chat", so we already set self.accept() above
            # This will be handled by the calling code
            pass
        else:
            # User clicked "Cancel", do nothing
            pass

# --- Chat Bubble Widget ---
class ChatBubble(QLabel):
    def __init__(self, message, user_type="Patient", parent=None):
        super().__init__(parent)
        # Store original message for width calculations
        self.original_message = message
        
        # Use rich text for better rendering
        self.setTextFormat(Qt.RichText)
        
        # Check if this is a medical summary (contains "Symptoms:", "Diagnosis:", and "Prescription:")
        is_medical_summary = ("Symptoms:" in message and "Diagnosis:" in message and "Prescription:" in message)
        
        if is_medical_summary:
            # For medical summaries, preserve the exact formatting
            processed_message = message.replace("\n", "<br>")
            display_text = f"""
            <div style='white-space: pre-wrap; word-wrap: break-word; 
                      word-break: normal; line-height: 130%;
                      text-align: left; display: inline-block;'>
                {processed_message}
            </div>
            """
        else:
            # For normal messages, use the existing word-wrapping logic
            processed_message = ""
            for word in message.split():
                if processed_message:
                    processed_message += " "
                processed_message += word
            
            # Handle newlines
            processed_message = processed_message.replace("\n", "<br>")
            
            display_text = f"""
            <div style='white-space: normal; word-wrap: break-word; 
                      word-break: normal; line-height: 130%;
                      text-align: left; display: inline-block;'>
                {processed_message}
            </div>
            """
        
        # Set the processed text
        self.setText(display_text)
        
        # Set font
        self.setFont(QFont("Arial", 14))
        
        # Calculate width based on content
        fm = self.fontMetrics()
        
        # Make width truly dynamic based on content
        words = message.split()
        word_count = len(words)
        
        # Get screen dimensions for maximum bounds
        screen_width = QApplication.desktop().screenGeometry().width()
        max_available_width = min(screen_width * 0.8, 800)  # 80% of screen width up to 800px
        
        # For very short messages (1-3 words), fit exactly to content plus padding
        if word_count <= 3:
            # Get exact width needed for text + minimal padding
            text_width = fm.horizontalAdvance(message)
            padding = fm.averageCharWidth() * 2  # Add just 1 character worth on each side
            
            # Set extremely tight fit for short messages
            min_width = text_width + padding
            max_width = min_width * 1.1  # Just a tiny bit of flexibility
        
        # For medium-length messages (4-15 words)
        elif word_count <= 15:
            # Get width based on content
            text_width = fm.horizontalAdvance(message)
            
            # Use natural width with modest padding
            min_width = text_width * 0.9  # Allow slightly less than text width to enable wrapping
            max_width = min(text_width * 1.2, max_available_width * 0.6)  # Moderate max width
        
        # For longer messages
        else:
            # Get width based on a reasonable target line length
            avg_chars_per_word = sum(len(w) for w in words) / word_count
            ideal_chars_per_line = min(60, avg_chars_per_word * 8)  # Target ~8 words per line
            
            # Calculate width based on ideal line length
            min_width = fm.averageCharWidth() * ideal_chars_per_line
            
            # For very long messages, use more horizontal space
            if word_count > 30:
                max_width = max_available_width
            else:
                max_width = min(max_available_width * 0.75, fm.averageCharWidth() * ideal_chars_per_line * 1.5)
        
        # Allow minimums to be very small for short messages
        min_width = max(50, min_width)
        
        # Ensure max isn't smaller than min
        max_width = max(min_width * 1.1, max_width)
        
        # Set constraints with more flexibility for longer messages
        self.setMinimumWidth(int(min_width))
        self.setMaximumWidth(int(max_width))
        
        # Ensure content fits
        self.adjustSize()
        
        # Enable word wrap (works with rich text)
        self.setWordWrap(True)
        
        # Set styling based on user type
        if user_type == "Patient":
            bg_color = "#00c29d"  # Teal
            text_color = "white"
        else:  # Doctor
            bg_color = "#0084ff"  # Blue
            text_color = "white"
            
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: 15px;
                padding: 8px 10px;  /* Reduced padding */
                margin: 2px;
            }}
        """)
        
        # Set alignment based on user type
        alignment = Qt.AlignLeft if user_type == "Doctor" else Qt.AlignRight
        self.setAlignment(alignment)
        
        # Set size policy to make bubble adapt to content while respecting constraints
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

# --- Message Item Widget ---
class MessageItem(QWidget):
    def __init__(self, message, user_type="Patient", parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 5)
        self.layout.setSpacing(12)  # Increased spacing between elements
        
        # Set size policy to use available space
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        # Create avatar label with visible styling
        self.avatar = QLabel()
        
        # Load the respective image directly from the images folder
        # Always use the standard image path - no fallbacks
        image_path = f"images/{user_type.lower()}.png"
        
        # Create blank transparent pixmap for the result
        avatar_pixmap = QPixmap(50, 50)
        avatar_pixmap.fill(Qt.transparent)
        
        try:
            # Load the source image
            source_pixmap = QPixmap(image_path)
            
            # Create a painter to draw on the result
            painter = QPainter(avatar_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Create a circular mask
            painter.setPen(Qt.NoPen)
            painter.setBrush(Qt.white)
            painter.drawEllipse(0, 0, 50, 50)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            
            # Calculate centered crop of source image with zoom
            src_width = source_pixmap.width()
            src_height = source_pixmap.height()
            size = min(src_width, src_height)
            
            # Use original size instead of zooming
            zoom_factor = 1.0  # Use 100% of original size (no zoom)
            zoomed_size = int(size * zoom_factor)
            
            # Center crop to square with zoom effect
            src_x = (src_width - zoomed_size) // 2
            src_y = (src_height - zoomed_size) // 2
            
            # Draw the cropped and scaled source image
            target_rect = QRect(0, 0, 50, 50)
            source_rect = QRect(src_x, src_y, zoomed_size, zoomed_size)
            painter.drawPixmap(target_rect, source_pixmap, source_rect)
            painter.end()
        except Exception as e:
            print(f"Error loading avatar from {image_path}: {e}")
            
            # Use user type color as fallback if needed
            color = "#00c29d" if user_type == "Patient" else "#0084ff"
            
            # Draw a colored circle as a fallback
            painter = QPainter(avatar_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, 50, 50)
            
            # Add text (initial letter)
            painter.setPen(Qt.white)
            painter.setFont(QFont("Arial", 20, QFont.Bold))
            painter.drawText(avatar_pixmap.rect(), Qt.AlignCenter, user_type[0])
            painter.end()
            
        self.avatar.setPixmap(avatar_pixmap)
        self.avatar.setFixedSize(50, 50)
        self.avatar.setAlignment(Qt.AlignCenter)
        
        # No background or border - completely transparent avatar container
        self.avatar.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                border-radius: 25px;
                padding: 0px;
            }
        """)
        
        # Create message container with vertical layout
        self.message_container = QWidget()
        self.message_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setContentsMargins(0, 0, 0, 0)
        self.message_layout.setSpacing(2)
        self.message_layout.setSizeConstraint(QLayout.SetMinAndMaxSize)  # Makes layout resize to content
        
        # Add sender name if needed
        self.sender_label = QLabel(user_type)
        # Match label color to the bubble color
        label_color = "#00c29d" if user_type == "Patient" else "#0084ff"  # Match bubble colors
        self.sender_label.setStyleSheet(f"color: {label_color}; font-weight: bold; font-size: 12px;")
        self.message_layout.addWidget(self.sender_label)
        
        # Add message bubble
        self.bubble = ChatBubble(message, user_type)
        self.message_layout.addWidget(self.bubble)
        
        # Add timestamp
        time_str = QTime.currentTime().toString("hh:mm")
        self.time_label = QLabel(time_str)
        self.time_label.setStyleSheet("color: #888888; font-size: 10px;")
        self.time_label.setAlignment(Qt.AlignRight if user_type == "Doctor" else Qt.AlignLeft)
        self.message_layout.addWidget(self.time_label)
        
        # FIXED: Arrange components based on user type - Doctor on right, Patient on left
        if user_type == "Patient":  # Patient on the left
            self.layout.addWidget(self.avatar)
            self.layout.addWidget(self.message_container)
            self.layout.addStretch()
        else:  # Doctor on the right
            self.layout.addStretch()
            self.layout.addWidget(self.message_container)
            self.layout.addWidget(self.avatar)

class TranslationModule(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SalinSign Translation Module")
        self.setGeometry(0, 0, 1920, 1080)
        self.setMinimumSize(360, 640)  # Set minimum size for mobile compatibility

        # Preloading flag - if True, don't start video yet
        self.preloaded = False

        # Set white background for the main window
        self.setStyleSheet("background-color: white;")

        # Initialize messages list
        self.messages = []

        # Initialize display mode (True for text, False for sign language)
        self.text_mode = True
        
        # Initialize edit mode (True for manual sending, False for automatic)
        self.edit_mode = False

        # Default camera ID
        self.current_camera_id = 0

        # Camera switching lock to prevent race conditions
        self.camera_switching = False

        # No custom icons - always using patient.png and doctor.png from images folder

        # Detect available cameras
        self.available_cameras = get_available_cameras()

        # Setup UI
        self.setup_ui()

        # Load external stylesheet
        self.load_stylesheet()

        # Setup sign language recognition
        self.sign_language_thread = None

        # Add resize event handler
        self.resizeEvent = self.handle_resize

        # Initialize sign recognition timing variables
        self.last_recognized_sign = None
        self.sign_buffer = ""
        self.last_sign_time = 0
        self.sign_interval = 1500  # 1.5 seconds interval between signs
        self.current_sign = None
        self.sign_start_time = 0
        self.sign_hold_time = 700  # 0.7 seconds to hold a sign before sending
        self.accumulated_chars = ""  # Buffer to accumulate characters for wordninja

        # Setup video stream (will be properly initialized when the UI is shown)
        self.video_thread = None

        # Initialize translation timer
        self.translation_timer = QTimer()
        self.translation_timer.setSingleShot(True)
        self.translation_timer.timeout.connect(self.move_translation_to_chat)
        self.last_gesture_time = 0

        # Flag to track navigation state
        self._navigating = False

    def setup_ui(self):
        # Main central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setCentralWidget(self.scroll_area)

        # Scroll area widget
        self.scroll_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_widget)

        # Main vertical layout
        self.main_layout = QVBoxLayout(self.scroll_widget)
        self.main_layout.setContentsMargins(20, 5, 20, 20)
        self.main_layout.setSpacing(5)

        # Back Button Layout
        button_header = QHBoxLayout()
        button_header.setContentsMargins(0, 0, 0, 0)
        self.back_button = QLabel()
        self.back_button.setObjectName("backButton")
        self.back_button.setPixmap(QPixmap("images/backbutton.png").scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.back_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.back_button.mousePressEvent = self.go_back
        button_header.addWidget(self.back_button, alignment=Qt.AlignLeft)

        # Add stretch to push the tooltip button to the right
        button_header.addStretch()

        # Add tooltip button to the right
        self.tooltip_button = QLabel()
        self.tooltip_button.setObjectName("tooltipButton")
        self.tooltip_button.setPixmap(QPixmap("images/tooltip.png").scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.tooltip_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.tooltip_button.mousePressEvent = self.show_tooltip
        button_header.addWidget(self.tooltip_button, alignment=Qt.AlignRight)

        self.main_layout.addLayout(button_header)

        # Header Image Layout
        header_container = QHBoxLayout()
        header_container.setContentsMargins(0, 0, 0, 0)
        header_container.setSpacing(0)
        self.header_image = QLabel()
        self.header_image.setObjectName("headerImage")
        self.header_image.setPixmap(QPixmap("images/Translation.png").scaledToWidth(600, Qt.SmoothTransformation))
        self.header_image.setAlignment(Qt.AlignCenter)
        self.header_image.setStyleSheet("""
            QLabel {
                padding: 0px;
                margin: 0px;
            }
        """)
        header_container.addWidget(self.header_image, alignment=Qt.AlignCenter)
        self.main_layout.addLayout(header_container)

        # Add minimal spacing after the header
        self.main_layout.addSpacing(5)

        # Container Layout (for the two main boxes)
        self.container = QHBoxLayout()
        self.container.setSpacing(20)

        # Box 1 - Video Stream and Translation
        self.box1 = QFrame()
        self.box1.setObjectName("box1")
        self.box1_layout = QVBoxLayout(self.box1)
        self.box1_layout.setContentsMargins(20, 20, 20, 20)
        self.box1_layout.setSpacing(15)

        # Box 1 Header
        self.stream_header = QLabel()
        self.stream_header.setPixmap(QPixmap("images/Stream.png").scaledToWidth(300, Qt.SmoothTransformation))
        self.stream_header.setAlignment(Qt.AlignCenter)
        self.box1_layout.addWidget(self.stream_header)

        # Camera selection dropdown
        camera_selection_layout = QHBoxLayout()
        camera_selection_layout.setContentsMargins(0, 0, 0, 0)
        camera_selection_layout.setSpacing(10)

        camera_label = QLabel("Camera Source:")
        camera_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333;
            }
        """)
        camera_selection_layout.addWidget(camera_label)

        self.camera_dropdown = QComboBox()
        self.camera_dropdown.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: white;
                min-height: 25px;
                font-size: 14px;
            }
            QComboBox::drop-down {
                width: 20px;
                border-left: 1px solid #ccc;
            }
        """)

        # Add available cameras to dropdown
        for camera in self.available_cameras:
            self.camera_dropdown.addItem(camera["name"], camera["id"])

        # Connect dropdown change event
        self.camera_dropdown.currentIndexChanged.connect(self.camera_selected)
        camera_selection_layout.addWidget(self.camera_dropdown)

        self.box1_layout.addLayout(camera_selection_layout)

        # Video Stream Placeholder
        self.video_placeholder = QLabel("Loading Video Stream...")
        self.video_placeholder.setObjectName("videoPlaceholder")
        self.video_placeholder.setAlignment(Qt.AlignCenter)
        self.video_placeholder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.box1_layout.addWidget(self.video_placeholder)
        
        # Edit Mode Toggle
        edit_mode_layout = QHBoxLayout()
        edit_mode_layout.setContentsMargins(0, 0, 0, 0)
        
        self.edit_mode_toggle = QCheckBox("Edit Mode")
        self.edit_mode_toggle.setChecked(False)
        self.edit_mode_toggle.setCursor(QCursor(Qt.PointingHandCursor))
        self.edit_mode_toggle.stateChanged.connect(self.toggle_edit_mode)
        self.edit_mode_toggle.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                font-weight: bold;
                color: #333;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #f0f0f0;
                border: 2px solid #ccc;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border: 2px solid #45a049;
                border-radius: 3px;
            }
        """)
        
        edit_mode_label = QLabel("(Enable to edit translations before sending)")
        edit_mode_label.setStyleSheet("font-size: 12px; color: #666;")
        
        edit_mode_layout.addWidget(self.edit_mode_toggle)
        edit_mode_layout.addWidget(edit_mode_label)
        edit_mode_layout.addStretch()
        
        self.box1_layout.addLayout(edit_mode_layout)

        # Translation Box Container
        self.translation_container = QHBoxLayout()
        
        # Translation Text Box
        self.translation_box = QLineEdit()
        self.translation_box.setReadOnly(True)  # Initially read-only
        self.translation_box.setObjectName("translationBox")
        self.translation_box.setPlaceholderText("Translations will appear here...")
        self.translation_box.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                min-height: 40px;
            }
        """)
        self.translation_container.addWidget(self.translation_box)
        
        # Send Button for Edit Mode (initially hidden)
        self.translation_send_button = QPushButton("Send")
        self.translation_send_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.translation_send_button.clicked.connect(self.send_translation)
        self.translation_send_button.setStyleSheet("""
            QPushButton {
                padding: 10px 15px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.translation_send_button.hide()  # Initially hidden
        self.translation_container.addWidget(self.translation_send_button)
        
        self.box1_layout.addLayout(self.translation_container)

        # Add Box 1 to container
        self.container.addWidget(self.box1)

        # Box 2 - Chat and Sign Language Display
        self.box2 = QFrame()
        self.box2.setObjectName("box2")
        self.box2_layout = QVBoxLayout(self.box2)
        self.box2_layout.setContentsMargins(20, 20, 20, 20)
        self.box2_layout.setSpacing(15)

        # Box 2 Header
        self.chat_header = QLabel()
        self.chat_header.setPixmap(QPixmap("images/Chatbox.png").scaledToWidth(200, Qt.SmoothTransformation))
        self.chat_header.setAlignment(Qt.AlignCenter)
        self.box2_layout.addWidget(self.chat_header)

        # Chat Box - Replace QTextEdit with a scrollable widget container
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setSpacing(5)  # Reduced default spacing
        self.chat_layout.setContentsMargins(5, 10, 5, 10)  # Add some padding
        self.chat_layout.addStretch()  # Push messages to the top
        
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setWidget(self.chat_container)
        self.chat_scroll.setObjectName("chatBox")
        self.chat_scroll.setStyleSheet("""
            QScrollArea {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                min-height: 300px;
            }
            QScrollBar:vertical {
                border: none;
                background: #f1f1f1;
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #888;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #555;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        self.box2_layout.addWidget(self.chat_scroll)
        
        # Sign Language Display Area
        self.sign_display_scroll = QScrollArea()
        self.sign_display_scroll.setWidgetResizable(True)
        self.sign_display_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sign_display_scroll.setStyleSheet("""
            QScrollArea {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            QScrollBar:vertical {
                border: none;
                background: #f1f1f1;
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #888;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #555;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        self.sign_display = QWidget()
        self.sign_display.setObjectName("signDisplay")
        self.sign_display.setStyleSheet("""
            QWidget {
                background-color: white;
                padding: 5px;
            }
        """)
        self.sign_display_layout = QVBoxLayout(self.sign_display)
        self.sign_display_layout.setSpacing(5)
        self.sign_display_layout.setContentsMargins(5, 5, 5, 5)

        self.sign_display_scroll.setWidget(self.sign_display)
        self.sign_display_scroll.setMinimumHeight(250)
        self.sign_display_scroll.hide()  # Hide sign display by default
        self.box2_layout.addWidget(self.sign_display_scroll)

        # Add predefined phrases for doctor
        predefined_phrases_layout = QVBoxLayout()
        predefined_phrases_layout.setContentsMargins(0, 0, 0, 5)
        predefined_phrases_layout.setSpacing(5)

        # Create a flow layout for phrase buttons
        phrases_container = QWidget()
        phrases_container.setObjectName("phrasesContainer")
        phrases_flow_layout = QHBoxLayout(phrases_container)
        phrases_flow_layout.setSpacing(8)
        # Increase vertical margins to add space above and below buttons
        phrases_flow_layout.setContentsMargins(0, 8, 0, 8)

        # List of predefined phrases
        phrases = [
            "Where does it hurt?",
            "How long have you felt this?",
            "I'll check your vital signs now.",
            "You need medicine — I'll give you instructions.",
            "Any questions before we finish?"
        ]

        # Create and add buttons for each phrase
        for phrase in phrases:
            button = QPushButton(phrase)
            button.setStyleSheet("""
                QPushButton {
                    padding: 8px 12px;
                    background-color: #e8f5ff;
                    color: #2a70a5;
                    border: none;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: 500;
                    min-height: 24px;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: #cce7ff;
                    color: #0058a5;
                }
            """)
            button.setCursor(QCursor(Qt.PointingHandCursor))
            # Connect button click to send the phrase as a doctor message
            button.clicked.connect(lambda checked=False, text=phrase: self.send_message("Doctor", text))
            phrases_flow_layout.addWidget(button)

        # Add horizontal scroll area that takes minimal space
        phrases_scroll = QScrollArea()
        phrases_scroll.setWidgetResizable(True)
        phrases_scroll.setWidget(phrases_container)
        phrases_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        phrases_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Increase scroll area height to provide more space
        phrases_scroll.setMaximumHeight(60)
        phrases_scroll.setMinimumHeight(60)
        phrases_scroll.setStyleSheet("""
            QScrollArea {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 10px;
                padding: 0px;
            }
            QScrollBar:horizontal {
                height: 6px;
                background: transparent;
                margin: 0px 0px 0px 0px;
                border-radius: 3px;
            }
            QScrollBar::handle:horizontal {
                background-color: rgba(128, 128, 128, 0.2);
                min-width: 40px;
                border-radius: 3px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: rgba(128, 128, 128, 0.5);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: transparent;
                width: 0px;
                height: 0px;
            }
        """)

        # Set styling for the phrases container too
        phrases_container.setStyleSheet("""
            QWidget#phrasesContainer {
                background-color: #f5f5f5;
                border-radius: 9px; /* 1px less than scroll area to fit nicely */
            }
        """)

        # Increase container height to match the new spacing
        phrases_container.setMaximumHeight(60)

        predefined_phrases_layout.addWidget(phrases_scroll)
        self.box2_layout.addLayout(predefined_phrases_layout)

        # Input Container for User 2 (Doctor)
        self.input_container2 = QHBoxLayout()
        self.input_user2 = QLineEdit()
        self.input_user2.setPlaceholderText("Doctor Type here...")
        self.input_user2.returnPressed.connect(lambda: self.send_message("Doctor", self.input_user2.text()))
        
        # Add predictive text functionality with QCompleter
        self.setup_predictive_text()

        self.send_button2 = QPushButton("Send")
        self.send_button2.setCursor(QCursor(Qt.PointingHandCursor))
        self.send_button2.clicked.connect(lambda: self.send_message("Doctor", self.input_user2.text()))

        # Add display mode toggle
        self.display_mode_toggle = QCheckBox("Text Mode")
        self.display_mode_toggle.setChecked(True)  # Set Text Mode as default
        self.display_mode_toggle.setCursor(QCursor(Qt.PointingHandCursor))
        self.display_mode_toggle.stateChanged.connect(self.toggle_display_mode)
        self.display_mode_toggle.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                font-weight: bold;
                color: #333;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #f0f0f0;
                border: 2px solid #ccc;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border: 2px solid #45a049;
                border-radius: 3px;
            }
        """)

        # Add medical summary template button
        self.medical_summary_button = QPushButton("Medical Summary")
        self.medical_summary_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.medical_summary_button.clicked.connect(self.show_medical_summary_template)
        self.medical_summary_button.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)

        # Add clear chat button
        self.clear_chat_button = QPushButton("Clear Chat")
        self.clear_chat_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.clear_chat_button.clicked.connect(self.clear_chat)
        self.clear_chat_button.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #ff4444;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #ff6666;
            }
        """)

        self.input_container2.addWidget(self.input_user2)
        self.input_container2.addWidget(self.send_button2)
        self.input_container2.addWidget(self.display_mode_toggle)
        self.input_container2.addWidget(self.medical_summary_button)
        self.input_container2.addWidget(self.clear_chat_button)
        self.box2_layout.addLayout(self.input_container2)

        # Add Box 2 to container
        self.container.addWidget(self.box2)

        # Add container to main layout
        self.main_layout.addLayout(self.container)
        
    def setup_predictive_text(self):
        """Set up predictive text for the doctor's input field"""
        # List of common phrases for suggestions
        phrases = [
            "How are you feeling today?",
            "Do you have any allergies?",
            "Are you currently taking any medications?",
            "Stay hydrated and get enough rest",
            "Contact me if your symptoms worsen",
            "Was this a problem before?",
            "Let me know if you feel dizzy or nauseous.",
            "I'm going to prescribe something to help.",
            "Make sure to take your medication on time.",
            "Very important to monitor your progress closely."
        ]
        
        # Create and configure the completer
        self.completer = QCompleter(phrases)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setFilterMode(Qt.MatchStartsWith)
        
        # Set the completer for the input field
        self.input_user2.setCompleter(self.completer)
        
        # Set up an event filter to capture Tab key for completion
        self.input_user2.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Custom event filter to handle Tab key for text completion"""
        if obj == self.input_user2 and event.type() == event.KeyPress:
            # Check if Tab key is pressed and completer has an active completion
            if event.key() == Qt.Key_Tab and self.completer.popup() and self.completer.popup().isVisible():
                # Manually trigger the current completion
                self.completer.activated.emit(self.completer.currentCompletion())
                return True
        
        # Let other events pass through
        return super().eventFilter(obj, event)
    
    def toggle_edit_mode(self, state):
        """Toggle between automatic and manual translation sending modes"""
        self.edit_mode = bool(state)
        
        if self.edit_mode:
            # Edit mode enabled - make translation box editable and show send button
            self.translation_box.setReadOnly(False)
            self.translation_box.setStyleSheet("""
                QLineEdit {
                    background-color: white;
                    border: 1px solid #4CAF50;
                    border-radius: 5px;
                    padding: 10px;
                    font-size: 14px;
                    min-height: 40px;
                }
            """)
            self.translation_send_button.show()
            
            # Stop automatic timer if it's running
            if self.translation_timer.isActive():
                self.translation_timer.stop()
        else:
            # Edit mode disabled - make translation box read-only and hide send button
            self.translation_box.setReadOnly(True)
            self.translation_box.setStyleSheet("""
                QLineEdit {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 10px;
                    font-size: 14px;
                    min-height: 40px;
                }
            """)
            self.translation_send_button.hide()
    
    def send_translation(self):
        """Send the current translation to the chat"""
        translation_text = self.translation_box.text()
        if translation_text:
            # Add the translation as a message from the Patient
            self.send_message("Patient", translation_text)
            # Clear the translation box and accumulated characters
            self.translation_box.clear()
            self.accumulated_chars = ""
            # Clear the sign language display
            self.clear_sign_display()
        
    def handle_resize(self, event):
        width = event.size().width()
        height = event.size().height()

        # Maintain original layout at 1920x1080
        if width >= 1920 and height >= 1080:
            self.container.setDirection(QHBoxLayout.LeftToRight)
            self.box1.setMinimumWidth(0)
            self.box2.setMinimumWidth(0)
            return

        # Switch to vertical layout for mobile screens
        if width < 768:
            self.container.setDirection(QVBoxLayout.TopToBottom)
            # Set minimum widths to prevent squishing
            self.box1.setMinimumWidth(width - 40)  # Account for margins
            self.box2.setMinimumWidth(width - 40)
            # Adjust margins for mobile
            self.main_layout.setContentsMargins(10, 10, 10, 10)
            self.box1_layout.setContentsMargins(10, 10, 10, 10)
            self.box2_layout.setContentsMargins(10, 10, 10, 10)
        else:
            self.container.setDirection(QHBoxLayout.LeftToRight)
            self.box1.setMinimumWidth(0)
            self.box2.setMinimumWidth(0)
            # Restore original margins
            self.main_layout.setContentsMargins(20, 20, 20, 20)
            self.box1_layout.setContentsMargins(20, 20, 20, 20)
            self.box2_layout.setContentsMargins(20, 20, 20, 20)

        # Scale images based on screen width
        scale_factor = min(width / 1920, 1.0)
        # Reduce the logo size by using a smaller scale factor
        logo_scale_factor = scale_factor * 0.6  # 60% of the original size
        self.header_image.setPixmap(QPixmap("images/Translation.png").scaledToWidth(int(600 * logo_scale_factor), Qt.SmoothTransformation))
        self.stream_header.setPixmap(QPixmap("images/Stream.png").scaledToWidth(int(300 * scale_factor), Qt.SmoothTransformation))
        self.chat_header.setPixmap(QPixmap("images/Chatbox.png").scaledToWidth(int(235 * scale_factor), Qt.SmoothTransformation))

        # Update font sizes
        font_size = max(12, int(14 * scale_factor))
        self.input_user2.setStyleSheet(f"font-size: {font_size}px;")
        
        # Update the chat scroll area style
        self.chat_scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                min-height: 300px;
                font-size: {font_size}px;
            }}
            QScrollBar:vertical {{
                border: none;
                background: #f1f1f1;
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: #888;
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #555;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)

        # Update button sizes
        button_width = max(80, int(100 * scale_factor))
        self.send_button2.setMinimumWidth(button_width)

        # Update video placeholder size
        if width < 768:
            video_height = int(width * 0.75)  # 4:3 aspect ratio
        else:
            video_height = int(height * 0.4)
        self.video_placeholder.setMinimumHeight(video_height)

        # Update chat box size
        if width < 768:
            chat_height = int(height * 0.4)
        else:
            chat_height = int(height * 0.4)
        self.chat_scroll.setMinimumHeight(chat_height)

        # Update sign display size if visible
        if not self.text_mode:
            self.sign_display.setMinimumWidth(self.box2.width() - 50)
            # Force layout update
            self.update_sign_display_for_all_messages()

    def load_stylesheet(self):
        """Load the external stylesheet"""
        style_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "translation_style.qss")

        if os.path.exists(style_path):
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())
        else:
            print(f"Warning: Could not find stylesheet at {style_path}")
            # Fall back to basic styling
            self.apply_basic_styles()

    def apply_basic_styles(self):
        """Apply basic styling if the stylesheet file is not found"""
        style = """
        QWidget {
            font-family: Arial, sans-serif;
        }
        
        #box1, #box2 {
            background-color: #f5f5f5;
            border-radius: 10px;
            border: 1px solid #ddd;
        }
        
        QLineEdit {
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 14px;
        }
        
        QPushButton {
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 14px;
            font-weight: bold;
        }
        
        #videoPlaceholder {
            background-color: #000;
            color: #fff;
            min-height: 300px;
        }
        
        #chatBox {
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
            font-size: 14px;
        }
        """

        self.setStyleSheet(style)

    def convert_text_to_sign(self, text):
        """Convert text to sign language images"""
        sign_images = []
        base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "signimages")
        print(f"Base path for sign images: {base_path}")  # Debug print

        for char in text.upper():
            if char.isalpha() or char.isdigit():
                # Check if image exists in signimages directory
                image_path = os.path.join(base_path, f"{char}.png")
                print(f"Checking image path: {image_path}")  # Debug print
                if os.path.exists(image_path):
                    print(f"Found image for {char}")  # Debug print
                    sign_images.append(image_path)
                else:
                    print(f"Image not found for {char}")  # Debug print

        print(f"Total images found: {len(sign_images)}")  # Debug print
        return sign_images

    def clear_sign_display(self):
        """Clear the sign language display area"""
        # Clear all existing rows
        while self.sign_display_layout.count():
            item = self.sign_display_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Clear the layout's items
                while item.layout().count():
                    sub_item = item.layout().takeAt(0)
                    if sub_item.widget():
                        sub_item.widget().deleteLater()
                # Delete the layout
                QWidget().setLayout(item.layout())

    def display_sign_images(self, image_paths):
        """Display sign language images in the sign display area"""
        if not image_paths:
            print("No images to display")
            self.clear_sign_display()
            return

        print(f"Displaying {len(image_paths)} images")

        # Clear existing display first
        self.clear_sign_display()

        # Available width for images in a row
        max_row_width = self.sign_display.width() - 30  # Account for margins
        default_image_size = 120  # Default image size
        min_image_size = 50  # Minimum size we'll reduce to

        # Group images by word (each word is followed by None)
        words = []
        current_word = []

        for img_path in image_paths:
            if img_path is None:  # Word boundary
                if current_word:  # Only add non-empty words
                    words.append(current_word)
                    current_word = []
            else:
                current_word.append(img_path)

        # Add the last word if there is one
        if current_word:
            words.append(current_word)

        current_row_layout = QHBoxLayout()
        current_row_layout.setSpacing(5)
        current_row_layout.setContentsMargins(0, 0, 0, 0)
        current_row_layout.setAlignment(Qt.AlignLeft)
        current_row_width = 0

        # Process each word
        for word_images in words:
            # Check if this word would fit at default size
            word_width = len(word_images) * (default_image_size + 5) - 5  # Account for spacing

            # If word doesn't fit at default size, calculate a smaller size
            image_size = default_image_size
            if word_width > max_row_width:
                # Calculate new size that will make the word fit
                image_size = max(min_image_size, int((max_row_width - (len(word_images) - 1) * 5) / len(word_images)))
                print(f"Reducing image size to {image_size} for word of length {len(word_images)}")

            # Check if we need to start a new row for this word
            word_scaled_width = len(word_images) * (image_size + 5) - 5
            if current_row_width + word_scaled_width > max_row_width and current_row_layout.count() > 0:
                # Add current row and start a new one
                self.sign_display_layout.addLayout(current_row_layout)
                current_row_layout = QHBoxLayout()
                current_row_layout.setSpacing(5)
                current_row_layout.setContentsMargins(0, 0, 0, 0)
                current_row_layout.setAlignment(Qt.AlignLeft)
                current_row_width = 0

            # Add all images for this word
            for img_path in word_images:
                image_label = QLabel()
                pixmap = QPixmap(img_path)
                if pixmap.isNull():
                    print(f"Failed to load image: {img_path}")
                    continue

                # Scale the image to the calculated size
                scaled_pixmap = pixmap.scaled(image_size, image_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                image_label.setPixmap(scaled_pixmap)
                image_label.setAlignment(Qt.AlignCenter)
                image_label.setFixedSize(image_size, image_size)
                current_row_layout.addWidget(image_label)
                current_row_width += image_size + 5

            # Add space after each word (if not the last word)
            spacer = QLabel()
            spacer.setFixedSize(10, image_size)  # Smaller visual space between words
            current_row_layout.addWidget(spacer)
            current_row_width += 10

        # Add the last row if it has any images
        if current_row_layout.count() > 0:
            self.sign_display_layout.addLayout(current_row_layout)

        # Add stretch at the bottom to push content to the top
        self.sign_display_layout.addStretch()

    def toggle_display_mode(self, state):
        """Toggle between text and sign language display modes"""
        self.text_mode = bool(state)
        self.display_mode_toggle.setText("Text Mode" if self.text_mode else "Sign Mode")

        # Update the display based on the current mode
        if self.text_mode:
            # Show text messages and hide sign language
            self.chat_scroll.show()
            self.sign_display_scroll.hide()
            self.refresh_chat_widgets()
        else:
            # Hide text messages and show sign language
            self.chat_scroll.hide()
            self.sign_display_scroll.show()
            
            # Ensure the sign display has its layout updated before showing
            self.sign_display_scroll.setWidgetResizable(True)
            self.sign_display.setMinimumWidth(self.box2.width() - 50)  # Allow enough width for the signs
            
            # Clear and update sign language display for all messages
            self.update_sign_display_for_all_messages()
    
    def refresh_chat_widgets(self):
        """Recreate all message widgets from messages list"""
        # Clear existing widgets from chat layout
        while self.chat_layout.count() > 1:  # Keep the stretch item at the end
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add all messages back as widgets
        for msg in self.messages:
            self.add_message_widget(msg["user"], msg["text"])
        
        # Scroll to bottom
        QTimer.singleShot(100, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        ))
    
    def update_sign_display_for_all_messages(self):
        """Update sign language display for all messages"""
        self.clear_sign_display()

        # Get all messages from the doctor
        doctor_messages = [msg["text"] for msg in self.messages if msg["user"] == "Doctor"]

        if doctor_messages:
            # Convert all messages to sign language
            all_sign_images = []
            for message in doctor_messages:
                # Split message into words
                words = message.split()
                for word in words:
                    sign_images = self.convert_text_to_sign(word)
                    all_sign_images.extend(sign_images)
                    all_sign_images.append(None)  # Add word boundary marker

            # Ensure sign display has correct size before displaying images
            self.sign_display.updateGeometry()
            QApplication.processEvents()

            # Display all sign images
            self.display_sign_images(all_sign_images)
    
    def clear_chat(self):
        """Clear all chat messages and sign language display"""
        # Clear messages list
        self.messages = []
        
        # Clear chat widgets
        while self.chat_layout.count() > 1:  # Keep the stretch item at the end
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Clear sign language display
        self.clear_sign_display()
        
        # Clear translation box and accumulated characters
        self.translation_box.clear()
        self.accumulated_chars = ""
    
    def send_message(self, user, message):
        if not message.strip():
            return
        
        # Add message to list
        self.messages.append({"user": user, "text": message})
        
        if self.text_mode:
            # In text mode, add the message widget to the chat
            self.add_message_widget(user, message)
            
            # Scroll to the bottom
            QTimer.singleShot(100, lambda: self.chat_scroll.verticalScrollBar().setValue(
                self.chat_scroll.verticalScrollBar().maximum()
            ))
            
        if user == "Doctor":
            if not self.text_mode:
                # In sign mode, only show the latest message
                self.clear_sign_display()
                # Split message into words
                words = message.split()
                all_sign_images = []
                for word in words:
                    sign_images = self.convert_text_to_sign(word)
                    all_sign_images.extend(sign_images)
                    all_sign_images.append(None)  # Add word boundary marker
                self.display_sign_images(all_sign_images)
            self.input_user2.clear()
    
    def add_message_widget(self, user, message):
        """Add a message widget to the chat layout"""
        # Check if we should show sender name
        show_sender = True
        if len(self.messages) > 1:
            # Check if the previous message was from the same sender
            if self.messages[-2]["user"] == user:
                show_sender = False
        
        # Create message item (ignoring custom icons - always using standard images)
        message_item = MessageItem(message, user, self.chat_container)
        
        # Hide sender label if not needed
        if not show_sender:
            message_item.sender_label.hide()
        
        # Add spacing widget if this is a new sender (different from previous)
        if len(self.messages) > 1 and self.messages[-2]["user"] != user:
            spacer = QWidget()
            spacer.setFixedHeight(15)  # 15px spacing between different senders
            self.chat_layout.insertWidget(self.chat_layout.count() - 1, spacer)
        
        # Force layout update to ensure proper sizing
        message_item.bubble.adjustSize()
        message_item.updateGeometry()
        
        # Insert before the stretch at the end
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, message_item)
        
        # Process events to ensure sizing takes effect
        QApplication.processEvents()
    
    def go_back(self, event):
        """Return to the main menu when the back button is clicked"""
        try:
            # Set a flag to prevent re-entering this method
            if hasattr(self, '_navigating') and self._navigating:
                print("Navigation already in progress, ignoring request")
                return
            self._navigating = True

            print("Starting navigation back to main menu...")

            # First, make sure all timers are stopped
            try:
                if hasattr(self, 'translation_timer') and self.translation_timer.isActive():
                    self.translation_timer.stop()
            except Exception as e:
                print(f"Error stopping timers: {e}")

            # Disconnect signals to prevent any callback issues
            try:
                if self.sign_language_thread is not None:
                    self.sign_language_thread.update_frame.disconnect()
                    self.sign_language_thread.update_text.disconnect()
            except Exception as e:
                print(f"Error disconnecting signals: {e}")

            # Stop the sign language thread
            try:
                print("Stopping sign language thread...")
                if self.sign_language_thread is not None:
                    self.sign_language_thread.running = False
                    self.sign_language_thread.stop()
                    # Give it a reasonable time to stop
                    for i in range(10):  # Try for about 1 second
                        if not self.sign_language_thread.isRunning():
                            break
                        self.msleep(100)

                    # If it's still running, terminate it
                    if self.sign_language_thread.isRunning():
                        print("Forcing thread termination...")
                        self.sign_language_thread.terminate()
                    self.sign_language_thread = None
            except Exception as e:
                print(f"Error stopping sign language thread: {e}")

            # Stop the video thread if it exists
            try:
                print("Stopping video thread...")
                if self.video_thread is not None:
                    self.video_thread.running = False
                    self.video_thread.stop()
                    # Give it a reasonable time to stop
                    for i in range(10):  # Try for about 1 second
                        if not self.video_thread.isRunning():
                            break
                        self.msleep(100)

                    # If it's still running, terminate it
                    if self.video_thread.isRunning():
                        print("Forcing video thread termination...")
                        self.video_thread.terminate()
                    self.video_thread = None
            except Exception as e:
                print(f"Error stopping video thread: {e}")

            # Clear data and run garbage collection
            try:
                self.clear_chat()
                # Force garbage collection
                gc.collect()
            except Exception as e:
                print(f"Error clearing data: {e}")

            # Set variables to None to help garbage collection
            try:
                self.sign_language_thread = None
                self.video_thread = None
            except Exception as e:
                print(f"Error nullifying thread references: {e}")

            # Import MainMenu ahead of time to make sure it's ready
            try:
                from MainMenu import Ui_MainWindow
                print("MainMenu imported successfully")
            except Exception as e:
                print(f"Error importing MainMenu: {e}")

            # Create a new MainWindow instance before closing this one
            try:
                main_window = QMainWindow()
                ui = Ui_MainWindow()
                ui.setupUi(main_window)
            except Exception as e:
                print(f"Error creating main menu: {e}")

            # Close current window and show main menu
            try:
                print("Showing main menu...")
                main_window.showFullScreen()
                print("Closing translation module...")
                self.close()
            except Exception as e:
                print(f"Error showing main menu: {e}")
                # Try simpler approach
                self.close()

        except Exception as e:
            print(f"Critical error in go_back: {e}")
            self._navigating = False
            # Last resort - just try to close
            try:
                self.close()
            except:
                pass

    def msleep(self, msecs):
        """Helper method to sleep for milliseconds without blocking UI"""
        deadline = QTime.currentTime().addMSecs(msecs)
        while QTime.currentTime() < deadline:
            QApplication.processEvents(QApplication.ExclusiveUserInputEvents)

    def update_video_frame(self, image):
        """Update the video placeholder with a new frame"""
        scaled_image = image.scaled(self.video_placeholder.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_placeholder.setPixmap(QPixmap.fromImage(scaled_image))

    def setup_video_stream(self):
        """Set up the sign language recognition and video streaming"""
        self.sign_language_thread = SignLanguageThread(self.current_camera_id)
        self.sign_language_thread.update_frame.connect(self.update_video_frame)
        self.sign_language_thread.update_text.connect(self.handle_recognized_sign)
        self.sign_language_thread.start()

    def handle_recognized_sign(self, sign):
        """Handle recognized sign language gestures with timing control and word segmentation"""
        current_time = QTime.currentTime().msecsSinceStartOfDay()

        # Update last gesture time
        self.last_gesture_time = current_time

        # If this is a new sign, start tracking it
        if sign != self.current_sign:
            self.current_sign = sign
            self.sign_start_time = current_time
            return

        # If we're still holding the same sign
        if sign == self.current_sign:
            # Check if we've held the sign long enough
            if current_time - self.sign_start_time >= self.sign_hold_time:
                # Check if enough time has passed since the last sent sign
                if current_time - self.last_sign_time >= self.sign_interval:
                    # Update the accumulated characters
                    self.accumulated_chars += sign
                    
                    # Apply word segmentation to the accumulated characters
                    segmented_text = self.apply_word_segmentation(self.accumulated_chars)
                    
                    # Update the translation box with the segmented text
                    self.translation_box.setText(segmented_text)
                    
                    # Update timing variables
                    self.last_sign_time = current_time
                    self.last_recognized_sign = sign

                    # Only start the translation timer if not in edit mode
                    if not self.edit_mode:
                        self.translation_timer.start(5000)  # 5 seconds before moving to chat

    def apply_word_segmentation(self, text):
        """Apply word segmentation with intelligent capitalization handling"""
        if not text:
            return ""
            
        # Preserve existing capitalization patterns before segmentation
        is_all_caps = text.isupper() and len(text) > 1
        is_first_cap = text[0].isupper()
        
        # Track potential acronyms (consecutive uppercase letters)
        acronyms = []
        current_acronym = ""
        
        for char in text:
            if char.isupper() and char.isalpha():
                current_acronym += char
            elif current_acronym:
                if len(current_acronym) > 1:  # Consider it an acronym if more than one uppercase letter
                    acronyms.append(current_acronym)
                current_acronym = ""
                
        # Add the last acronym if there is one
        if current_acronym and len(current_acronym) > 1:
            acronyms.append(current_acronym)
            
        # Split the text into words using wordninja
        segmented_words = wordninja.split(text.lower())
        
        # Apply capitalization rules
        result = []
        sentence_start = True
        
        for word in segmented_words:
            # Check if this word matches any of our acronyms
            is_acronym = False
            for acronym in acronyms:
                if word.lower() == acronym.lower():
                    result.append(acronym)
                    is_acronym = True
                    break
            
            if is_acronym:
                sentence_start = False
                continue
                
            # Apply sentence-start capitalization
            if sentence_start:
                word = word.capitalize()
                sentence_start = False
            
            # Add the word to the result
            result.append(word)
            
            # Check if this might be the end of a sentence
            if word.endswith(('.', '!', '?')):
                sentence_start = True
        
        # For single-letter words that might be 'I', capitalize them
        for i in range(len(result)):
            if result[i] == 'i':
                result[i] = 'I'
                
        # If the original text was all caps, convert back
        if is_all_caps:
            result = [word.upper() for word in result]
        
        # Join the words with spaces
        return ' '.join(result)

    def move_translation_to_chat(self):
        """Move the translation text to the chat box and clear the translation box
        This is called automatically when not in edit mode"""
        # Only proceed if not in edit mode
        if not self.edit_mode:
            translation_text = self.translation_box.text()
            if translation_text:
                # Add the translation as a message from the Patient
                self.send_message("Patient", translation_text)
                # Clear the translation box and accumulated characters
                self.translation_box.clear()
                self.accumulated_chars = ""
                # Clear the sign language display
                self.clear_sign_display()

    def showEvent(self, event):
        """Start video streaming when the window is shown"""
        super().showEvent(event)

        # Only start video stream if not preloaded
        if not self.preloaded:
            # Use a small delay to let the UI render first
            QTimer.singleShot(100, self.setup_video_stream)

            # Show a loading message while camera initializes
            self.video_placeholder.setText("Initializing camera...")
            self.video_placeholder.setStyleSheet("""
                QLabel {
                    background-color: #000;
                    color: #fff;
                    font-size: 18px;
                    qproperty-alignment: AlignCenter;
                }
            """)

            # Update UI immediately
            QApplication.processEvents()

    def closeEvent(self, event):
        """Clean up resources when closing the window"""
        print("Translation module closeEvent triggered")
        try:
            # Disconnect all signals first to prevent callbacks during cleanup
            try:
                if self.sign_language_thread is not None:
                    self.sign_language_thread.update_frame.disconnect()
                    self.sign_language_thread.update_text.disconnect()
            except Exception as e:
                print(f"Error disconnecting signals: {e}")

            # Stop all timers
            try:
                if hasattr(self, 'translation_timer') and self.translation_timer.isActive():
                    self.translation_timer.stop()
            except Exception as e:
                print(f"Error stopping timers: {e}")

            # Stop the sign language thread
            try:
                if self.sign_language_thread is not None:
                    self.sign_language_thread.running = False
                    self.sign_language_thread.stop()
                    # Controlled wait with timeout
                    for i in range(10):  # Try for about 1 second
                        if not self.sign_language_thread.isRunning():
                            break
                        self.msleep(100)

                    # If it's still running, terminate it
                    if self.sign_language_thread.isRunning():
                        print("Forcing sign language thread termination")
                        self.sign_language_thread.terminate()
                    # Set to None to help garbage collection
                    self.sign_language_thread = None
            except Exception as e:
                print(f"Error stopping sign language thread: {e}")

            # Stop the video thread
            try:
                if self.video_thread is not None:
                    self.video_thread.running = False
                    self.video_thread.stop()
                    # Controlled wait with timeout
                    for i in range(10):  # Try for about 1 second
                        if not self.video_thread.isRunning():
                            break
                        self.msleep(100)

                    # If it's still running, terminate it
                    if self.video_thread.isRunning():
                        print("Forcing video thread termination")
                        self.video_thread.terminate()
                    # Set to None to help garbage collection
                    self.video_thread = None
            except Exception as e:
                print(f"Error stopping video thread: {e}")

            # Clear data structures
            try:
                # Clear messages and free resources
                self.messages = []

                # Clear widgets if possible
                if hasattr(self, 'chat_box'):
                    self.chat_box.clear()
                if hasattr(self, 'translation_box'):
                    self.translation_box.clear()
                if hasattr(self, 'sign_display_layout'):
                    self.clear_sign_display()
            except Exception as e:
                print(f"Error clearing data structures: {e}")

            # Remove any remaining references
            try:
                # Delete remaining references
                self.sign_language_thread = None
                self.video_thread = None
            except Exception as e:
                print(f"Error removing references: {e}")

            # Force garbage collection
            try:
                gc.collect()
            except Exception as e:
                print(f"Error during garbage collection: {e}")

            print("Translation module cleanup completed")
        except Exception as e:
            print(f"Error during closeEvent cleanup: {e}")

        # Always accept the close event
        event.accept()

    def hideEvent(self, event):
        """Handle window hide event with proper cleanup"""
        print("Translation module hideEvent triggered")
        try:
            # Check if we're in the middle of navigating back
            if hasattr(self, '_navigating') and self._navigating:
                print("Already navigating, skipping duplicate cleanup")
                super().hideEvent(event)
                return

            # Disconnect signals to prevent callbacks during cleanup
            try:
                if self.sign_language_thread is not None:
                    try:
                        self.sign_language_thread.update_frame.disconnect()
                        self.sign_language_thread.update_text.disconnect()
                    except:
                        # It's okay if signals are already disconnected
                        pass
            except Exception as e:
                print(f"Error disconnecting signals during hide: {e}")

            # Stop all timers
            try:
                if hasattr(self, 'translation_timer') and self.translation_timer.isActive():
                    self.translation_timer.stop()
            except Exception as e:
                print(f"Error stopping timers during hide: {e}")

            # Stop the sign language thread
            try:
                if self.sign_language_thread is not None:
                    self.sign_language_thread.running = False
                    self.sign_language_thread.stop()
                    # Controlled wait with timeout
                    for i in range(5):  # Try for about 0.5 seconds
                        if not self.sign_language_thread.isRunning():
                            break
                        self.msleep(100)
                    # If it's still running, we'll let it be handled by closeEvent later
                    self.sign_language_thread = None
            except Exception as e:
                print(f"Error stopping sign language thread during hide: {e}")

            # Stop the video thread
            try:
                if self.video_thread is not None:
                    self.video_thread.running = False
                    self.video_thread.stop()
                    # Controlled wait with timeout
                    for i in range(5):  # Try for about 0.5 seconds
                        if not self.video_thread.isRunning():
                            break
                        self.msleep(100)
                    # If it's still running, we'll let it be handled by closeEvent later
                    self.video_thread = None
            except Exception as e:
                print(f"Error stopping video thread during hide: {e}")

            # Force garbage collection
            try:
                gc.collect()
            except Exception as e:
                print(f"Error during garbage collection in hide: {e}")

            print("Translation module hide cleanup completed")
        except Exception as e:
            print(f"Error during hideEvent cleanup: {e}")

        # Always call parent's hideEvent
        super().hideEvent(event)

    def show_tooltip(self, event):
        """Show the tooltip popup window when tooltip button is clicked"""
        popup = PopupWindow(
            self,
            "",  # No text content needed since we're using an image
            "first",
            "images/helpassets/both/welcomepopup.png"  # Path to the welcome image
        )
        popup.exec_()

    def camera_selected(self, index):
        """Handle camera selection from dropdown"""
        if index < 0 or index >= len(self.available_cameras):
            return

        # Make sure we're not navigating back
        if self._navigating:
            return

        # Set camera switching flag to prevent race conditions
        self.camera_switching = True

        try:
            # Get the selected camera ID
            new_camera_id = self.available_cameras[index]["id"]

            # Update the current camera ID
            self.current_camera_id = new_camera_id

            # If video thread is running, update it with safe error handling
            if self.sign_language_thread is not None and self.sign_language_thread.isRunning():
                try:
                    self.sign_language_thread.set_camera(new_camera_id)
                except Exception as e:
                    print(f"Error switching camera: {e}")
                    # Restart the thread if camera switching fails
                    try:
                        self.sign_language_thread.stop()
                        self.sign_language_thread.wait(2000)
                        self.sign_language_thread = None
                        # Short delay before restarting
                        QTimer.singleShot(500, self.setup_video_stream)
                    except Exception as e2:
                        print(f"Error restarting video thread: {e2}")
        finally:
            # Clear camera switching flag
            self.camera_switching = False

    def show_medical_summary_template(self):
        """Show the medical summary template dialog"""
        dialog = MedicalSummaryTemplate(self)
        if dialog.exec_() == QDialog.Accepted:
            # If dialog is accepted, add the summary to chat
            if hasattr(dialog, 'plain_summary'):
                self.send_message("Doctor", dialog.plain_summary)

    # Custom icon methods removed - we're always using patient.png and doctor.png
    # No longer supporting custom icons at runtime

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TranslationModule()
    window.showFullScreen()  # Show in fullscreen mode
    sys.exit(app.exec_())