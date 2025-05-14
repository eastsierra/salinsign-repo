# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import os
import gc  # Import garbage collector

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        try:
            MainWindow.setObjectName("MainWindow")
            MainWindow.resize(1920, 1080)
            MainWindow.setMinimumSize(360, 640)  # Set minimum size for mobile compatibility
            font = QtGui.QFont()
            font.setFamily("Comic Sans MS")
            MainWindow.setFont(font)
            MainWindow.setAcceptDrops(False)
            MainWindow.setTabShape(QtWidgets.QTabWidget.Rounded)
            # Set window to fullscreen
            MainWindow.showFullScreen()
            
            # Save reference to MainWindow for later use
            self.window = MainWindow
            
            # Initialize module windows to None
            self.translation_window = None
            self.dictionary_window = None
            self.user_guide_window = None
            
            # Preload Translation module in background with safety checks
            QtCore.QTimer.singleShot(500, self.preload_translation_module)
            
            self.centralwidget = QtWidgets.QWidget(MainWindow)
            self.centralwidget.setStyleSheet("background-color: rgb(255, 255, 255);")
            self.centralwidget.setObjectName("centralwidget")

            # Add background image label
            self.background_label = QtWidgets.QLabel(self.centralwidget)
            self.background_label.setGeometry(QtCore.QRect(0, 0, 1920, 1080)) # Initial size
            self.background_label.setPixmap(QtGui.QPixmap("RevampedMainDesign.png"))
            self.background_label.setScaledContents(True)
            self.background_label.setObjectName("background_label")
            self.background_label.lower() # Ensure it's behind other widgets
            
            # Create buttons with original styling
            self.SignLibraryButton = QtWidgets.QPushButton(self.centralwidget)
            self.SignLibraryButton.setGeometry(QtCore.QRect(824, 620, 271, 51))
            font = QtGui.QFont()
            font.setPointSize(18)
            self.SignLibraryButton.setFont(font)
            self.SignLibraryButton.setStyleSheet("""
                QPushButton {
                    border-radius: 25px;
                    border: none;
                    background-color: #97cee8;
                    color: black;
                }
                QPushButton:hover {
                    background-color: #a2defa;
                }
            """)
            self.SignLibraryButton.setText("")
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap("images/SignLibraryButtonIcon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.SignLibraryButton.setIcon(icon)
            self.SignLibraryButton.setIconSize(QtCore.QSize(200, 130))
            self.SignLibraryButton.setObjectName("SignLibraryButton")
            
            self.TranslationButton = QtWidgets.QPushButton(self.centralwidget)
            self.TranslationButton.setGeometry(QtCore.QRect(824, 550, 271, 51))
            font = QtGui.QFont()
            font.setFamily("Comic Sans MS")
            font.setPointSize(18)
            self.TranslationButton.setFont(font)
            self.TranslationButton.setStyleSheet("""
                QPushButton {
                    border-radius: 25px;
                    border: none;
                    background-color: #97cee8;
                    color: black;
                    cursor: pointer;
                }
                QPushButton:hover {
                    background-color: #a2defa;
                }
            """)
            self.TranslationButton.setText("")
            icon2 = QtGui.QIcon()
            icon2.addPixmap(QtGui.QPixmap("images/TranslateButtonIcon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.TranslationButton.setIcon(icon2)
            self.TranslationButton.setIconSize(QtCore.QSize(200, 130))
            self.TranslationButton.setObjectName("TranslationButton")
            
            # Add User Guide Button - adjust Y position to be after Sign Library button
            self.UserGuideButton = QtWidgets.QPushButton(self.centralwidget)
            self.UserGuideButton.setGeometry(QtCore.QRect(824, 690, 271, 51))  # Updated Y position
            font = QtGui.QFont()
            font.setPointSize(18)
            self.UserGuideButton.setFont(font)
            self.UserGuideButton.setStyleSheet("""
                QPushButton {
                    border-radius: 25px;
                    border: none;
                    background-color: #97cee8;
                    color: black;
                }
                QPushButton:hover {
                    background-color: #a2defa;
                }
            """)
            self.UserGuideButton.setText("")
            icon3 = QtGui.QIcon()
            icon3.addPixmap(QtGui.QPixmap("images/UserGuideButtonIcon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.UserGuideButton.setIcon(icon3)
            self.UserGuideButton.setIconSize(QtCore.QSize(200, 130))
            self.UserGuideButton.setObjectName("UserGuideButton")
            
            MainWindow.setCentralWidget(self.centralwidget)
            self.menubar = QtWidgets.QMenuBar(MainWindow)
            self.menubar.setGeometry(QtCore.QRect(0, 0, 1920, 21))
            self.menubar.setObjectName("menubar")
            MainWindow.setMenuBar(self.menubar)
            
            self.statusbar = QtWidgets.QStatusBar(MainWindow)
            self.statusbar.setObjectName("statusbar")
            MainWindow.setStatusBar(self.statusbar)

            self.retranslateUi(MainWindow)
            QtCore.QMetaObject.connectSlotsByName(MainWindow)
            
            # Add resize event handler
            MainWindow.resizeEvent = self.handle_resize

        except Exception as e:
            print(f"Error during MainMenu setup: {e}")
            # Create minimal UI if setup fails
            self.create_fallback_ui(MainWindow)

    def create_fallback_ui(self, MainWindow):
        """Create a minimal UI if the main setup fails"""
        try:
            # Clear any partial setup
            if hasattr(self, 'centralwidget'):
                for child in self.centralwidget.children():
                    child.deleteLater()
            
            # Create basic layout
            self.centralwidget = QtWidgets.QWidget(MainWindow)
            MainWindow.setCentralWidget(self.centralwidget)
            layout = QtWidgets.QVBoxLayout(self.centralwidget)
            
            # Error message
            error_label = QtWidgets.QLabel("An error occurred during application startup. Please restart the application.")
            error_label.setStyleSheet("color: red; font-size: 16px;")
            layout.addWidget(error_label)
            
            # Basic buttons
            translation_btn = QtWidgets.QPushButton("Translation")
            translation_btn.clicked.connect(self.open_translation_safe)
            layout.addWidget(translation_btn)
            
            dictionary_btn = QtWidgets.QPushButton("Sign Library")
            dictionary_btn.clicked.connect(self.open_dictionary_safe)
            layout.addWidget(dictionary_btn)
            
            guide_btn = QtWidgets.QPushButton("User Guide")
            guide_btn.clicked.connect(self.open_user_guide_safe)
            layout.addWidget(guide_btn)
            
            # Exit button
            exit_btn = QtWidgets.QPushButton("Exit")
            exit_btn.clicked.connect(MainWindow.close)
            layout.addWidget(exit_btn)
            
        except Exception as e:
            print(f"Critical error creating fallback UI: {e}")

    def handle_resize(self, event):
        width = event.size().width()
        height = event.size().height()
        
        # Update background label size
        if hasattr(self, 'background_label'):
            self.background_label.setGeometry(QtCore.QRect(0, 0, width, height))
        
        # Calculate scale factor based on both width and height
        width_scale = width / 1920
        height_scale = height / 1080
        scale_factor = min(width_scale, height_scale)
        
        # Adjust scale factor for different screen sizes
        if width < 768:  # Mobile devices
            scale_factor *= 1.2  # Slightly larger elements on mobile
            # Hide decorative images on very small screens
            # Ensure UserGuideButton visibility logic is separate and correct if needed
            # For now, we assume UserGuideButton should always be visible or its logic is handled elsewhere
        else:
            # Ensure UserGuideButton visibility logic is separate and correct if needed
            pass # No specific visibility changes for these labels on larger screens anymore
            
        # Scale and center elements
        self.center_elements(width, height, scale_factor)

    def center_elements(self, width, height, scale_factor=1.0):
        # Scale button sizes
        button_width = int(271 * scale_factor)
        button_height = int(51 * scale_factor)
        
        # Calculate border radius based on button height
        border_radius = int(button_height / 2)
        
        # Update button styles with dynamic border radius
        button_style = f"""
            QPushButton {{
                border-radius: {border_radius}px;
                border: none;
                background-color: #97cee8;
                color: black;
                cursor: pointer;
            }}
            QPushButton:hover {{
                background-color: #a2defa;
            }}
        """
        
        # Calculate center x position for buttons
        center_x = (width - button_width) // 2
        
        # Update button positions and styles
        for button in [self.TranslationButton, self.SignLibraryButton, self.UserGuideButton]:
            button.setStyleSheet(button_style)
        
        # Calculate vertical spacing between buttons
        button_spacing = int(70 * scale_factor)
        start_y = int(height * 0.5)  # Start buttons from middle of screen
        
        # Position buttons with consistent spacing
        self.TranslationButton.setGeometry(QtCore.QRect(
            center_x,
            start_y,
            button_width,
            button_height
        ))
        
        # Position Sign Library button immediately after Translation button
        self.SignLibraryButton.setGeometry(QtCore.QRect(
            center_x,
            start_y + button_spacing,
            button_width,
            button_height
        ))
        
        # Position User Guide button immediately after Sign Library button
        self.UserGuideButton.setGeometry(QtCore.QRect(
            center_x,
            start_y + (button_spacing * 2),  # Position right after SignLibraryButton
            button_width,
            button_height
        ))
        
        # Update icon sizes
        icon_width = int(200 * scale_factor)
        icon_height = int(130 * scale_factor)
        for button in [self.TranslationButton, self.SignLibraryButton, self.UserGuideButton]:
            button.setIconSize(QtCore.QSize(icon_width, icon_height))

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "SalinSign"))
        
        # Set up exception handling for button connections
        try:
            # Connect buttons to their respective functions
            self.TranslationButton.clicked.connect(self.open_translation)
            self.SignLibraryButton.clicked.connect(self.open_dictionary)
            self.UserGuideButton.clicked.connect(self.open_user_guide)
        except Exception as e:
            print(f"Error connecting button signals: {e}")

    def preload_translation_module(self):
        """Preload the Translation module to make navigation faster"""
        try:
            from Translation import TranslationModule
            self.translation_window = TranslationModule()
            # Don't show it yet, just initialize it
            # Set flag to prevent video from starting
            self.translation_window.preloaded = True
        except Exception as e:
            print(f"Error preloading Translation module: {e}")
            # Set to None so we'll create it when needed
            self.translation_window = None

    def open_translation_safe(self):
        """Safe wrapper for open_translation"""
        try:
            self.open_translation()
        except Exception as e:
            print(f"Error opening Translation module: {e}")
            QtWidgets.QMessageBox.critical(self.window, "Error", 
                f"Could not open Translation module: {str(e)}")

    def open_dictionary_safe(self):
        """Safe wrapper for open_dictionary"""
        try:
            self.open_dictionary()
        except Exception as e:
            print(f"Error opening Sign Library: {e}")
            QtWidgets.QMessageBox.critical(self.window, "Error", 
                f"Could not open Sign Library: {str(e)}")

    def open_user_guide_safe(self):
        """Safe wrapper for open_user_guide"""
        try:
            self.open_user_guide()
        except Exception as e:
            print(f"Error opening User Guide: {e}")
            QtWidgets.QMessageBox.critical(self.window, "Error", 
                f"Could not open User Guide: {str(e)}")

    def open_translation(self):
        # Force garbage collection to free memory
        gc.collect()
        
        try:
            # If module is already preloaded, just show it
            if self.translation_window is not None:
                self.translation_window.preloaded = False  # Allow normal operation now
                self.translation_window.showFullScreen()  # Use fullscreen
                self.window.hide()
            else:
                # Fall back to normal loading if preloading failed
                from Translation import TranslationModule
                self.translation_window = TranslationModule()
                self.translation_window.showFullScreen()  # Use fullscreen
                self.window.hide()
        except Exception as e:
            print(f"Error in open_translation: {e}")
            # Show error message
            QtWidgets.QMessageBox.critical(self.window, "Error", 
                f"Could not open Translation module: {str(e)}")
        
    def open_dictionary(self):
        # Force garbage collection to free memory
        gc.collect()
        
        try:
            # Clean up existing window if it exists
            if self.dictionary_window is not None:
                self.dictionary_window.close()
                self.dictionary_window = None
                
            from sign_language_library import SignLanguageLibrary
            self.dictionary_window = SignLanguageLibrary()
            self.dictionary_window.showFullScreen()  # Make window full screen
            self.window.hide()  # Hide the main menu window using the saved reference
        except Exception as e:
            print(f"Error in open_dictionary: {e}")
            # Show error message
            QtWidgets.QMessageBox.critical(self.window, "Error", 
                f"Could not open Sign Library: {str(e)}")
        
    def open_user_guide(self):
        # Force garbage collection to free memory
        gc.collect()
        
        try:
            # Clean up existing window if it exists
            if self.user_guide_window is not None:
                self.user_guide_window.close()
                self.user_guide_window = None
                
            from UserGuide import UserGuideModule
            self.user_guide_window = UserGuideModule()
            self.user_guide_window.showFullScreen()  # Make window full screen
            self.window.hide()  # Hide the main menu window using the saved reference
        except Exception as e:
            print(f"Error in open_user_guide: {e}")
            # Show error message
            QtWidgets.QMessageBox.critical(self.window, "Error", 
                f"Could not open User Guide: {str(e)}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
