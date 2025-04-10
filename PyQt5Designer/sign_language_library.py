import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTabWidget, 
                             QListWidget, QListWidgetItem, QSplitter, QFrame,
                             QGraphicsDropShadowEffect, QAbstractItemView)
from PyQt5.QtGui import QPixmap, QIcon, QFont, QColor
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve

class SignLanguageLibrary(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sign Language Library")
        self.setMinimumSize(1000, 600)
        
        # Set app-wide font
        font = QFont("Segoe UI", 10)
        QApplication.setFont(font)
        
        # Define a consistent color scheme
        self.colors = {
            "primary": "#4FB0AA",
            "secondary": "#4FB0AA",  # Matching primary for consistency
            "background": "#f8f9fa",
            "surface": "#ffffff",
            "border": "#e0e0e0",
            "hover": "#f0f0f0",
            "active": "#e0e0e0",
            "text": "#333333",
            "text_light": "#666666",
            "active_text": "#ffffff",  # Text color for active items
            "tab_background": "#F0F0F0"  # Light grey for tab backgrounds
        }
        
        # Define tab colors
        self.tab_colors = {
            "alphabet": {
                "primary": "#4FB0AA",  # Teal
                "hover": "#E6F7F6",
                "item_bg": "#E6F7F6",
                "item_selected": "#4FB0AA",
                "item_hover": "#D0EFED"
            },
            "numbers": {
                "primary": "#5B6ABB",  # Blue
                "hover": "#E6E9F7",
                "item_bg": "#E6E9F7",
                "item_selected": "#5B6ABB",
                "item_hover": "#D0D6EF"
            },
            "greetings": {
                "primary": "#E67E22",  # Orange
                "hover": "#FBF1E6",
                "item_bg": "#FBF1E6",
                "item_selected": "#E67E22",
                "item_hover": "#F7E0C9"
            },
            "medical": {
                "primary": "#E74C3C",  # Red
                "hover": "#FCE9E7",
                "item_bg": "#FCE9E7",
                "item_selected": "#E74C3C",
                "item_hover": "#F8D4D0"
            }
        }
        
        # Create central widget and main layout
        central_widget = QWidget()
        central_widget.setStyleSheet(f"background-color: {self.colors['background']};")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create header
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors['surface']};
                border-bottom: 1px solid {self.colors['border']};
            }}
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # Improved back button with larger icon
        back_button = QPushButton()
        back_icon = QIcon("images/backbutton.png")
        back_button.setIcon(back_icon)
        back_button.setIconSize(QSize(50, 50))  # Adjust icon size here
        back_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['surface']};
                border: none;
                border-radius: 22px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['hover']};
            }}
            QPushButton:pressed {{
                background-color: {self.colors['active']};
            }}
        """)
        back_button.setFixedSize(50, 50)  # Adjust button size here
        
        # Title with modern styling
        title_label = QLabel()
        title_pixmap = QPixmap("images/signlibrary.png")
        title_label.setPixmap(title_pixmap)
        title_label.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(back_button)
        header_layout.addWidget(title_label)
        
        # Add header to main layout
        main_layout.addWidget(header_frame)
        
        # Create container for tab widget with padding
        tab_container = QWidget()
        tab_container.setStyleSheet(f"background-color: transparent;")  # Make this transparent
        tab_container_layout = QVBoxLayout(tab_container)
        tab_container_layout.setContentsMargins(20, 20, 20, 20)
        
        # Create tab widget with custom styling
        tab_widget = QTabWidget()
        # Make the tab widget itself transparent
        tab_widget.setStyleSheet(f"background-color: transparent;")
        
        # Helper function for creating tab content with unified design
        def create_tab_content(items, initial_title, color_scheme):
            tab = QWidget()
            # Set the tab background to match the color scheme
            tab.setStyleSheet(f"""
                background-color: {color_scheme['primary']};
                border-top-left-radius: 0px;
                border-top-right-radius: 8px;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            """)
            
            layout = QVBoxLayout(tab)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            # Create inner container with rounded corners
            inner_container = QWidget(tab)
            inner_container.setStyleSheet(f"""
                background-color: {color_scheme['primary']};
                border-radius: 8px;
            """)
            inner_layout = QVBoxLayout(inner_container)
            inner_layout.setContentsMargins(15, 15, 15, 15)
            
            # Create splitter with custom styling
            splitter = QSplitter(Qt.Horizontal)
            splitter.setHandleWidth(1)
            splitter.setStyleSheet(f"""
                QSplitter::handle {{
                    background-color: {self.colors['active_text']};
                }}
            """)
            
            # List widget container with rounded corners and shadow
            list_container = QFrame()
            list_container.setStyleSheet(f"""
                background-color: {self.colors['surface']};
                border-radius: 8px;
                margin: 0px;
                padding: 0px;
            """)
            list_container_layout = QVBoxLayout(list_container)
            list_container_layout.setContentsMargins(5, 5, 5, 5)
            list_container_layout.setSpacing(0)
            
            # Apply shadow to list container
            list_shadow = QGraphicsDropShadowEffect()
            list_shadow.setBlurRadius(20)
            list_shadow.setColor(QColor(0, 0, 0, 30))
            list_shadow.setOffset(0, 3)
            list_container.setGraphicsEffect(list_shadow)
            
            # Enhanced list widget for word library with button-like items
            list_widget = QListWidget()
            list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
            list_widget.setStyleSheet(f"""
                QListWidget {{
                    background: {self.colors['surface']};
                    border: none;
                    border-radius: 6px;
                    padding: 5px;
                    outline: none;
                }}
                QListWidget::item {{
                    background-color: {color_scheme['item_bg']};
                    padding: 12px 15px;
                    border-radius: 6px;
                    color: {self.colors['text']};
                    margin: 3px 2px;
                    font-weight: 500;
                    font-size: 11px;
                }}
                QListWidget::item:selected {{
                    background: {color_scheme['item_selected']};
                    color: {self.colors['active_text']};
                    border: none;
                    outline: none;
                    font-weight: bold;
                }}
                QListWidget::item:hover:!selected {{
                    background: {color_scheme['item_hover']};
                }}
                
                /* Hide focus rectangle completely */
                QListWidget:focus {{
                    outline: none;
                }}
                QListWidget::item:focus {{
                    outline: none;
                    border: none;
                }}
            """)
            
            # Disable focus rect explicitly
            list_widget.setFocusPolicy(Qt.NoFocus)
            
            # Add items
            for item_text in items:
                item = QListWidgetItem(item_text)
                list_widget.addItem(item)
            
            list_container_layout.addWidget(list_widget)
            
            # Content frame with improved layout and matching color
            content_frame = QFrame()
            content_frame.setStyleSheet(f"""
                QFrame {{
                    background: {color_scheme['primary']};
                    padding: 0px;
                    border: none;
                    border-radius: 8px;
                }}
            """)
            content_layout = QVBoxLayout(content_frame)
            content_layout.setContentsMargins(25, 15, 25, 15)
            content_layout.setSpacing(10)
            
            # Title with white text to contrast with the primary color
            title_label = QLabel(initial_title)
            title_label.setStyleSheet(f"""
                color: {self.colors['active_text']}; 
                font-size: 22px; 
                font-weight: bold;
                padding: 5px 0;
                margin: 0;
            """)
            title_label.setAlignment(Qt.AlignLeft)
            title_label.setMaximumHeight(40)
            
            # Improved image container with contrasting background
            image_container = QFrame()
            image_container.setStyleSheet(f"""
                background: {self.colors['surface']};
                border-radius: 12px;
                padding: 0px;
                border: none;
            """)
            image_container_layout = QVBoxLayout(image_container)
            image_container_layout.setContentsMargins(0, 0, 0, 0)
            
            image_label = QLabel()
            image_label.setStyleSheet("""
                background-color: transparent;
                min-height: 300px;
                border-radius: 12px;
            """)
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setScaledContents(False)
            
            # Apply shadow effect to image container
            image_shadow = QGraphicsDropShadowEffect()
            image_shadow.setBlurRadius(20)
            image_shadow.setColor(QColor(0, 0, 0, 30))
            image_shadow.setOffset(0, 3)
            image_container.setGraphicsEffect(image_shadow)
            
            image_container_layout.addWidget(image_label)
            
            # Add widgets to content layout
            content_layout.addWidget(title_label)
            content_layout.addWidget(image_container, 1)
            
            # Add widgets to splitter
            splitter.addWidget(list_container)
            splitter.addWidget(content_frame)
            splitter.setSizes([250, 750])
            
            inner_layout.addWidget(splitter)
            layout.addWidget(inner_container)
            
            return tab, list_widget, title_label, image_label
        
        # Create all tabs with different color schemes
        alphabet_items = [f"Letter {letter}" for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
        alphabet_tab, letter_list, letter_title, letter_image = create_tab_content(
            alphabet_items, "Letter A", self.tab_colors["alphabet"]
        )
        
        number_items = [f"Number {num}" for num in range(1, 11)]
        numbers_tab, numbers_list, number_title, number_image = create_tab_content(
            number_items, "Number 1", self.tab_colors["numbers"]
        )
        
        greetings = ["Hello", "Good morning", "Good afternoon", "Good evening", "Thank you", "Goodbye"]
        greetings_tab, greetings_list, greeting_title, greeting_image = create_tab_content(
            greetings, "Hello", self.tab_colors["greetings"]
        )
        
        medical_terms = ["Pain", "Sick", "Headache", "Dizzy", "Vomit", "Diarrhea",
                        "Cough", "Allergy", "Strong", "Weak", "Stomachache", "Sore throat",
                        "Injury", "Breathing Difficulty", "Food Poisoning", "Wound", "Stress", 
                        "Conditions", "Fever", "Diabetes", "Back pain", "Cold", "Stroke", 
                        "Blood Pressure", "Heartache"]
        medical_tab, medical_list, medical_title, medical_image = create_tab_content(
            medical_terms, "Pain", self.tab_colors["medical"]
        )
        
        # Create a list of tab color schemes in the same order as tabs will be added
        tab_color_schemes = [
            self.tab_colors["alphabet"],
            self.tab_colors["numbers"],
            self.tab_colors["greetings"],
            self.tab_colors["medical"]
        ]
        
        # Set the base styling for tab widget - with completely transparent pane
        tab_widget.setStyleSheet(f"""
            QTabWidget {{
                background-color: transparent;
            }}
            QTabWidget::pane {{
                border: none;
                background-color: transparent;
                padding: 0px;
            }}
            QTabBar::tab {{
                font-weight: bold;
                padding: 12px 40px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border: none;
                min-width: 120px;
                color: {self.colors['text']};
                background: {self.colors['tab_background']};
            }}
            
            /* Modern scrollbar styling */
            QScrollBar:vertical {{
                border: none;
                background: {self.colors['background']};
                width: 8px;
                margin: 0px 0px 0px 0px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(0, 0, 0, 0.3);
                min-height: 30px;
                border-radius: 4px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            
            /* Horizontal scrollbar */
            QScrollBar:horizontal {{
                border: none;
                background: {self.colors['background']};
                height: 8px;
                margin: 0px 0px 0px 0px;
                border-radius: 4px;
            }}
            QScrollBar::handle:horizontal {{
                background: rgba(0, 0, 0, 0.3);
                min-width: 30px;
                border-radius: 4px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                border: none;
                background: none;
                width: 0px;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
        """)
        
        # Apply drop shadow to tab widget
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 2)
        tab_widget.setGraphicsEffect(shadow)
        
        # Add tabs to tab widget
        tab_widget.addTab(alphabet_tab, "Alphabet")
        tab_widget.addTab(numbers_tab, "Numbers")
        tab_widget.addTab(greetings_tab, "Greetings")
        tab_widget.addTab(medical_tab, "Medical")
        
        # Use a more reliable method to style individual tabs
        # This method gets the actual tab widget and styles it directly
        # We get the tabBar and then style each tab separately
        tab_bar = tab_widget.tabBar()
        
        # Apply the specific color scheme to each tab
        for i, scheme in enumerate(tab_color_schemes):
            # Create a style sheet for each individual tab
            tab_style = f"""
                QTabBar::tab:selected:only-one, QTabBar::tab:selected {{
                    background: {scheme['primary']};
                    color: {self.colors['active_text']};
                }}
                QTabBar::tab:!selected:hover {{
                    background: {scheme['hover']};
                }}
            """
            
            # Set the style sheet for this specific tab
            tab_bar.setTabData(i, tab_style)
            
        # Override the paintEvent of the tab bar to apply individual tab styles
        original_paint_event = tab_bar.paintEvent
        
        def custom_paint_event(event):
            # Apply individual styling before painting
            for i in range(tab_bar.count()):
                if tab_bar.tabData(i):
                    # If this tab is currently selected
                    if i == tab_bar.currentIndex():
                        tab_bar.setStyleSheet(tab_bar.tabData(i))
            
            # Call the original paint event
            original_paint_event(event)
        
        # Replace the paint event with our custom one
        tab_bar.paintEvent = custom_paint_event
        
        # Add tab widget to container
        tab_container_layout.addWidget(tab_widget)
        
        # Add container to main layout
        main_layout.addWidget(tab_container)
        
        # Set initial selection for each list to avoid empty state
        letter_list.setCurrentRow(0)
        numbers_list.setCurrentRow(0)
        greetings_list.setCurrentRow(0)
        medical_list.setCurrentRow(0)
        
        # Unified update function for all tabs
        def update_content(title_label, image_label, text, image_prefix):
            # Update title with unified styling
            title_label.setText(text)
            
            # Get image path
            if "Letter" in text:
                letter_value = text.split()[-1].lower()
                image_path = f"images/{image_prefix}_{letter_value}.png"
            elif "Number" in text:
                number_value = text.split()[-1]
                image_path = f"images/{image_prefix}_{number_value}.png"
            else:
                filename = text.lower().replace(' ', '_').replace('?', '').replace('!', '')
                image_path = f"images/{image_prefix}_{filename}.png"
            
            # Update image with proper scaling
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Use scaled to maintain aspect ratio
                max_width = 800
                max_height = 480
                
                # Scale the image while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    max_width, 
                    max_height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                
                image_label.setPixmap(scaled_pixmap)
        
        # Connect signals with the unified update function
        letter_list.itemClicked.connect(
            lambda item: update_content(letter_title, letter_image, item.text(), "letter")
        )
        numbers_list.itemClicked.connect(
            lambda item: update_content(number_title, number_image, item.text(), "number")
        )
        greetings_list.itemClicked.connect(
            lambda item: update_content(greeting_title, greeting_image, item.text(), "greeting")
        )
        medical_list.itemClicked.connect(
            lambda item: update_content(medical_title, medical_image, item.text(), "medical")
        )
        
        # Connect tab changed signal to update the tab styling
        def handle_tab_change(index):
            # Update the tab bar style to match the currently selected tab
            if 0 <= index < tab_bar.count() and tab_bar.tabData(index):
                tab_bar.setStyleSheet(tab_bar.tabData(index))
        
        tab_widget.currentChanged.connect(handle_tab_change)
        
        # Initialize with first items' content
        update_content(letter_title, letter_image, "Letter A", "letter")
        update_content(number_title, number_image, "Number 1", "number")
        update_content(greeting_title, greeting_image, "Hello", "greeting")
        update_content(medical_title, medical_image, "Pain", "medical")
        
        # Connect back button
        back_button.clicked.connect(self.go_back)
        
        # Trigger initial tab style
        handle_tab_change(0)

    def go_back(self):
        # Import the main menu and return to it
        from MainMenu import Ui_MainWindow
        
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    window = SignLanguageLibrary()
    window.show()
    sys.exit(app.exec_())