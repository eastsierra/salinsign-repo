"""
User Guide module -- a 17-slide walkthrough of the application.
"""

import logging
import sys
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QCursor, QFont

import config

log = logging.getLogger(__name__)


class UserGuideModule(QMainWindow):
    """Full-screen slideshow with previous / next navigation."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SalinSign User Guide")
        self.setGeometry(0, 0, *config.WINDOW_SIZE)
        self.setMinimumSize(*config.WINDOW_MIN_SIZE)
        self.setStyleSheet("background-color:white;")

        self.current_slide = 1
        self.total_slides = config.TOTAL_SLIDES

        try:
            self._setup_ui()
            self.resizeEvent = self._handle_resize
        except Exception:
            log.exception("Error initializing UserGuide")
            self._create_error_ui("Failed to load the User Guide")

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        cw = QWidget()
        self.setCentralWidget(cw)
        self.main_layout = QVBoxLayout(cw)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        back_row = QHBoxLayout()
        back_row.setContentsMargins(0, 0, 0, 0)
        self.back_label = QLabel()
        self.back_label.setPixmap(
            QPixmap(config.asset("backbutton.png")).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        self.back_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.back_label.mousePressEvent = self._go_back
        back_row.addWidget(self.back_label, alignment=Qt.AlignLeft)
        back_row.addStretch()
        self.main_layout.addLayout(back_row)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 10)
        self.header_image = QLabel()
        self.header_image.setPixmap(
            QPixmap(os.path.join(config.USER_GUIDE_ASSETS_DIR, "userguideicon.png")).scaledToWidth(
                400, Qt.SmoothTransformation
            )
        )
        self.header_image.setAlignment(Qt.AlignCenter)
        header_row.addStretch(1)
        header_row.addWidget(self.header_image, alignment=Qt.AlignCenter)
        header_row.addStretch(1)
        self.main_layout.addLayout(header_row)

        self.slide_image = QLabel()
        self.slide_image.setAlignment(Qt.AlignCenter)
        self.slide_image.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.slide_image.setStyleSheet("background-color:white;")
        self.main_layout.addWidget(self.slide_image)

        nav_row = QHBoxLayout()
        self.prev_label = QLabel()
        self.prev_label.setPixmap(
            QPixmap(os.path.join(config.USER_GUIDE_ASSETS_DIR, "back.png")).scaled(
                60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )
        self.prev_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.prev_label.mousePressEvent = self._prev_slide

        self.next_label = QLabel()
        self.next_label.setPixmap(
            QPixmap(os.path.join(config.USER_GUIDE_ASSETS_DIR, "forward.png")).scaled(
                60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )
        self.next_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.next_label.mousePressEvent = self._next_slide

        nav_row.addStretch(1)
        nav_row.addWidget(self.prev_label)
        nav_row.addSpacing(40)
        nav_row.addWidget(self.next_label)
        nav_row.addStretch(1)
        self.main_layout.addLayout(nav_row)

        self._update_slide()

    def _create_error_ui(self, message: str) -> None:
        cw = QWidget()
        self.setCentralWidget(cw)
        lo = QVBoxLayout(cw)
        lo.addWidget(QLabel(f"An error occurred: {message}"))
        btn = QPushButton("Return to Main Menu")
        btn.clicked.connect(lambda: self._go_back(None))
        lo.addWidget(btn)

    # ------------------------------------------------------------------
    # Slide logic
    # ------------------------------------------------------------------

    def _update_slide(self) -> None:
        path = os.path.join(config.USER_GUIDE_ASSETS_DIR, f"{self.current_slide}.png")
        w = self.width()
        h = self.height() - 200
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.slide_image.setPixmap(pixmap.scaled(w - 40, h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.slide_image.setText(f"Could not load: {path}")

        self.prev_label.setEnabled(self.current_slide > 1)
        self.next_label.setEnabled(self.current_slide < self.total_slides)
        self.prev_label.setStyleSheet("opacity:0.5;" if self.current_slide == 1 else "opacity:1;")
        self.next_label.setStyleSheet("opacity:0.5;" if self.current_slide == self.total_slides else "opacity:1;")

    def _next_slide(self, _event) -> None:
        if self.current_slide < self.total_slides:
            self.current_slide += 1
            self._update_slide()

    def _prev_slide(self, _event) -> None:
        if self.current_slide > 1:
            self.current_slide -= 1
            self._update_slide()

    # ------------------------------------------------------------------
    # Resize
    # ------------------------------------------------------------------

    def _handle_resize(self, event) -> None:
        w = event.size().width()
        scale = min(w / config.REFERENCE_WIDTH, 1.0)
        logo_scale = scale * 0.8

        self.header_image.setPixmap(
            QPixmap(os.path.join(config.USER_GUIDE_ASSETS_DIR, "userguideicon.png")).scaledToWidth(
                int(400 * logo_scale), Qt.SmoothTransformation
            )
        )
        self.back_label.setPixmap(
            QPixmap(config.asset("backbutton.png")).scaled(
                int(40 * scale), int(40 * scale), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )
        nav_size = int(60 * scale)
        self.prev_label.setPixmap(
            QPixmap(os.path.join(config.USER_GUIDE_ASSETS_DIR, "back.png")).scaled(
                nav_size, nav_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )
        self.next_label.setPixmap(
            QPixmap(os.path.join(config.USER_GUIDE_ASSETS_DIR, "forward.png")).scaled(
                nav_size, nav_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )
        self._update_slide()

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _go_back(self, _event) -> None:
        try:
            from ui.navigation import NavigationManager
            self.close()
            NavigationManager.instance().go_to_main_menu()
        except Exception:
            log.exception("Error navigating back")
            self.close()

    def closeEvent(self, event) -> None:
        event.accept()


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    app = QApplication(sys.argv)
    win = UserGuideModule()
    win.showFullScreen()
    sys.exit(app.exec_())
