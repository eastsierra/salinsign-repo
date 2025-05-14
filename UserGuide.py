from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy)
from PyQt5 import QtWidgets  # Add this for QtWidgets.QMainWindow
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QCursor, QFont
import sys
import os

class UserGuideModule(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SalinSign User Guide")
        self.setGeometry(0, 0, 1920, 1080)
        self.setMinimumSize(360, 640)  # Set minimum size for mobile compatibility
        
        # Set white background for the main window
        self.setStyleSheet("background-color: white;")
        
        # Keep track of current slide
        self.current_slide = 1
        self.total_slides = 10
        
        # Error handling for image loading
        try:
            # Setup UI
            self.setup_ui()
            
            # Add resize event handler
            self.resizeEvent = self.handle_resize
        except Exception as e:
            print(f"Error initializing UserGuide: {e}")
            # Create a simple UI with error message if setup fails
            self.create_error_ui(str(e))
        
    def setup_ui(self):
        # Main central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main vertical layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        # Back button in its own layout at top left
        back_container = QHBoxLayout()
        back_container.setContentsMargins(0, 0, 0, 0)
        
        # Back to main menu button
        self.main_back_button = QLabel()
        self.main_back_button.setObjectName("mainBackButton")
        self.main_back_button.setPixmap(QPixmap("images/backbutton.png").scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.main_back_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.main_back_button.mousePressEvent = self.go_back
        back_container.addWidget(self.main_back_button, alignment=Qt.AlignLeft)
        back_container.addStretch()
        
        self.main_layout.addLayout(back_container)
        
        # Header image in its own layout, centered
        header_container = QHBoxLayout()
        header_container.setContentsMargins(0, 0, 0, 10)  # Add bottom margin
        
        # Add header image
        self.header_image = QLabel()
        self.header_image.setObjectName("headerImage")
        self.header_image.setPixmap(QPixmap("images/userguideassets/userguideicon.png").scaledToWidth(400, Qt.SmoothTransformation))
        self.header_image.setAlignment(Qt.AlignCenter)
        
        header_container.addStretch(1)
        header_container.addWidget(self.header_image, alignment=Qt.AlignCenter)
        header_container.addStretch(1)
        
        self.main_layout.addLayout(header_container)
        
        # Slideshow content
        self.slide_image = QLabel()
        self.slide_image.setObjectName("slideImage")
        self.slide_image.setAlignment(Qt.AlignCenter)
        self.slide_image.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.slide_image.setStyleSheet("background-color: white;")
        self.main_layout.addWidget(self.slide_image)
        
        # Navigation buttons
        self.nav_layout = QHBoxLayout()
        
        # Previous slide button
        self.prev_button = QLabel()
        self.prev_button.setObjectName("prevButton")
        self.prev_button.setPixmap(QPixmap("images/userguideassets/back.png").scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.prev_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.prev_button.mousePressEvent = self.prev_slide
        
        # Next slide button
        self.next_button = QLabel()
        self.next_button.setObjectName("nextButton")
        self.next_button.setPixmap(QPixmap("images/userguideassets/forward.png").scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.next_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.next_button.mousePressEvent = self.next_slide
        
        # Add buttons to layout with stretch for centering
        self.nav_layout.addStretch(1)
        self.nav_layout.addWidget(self.prev_button)
        self.nav_layout.addSpacing(40)  # Space between buttons
        self.nav_layout.addWidget(self.next_button)
        self.nav_layout.addStretch(1)
        
        self.main_layout.addLayout(self.nav_layout)
        
        # Now that all UI elements are created, set the initial slide
        self.update_slide()
    
    def update_slide(self):
        """Update the slide image based on current_slide"""
        try:
            slide_path = f"images/userguideassets/{self.current_slide}.png"
            
            # Get window size for scaling
            width = self.width()
            height = self.height() - 200  # Account for header and nav buttons
            
            # Load and scale image to fit width while maintaining aspect ratio
            pixmap = QPixmap(slide_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(width - 40, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.slide_image.setPixmap(scaled_pixmap)
            else:
                # If image not found, show error message
                self.slide_image.setText(f"Could not load image: {slide_path}")
                print(f"Could not load image: {slide_path}")
            
            # Update button states
            self.prev_button.setEnabled(self.current_slide > 1)
            self.next_button.setEnabled(self.current_slide < self.total_slides)
            
            # Visual feedback for disabled buttons
            if self.current_slide == 1:
                self.prev_button.setStyleSheet("opacity: 0.5;")
            else:
                self.prev_button.setStyleSheet("opacity: 1;")
            
            if self.current_slide == self.total_slides:
                self.next_button.setStyleSheet("opacity: 0.5;")
            else:
                self.next_button.setStyleSheet("opacity: 1;")
        except Exception as e:
            print(f"Error updating slide: {e}")
            self.slide_image.setText(f"Error: {e}")
    
    def next_slide(self, event):
        """Go to the next slide"""
        if self.current_slide < self.total_slides:
            self.current_slide += 1
            self.update_slide()
    
    def prev_slide(self, event):
        """Go to the previous slide"""
        if self.current_slide > 1:
            self.current_slide -= 1
            self.update_slide()
    
    def handle_resize(self, event):
        """Handle window resize event"""
        width = event.size().width()
        height = event.size().height()
        
        # Rescale header image
        scale_factor = min(width / 1920, 1.0)
        logo_scale_factor = scale_factor * 0.8  # 80% of the original size
        self.header_image.setPixmap(QPixmap("images/userguideassets/userguideicon.png").scaledToWidth(int(400 * logo_scale_factor), Qt.SmoothTransformation))
        
        # Rescale main back button
        self.main_back_button.setPixmap(QPixmap("images/backbutton.png").scaled(
            int(40 * scale_factor), 
            int(40 * scale_factor),
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        ))
        
        # Rescale navigation buttons
        nav_button_size = int(60 * scale_factor)
        self.prev_button.setPixmap(QPixmap("images/userguideassets/back.png").scaled(
            nav_button_size, 
            nav_button_size,
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        ))
        self.next_button.setPixmap(QPixmap("images/userguideassets/forward.png").scaled(
            nav_button_size, 
            nav_button_size,
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        ))
        
        # Update the slide for new dimensions
        self.update_slide()
        
    def create_error_ui(self, error_message):
        """Create a simple UI when normal initialization fails"""
        # Main central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Simple layout
        layout = QVBoxLayout(self.central_widget)
        
        # Error message
        error_label = QLabel(f"An error occurred: {error_message}")
        error_label.setWordWrap(True)
        error_label.setStyleSheet("color: red; font-size: 16px;")
        layout.addWidget(error_label)
        
        # Back button
        back_button = QPushButton("Return to Main Menu")
        back_button.clicked.connect(self.go_back_safe)
        layout.addWidget(back_button)
    
    def go_back_safe(self, event=None):
        """Safe version of go_back that handles exceptions"""
        try:
            self.go_back(event if event else None)
        except Exception as e:
            print(f"Error going back to main menu: {e}")
            # Try a simpler way to get back to main menu
            try:
                from MainMenu import Ui_MainWindow
                self.close()
                main_window = QtWidgets.QMainWindow()
                ui = Ui_MainWindow()
                ui.setupUi(main_window)
                main_window.showFullScreen()
            except Exception as e2:
                print(f"Critical error returning to main menu: {e2}")
                # Last resort - just close this window
                self.close()
    
    def go_back(self, event):
        """Return to the main menu when the back button is clicked"""
        try:
            # Import the main menu
            from MainMenu import Ui_MainWindow
            
            # Close current window
            self.close()
            
            # Close any other windows like Translation module
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, QMainWindow) and widget != self:
                    widget.close()
            
            # Create a new MainWindow instance
            main_window = QtWidgets.QMainWindow()
            ui = Ui_MainWindow()
            ui.setupUi(main_window)
            main_window.showFullScreen()  # Show in full screen mode
        except Exception as e:
            print(f"Error in go_back: {e}")
            # Try a simpler approach
            self.close()
    
    def closeEvent(self, event):
        """Handle window close event with proper cleanup"""
        try:
            # Any cleanup needed
            pass
        except Exception as e:
            print(f"Error during UserGuide close: {e}")
        event.accept()  # Always accept the close event


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UserGuideModule()
    window.showFullScreen()  # Show in full screen mode
    sys.exit(app.exec_()) 