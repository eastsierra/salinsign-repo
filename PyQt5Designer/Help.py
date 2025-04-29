from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QTextEdit,
                             QFrame, QSlider)
from PyQt5.QtGui import QPixmap, QCursor, QIcon
from PyQt5.QtCore import Qt, QSize, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

import sys
import os

# Import the MainWindow class from the previous code
from MainMenu import Ui_MainWindow  # Make sure the file name is correct

class HelpModule(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Help Module")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: #f8f9fa;")
        
        self.setup_ui()

    def setup_ui(self):
        # Main container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Back Button
        back_button = QPushButton()
        back_icon = QIcon("images/backbutton.png")
        back_button.setIcon(back_icon)
        back_button.setIconSize(QSize(70, 70))
        back_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
        """)
        back_button.setCursor(QCursor(Qt.PointingHandCursor))
        back_button.clicked.connect(self.go_back)
        main_layout.addWidget(back_button, alignment=Qt.AlignLeft)

        # Header Image
        header_image = QLabel()
        header_image.setPixmap(QPixmap("images/HeaderHelp.png").scaledToWidth(350, Qt.SmoothTransformation))
        header_image.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header_image)

        # Help Content
        help_content = QFrame()
        content_layout = QHBoxLayout(help_content)

        # Video Section Layout
        video_section_layout = QVBoxLayout()

        # Video Widget
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(400, 250)
        video_section_layout.addWidget(self.video_widget)

        # Media Player
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)

        # Load Video
        video_file_path = os.path.join("video", "demo.mp4")
        if os.path.exists(video_file_path):
            video_url = QUrl.fromLocalFile(os.path.abspath(video_file_path))
            self.media_player.setMedia(QMediaContent(video_url))
        else:
            print("Video file not found:", video_file_path)

        # Controls Layout
        controls_layout = QHBoxLayout()

        # Play Button
        play_button = QPushButton("Play")
        play_button.clicked.connect(self.play_video)
        controls_layout.addWidget(play_button)

        # Pause Button
        pause_button = QPushButton("Pause")
        pause_button.clicked.connect(self.pause_video)
        controls_layout.addWidget(pause_button)

        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.set_position)
        controls_layout.addWidget(self.slider)

        # Connect video player signals
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.durationChanged.connect(self.update_duration)

        video_section_layout.addLayout(controls_layout)
        content_layout.addLayout(video_section_layout)

        # Help Text Section
        text_box = QTextEdit()
        text_box.setReadOnly(True)
        text_box.setStyleSheet("""
            padding: 15px;
            border-radius: 10px;
            border: 4px solid #333;
            background-color: white;
            font-size: 16px;
            color: #333;
            text-align: justify;
            line-height: 1.5;
        """)
        text_box.setText(
            "<strong>Lorem ipsum dolor sit amet,</strong> consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
            " Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure"
            " dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non"
            " proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
        )
        content_layout.addWidget(text_box)

        main_layout.addWidget(help_content)

    def play_video(self):
        """Play the video."""
        self.media_player.play()

    def pause_video(self):
        """Pause the video."""
        self.media_player.pause()

    def set_position(self, position):
        """Set the position of the media player."""
        self.media_player.setPosition(position)

    def update_position(self, position):
        """Update the slider position."""
        self.slider.setValue(position)

    def update_duration(self, duration):
        """Update the slider range based on the video duration."""
        self.slider.setRange(0, duration)

    def go_back(self):
        """Handle back button click"""
        self.main_window = QMainWindow()  # Create a new QMainWindow
        self.ui = Ui_MainWindow()  # Create an instance of the Ui_MainWindow
        self.ui.setupUi(self.main_window)  # Set up the UI for the main window
        self.main_window.show()  # Show the main window
        self.close()  # Close the current HelpModule window

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HelpModule()
    window.show()
    sys.exit(app.exec_())
