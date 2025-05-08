import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTabWidget, 
                             QScrollArea, QGridLayout, QFrame, QSizePolicy,
                             QGraphicsDropShadowEffect, QDialog, QTabBar,
                             QLineEdit, QComboBox, QListWidget, QListWidgetItem,
                             QSplitter, QAbstractItemView)
from PyQt5.QtGui import QPixmap, QIcon, QFont, QColor, QPainterPath, QPen, QPainter
from PyQt5.QtCore import Qt, QSize, QRectF, QPoint, pyqtProperty, QPropertyAnimation, QEasingCurve
from functools import partial

class RoundedItemFrame(QFrame):
    """Custom rounded frame for catalog items"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.radius = 15  # Increased radius for more modern look
        self.setMinimumSize(180, 200)
        self.setMaximumSize(220, 240)  # Set maximum size for consistency
        
    def paintEvent(self, event):
        """Custom paint event to create rounded corners"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        path = QPainterPath()
        rect = QRectF(0, 0, float(self.width()), float(self.height()))
        path.addRoundedRect(rect, self.radius, self.radius)
        
        painter.setClipPath(path)
        painter.fillRect(0, 0, self.width(), self.height(), self.palette().color(self.backgroundRole()))
        
        # Add subtle border
        pen = QPen(QColor(0, 0, 0, 20))  # Very light border
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawPath(path)

class CatalogItem(QWidget):
    """Widget for individual catalog items"""
    def __init__(self, title, image_path, color_scheme, category, parent=None):
        super().__init__(parent)
        self.title = title
        self.image_path = image_path
        self.color_scheme = color_scheme
        self.category = category
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Container with shadow
        self.container = RoundedItemFrame()
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {self.color_scheme['item_bg']};
                border: none;
            }}
        """)
        self.container.setAutoFillBackground(True)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 2)
        self.container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(5)
        
        # Image container with fixed size and white background
        image_container = QFrame()
        image_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
        """)
        image_container.setFixedSize(160, 160)
        
        # Image label with fixed size for uniform grid
        self.image_label = QLabel()
        self.image_label.setFixedSize(150, 150)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border-radius: 10px;
            }
        """)
        
        # Load and scale the image
        pixmap = QPixmap(self.image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(140, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText("Image not found")
        
        # Center the image in its container
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.addWidget(self.image_label, 0, Qt.AlignCenter)
        
        # Title label with fixed height
        self.title_label = QLabel(self.title)
        self.title_label.setFixedHeight(25)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(f"""
            color: {self.color_scheme['text_color']};
            font-weight: bold;
            font-size: 12px;
        """)
        
        container_layout.addWidget(image_container, 0, Qt.AlignCenter)
        container_layout.addWidget(self.title_label)
        
        layout.addWidget(self.container)
        
        # Make the item clickable
        self.setCursor(Qt.PointingHandCursor)
        
        # Set tooltip
        self.setToolTip(f"Click to view details of {self.title}")
        
        # Add hover effect
        self.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
            }}
            QWidget:hover {{
                background-color: {self.color_scheme['item_hover']};
                border-radius: 15px;
            }}
        """)
        
    def enterEvent(self, event):
        """Handle mouse enter event"""
        # Scale up the container slightly
        self.container.setGraphicsEffect(QGraphicsDropShadowEffect(
            blurRadius=20,
            color=QColor(0, 0, 0, 60),
            offset=QPoint(0, 3)
        ))
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Handle mouse leave event"""
        # Restore original shadow
        self.container.setGraphicsEffect(QGraphicsDropShadowEffect(
            blurRadius=15,
            color=QColor(0, 0, 0, 40),
            offset=QPoint(0, 2)
        ))
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        """Handle mouse press to show detail dialog"""
        if event.button() == Qt.LeftButton:
            self.show_detail_dialog()
            
    def show_detail_dialog(self):
        """Show a dialog with larger image and details"""
        dialog = DetailDialog(self.title, self.image_path, self.color_scheme, self.category, self)
        dialog.exec_()

class DetailDialog(QDialog):
    """Dialog showing details for a selected sign"""
    def __init__(self, title, image_path, color_scheme, category, parent=None):
        super().__init__(parent)
        self.title = title
        self.image_path = image_path
        self.color_scheme = color_scheme
        self.category = category
        self.offset = None
        
        self.setWindowTitle(title)
        self.setMinimumSize(600, 500)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setup_ui()
        
        # Animation for opening
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(250)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.start()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Main content frame with rounded corners
        main_frame = QFrame()
        main_frame.setStyleSheet(f"""
            background-color: {self.color_scheme['primary']};
            border-radius: 15px;
        """)
        
        # Add shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        main_frame.setGraphicsEffect(shadow)
        
        main_layout = QVBoxLayout(main_frame)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header with title and close button
        header_layout = QHBoxLayout()
        
        # Add category badge
        category_badge = QLabel(self.category)
        category_badge.setStyleSheet(f"""
            background-color: rgba(255, 255, 255, 0.3);
            color: white;
            font-size: 14px;
            font-weight: bold;
            border-radius: 10px;
            padding: 3px 10px;
        """)
        category_badge.setFixedHeight(25)
        
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            color: white;
            font-size: 24px;
            font-weight: bold;
        """)
        
        close_button = QPushButton("×")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                font-size: 24px;
                font-weight: bold;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 15px;
            }
        """)
        close_button.setFixedSize(30, 30)
        close_button.clicked.connect(self.close)
        
        header_layout.addWidget(category_badge)
        header_layout.addSpacing(10)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(close_button)
        
        # Image container with white background
        image_container = QFrame()
        image_container.setStyleSheet("""
            background-color: white;
            border-radius: 10px;
        """)
        image_container_layout = QVBoxLayout(image_container)
        
        # Image label
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setMinimumSize(500, 350)
        
        # Load and scale image
        pixmap = QPixmap(self.image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                500, 350,
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            # Center the pixmap in the label
            image_label.setPixmap(scaled_pixmap)
            image_label.setAlignment(Qt.AlignCenter)
            # Add padding to center the image
            image_label.setContentsMargins(10, 10, 10, 10)
        else:
            image_label.setText("Image not found")
            image_label.setStyleSheet("color: #333; font-size: 16px;")
        
        image_container_layout.addWidget(image_label)
        
        # Additional content could go here
        description_label = QLabel("Practice this sign by following the image.")
        description_label.setStyleSheet("color: white; font-size: 14px;")
        description_label.setAlignment(Qt.AlignCenter)
        
        # Add widgets to main layout
        main_layout.addLayout(header_layout)
        main_layout.addWidget(image_container, 1)  # 1 = stretch factor
        main_layout.addWidget(description_label)
        
        layout.addWidget(main_frame)
    
    def mousePressEvent(self, event):
        """Allow dialog to be moved by dragging"""
        if event.button() == Qt.LeftButton:
            self.offset = event.pos()
        else:
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event):
        """Move dialog with mouse"""
        if self.offset is not None and event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.pos() - self.offset)
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event):
        """Reset offset on mouse release"""
        self.offset = None
        super().mouseReleaseEvent(event)
        
    def close(self):
        """Override close with fade animation"""
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(150)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.finished.connect(super().close)
        self.animation.start()

class CustomTabBar(QTabBar):
    """Custom tab bar with modern browser-like curved tabs"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab_colors = []
        
    def set_tab_colors(self, colors):
        """Set colors for different tabs"""
        self.tab_colors = colors
        self.update()
        
    def paintEvent(self, event):
        """Custom paint event to style tabs with curved edges"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        for i in range(self.count()):
            rect = self.tabRect(i)
            
            # Create path with curved top corners
            path = QPainterPath()
            radius = 10  # Corner radius
            
            # Start from bottom-left
            path.moveTo(rect.left(), rect.bottom())
            
            # Draw line to top-left and add curve for top-left corner
            path.lineTo(rect.left(), rect.top() + radius)
            path.arcTo(rect.left(), rect.top(), radius * 2, radius * 2, 180, -90)
            
            # Draw line across top and add curve for top-right corner
            path.lineTo(rect.right() - radius, rect.top())
            path.arcTo(rect.right() - radius * 2, rect.top(), radius * 2, radius * 2, 90, -90)
            
            # Draw line to bottom-right and close the path
            path.lineTo(rect.right(), rect.bottom())
            path.lineTo(rect.left(), rect.bottom())
            
            # Fill with appropriate color
            if i == self.currentIndex() and i < len(self.tab_colors):
                painter.fillPath(path, QColor(self.tab_colors[i]))
            else:
                painter.fillPath(path, QColor("#F0F0F0"))  # Default background color
            
            # Draw text with appropriate color
            text = self.tabText(i)
            if i == self.currentIndex():
                painter.setPen(QColor("#FFFFFF"))  # White text for selected tab
            else:
                # Use the tab's color for text when not selected
                painter.setPen(QColor(self.tab_colors[i]) if i < len(self.tab_colors) else QColor("#333333"))
            
            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
            
            # Center text in tab
            text_rect = rect.adjusted(10, 5, -10, -5)
            painter.drawText(text_rect, Qt.AlignCenter, text)

class SignLanguageLibrary(QMainWindow):
    def __init__(self):
        super().__init__()
        # Set up window properties
        self.setWindowTitle("Sign Language Library")
        self.setGeometry(100, 100, 1920, 1080)
        self.setMinimumSize(600, 400)
        # Set window to fullscreen
        self.showFullScreen()
        
        # Set app-wide font
        font = QFont("Segoe UI", 10)
        QApplication.setFont(font)
        
        # Define a consistent color scheme
        self.colors = {
            "primary": "#4FB0AA",
            "secondary": "#4FB0AA",
            "background": "#f8f9fa",
            "surface": "#ffffff",
            "border": "#e0e0e0",
            "hover": "#f0f0f0",
            "active": "#e0e0e0",
            "text": "#333333",
            "text_light": "#666666",
            "active_text": "#ffffff",
            "tab_background": "#F0F0F0"
        }
        
        # Define tab colors (keeping your preferred order)
        self.tab_colors = {
            "alphabet": {
                "primary": "#4FB0AA",  # Teal
                "hover": "#E6F7F6",
                "item_bg": "#E6F7F6",
                "item_selected": "#4FB0AA",
                "item_hover": "#D0EFED",
                "text_color": "#2A6762"
            },
            "numbers": {
                "primary": "#5B6ABB",  # Blue
                "hover": "#E6E9F7",
                "item_bg": "#E6E9F7",
                "item_selected": "#5B6ABB",
                "item_hover": "#D0D6EF",
                "text_color": "#344380"
            },
            "greetings": {
                "primary": "#E67E22",  # Orange
                "hover": "#FBF1E6",
                "item_bg": "#FBF1E6",
                "item_selected": "#E67E22",
                "item_hover": "#F7E0C9",
                "text_color": "#A05816"
            },
            "medical": {
                "primary": "#E74C3C",  # Red
                "hover": "#FCE9E7",
                "item_bg": "#FCE9E7",
                "item_selected": "#E74C3C",
                "item_hover": "#F8D4D0",
                "text_color": "#A03529"
            }
        }
        
        # Store all items for search functionality
        self.all_items = {}
        
        # Initialize UI
        self.setup_ui()
        
    def setup_ui(self):
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
        
        # Back button with icon
        back_button = QPushButton()
        back_icon = QIcon("images/backbutton.png")
        back_button.setIcon(back_icon)
        back_button.setIconSize(QSize(40, 40))
        back_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['surface']};
                border: none;
                border-radius: 20px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['hover']};
            }}
            QPushButton:pressed {{
                background-color: {self.colors['active']};
            }}
        """)
        back_button.setFixedSize(40, 40)
        back_button.clicked.connect(self.go_back)
        
        # Title with logo
        title_label = QLabel()
        title_pixmap = QPixmap("images/signlibrary.png")
        title_label.setPixmap(title_pixmap)
        title_label.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(back_button)
        header_layout.addWidget(title_label)
        
        # Add header to main layout
        main_layout.addWidget(header_frame)
        
        # Create search bar container
        search_container = QFrame()
        search_container.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors['surface']};
                border-bottom: 1px solid {self.colors['border']};
            }}
            QLineEdit {{
                border: 1px solid {self.colors['border']};
                border-radius: 20px;
                padding: 8px 15px;
                background-color: {self.colors['background']};
                selection-background-color: {self.colors['primary']};
            }}
            QComboBox {{
                border: 1px solid {self.colors['border']};
                border-radius: 20px;
                padding: 8px 15px;
                background-color: {self.colors['background']};
                selection-background-color: {self.colors['primary']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QPushButton {{
                background-color: {self.colors['primary']};
                color: white;
                border: none;
                border-radius: 20px;
                padding: 8px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #45A29A;
            }}
            QPushButton:pressed {{
                background-color: #3A8A84;
            }}
        """)
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(20, 10, 20, 10)
        
        # Search icon
        search_icon_label = QLabel()
        search_icon = QPixmap("images/search_icon.png")
        if search_icon.isNull():
            search_icon_label.setText("🔍")
            search_icon_label.setStyleSheet("font-size: 16px; color: #888;")
        else:
            search_icon_label.setPixmap(search_icon.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        search_icon_label.setFixedSize(30, 30)
        search_icon_label.setAlignment(Qt.AlignCenter)
        
        # Search input field
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search sign language...")
        self.search_input.setMinimumWidth(300)
        
        # Clear button (X)
        clear_search_button = QPushButton("×")
        clear_search_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                font-size: 18px;
                font-weight: bold;
                border: none;
                padding: 5px;
                margin-right: 5px;
            }
            QPushButton:hover {
                color: #333;
            }
        """)
        clear_search_button.setFixedSize(30, 30)
        clear_search_button.clicked.connect(self.clear_search)
        
        # Search button
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.perform_search)
        
        # Add search elements to layout
        search_layout.addWidget(search_icon_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(clear_search_button)
        search_layout.addWidget(search_button)
        
        # Add search container to main layout
        main_layout.addWidget(search_container)
        
        # Create tab widget with custom tab bar
        self.tab_widget = QTabWidget()
        # Replace default tab bar with our custom one
        custom_tab_bar = CustomTabBar()
        self.tab_widget.setTabBar(custom_tab_bar)
        
        # Set the tab colors in your preferred order
        custom_tab_bar.set_tab_colors([
            self.tab_colors["medical"]["primary"],
            self.tab_colors["greetings"]["primary"],
            self.tab_colors["alphabet"]["primary"],
            self.tab_colors["numbers"]["primary"]
        ])
        
        # Apply the tab styling from your old code
        self.tab_widget.setStyleSheet(f"""
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
        self.tab_widget.setGraphicsEffect(shadow)
        
        # Define categories with their items, alphabetically sorted
        alphabet_items = sorted([f"Letter {letter}" for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"])
        
        number_items = sorted([f"Number {num}" for num in range(1, 11)], 
                             key=lambda x: int(x.split()[-1]))  # Sort numerically
        
        greeting_items = sorted([
            "Good afternoon", "Good evening", "Good morning", "Goodbye", "Hello", "Thank you"
        ])
        
        medical_items = sorted([
            "Allergy", "Back pain", "Blood Pressure", "Cold", "Conditions", 
            "Cough", "Diabetes", "Diarrhea", "Dizzy", "Fever", "Food Poisoning", 
            "Headache", "Heartache", "Injury", "Pain", "Sick", "Sore throat", 
            "Stomachache", "Stress", "Stroke", "Strong", "Vomit", "Weak", 
            "Wound", "Breathing Difficulty"
        ])
        
        # Create tabs with catalog grid layout in your preferred order
        self.tab_widget.addTab(self.create_catalog_tab(
            "Medical", medical_items, self.tab_colors["medical"]
        ), "Medical")

        self.tab_widget.addTab(self.create_catalog_tab(
            "Greetings", greeting_items, self.tab_colors["greetings"]
        ), "Greetings")

        self.tab_widget.addTab(self.create_catalog_tab(
            "Alphabet", alphabet_items, self.tab_colors["alphabet"]
        ), "Alphabet")
        
        self.tab_widget.addTab(self.create_catalog_tab(
            "Numbers", number_items, self.tab_colors["numbers"]
        ), "Numbers")
        
        # Create search results tab (initially hidden)
        self.search_results_tab = self.create_empty_search_tab()
        
        # Add tab widget to main layout with padding
        tab_container = QWidget()
        tab_container_layout = QVBoxLayout(tab_container)
        tab_container_layout.setContentsMargins(20, 20, 20, 20)
        tab_container_layout.addWidget(self.tab_widget)
        main_layout.addWidget(tab_container)
        
        # Connect search input to search function
        self.search_input.returnPressed.connect(self.perform_search)
        
    def create_catalog_tab(self, category, items, color_scheme):
        """Create a tab with a grid of catalog items"""
        # Container widget
        tab = QWidget()
        tab.setStyleSheet(f"background-color: {color_scheme['primary']};")
        
        # Main layout
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove outer margins
        
        # Create a scroll area for the grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet(f"background-color: {color_scheme['primary']};")
        
        # Create content widget for the scroll area
        content = QWidget()
        content.setStyleSheet(f"background-color: {color_scheme['primary']};")
        
        # Main vertical layout for rows
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # Store items for search functionality
        if category not in self.all_items:
            self.all_items[category] = []
        
        # Calculate items per row based on window width
        # Assuming minimum item width of 180px and spacing of 15px
        window_width = self.width()
        min_item_width = 180
        spacing = 15
        items_per_row = max(3, min(6, (window_width - 40) // (min_item_width + spacing)))
        
        # Create rows of items
        current_row = []
        row_layout = None
        
        for item_text in items:
            # Determine image path based on the item type
            if "Letter" in item_text:
                letter_value = item_text.split()[-1].lower()
                image_path = f"images/letter_{letter_value}.png"
            elif "Number" in item_text:
                number_value = item_text.split()[-1]
                image_path = f"images/number_{number_value}.png"
            else:
                filename = item_text.lower().replace(' ', '_').replace('?', '').replace('!', '')
                image_path = f"images/{category.lower()}_{filename}.png"
            
            # Store item info for search
            self.all_items[category].append({
                'title': item_text,
                'image_path': image_path,
                'color_scheme': color_scheme,
                'category': category
            })
            
            # Create catalog item
            catalog_item = CatalogItem(item_text, image_path, color_scheme, category)
            
            # Calculate item size based on items per row
            item_width = (window_width - 40 - (items_per_row - 1) * spacing) // items_per_row
            item_height = int(item_width * 1.1)  # Maintain aspect ratio
            
            # Set fixed size for uniform grid
            catalog_item.setFixedSize(item_width, item_height)
            
            # Add to current row
            current_row.append(catalog_item)
            
            # If row is full or this is the last item, create a new row
            if len(current_row) == items_per_row or item_text == items[-1]:
                # Create new row layout
                row_layout = QHBoxLayout()
                row_layout.setSpacing(spacing)
                row_layout.setContentsMargins(0, 0, 0, 0)
                
                # Add items to row
                for item in current_row:
                    row_layout.addWidget(item)
                
                # If this is the last row and it's not full, add spacers to fill the row
                if len(current_row) < items_per_row and item_text == items[-1]:
                    for _ in range(items_per_row - len(current_row)):
                        spacer = QWidget()
                        spacer.setFixedSize(item_width, item_height)
                        row_layout.addWidget(spacer)
                
                # Add row to main layout
                main_layout.addLayout(row_layout)
                
                # Clear current row
                current_row = []
        
        # Set scroll content
        scroll_area.setWidget(content)
        
        # Add scroll area to layout
        layout.addWidget(scroll_area)
        
        return tab
        
    def create_empty_search_tab(self):
        """Create an empty tab for search results"""
        tab = QWidget()
        tab.setStyleSheet(f"background-color: {self.colors['background']};")
        
        layout = QVBoxLayout(tab)
        layout.setAlignment(Qt.AlignCenter)
        
        message = QLabel("Search results will appear here")
        message.setStyleSheet("color: #888; font-size: 16px;")
        message.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(message)
        
        return tab
        
    def create_search_results_tab(self, results, query):
        """Create a tab with search results"""
        tab = QWidget()
        tab.setStyleSheet(f"background-color: {self.colors['primary']};")

        # Main layout
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
 
        # Add search bar and cancel button at the top
        search_header = QHBoxLayout()
        search_label = QLabel(f"Search results for: '{query}'")
        search_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")

        clear_button = QPushButton("Clear Search")
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #333;
                border: none;
                border-radius: 15px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #eee;
            }
        """)
        clear_button.clicked.connect(self.clear_search)

        search_header.addWidget(search_label)
        search_header.addStretch()
        search_header.addWidget(clear_button)
        layout.addLayout(search_header)

        # Create a scroll area for the grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet(f"background-color: {self.colors['primary']};")

        # Create content widget for the scroll area
        content = QWidget()
        content.setStyleSheet(f"background-color: {self.colors['primary']};")

        if not results:
            # Handle no results case
            empty_layout = QVBoxLayout(content)
            empty_label = QLabel("No results found")
            empty_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_layout.addWidget(empty_label)
            empty_layout.setAlignment(Qt.AlignCenter)
        else:
            # Grid layout for items with center alignment
            grid = QGridLayout(content)
            grid.setContentsMargins(10, 10, 10, 10)
            grid.setSpacing(20)
        
            # Calculate the number of rows and columns needed
            max_cols = 4  # 4 items per row
            num_results = len(results)
            num_rows = (num_results + max_cols - 1) // max_cols  # Ceiling division
        
            # Create catalog items and add to grid
            item_index = 0
        
            # Calculate horizontal offset to center items if the last row isn't full
            items_in_last_row = num_results % max_cols
            if items_in_last_row == 0 and num_results > 0:
                items_in_last_row = max_cols
            
            # Center the items in the grid
            grid.setAlignment(Qt.AlignCenter)
        
            for row in range(num_rows):
                # Determine how many items in this row
                items_in_row = min(max_cols, num_results - row * max_cols)
            
                # Calculate offset for centering items in this row
                offset = (max_cols - items_in_row) // 2 if items_in_row < max_cols else 0
            
                for col in range(items_in_row):
                    if item_index < num_results:
                        item = results[item_index]
                    
                        # Create catalog item
                        catalog_item = CatalogItem(
                            item['title'], 
                            item['image_path'], 
                            item['color_scheme'],
                            item['category']
                        )
                
                        # Set fixed size for uniform grid
                        catalog_item.setFixedSize(200, 220)
                
                        # Add to grid with proper centering
                        grid_col = col + offset
                        grid.addWidget(catalog_item, row, grid_col)
                    
                        item_index += 1

        # Set scroll content
        scroll_area.setWidget(content)

        # Add scroll area to layout
        layout.addWidget(scroll_area)

        return tab

    def perform_search(self):
        """Search for items across all categories"""
        query = self.search_input.text().lower().strip()
        
        # If query is empty, do nothing
        if not query:
            return
        
        results = []
        
        # Search across all categories
        for category, items in self.all_items.items():
            for item in items:
                # Check if query is in the item title
                if query in item['title'].lower():
                    # Add category info to the item
                    item_copy = item.copy()
                    item_copy['category'] = category
                    results.append(item_copy)
        
        # Sort results alphabetically
        results.sort(key=lambda x: x['title'])
        
        # Check if "Search Results" tab already exists and remove it
        search_tab_index = -1
        for i in range(self.tab_widget.count()):
            if "Search Results" in self.tab_widget.tabText(i):
                search_tab_index = i
                break
            
        if search_tab_index >= 0:
            self.tab_widget.removeTab(search_tab_index)
    
        # Create search results tab
        search_results_tab = self.create_search_results_tab(results, query)
    
        # Add search results tab at the end and switch to it
        self.tab_widget.addTab(search_results_tab, f"Search Results ({len(results)})")
        self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)
    
        # Update tab bar colors to include the search tab
        custom_tab_bar = self.tab_widget.tabBar()
        if isinstance(custom_tab_bar, CustomTabBar):
            tab_colors = [
                self.tab_colors["medical"]["primary"],
                self.tab_colors["greetings"]["primary"],
                self.tab_colors["alphabet"]["primary"],
                self.tab_colors["numbers"]["primary"],
                self.colors["primary"]  # Color for search results tab
            ]
            custom_tab_bar.set_tab_colors(tab_colors)

    def clear_search(self):
        """Clear search and remove search results tab"""
        # Clear search input
        self.search_input.clear()
    
        # Find and remove the search results tab
        for i in range(self.tab_widget.count()):
            if "Search Results" in self.tab_widget.tabText(i):
                self.tab_widget.removeTab(i)
                break
    
        # Reset tab bar colors after removing the search tab
        custom_tab_bar = self.tab_widget.tabBar()
        if isinstance(custom_tab_bar, CustomTabBar):
            tab_colors = [
                self.tab_colors["medical"]["primary"],
                self.tab_colors["greetings"]["primary"],
                self.tab_colors["alphabet"]["primary"],
                self.tab_colors["numbers"]["primary"]
            ]
            custom_tab_bar.set_tab_colors(tab_colors)

    def get_tab_title_by_index(self, index):
        """Get the original tab title by index"""
        tab_titles = ["Medical", "Greetings", "Alphabet", "Numbers"]
        if 0 <= index < len(tab_titles):
            return tab_titles[index]
        return "Tab"

    def go_back(self):
        """Handle back button click"""
        # If in search mode, cancel search and return to normal view
        if hasattr(self, 'in_search_mode') and self.in_search_mode:
            self.cancel_search()
            return
        
        # Otherwise, return to main menu
        try:
            from MainMenu import Ui_MainWindow
            # Close current window
            self.close()
            
            # Show the main menu window again
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, QMainWindow) and widget != self:
                    widget.show()
                    return
            
            # If no existing main window is found, create a new one
            self.main_window = QMainWindow()
            self.ui = Ui_MainWindow()
            self.ui.setupUi(self.main_window)
            self.main_window.show()
        except ImportError:
            pass

    def resizeEvent(self, event):
        """Handle window resize to update item sizes"""
        super().resizeEvent(event)
        # Update all catalog tabs when window is resized
        if hasattr(self, 'tab_widget') and self.tab_widget is not None:
            for i in range(self.tab_widget.count()):
                tab = self.tab_widget.widget(i)
                if hasattr(tab, 'layout'):
                    # Force layout update
                    tab.layout().update()

# Main application entry point
def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for a modern look
    
    # Set application-wide stylesheet
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f8f9fa;
        }
        QWidget {
            font-family: 'Segoe UI', Arial, sans-serif;
        }
    """)
    
    window = SignLanguageLibrary()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()