"""
Sign-library catalog widgets: item cards, detail dialog, and custom tab bar.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QGraphicsDropShadowEffect, QDialog, QTabBar,
)
from PyQt5.QtGui import QColor, QPainterPath, QPen, QPainter, QPixmap
from PyQt5.QtCore import Qt, QSize, QRectF, QPoint, QPropertyAnimation, QEasingCurve


class RoundedItemFrame(QFrame):
    """Frame with rounded corners for catalog cards."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.radius = 15
        self.setMinimumSize(180, 200)
        self.setMaximumSize(220, 240)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), self.radius, self.radius)
        painter.setClipPath(path)
        painter.fillRect(0, 0, self.width(), self.height(), self.palette().color(self.backgroundRole()))
        pen = QPen(QColor(0, 0, 0, 20))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawPath(path)


class CatalogItem(QWidget):
    """A clickable card representing a single sign in the library."""

    def __init__(self, title: str, image_path: str, color_scheme: dict, category: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.image_path = image_path
        self.color_scheme = color_scheme
        self.category = category
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.container = RoundedItemFrame()
        self.container.setStyleSheet(f"QFrame{{background-color:{self.color_scheme['item_bg']};border:none;}}")
        self.container.setAutoFillBackground(True)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 2)
        self.container.setGraphicsEffect(shadow)

        clayout = QVBoxLayout(self.container)
        clayout.setContentsMargins(10, 10, 10, 10)
        clayout.setSpacing(5)

        img_frame = QFrame()
        img_frame.setStyleSheet("QFrame{background-color:white;border-radius:12px;border:1px solid rgba(0,0,0,0.1);}")
        img_frame.setFixedSize(160, 160)

        self.image_label = QLabel()
        self.image_label.setFixedSize(150, 150)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("QLabel{background-color:transparent;border-radius:10px;}")

        pixmap = QPixmap(self.image_path)
        if not pixmap.isNull():
            self.image_label.setPixmap(pixmap.scaled(140, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.image_label.setText("Image not found")

        img_layout = QVBoxLayout(img_frame)
        img_layout.setContentsMargins(0, 0, 0, 0)
        img_layout.addWidget(self.image_label, 0, Qt.AlignCenter)

        self.title_label = QLabel(self.title)
        self.title_label.setFixedHeight(25)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(
            f"color:{self.color_scheme['text_color']};font-weight:bold;font-size:12px;"
        )

        clayout.addWidget(img_frame, 0, Qt.AlignCenter)
        clayout.addWidget(self.title_label)
        layout.addWidget(self.container)

        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(f"Click to view details of {self.title}")
        self.setStyleSheet(
            f"QWidget{{background-color:transparent;}}"
            f"QWidget:hover{{background-color:{self.color_scheme['item_hover']};border-radius:15px;}}"
        )

    def enterEvent(self, event):
        self.container.setGraphicsEffect(
            QGraphicsDropShadowEffect(blurRadius=20, color=QColor(0, 0, 0, 60), offset=QPoint(0, 3))
        )
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.container.setGraphicsEffect(
            QGraphicsDropShadowEffect(blurRadius=15, color=QColor(0, 0, 0, 40), offset=QPoint(0, 2))
        )
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            DetailDialog(self.title, self.image_path, self.color_scheme, self.category, self).exec_()


class DetailDialog(QDialog):
    """Enlarged view of a selected sign with category badge."""

    def __init__(self, title, image_path, color_scheme, category, parent=None):
        super().__init__(parent)
        self.color_scheme = color_scheme
        self.offset = None
        self.setWindowTitle(title)
        self.setMinimumSize(600, 500)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._setup_ui(title, image_path, category)

        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(250)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.start()

    def _setup_ui(self, title, image_path, category):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        main_frame = QFrame()
        main_frame.setStyleSheet(f"background-color:{self.color_scheme['primary']};border-radius:15px;")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        main_frame.setGraphicsEffect(shadow)

        ml = QVBoxLayout(main_frame)
        ml.setContentsMargins(15, 15, 15, 15)

        header = QHBoxLayout()
        badge = QLabel(category)
        badge.setStyleSheet(
            "background-color:rgba(255,255,255,0.3);color:white;"
            "font-size:14px;font-weight:bold;border-radius:10px;padding:3px 10px;"
        )
        badge.setFixedHeight(25)
        tlabel = QLabel(title)
        tlabel.setStyleSheet("color:white;font-size:24px;font-weight:bold;")
        close_btn = QPushButton("\u00d7")
        close_btn.setStyleSheet(
            "QPushButton{background-color:transparent;color:white;font-size:24px;"
            "font-weight:bold;border:none;padding:5px;}"
            "QPushButton:hover{background-color:rgba(255,255,255,0.2);border-radius:15px;}"
        )
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.close)
        header.addWidget(badge)
        header.addSpacing(10)
        header.addWidget(tlabel)
        header.addStretch()
        header.addWidget(close_btn)

        img_container = QFrame()
        img_container.setStyleSheet("background-color:white;border-radius:10px;")
        icl = QVBoxLayout(img_container)
        img_label = QLabel()
        img_label.setAlignment(Qt.AlignCenter)
        img_label.setMinimumSize(500, 350)
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            img_label.setPixmap(pixmap.scaled(500, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            img_label.setContentsMargins(10, 10, 10, 10)
        else:
            img_label.setText("Image not found")
            img_label.setStyleSheet("color:#333;font-size:16px;")
        icl.addWidget(img_label)

        desc = QLabel("Practice this sign by following the image.")
        desc.setStyleSheet("color:white;font-size:14px;")
        desc.setAlignment(Qt.AlignCenter)

        ml.addLayout(header)
        ml.addWidget(img_container, 1)
        ml.addWidget(desc)
        layout.addWidget(main_frame)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.offset = event.pos()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.offset is not None and event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.pos() - self.offset)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.offset = None
        super().mouseReleaseEvent(event)

    def close(self):
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(150)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.finished.connect(super().close)
        self.animation.start()


class CustomTabBar(QTabBar):
    """Tab bar with modern curved styling and per-tab colours."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab_colors: list[str] = []

    def set_tab_colors(self, colors: list[str]):
        self.tab_colors = colors
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        for i in range(self.count()):
            rect = self.tabRect(i)
            path = QPainterPath()
            r = 10
            path.moveTo(rect.left(), rect.bottom())
            path.lineTo(rect.left(), rect.top() + r)
            path.arcTo(rect.left(), rect.top(), r * 2, r * 2, 180, -90)
            path.lineTo(rect.right() - r, rect.top())
            path.arcTo(rect.right() - r * 2, rect.top(), r * 2, r * 2, 90, -90)
            path.lineTo(rect.right(), rect.bottom())
            path.lineTo(rect.left(), rect.bottom())

            if i == self.currentIndex() and i < len(self.tab_colors):
                painter.fillPath(path, QColor(self.tab_colors[i]))
            else:
                painter.fillPath(path, QColor("#F0F0F0"))

            if i == self.currentIndex():
                painter.setPen(QColor("#FFFFFF"))
            else:
                painter.setPen(QColor(self.tab_colors[i]) if i < len(self.tab_colors) else QColor("#333333"))

            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(rect.adjusted(10, 5, -10, -5), Qt.AlignCenter, self.tabText(i))
