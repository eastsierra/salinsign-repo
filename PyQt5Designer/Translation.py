from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit,
                           QScrollArea, QSizePolicy, QFrame, QCheckBox)
from PyQt5.QtCore import Qt, QSize, QUrl, QThread, pyqtSignal, QByteArray, QTime, QTimer
from PyQt5.QtGui import QPixmap, QCursor, QFont, QImage
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import sys
import os
import pickle
import cv2
import mediapipe as mp
import numpy as np

class VideoStreamThread(QThread):
    update_frame = pyqtSignal(QImage)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.running = True
        
    def run(self):
        # This is a placeholder for video streaming
        # In a real implementation, you would use OpenCV or other libraries
        # to fetch video frames from the URL and emit them as QImage objects
        
        # For demonstration purposes, we'll use a network manager to try to fetch images
        # Note: This is not a proper video streaming implementation and would need to be 
        # replaced with a proper video streaming solution in production
        
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handle_reply)
        
        # Continually request new frames while running
        while self.running:
            self.network_manager.get(QNetworkRequest(QUrl(self.url)))
            # Sleep to avoid overwhelming the network
            self.msleep(100)  # 10 FPS
            
    def handle_reply(self, reply):
        if reply.error() == QNetworkReply.NoError:
            # Convert data to QImage
            data = reply.readAll()
            image = QImage.fromData(data)
            if not image.isNull():
                self.update_frame.emit(image)
        
    def stop(self):
        self.running = False
        self.wait()

class SignLanguageThread(QThread):
    update_frame = pyqtSignal(QImage)
    update_text = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.model_dict = pickle.load(open('./model.p', 'rb'))
        self.model = self.model_dict['model']
        self.labels_dict = {0: 'Pain', 1: 'Sick', 2: 'Headache', 3: 'Dizzy', 4: 'Vomit', 5: 'Diarrhea', 6: 'Cough', 7: 'Allergy', 
                           8: 'Strong', 9: 'Weak', 10: 'Stomachache', 11: 'Sore Throat', 12: 'Sore Throat', 13: 'Injury', 
                           14: 'Breathing Difficulty', 15: 'Food Poisoning', 16: 'Wound', 17: 'Stress',
                           18: 'Conditions', 19: 'Fever', 20: 'Diabetes', 21: 'Back Pain', 22: 'Back Pain', 23: 'Colds', 24: 'Stroke',
                           25: 'Blood Pressure', 26: 'Heartache', 27: 'A', 28: 'B', 29: 'C', 30: 'D', 31: 'E', 32: 'F', 33: 'G', 34: 'H', 35: 'I', 
                           36: 'J', 37: 'K', 38: 'L', 39: 'M', 40: 'N', 41: 'O', 42: 'P', 43: 'Q', 44: 'R', 45: 'S', 46: 'T', 
                           47: 'U', 48: 'V', 49: 'W', 50: 'X', 51: 'Y', 52: 'Z', 53: 'Hello', 54: 'Good Morning', 55: 'Good Afternooon',
                           56: 'Good Evening'}
        
    def run(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        mp_hands = mp.solutions.hands
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing_styles = mp.solutions.drawing_styles
        
        hands = mp_hands.Hands(static_image_mode=True, min_detection_confidence=0.3)
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
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
                    
                    prediction = self.model.predict([np.asarray(data_aux)])
                    predicted_character = self.labels_dict[int(prediction[0])]
                    
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 4)
                    cv2.putText(frame, predicted_character, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 0), 3, cv2.LINE_AA)
                    
                    # Emit the predicted character
                    self.update_text.emit(predicted_character)
            
            # Convert frame to QImage
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.update_frame.emit(qt_image)
            
        cap.release()
        
    def stop(self):
        self.running = False
        self.wait()

class TranslationModule(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SalinSign Translation Module")
        self.setGeometry(0, 0, 1920, 1080)
        self.setMinimumSize(360, 640)  # Set minimum size for mobile compatibility
        
        # Set white background for the main window
        self.setStyleSheet("background-color: white;")
        
        # Initialize messages list
        self.messages = []
        
        # Initialize display mode (True for text, False for sign language)
        self.text_mode = True
        
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
        button_header.addStretch()
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
        
        # Create a new row for each word
        current_row_layout = QHBoxLayout()
        current_row_layout.setSpacing(5)
        current_row_layout.setContentsMargins(0, 0, 0, 0)
        current_row_layout.setAlignment(Qt.AlignLeft)  # Align to the left
        
        for image_path in image_paths:
            if image_path is None:  # Word boundary marker
                # Add the current row to the main layout
                self.sign_display_layout.addLayout(current_row_layout)
                # Create a new row for the next word
                current_row_layout = QHBoxLayout()
                current_row_layout.setSpacing(5)
                current_row_layout.setContentsMargins(0, 0, 0, 0)
                current_row_layout.setAlignment(Qt.AlignLeft)  # Align to the left
                continue
                
            image_label = QLabel()
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                print(f"Failed to load image: {image_path}")
                continue
            # Scale the image to a larger size
            scaled_pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)
            image_label.setAlignment(Qt.AlignLeft)  # Align image to the left
            image_label.setMinimumSize(120, 120)
            current_row_layout.addWidget(image_label)
        
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
                    background-color: #f0f2f5;
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
                    font-size: 40px;  /* Increased from 14px */
                    line-height: 1.4;
                    position: relative;
                }
                .patient-bubble {
                    background-color: #f0f2f5;
                    color: #333;
                    border-bottom-left-radius: 5px;
                    margin-left: 5px;
                }
                .doctor-bubble {
                    background-color: #f0f2f5;
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
        # Import the main menu and return to it
        from MainMenu import Ui_MainWindow
        
        # Clean up video thread if it exists
        if self.video_thread is not None:
            self.video_thread.stop()
            
        # Close current window
        self.close()
        
        # Show the main menu window again
        # Get the instance that was created in __main__
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QMainWindow) and widget != self:
                widget.show()
                return
        
        # If no existing main window is found, create a new one
        self.main_window = QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.main_window)
        self.main_window.show()
    
    def update_video_frame(self, image):
        """Update the video placeholder with a new frame"""
        scaled_image = image.scaled(self.video_placeholder.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_placeholder.setPixmap(QPixmap.fromImage(scaled_image))
    
    def setup_video_stream(self):
        """Set up the sign language recognition and video streaming"""
        self.sign_language_thread = SignLanguageThread()
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
        self.setup_video_stream()
    
    def closeEvent(self, event):
        """Clean up resources when closing the window"""
        if self.sign_language_thread is not None:
            self.sign_language_thread.stop()
        if self.video_thread is not None:
            self.video_thread.stop()
        super().closeEvent(event)

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TranslationModule()
    window.show()
    sys.exit(app.exec_())
