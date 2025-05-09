from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit,
                           QScrollArea, QSizePolicy, QFrame, QCheckBox, QDialog, QComboBox)
from PyQt5.QtCore import Qt, QSize, QUrl, QThread, pyqtSignal, QByteArray, QTime, QTimer
from PyQt5.QtGui import QPixmap, QCursor, QFont, QImage
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import sys
import os
import pickle
import cv2
import mediapipe as mp
import numpy as np

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
        self.running = False
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        self.wait()

class SignLanguageThread(QThread):
    update_frame = pyqtSignal(QImage)
    update_text = pyqtSignal(str)
    
    def __init__(self, camera_id=0):
        super().__init__()
        self.camera_id = camera_id
        self.running = True
        self.cap = None
        
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
                            mp_drawing.draw_landmarks(
                                frame,
                                hand_landmarks,
                                mp_hands.HAND_CONNECTIONS,
                                mp_drawing_styles.get_default_hand_landmarks_style(),
                                mp_drawing_styles.get_default_hand_connections_style())
                            
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
                                prediction = self.model.predict([np.asarray(data_aux)])
                                predicted_character = self.labels_dict[int(prediction[0])]
                                
                                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 4)
                                cv2.putText(frame, predicted_character, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 0), 3, cv2.LINE_AA)
                                
                                # Emit the predicted character
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
        print("SignLanguageThread stopping...")
        self.running = False
        try:
            if self.cap is not None and self.cap.isOpened():
                self.cap.release()
        except Exception as e:
            print(f"Error releasing camera during stop: {e}")

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
        
        # Default camera ID
        self.current_camera_id = 0
        
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
        self.sign_interval = 1500  # 2 seconds interval between signs
        self.current_sign = None
        self.sign_start_time = 0
        self.sign_hold_time = 700  # 1 second to hold a sign before sending
        
        # Setup video stream (will be properly initialized when the UI is shown)
        self.video_thread = None
        
        # Initialize translation timer
        self.translation_timer = QTimer()
        self.translation_timer.setSingleShot(True)
        self.translation_timer.timeout.connect(self.move_translation_to_chat)
        self.last_gesture_time = 0
        
        # Initialize word spacing timer
        self.word_spacing_timer = QTimer()
        self.word_spacing_timer.setSingleShot(True)
        self.word_spacing_timer.timeout.connect(self.add_space)
        self.last_gesture_time = 0

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
        
        # Translation Text Box
        self.translation_box = QLineEdit()
        self.translation_box.setReadOnly(True)
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
        self.box1_layout.addWidget(self.translation_box)
        
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
        
        # Chat Box
        self.chat_box = QTextEdit()
        self.chat_box.setReadOnly(True)
        self.chat_box.setObjectName("chatBox")
        self.chat_box.setPlaceholderText("No messages yet. Start typing to begin the conversation.")
        self.chat_box.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                font-size: 18px;  /* Increased from 14px */
                min-height: 300px;
            }
        """)
        self.box2_layout.addWidget(self.chat_box)
        
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
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #888;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
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
        
        # Input Container for User 2 (Doctor)
        self.input_container2 = QHBoxLayout()
        self.input_user2 = QLineEdit()
        self.input_user2.setPlaceholderText("Doctor Type here...")
        self.input_user2.returnPressed.connect(lambda: self.send_message("Doctor", self.input_user2.text()))
        
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
        self.input_container2.addWidget(self.clear_chat_button)
        self.box2_layout.addLayout(self.input_container2)
        
        # Add Box 2 to container
        self.container.addWidget(self.box2)
        
        # Add container to main layout
        self.main_layout.addLayout(self.container)
        
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
        self.chat_box.setStyleSheet(f"font-size: {font_size}px;")
        
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
        self.chat_box.setMinimumHeight(chat_height)
        
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
            self.chat_box.show()
            self.sign_display_scroll.hide()
            self.display_messages()
        else:
            # Hide text messages and show sign language
            self.chat_box.hide()
            self.sign_display_scroll.show()
            
            # Ensure the sign display has its layout updated before showing
            self.sign_display_scroll.setWidgetResizable(True)
            self.sign_display.setMinimumWidth(self.box2.width() - 50)  # Allow enough width for the signs
            
            # Clear and update sign language display for all messages
            self.update_sign_display_for_all_messages()
    
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
    
    def send_message(self, user, message):
        if not message.strip():
            return
            
        # Add message to list
        self.messages.append({"user": user, "text": message})
        
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
            else:
                # In text mode, just display the messages
                self.display_messages()
            self.input_user2.clear()
        else:
            # For patient messages, only update in text mode
            if self.text_mode:
                self.display_messages()
    
    def display_messages(self):
        # Clear the chatbox
        self.chat_box.clear()
        
        # Create HTML for all messages with inline styles to ensure bubbles appear
        html_content = """
        <html>
        <head>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                    background-color: white;
                }
                .message-row {
                    width: 100%;
                    clear: both;
                    overflow: hidden;
                    margin-bottom: 8px;
                }
                .message-container-left {
                    float: left;
                    width: 70%;
                    margin-left: 10px;
                }
                .message-container-right {
                    float: right;
                    width: 70%;
                    margin-right: 10px;
                }
                .message-bubble {
                    border-radius: 20px;
                    padding: 10px 15px;
                    display: inline-block;
                    max-width: 100%;
                    word-wrap: break-word;
                    font-size: 28px;  /* Increased from 14px */
                    line-height: 1.4;
                    position: relative;
                }
                .patient-bubble {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    color: #333;
                    border-bottom-left-radius: 5px;
                    margin-left: 5px;
                }
                .doctor-bubble {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    color: #333;
                    border-bottom-right-radius: 5px;
                    margin-right: 5px;
                }
                .message-sender {
                    font-weight: bold;
                    margin-bottom: 2px;
                    font-size: 16px;  /* Increased from 14px */
                    padding-left: 8px;
                    padding-right: 8px;
                    text-align: left;
                }
                .patient-sender {
                    color: #0066cc;
                }
                .doctor-sender {
                    color: #009933;
                }
                .message-text {
                    white-space: pre-wrap;
                }
                .clear {
                    clear: both;
                }
            </style>
        </head>
        <body>
        """
        
        current_user = None
        for msg in self.messages:
            # Add sender label only when the user changes
            show_sender = (current_user != msg['user'])
            current_user = msg['user']
            
            if msg['user'] == "Patient":
                # Patient message - left aligned
                if show_sender:
                    html_content += f'<div class="message-sender patient-sender">{msg["user"]}</div>'
                
                html_content += f"""
                <div class="message-row">
                    <div class="message-container-left">
                        <div class="message-bubble patient-bubble">
                            <div class="message-text">{msg["text"]}</div>
                        </div>
                    </div>
                    <div class="clear"></div>
                </div>
                """
            else:
                # Doctor message - right aligned
                if show_sender:
                    html_content += f'<div class="message-sender doctor-sender">{msg["user"]}</div>'
                
                html_content += f"""
                <div class="message-row">
                    <div class="message-container-right">
                        <div class="message-bubble doctor-bubble">
                            <div class="message-text">{msg["text"]}</div>
                        </div>
                    </div>
                    <div class="clear"></div>
                </div>
                """
        
        # Add some spacing at the bottom for better scrolling
        html_content += """
        <div style="height: 20px"></div>
        </body>
        </html>
        """
        
        # Set the HTML content
        self.chat_box.setHtml(html_content)
        
        # Scroll to the bottom of the chat box
        cursor = self.chat_box.textCursor()
        cursor.movePosition(cursor.End)
        self.chat_box.setTextCursor(cursor)
    
    def go_back(self, event):
        """Return to the main menu when the back button is clicked"""
        try:
            # Set a flag to prevent re-entering this method
            if hasattr(self, '_navigating') and self._navigating:
                print("Navigation already in progress, ignoring request")
                return
            self._navigating = True

            # First, stop video processing to free up resources
            print("Stopping sign language thread...")
            if self.sign_language_thread is not None:
                try:
                    self.sign_language_thread.stop()
                    # Use a timeout to avoid hanging if thread doesn't respond
                    if not self.sign_language_thread.wait(3000):  # 3 second timeout
                        print("Warning: Sign language thread did not stop cleanly")
                    self.sign_language_thread = None
                except Exception as e:
                    print(f"Error stopping sign language thread: {e}")
            
            print("Stopping video thread...")
            if self.video_thread is not None:
                try:
                    self.video_thread.stop()
                    # Use a timeout to avoid hanging if thread doesn't respond
                    if not self.video_thread.wait(3000):  # 3 second timeout
                        print("Warning: Video thread did not stop cleanly")
                    self.video_thread = None
                except Exception as e:
                    print(f"Error stopping video thread: {e}")
            
            # Explicitly stop timers
            print("Stopping timers...")
            if hasattr(self, 'translation_timer') and self.translation_timer.isActive():
                try:
                    self.translation_timer.stop()
                except Exception as e:
                    print(f"Error stopping translation timer: {e}")
                
            if hasattr(self, 'word_spacing_timer') and self.word_spacing_timer.isActive():
                try:
                    self.word_spacing_timer.stop()
                except Exception as e:
                    print(f"Error stopping word spacing timer: {e}")

            # Delay the actual navigation to give threads time to clean up
            def perform_navigation():
                try:
                    # Close current window instead of hiding it
                    self.close()
                    
                    # Import the main menu
                    from MainMenu import Ui_MainWindow
                    
                    # Close any other windows like Sign Language Library module
                    for widget in QApplication.topLevelWidgets():
                        if isinstance(widget, QMainWindow) and widget != self:
                            widget.close()
                    
                    # Create a new MainWindow instance
                    main_window = QMainWindow()
                    ui = Ui_MainWindow()
                    ui.setupUi(main_window)
                    main_window.showFullScreen()
                except Exception as e:
                    print(f"Error during navigation: {e}")
                    # Ensure we still try to show the main menu even if there's an error
                    try:
                        from MainMenu import Ui_MainWindow
                        main_window = QMainWindow()
                        ui = Ui_MainWindow()
                        ui.setupUi(main_window)
                        main_window.showFullScreen()
                    except Exception as e2:
                        print(f"Critical error returning to main menu: {e2}")
            
            # Use a timer to delay the navigation
            QTimer.singleShot(300, perform_navigation)
            
        except Exception as e:
            print(f"Error during back button handling: {e}")
            # Fallback to try to show the main menu
            try:
                from MainMenu import Ui_MainWindow
                main_window = QMainWindow()
                ui = Ui_MainWindow()
                ui.setupUi(main_window)
                main_window.showFullScreen()
            except Exception as e2:
                print(f"Critical error returning to main menu: {e2}")
    
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
        """Handle recognized sign language gestures with timing control"""
        current_time = QTime.currentTime().msecsSinceStartOfDay()
        
        # Update last gesture time and restart word spacing timer
        self.last_gesture_time = current_time
        self.word_spacing_timer.start(2000)  # 2 seconds for word spacing
        
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
                    # Get current text and append new sign
                    current_text = self.translation_box.text()
                    if current_text:
                        new_text = f"{current_text}{sign}"
                    else:
                        new_text = sign
                    self.translation_box.setText(new_text)
                    self.last_sign_time = current_time
                    self.last_recognized_sign = sign
                    self.sign_buffer = sign
                    
                    # Restart the translation timer
                    self.translation_timer.start(5000)  # 5 seconds

    def add_space(self):
        """Add a space to the translation text"""
        current_text = self.translation_box.text()
        if current_text and not current_text.endswith(' '):
            self.translation_box.setText(f"{current_text} ")
    
    def move_translation_to_chat(self):
        """Move the translation text to the chat box and clear the translation box"""
        translation_text = self.translation_box.text()
        if translation_text:
            # Add the translation as a message from the Patient
            self.send_message("Patient", translation_text)
            # Clear the translation box
            self.translation_box.clear()
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
        try:
            if self.sign_language_thread is not None:
                self.sign_language_thread.stop()
                # Use timeout to prevent hanging
                if not self.sign_language_thread.wait(2000):  # 2 second timeout
                    print("Warning: Sign language thread did not stop cleanly on close")
                self.sign_language_thread = None
                
            if self.video_thread is not None:
                self.video_thread.stop()
                # Use timeout to prevent hanging
                if not self.video_thread.wait(2000):  # 2 second timeout
                    print("Warning: Video thread did not stop cleanly on close")
                self.video_thread = None
                
            # Explicitly stop timers
            if hasattr(self, 'translation_timer') and self.translation_timer.isActive():
                self.translation_timer.stop()
                
            if hasattr(self, 'word_spacing_timer') and self.word_spacing_timer.isActive():
                self.word_spacing_timer.stop()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        
        # Call the base class implementation
        super().closeEvent(event)

    def hideEvent(self, event):
        """Ensure resources are cleaned up when hiding the window"""
        try:
            # Stop video processing to free up resources
            if self.sign_language_thread is not None:
                self.sign_language_thread.stop()
                self.sign_language_thread.wait()  # Ensure thread is fully stopped
                self.sign_language_thread = None
                
            if self.video_thread is not None:
                self.video_thread.stop()
                self.video_thread.wait()  # Ensure thread is fully stopped
                self.video_thread = None
                
            # Explicitly stop timers
            if hasattr(self, 'translation_timer') and self.translation_timer.isActive():
                self.translation_timer.stop()
                
            if hasattr(self, 'word_spacing_timer') and self.word_spacing_timer.isActive():
                self.word_spacing_timer.stop()
        except Exception as e:
            print(f"Error during hide cleanup: {e}")
        
        super().hideEvent(event)

    def clear_chat(self):
        """Clear all chat messages and sign language display"""
        # Clear messages list
        self.messages = []
        
        # Clear chat box
        self.chat_box.clear()
        
        # Clear sign language display
        self.clear_sign_display()
        
        # Clear translation box
        self.translation_box.clear()

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
            
        # Get the selected camera ID
        new_camera_id = self.available_cameras[index]["id"]
        
        # Update the current camera ID
        self.current_camera_id = new_camera_id
        
        # If video thread is running, update it
        if self.sign_language_thread is not None and self.sign_language_thread.isRunning():
            self.sign_language_thread.set_camera(new_camera_id)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TranslationModule()
    window.showFullScreen()  # Show in fullscreen mode
    sys.exit(app.exec_())