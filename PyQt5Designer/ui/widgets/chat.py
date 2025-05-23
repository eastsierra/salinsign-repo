"""
Chat widgets: ChatBubble and MessageItem used in the Translation module.
"""

from PyQt5.QtWidgets import (
    QApplication, QLabel, QWidget, QHBoxLayout, QVBoxLayout, QSizePolicy, QLayout,
)
from PyQt5.QtCore import Qt, QTime, QRect
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor

import config


class ChatBubble(QLabel):
    """A single chat-message bubble with dynamic sizing."""

    def __init__(self, message: str, user_type: str = "Patient", parent=None):
        super().__init__(parent)
        self.original_message = message
        self.setTextFormat(Qt.RichText)

        is_medical = all(k in message for k in ("Symptoms:", "Diagnosis:", "Prescription:"))

        if is_medical:
            html = message.replace("\n", "<br>")
            display = (
                "<div style='white-space:pre-wrap;word-wrap:break-word;"
                "word-break:normal;line-height:130%;text-align:left;"
                f"display:inline-block;'>{html}</div>"
            )
        else:
            html = " ".join(message.split()).replace("\n", "<br>")
            display = (
                "<div style='white-space:normal;word-wrap:break-word;"
                "word-break:normal;line-height:130%;text-align:left;"
                f"display:inline-block;'>{html}</div>"
            )

        self.setText(display)
        self.setFont(QFont("Arial", 14))
        self._compute_size(message)

        bg = config.CHAT_COLORS["patient_bg"] if user_type == "Patient" else config.CHAT_COLORS["doctor_bg"]
        fg = config.CHAT_COLORS["text"]
        self.setStyleSheet(
            f"QLabel{{background-color:{bg};color:{fg};"
            "border-radius:15px;padding:8px 10px;margin:2px;}}"
        )
        self.setAlignment(Qt.AlignLeft if user_type == "Doctor" else Qt.AlignRight)
        self.setWordWrap(True)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

    def _compute_size(self, message: str):
        fm = self.fontMetrics()
        words = message.split()
        word_count = len(words)
        screen_w = QApplication.desktop().screenGeometry().width()
        max_avail = min(screen_w * 0.8, 800)

        if word_count <= 3:
            text_w = fm.horizontalAdvance(message)
            pad = fm.averageCharWidth() * 2
            min_w = text_w + pad
            max_w = min_w * 1.1
        elif word_count <= 15:
            text_w = fm.horizontalAdvance(message)
            min_w = text_w * 0.9
            max_w = min(text_w * 1.2, max_avail * 0.6)
        else:
            avg_cw = sum(len(w) for w in words) / word_count
            ideal = min(60, avg_cw * 8)
            min_w = fm.averageCharWidth() * ideal
            max_w = max_avail if word_count > 30 else min(max_avail * 0.75, fm.averageCharWidth() * ideal * 1.5)

        min_w = max(50, min_w)
        max_w = max(min_w * 1.1, max_w)
        self.setMinimumWidth(int(min_w))
        self.setMaximumWidth(int(max_w))
        self.adjustSize()


class MessageItem(QWidget):
    """A full message row: avatar + bubble + timestamp."""

    def __init__(self, message: str, user_type: str = "Patient", parent=None):
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(10, 5, 10, 5)
        self._layout.setSpacing(12)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.avatar = self._build_avatar(user_type)
        self.message_container = QWidget()
        self.message_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        msg_layout = QVBoxLayout(self.message_container)
        msg_layout.setContentsMargins(0, 0, 0, 0)
        msg_layout.setSpacing(2)
        msg_layout.setSizeConstraint(QLayout.SetMinAndMaxSize)

        label_color = config.CHAT_COLORS["patient_bg"] if user_type == "Patient" else config.CHAT_COLORS["doctor_bg"]
        self.sender_label = QLabel(user_type)
        self.sender_label.setStyleSheet(f"color:{label_color};font-weight:bold;font-size:12px;")
        msg_layout.addWidget(self.sender_label)

        self.bubble = ChatBubble(message, user_type)
        msg_layout.addWidget(self.bubble)

        self.time_label = QLabel(QTime.currentTime().toString("hh:mm"))
        self.time_label.setStyleSheet("color:#888888;font-size:10px;")
        self.time_label.setAlignment(Qt.AlignRight if user_type == "Doctor" else Qt.AlignLeft)
        msg_layout.addWidget(self.time_label)

        if user_type == "Patient":
            self._layout.addWidget(self.avatar)
            self._layout.addWidget(self.message_container)
            self._layout.addStretch()
        else:
            self._layout.addStretch()
            self._layout.addWidget(self.message_container)
            self._layout.addWidget(self.avatar)

    def _build_avatar(self, user_type: str) -> QLabel:
        label = QLabel()
        avatar_px = QPixmap(50, 50)
        avatar_px.fill(Qt.transparent)

        image_path = config.asset(f"{user_type.lower()}.png")
        try:
            src = QPixmap(image_path)
            painter = QPainter(avatar_px)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Qt.NoPen)
            painter.setBrush(Qt.white)
            painter.drawEllipse(0, 0, 50, 50)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)

            sw, sh = src.width(), src.height()
            side = min(sw, sh)
            sx = (sw - side) // 2
            sy = (sh - side) // 2
            painter.drawPixmap(QRect(0, 0, 50, 50), src, QRect(sx, sy, side, side))
            painter.end()
        except Exception:
            color = config.CHAT_COLORS["patient_bg"] if user_type == "Patient" else config.CHAT_COLORS["doctor_bg"]
            painter = QPainter(avatar_px)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, 50, 50)
            painter.setPen(Qt.white)
            painter.setFont(QFont("Arial", 20, QFont.Bold))
            painter.drawText(avatar_px.rect(), Qt.AlignCenter, user_type[0])
            painter.end()

        label.setPixmap(avatar_px)
        label.setFixedSize(50, 50)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("QLabel{background-color:transparent;border:none;border-radius:25px;padding:0px;}")
        return label
