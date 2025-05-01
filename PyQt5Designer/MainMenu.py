# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import os

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
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
        
        # Preload Translation module in background
        self.translation_window = None
        QtCore.QTimer.singleShot(100, self.preload_translation_module)
        
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.centralwidget.setObjectName("centralwidget")
        
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
        
        # Create labels with proper scaling settings
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(-80, 540, 791, 511))
        self.label_2.setText("")
        self.label_2.setPixmap(QtGui.QPixmap("images/doctorBottomLeft.png"))
        self.label_2.setScaledContents(True)
        self.label_2.setObjectName("label_2")
        
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(474, 50, 971, 481))
        self.label.setText("")
        self.label.setPixmap(QtGui.QPixmap("images/SalinSignLogo.png"))
        self.label.setScaledContents(True)
        self.label.setObjectName("label")
        
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(1170, 550, 791, 511))
        self.label_3.setText("")
        self.label_3.setPixmap(QtGui.QPixmap("images/deafBottomRight.png"))
        self.label_3.setScaledContents(True)
        self.label_3.setObjectName("label_3")
        
        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setGeometry(QtCore.QRect(170, 30, 271, 271))
        self.label_4.setText("")
        self.label_4.setPixmap(QtGui.QPixmap("images/CrossUpperLeft.png"))
        self.label_4.setScaledContents(True)
        self.label_4.setObjectName("label_4")
        
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

    def handle_resize(self, event):
        width = event.size().width()
        height = event.size().height()
        
        # Calculate scale factor based on both width and height
        width_scale = width / 1920
        height_scale = height / 1080
        scale_factor = min(width_scale, height_scale)
        
        # Adjust scale factor for different screen sizes
        if width < 768:  # Mobile devices
            scale_factor *= 1.2  # Slightly larger elements on mobile
            # Hide decorative images on very small screens
            self.label_4.setVisible(width > 480)
            self.label_2.setVisible(width > 480)
            self.label_3.setVisible(width > 480)
        else:
            self.label_4.setVisible(True)
            self.label_2.setVisible(True)
            self.label_3.setVisible(True)
            
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
        
        # Scale logo size
        logo_width = int(971 * scale_factor)
        logo_height = int(481 * scale_factor)
        
        # Calculate center positions
        center_x = (width - button_width) // 2
        logo_center_x = (width - logo_width) // 2
        
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
        
        # Update logo position (centered at top)
        self.label.setGeometry(QtCore.QRect(
            logo_center_x,
            int(height * 0.05),  # 5% from top
            logo_width,
            logo_height
        ))
        
        # Update decorative images if visible
        if self.label_4.isVisible():
            cross_size = int(271 * scale_factor)
            self.label_4.setGeometry(QtCore.QRect(
                int(width * 0.05),  # 5% from left
                int(height * 0.05),  # 5% from top
                cross_size,
                cross_size
            ))
            self.label_4.setPixmap(QtGui.QPixmap("images/CrossUpperLeft.png").scaled(
                cross_size, cross_size, 
                QtCore.Qt.KeepAspectRatio, 
                QtCore.Qt.SmoothTransformation
            ))
        
        if self.label_2.isVisible():
            doctor_width = int(791 * scale_factor)
            doctor_height = int(511 * scale_factor)
            self.label_2.setGeometry(QtCore.QRect(
                int(-80 * scale_factor),
                int(height * 0.5),  # Middle of screen
                doctor_width,
                doctor_height
            ))
            self.label_2.setPixmap(QtGui.QPixmap("images/doctorBottomLeft.png").scaled(
                doctor_width, doctor_height,
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation
            ))
        
        if self.label_3.isVisible():
            deaf_width = int(791 * scale_factor)
            deaf_height = int(511 * scale_factor)
            self.label_3.setGeometry(QtCore.QRect(
                width - deaf_width - int(width * 0.05),  # 5% from right
                int(height * 0.5),  # Middle of screen
                deaf_width,
                deaf_height
            ))
            self.label_3.setPixmap(QtGui.QPixmap("images/deafBottomRight.png").scaled(
                deaf_width, deaf_height,
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation
            ))
        
        # Update icon sizes
        icon_width = int(200 * scale_factor)
        icon_height = int(130 * scale_factor)
        for button in [self.TranslationButton, self.SignLibraryButton, self.UserGuideButton]:
            button.setIconSize(QtCore.QSize(icon_width, icon_height))

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "SalinSign"))
        
        # Connect buttons to their respective functions
        self.TranslationButton.clicked.connect(self.open_translation)
        self.SignLibraryButton.clicked.connect(self.open_dictionary)
        self.UserGuideButton.clicked.connect(self.open_user_guide)

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

    def open_translation(self):
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
        
    def open_dictionary(self):
        from sign_language_library import SignLanguageLibrary
        self.dictionary_window = SignLanguageLibrary()
        self.dictionary_window.showFullScreen()  # Make window full screen
        self.window.hide()  # Hide the main menu window using the saved reference
        
    def open_user_guide(self):
        from UserGuide import UserGuideModule
        self.user_guide_window = UserGuideModule()
        self.user_guide_window.showFullScreen()  # Make window full screen
        self.window.hide()  # Hide the main menu window using the saved reference

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
