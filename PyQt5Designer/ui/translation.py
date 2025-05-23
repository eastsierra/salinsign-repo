"""
Translation module – real-time sign language recognition with chat interface.

Combines a live camera feed with ML inference, a patient/doctor chat panel,
sign-language image display, and a medical summary composer.
"""

import gc
import os

import wordninja
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QScrollArea, QSizePolicy,
    QFrame, QCheckBox, QComboBox, QCompleter, QDialog,
)
from PyQt5.QtCore import Qt, QSize, QTimer, QTime
from PyQt5.QtGui import QPixmap, QCursor, QFont, QImage

import config
from core.camera import get_available_cameras
from core.inference import SignLanguageThread
from ui.widgets.chat import MessageItem
from ui.widgets.popups import PopupWindow, MedicalSummaryTemplate


class TranslationModule(QMainWindow):
    """Full-screen translation interface: camera + chat + sign display."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SalinSign Translation Module")
        self.setGeometry(0, 0, *config.WINDOW_SIZE)
        self.setMinimumSize(*config.WINDOW_MIN_SIZE)
        self.setStyleSheet("background-color:white;")

        self.preloaded = False
        self.messages: list[dict] = []
        self.text_mode = True
        self.edit_mode = False
        self.current_camera_id = 0
        self.camera_switching = False
        self._navigating = False

        self.available_cameras = get_available_cameras()
        self._setup_ui()
        self._load_stylesheet()

        self.sign_language_thread: SignLanguageThread | None = None
        self.video_thread = None
        self.resizeEvent = self._handle_resize

        self.last_recognized_sign = None
        self.sign_buffer = ""
        self.last_sign_time = 0
        self.current_sign = None
        self.sign_start_time = 0
        self.accumulated_chars = ""

        self.translation_timer = QTimer()
        self.translation_timer.setSingleShot(True)
        self.translation_timer.timeout.connect(self._move_translation_to_chat)
        self.last_gesture_time = 0

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self):
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setCentralWidget(self.scroll_area)

        self.scroll_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_widget)
        self.main_layout = QVBoxLayout(self.scroll_widget)
        self.main_layout.setContentsMargins(20, 5, 20, 20)
        self.main_layout.setSpacing(5)

        self._build_header()
        self._build_boxes()

    def _build_header(self):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)

        self.back_label = QLabel()
        self.back_label.setPixmap(
            QPixmap(config.asset("backbutton.png")).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        self.back_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.back_label.mousePressEvent = self._go_back
        row.addWidget(self.back_label, alignment=Qt.AlignLeft)
        row.addStretch()

        self.tooltip_label = QLabel()
        self.tooltip_label.setPixmap(
            QPixmap(config.asset("tooltip.png")).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        self.tooltip_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.tooltip_label.mousePressEvent = self._show_tooltip
        row.addWidget(self.tooltip_label, alignment=Qt.AlignRight)
        self.main_layout.addLayout(row)

        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 0, 0, 0)
        self.header_image = QLabel()
        self.header_image.setPixmap(
            QPixmap(config.asset("Translation.png")).scaledToWidth(600, Qt.SmoothTransformation)
        )
        self.header_image.setAlignment(Qt.AlignCenter)
        self.header_image.setStyleSheet("QLabel{padding:0;margin:0;}")
        hdr.addWidget(self.header_image, alignment=Qt.AlignCenter)
        self.main_layout.addLayout(hdr)
        self.main_layout.addSpacing(5)

    def _build_boxes(self):
        self.container = QHBoxLayout()
        self.container.setSpacing(20)

        # --- Box 1: Video + Translation ---
        self.box1 = QFrame()
        self.box1.setObjectName("box1")
        self.box1_layout = QVBoxLayout(self.box1)
        self.box1_layout.setContentsMargins(20, 20, 20, 20)
        self.box1_layout.setSpacing(15)

        self.stream_header = QLabel()
        self.stream_header.setPixmap(QPixmap(config.asset("Stream.png")).scaledToWidth(300, Qt.SmoothTransformation))
        self.stream_header.setAlignment(Qt.AlignCenter)
        self.box1_layout.addWidget(self.stream_header)

        cam_row = QHBoxLayout()
        cam_row.setContentsMargins(0, 0, 0, 0)
        cam_row.setSpacing(10)
        cam_lbl = QLabel("Camera Source:")
        cam_lbl.setStyleSheet("QLabel{font-size:14px;font-weight:bold;color:#333;}")
        cam_row.addWidget(cam_lbl)

        self.camera_dropdown = QComboBox()
        self.camera_dropdown.setStyleSheet(
            "QComboBox{padding:5px;border:1px solid #ccc;border-radius:3px;"
            "background-color:white;min-height:25px;font-size:14px;}"
            "QComboBox::drop-down{width:20px;border-left:1px solid #ccc;}"
        )
        for cam in self.available_cameras:
            self.camera_dropdown.addItem(cam["name"], cam["id"])
        self.camera_dropdown.currentIndexChanged.connect(self._camera_selected)
        cam_row.addWidget(self.camera_dropdown)
        self.box1_layout.addLayout(cam_row)

        self.video_placeholder = QLabel("Loading Video Stream...")
        self.video_placeholder.setObjectName("videoPlaceholder")
        self.video_placeholder.setAlignment(Qt.AlignCenter)
        self.video_placeholder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.box1_layout.addWidget(self.video_placeholder)

        # Edit mode
        em_row = QHBoxLayout()
        em_row.setContentsMargins(0, 0, 0, 0)
        self.edit_mode_toggle = QCheckBox("Edit Mode")
        self.edit_mode_toggle.setChecked(False)
        self.edit_mode_toggle.setCursor(QCursor(Qt.PointingHandCursor))
        self.edit_mode_toggle.stateChanged.connect(self._toggle_edit_mode)
        self.edit_mode_toggle.setStyleSheet(
            "QCheckBox{font-size:14px;font-weight:bold;color:#333;spacing:5px;}"
            "QCheckBox::indicator{width:20px;height:20px;}"
            "QCheckBox::indicator:unchecked{background-color:#f0f0f0;border:2px solid #ccc;border-radius:3px;}"
            "QCheckBox::indicator:checked{background-color:#4CAF50;border:2px solid #45a049;border-radius:3px;}"
        )
        em_lbl = QLabel("(Enable to edit translations before sending)")
        em_lbl.setStyleSheet("font-size:12px;color:#666;")
        em_row.addWidget(self.edit_mode_toggle)
        em_row.addWidget(em_lbl)
        em_row.addStretch()
        self.box1_layout.addLayout(em_row)

        # Translation box + send
        tx_row = QHBoxLayout()
        self.translation_box = QLineEdit()
        self.translation_box.setReadOnly(True)
        self.translation_box.setObjectName("translationBox")
        self.translation_box.setPlaceholderText("Translations will appear here...")
        self.translation_box.setStyleSheet(
            "QLineEdit{background-color:white;border:1px solid #ddd;"
            "border-radius:5px;padding:10px;font-size:14px;min-height:40px;}"
        )
        tx_row.addWidget(self.translation_box)

        self.translation_send_button = QPushButton("Send")
        self.translation_send_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.translation_send_button.clicked.connect(self._send_translation)
        self.translation_send_button.setStyleSheet(
            "QPushButton{padding:10px 15px;background-color:#4CAF50;color:white;"
            "border:none;border-radius:5px;font-size:14px;font-weight:bold;min-height:40px;}"
            "QPushButton:hover{background-color:#45a049;}"
        )
        self.translation_send_button.hide()
        tx_row.addWidget(self.translation_send_button)
        self.box1_layout.addLayout(tx_row)
        self.container.addWidget(self.box1)

        # --- Box 2: Chat + Sign Display ---
        self.box2 = QFrame()
        self.box2.setObjectName("box2")
        self.box2_layout = QVBoxLayout(self.box2)
        self.box2_layout.setContentsMargins(20, 20, 20, 20)
        self.box2_layout.setSpacing(15)

        self.chat_header = QLabel()
        self.chat_header.setPixmap(QPixmap(config.asset("Chatbox.png")).scaledToWidth(200, Qt.SmoothTransformation))
        self.chat_header.setAlignment(Qt.AlignCenter)
        self.box2_layout.addWidget(self.chat_header)

        # Chat area
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setSpacing(5)
        self.chat_layout.setContentsMargins(5, 10, 5, 10)
        self.chat_layout.addStretch()

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setWidget(self.chat_container)
        self.chat_scroll.setObjectName("chatBox")
        self.chat_scroll.setStyleSheet(
            "QScrollArea{background-color:white;border:1px solid #ddd;"
            "border-radius:5px;padding:5px;min-height:300px;}"
            "QScrollBar:vertical{border:none;background:#f1f1f1;width:8px;border-radius:4px;}"
            "QScrollBar::handle:vertical{background:#888;min-height:20px;border-radius:4px;}"
            "QScrollBar::handle:vertical:hover{background:#555;}"
            "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}"
            "QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{background:none;}"
        )
        self.box2_layout.addWidget(self.chat_scroll)

        # Sign display (hidden by default)
        self.sign_display_scroll = QScrollArea()
        self.sign_display_scroll.setWidgetResizable(True)
        self.sign_display_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sign_display_scroll.setStyleSheet(
            "QScrollArea{background-color:white;border:1px solid #ddd;border-radius:5px;}"
            "QScrollBar:vertical{border:none;background:#f1f1f1;width:8px;border-radius:4px;}"
            "QScrollBar::handle:vertical{background:#888;min-height:20px;border-radius:4px;}"
            "QScrollBar::handle:vertical:hover{background:#555;}"
            "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}"
            "QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{background:none;}"
        )
        self.sign_display = QWidget()
        self.sign_display.setObjectName("signDisplay")
        self.sign_display.setStyleSheet("QWidget{background-color:white;padding:5px;}")
        self.sign_display_layout = QVBoxLayout(self.sign_display)
        self.sign_display_layout.setSpacing(5)
        self.sign_display_layout.setContentsMargins(5, 5, 5, 5)
        self.sign_display_scroll.setWidget(self.sign_display)
        self.sign_display_scroll.setMinimumHeight(250)
        self.sign_display_scroll.hide()
        self.box2_layout.addWidget(self.sign_display_scroll)

        # Predefined phrases
        self._build_phrase_bar()

        # Doctor input row
        input_row = QHBoxLayout()
        self.input_user2 = QLineEdit()
        self.input_user2.setPlaceholderText("Doctor Type here...")
        self.input_user2.returnPressed.connect(lambda: self.send_message("Doctor", self.input_user2.text()))
        self._setup_predictive_text()

        self.send_button2 = QPushButton("Send")
        self.send_button2.setCursor(QCursor(Qt.PointingHandCursor))
        self.send_button2.clicked.connect(lambda: self.send_message("Doctor", self.input_user2.text()))

        self.display_mode_toggle = QCheckBox("Text Mode")
        self.display_mode_toggle.setChecked(True)
        self.display_mode_toggle.setCursor(QCursor(Qt.PointingHandCursor))
        self.display_mode_toggle.stateChanged.connect(self._toggle_display_mode)
        self.display_mode_toggle.setStyleSheet(
            "QCheckBox{font-size:14px;font-weight:bold;color:#333;spacing:5px;}"
            "QCheckBox::indicator{width:20px;height:20px;}"
            "QCheckBox::indicator:unchecked{background-color:#f0f0f0;border:2px solid #ccc;border-radius:3px;}"
            "QCheckBox::indicator:checked{background-color:#4CAF50;border:2px solid #45a049;border-radius:3px;}"
        )

        self.medical_summary_button = QPushButton("Medical Summary")
        self.medical_summary_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.medical_summary_button.clicked.connect(self._show_medical_summary)
        self.medical_summary_button.setStyleSheet(
            "QPushButton{padding:10px 20px;background-color:#2196F3;color:white;"
            "border:none;border-radius:5px;font-size:14px;font-weight:bold;min-width:80px;}"
            "QPushButton:hover{background-color:#0b7dda;}"
        )

        self.clear_chat_button = QPushButton("Clear Chat")
        self.clear_chat_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.clear_chat_button.clicked.connect(self._clear_chat)
        self.clear_chat_button.setStyleSheet(
            "QPushButton{padding:10px 20px;background-color:#ff4444;color:white;"
            "border:none;border-radius:5px;font-size:14px;font-weight:bold;min-width:80px;}"
            "QPushButton:hover{background-color:#ff6666;}"
        )

        input_row.addWidget(self.input_user2)
        input_row.addWidget(self.send_button2)
        input_row.addWidget(self.display_mode_toggle)
        input_row.addWidget(self.medical_summary_button)
        input_row.addWidget(self.clear_chat_button)
        self.box2_layout.addLayout(input_row)

        self.container.addWidget(self.box2)
        self.main_layout.addLayout(self.container)

    def _build_phrase_bar(self):
        phrases_widget = QWidget()
        phrases_widget.setObjectName("phrasesContainer")
        fl = QHBoxLayout(phrases_widget)
        fl.setSpacing(8)
        fl.setContentsMargins(0, 8, 0, 8)

        for phrase in config.DOCTOR_QUICK_PHRASES:
            btn = QPushButton(phrase)
            btn.setStyleSheet(
                "QPushButton{padding:8px 12px;background-color:#e8f5ff;color:#2a70a5;"
                "border:none;border-radius:12px;font-size:12px;font-weight:500;"
                "min-height:24px;text-align:center;}"
                "QPushButton:hover{background-color:#cce7ff;color:#0058a5;}"
            )
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.clicked.connect(lambda _=False, t=phrase: self.send_message("Doctor", t))
            fl.addWidget(btn)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(phrases_widget)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setMaximumHeight(60)
        scroll.setMinimumHeight(60)
        scroll.setStyleSheet(
            "QScrollArea{background-color:#f5f5f5;border:1px solid #ddd;border-radius:10px;padding:0;}"
            "QScrollBar:horizontal{height:6px;background:transparent;border-radius:3px;}"
            "QScrollBar::handle:horizontal{background-color:rgba(128,128,128,0.2);min-width:40px;border-radius:3px;}"
            "QScrollBar::handle:horizontal:hover{background-color:rgba(128,128,128,0.5);}"
            "QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal,"
            "QScrollBar::add-page:horizontal,QScrollBar::sub-page:horizontal"
            "{background:transparent;width:0;height:0;}"
        )
        phrases_widget.setStyleSheet("QWidget#phrasesContainer{background-color:#f5f5f5;border-radius:9px;}")
        phrases_widget.setMaximumHeight(60)

        pl = QVBoxLayout()
        pl.setContentsMargins(0, 0, 0, 5)
        pl.setSpacing(5)
        pl.addWidget(scroll)
        self.box2_layout.addLayout(pl)

    def _setup_predictive_text(self):
        self.completer = QCompleter(config.DOCTOR_AUTOCOMPLETE_PHRASES)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setFilterMode(Qt.MatchStartsWith)
        self.input_user2.setCompleter(self.completer)
        self.input_user2.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.input_user2 and event.type() == event.KeyPress:
            if event.key() == Qt.Key_Tab and self.completer.popup() and self.completer.popup().isVisible():
                self.completer.activated.emit(self.completer.currentCompletion())
                return True
        return super().eventFilter(obj, event)

    # ------------------------------------------------------------------
    # Stylesheet
    # ------------------------------------------------------------------

    def _load_stylesheet(self):
        if os.path.exists(config.STYLESHEET_PATH):
            with open(config.STYLESHEET_PATH, "r") as f:
                self.setStyleSheet(f.read())
        else:
            self._apply_basic_styles()

    def _apply_basic_styles(self):
        self.setStyleSheet(
            "QWidget{font-family:Arial,sans-serif;}"
            "#box1,#box2{background-color:#f5f5f5;border-radius:10px;border:1px solid #ddd;}"
            "QLineEdit{padding:10px;border-radius:5px;border:1px solid #ccc;font-size:14px;}"
            "QPushButton{padding:10px 20px;background-color:#4CAF50;color:white;"
            "border:none;border-radius:5px;font-size:14px;font-weight:bold;}"
            "#videoPlaceholder{background-color:#000;color:#fff;min-height:300px;}"
            "#chatBox{background-color:white;border:1px solid #ddd;border-radius:5px;"
            "padding:10px;font-size:14px;}"
        )

    # ------------------------------------------------------------------
    # Edit mode / translation controls
    # ------------------------------------------------------------------

    def _toggle_edit_mode(self, state):
        self.edit_mode = bool(state)
        if self.edit_mode:
            self.translation_box.setReadOnly(False)
            self.translation_box.setStyleSheet(
                "QLineEdit{background-color:white;border:1px solid #4CAF50;"
                "border-radius:5px;padding:10px;font-size:14px;min-height:40px;}"
            )
            self.translation_send_button.show()
            if self.translation_timer.isActive():
                self.translation_timer.stop()
        else:
            self.translation_box.setReadOnly(True)
            self.translation_box.setStyleSheet(
                "QLineEdit{background-color:white;border:1px solid #ddd;"
                "border-radius:5px;padding:10px;font-size:14px;min-height:40px;}"
            )
            self.translation_send_button.hide()

    def _send_translation(self):
        text = self.translation_box.text()
        if text:
            self.send_message("Patient", text)
            self.translation_box.clear()
            self.accumulated_chars = ""
            self._clear_sign_display()

    # ------------------------------------------------------------------
    # Chat
    # ------------------------------------------------------------------

    def send_message(self, user: str, message: str):
        if not message.strip():
            return
        self.messages.append({"user": user, "text": message})
        if self.text_mode:
            self._add_message_widget(user, message)
            QTimer.singleShot(100, lambda: self.chat_scroll.verticalScrollBar().setValue(
                self.chat_scroll.verticalScrollBar().maximum()
            ))
        if user == "Doctor":
            if not self.text_mode:
                self._clear_sign_display()
                imgs = []
                for word in message.split():
                    imgs.extend(self._text_to_sign_images(word))
                    imgs.append(None)
                self._display_sign_images(imgs)
            self.input_user2.clear()

    def _add_message_widget(self, user: str, message: str):
        show_sender = True
        if len(self.messages) > 1 and self.messages[-2]["user"] == user:
            show_sender = False

        item = MessageItem(message, user, self.chat_container)
        if not show_sender:
            item.sender_label.hide()

        if len(self.messages) > 1 and self.messages[-2]["user"] != user:
            spacer = QWidget()
            spacer.setFixedHeight(15)
            self.chat_layout.insertWidget(self.chat_layout.count() - 1, spacer)

        item.bubble.adjustSize()
        item.updateGeometry()
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, item)
        QApplication.processEvents()

    def _clear_chat(self):
        self.messages.clear()
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._clear_sign_display()
        self.translation_box.clear()
        self.accumulated_chars = ""

    def _refresh_chat_widgets(self):
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for msg in self.messages:
            self._add_message_widget(msg["user"], msg["text"])
        QTimer.singleShot(100, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        ))

    # ------------------------------------------------------------------
    # Sign-image display
    # ------------------------------------------------------------------

    def _text_to_sign_images(self, text: str) -> list[str]:
        images = []
        for ch in text.upper():
            if ch.isalpha() or ch.isdigit():
                path = os.path.join(config.SIGN_IMAGES_DIR, f"{ch}.png")
                if os.path.exists(path):
                    images.append(path)
        return images

    def _clear_sign_display(self):
        while self.sign_display_layout.count():
            item = self.sign_display_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()
                QWidget().setLayout(item.layout())

    def _display_sign_images(self, paths: list):
        if not paths:
            self._clear_sign_display()
            return
        self._clear_sign_display()

        max_row_w = self.sign_display.width() - 30
        default_sz = 120
        min_sz = 50

        words: list[list[str]] = []
        cur: list[str] = []
        for p in paths:
            if p is None:
                if cur:
                    words.append(cur)
                    cur = []
            else:
                cur.append(p)
        if cur:
            words.append(cur)

        row_layout = QHBoxLayout()
        row_layout.setSpacing(5)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setAlignment(Qt.AlignLeft)
        row_w = 0

        for word_imgs in words:
            sz = default_sz
            word_w = len(word_imgs) * (sz + 5) - 5
            if word_w > max_row_w:
                sz = max(min_sz, int((max_row_w - (len(word_imgs) - 1) * 5) / len(word_imgs)))

            scaled_w = len(word_imgs) * (sz + 5) - 5
            if row_w + scaled_w > max_row_w and row_layout.count() > 0:
                self.sign_display_layout.addLayout(row_layout)
                row_layout = QHBoxLayout()
                row_layout.setSpacing(5)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setAlignment(Qt.AlignLeft)
                row_w = 0

            for ip in word_imgs:
                lbl = QLabel()
                px = QPixmap(ip)
                if px.isNull():
                    continue
                lbl.setPixmap(px.scaled(sz, sz, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setFixedSize(sz, sz)
                row_layout.addWidget(lbl)
                row_w += sz + 5

            spacer = QLabel()
            spacer.setFixedSize(10, sz)
            row_layout.addWidget(spacer)
            row_w += 10

        if row_layout.count() > 0:
            self.sign_display_layout.addLayout(row_layout)
        self.sign_display_layout.addStretch()

    def _toggle_display_mode(self, state):
        self.text_mode = bool(state)
        self.display_mode_toggle.setText("Text Mode" if self.text_mode else "Sign Mode")
        if self.text_mode:
            self.chat_scroll.show()
            self.sign_display_scroll.hide()
            self._refresh_chat_widgets()
        else:
            self.chat_scroll.hide()
            self.sign_display_scroll.show()
            self.sign_display_scroll.setWidgetResizable(True)
            self.sign_display.setMinimumWidth(self.box2.width() - 50)
            self._update_sign_display_all()

    def _update_sign_display_all(self):
        self._clear_sign_display()
        doctor_msgs = [m["text"] for m in self.messages if m["user"] == "Doctor"]
        if doctor_msgs:
            all_imgs = []
            for msg in doctor_msgs:
                for word in msg.split():
                    all_imgs.extend(self._text_to_sign_images(word))
                    all_imgs.append(None)
            self.sign_display.updateGeometry()
            QApplication.processEvents()
            self._display_sign_images(all_imgs)

    # ------------------------------------------------------------------
    # Resize
    # ------------------------------------------------------------------

    def _handle_resize(self, event):
        w, h = event.size().width(), event.size().height()

        if w >= 1920 and h >= 1080:
            self.container.setDirection(QHBoxLayout.LeftToRight)
            self.box1.setMinimumWidth(0)
            self.box2.setMinimumWidth(0)
            return

        if w < 768:
            self.container.setDirection(QVBoxLayout.TopToBottom)
            self.box1.setMinimumWidth(w - 40)
            self.box2.setMinimumWidth(w - 40)
            self.main_layout.setContentsMargins(10, 10, 10, 10)
            self.box1_layout.setContentsMargins(10, 10, 10, 10)
            self.box2_layout.setContentsMargins(10, 10, 10, 10)
        else:
            self.container.setDirection(QHBoxLayout.LeftToRight)
            self.box1.setMinimumWidth(0)
            self.box2.setMinimumWidth(0)
            self.main_layout.setContentsMargins(20, 20, 20, 20)
            self.box1_layout.setContentsMargins(20, 20, 20, 20)
            self.box2_layout.setContentsMargins(20, 20, 20, 20)

        scale = min(w / 1920, 1.0)
        logo_s = scale * 0.6
        self.header_image.setPixmap(
            QPixmap(config.asset("Translation.png")).scaledToWidth(int(600 * logo_s), Qt.SmoothTransformation)
        )
        self.stream_header.setPixmap(
            QPixmap(config.asset("Stream.png")).scaledToWidth(int(300 * scale), Qt.SmoothTransformation)
        )
        self.chat_header.setPixmap(
            QPixmap(config.asset("Chatbox.png")).scaledToWidth(int(235 * scale), Qt.SmoothTransformation)
        )

        fs = max(12, int(14 * scale))
        self.input_user2.setStyleSheet(f"font-size:{fs}px;")
        self.chat_scroll.setStyleSheet(
            f"QScrollArea{{background-color:white;border:1px solid #ddd;"
            f"border-radius:5px;padding:5px;min-height:300px;font-size:{fs}px;}}"
            "QScrollBar:vertical{border:none;background:#f1f1f1;width:8px;border-radius:4px;}"
            "QScrollBar::handle:vertical{background:#888;min-height:20px;border-radius:4px;}"
            "QScrollBar::handle:vertical:hover{background:#555;}"
            "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}"
            "QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{background:none;}"
        )
        self.send_button2.setMinimumWidth(max(80, int(100 * scale)))
        vid_h = int(w * 0.75) if w < 768 else int(h * 0.4)
        self.video_placeholder.setMinimumHeight(vid_h)
        self.chat_scroll.setMinimumHeight(int(h * 0.4))

        if not self.text_mode:
            self.sign_display.setMinimumWidth(self.box2.width() - 50)
            self._update_sign_display_all()

    # ------------------------------------------------------------------
    # Video / inference
    # ------------------------------------------------------------------

    def _setup_video_stream(self):
        self.sign_language_thread = SignLanguageThread(self.current_camera_id)
        self.sign_language_thread.update_frame.connect(self._update_video_frame)
        self.sign_language_thread.update_text.connect(self._handle_recognized_sign)
        self.sign_language_thread.start()

    def _update_video_frame(self, image: QImage):
        scaled = image.scaled(self.video_placeholder.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_placeholder.setPixmap(QPixmap.fromImage(scaled))

    def _handle_recognized_sign(self, sign: str):
        now = QTime.currentTime().msecsSinceStartOfDay()
        self.last_gesture_time = now

        if sign != self.current_sign:
            self.current_sign = sign
            self.sign_start_time = now
            return

        if now - self.sign_start_time >= config.SIGN_HOLD_MS:
            if now - self.last_sign_time >= config.SIGN_INTERVAL_MS:
                self.accumulated_chars += sign
                self.translation_box.setText(self._segment_words(self.accumulated_chars))
                self.last_sign_time = now
                self.last_recognized_sign = sign
                if not self.edit_mode:
                    self.translation_timer.start(config.TRANSLATION_TIMEOUT_MS)

    def _move_translation_to_chat(self):
        if not self.edit_mode:
            text = self.translation_box.text()
            if text:
                self.send_message("Patient", text)
                self.translation_box.clear()
                self.accumulated_chars = ""
                self._clear_sign_display()

    @staticmethod
    def _segment_words(text: str) -> str:
        if not text:
            return ""
        words = wordninja.split(text.lower())
        result = []
        sentence_start = True
        for w in words:
            if sentence_start:
                w = w.capitalize()
                sentence_start = False
            result.append(w)
            if w.endswith((".", "!", "?")):
                sentence_start = True
        for i, w in enumerate(result):
            if w == "i":
                result[i] = "I"
        return " ".join(result)

    def _camera_selected(self, index: int):
        if index < 0 or index >= len(self.available_cameras) or self._navigating:
            return
        self.camera_switching = True
        try:
            new_id = self.available_cameras[index]["id"]
            self.current_camera_id = new_id
            if self.sign_language_thread is not None and self.sign_language_thread.isRunning():
                try:
                    self.sign_language_thread.set_camera(new_id)
                except Exception:
                    self.sign_language_thread.stop()
                    self.sign_language_thread.wait(2000)
                    self.sign_language_thread = None
                    QTimer.singleShot(500, self._setup_video_stream)
        finally:
            self.camera_switching = False

    # ------------------------------------------------------------------
    # Popups
    # ------------------------------------------------------------------

    def _show_tooltip(self, _event):
        PopupWindow(self, "first").exec_()

    def _show_medical_summary(self):
        dlg = MedicalSummaryTemplate(self)
        if dlg.exec_() == QDialog.Accepted and hasattr(dlg, "plain_summary"):
            self.send_message("Doctor", dlg.plain_summary)

    # ------------------------------------------------------------------
    # Navigation / lifecycle
    # ------------------------------------------------------------------

    def _go_back(self, _event):
        if self._navigating:
            return
        self._navigating = True
        self._stop_threads()
        self._clear_chat()
        gc.collect()
        try:
            from ui.navigation import NavigationManager
            self.close()
            NavigationManager.instance().go_to_main_menu()
        except Exception as e:
            print(f"Error navigating back: {e}")
            self.close()
        finally:
            self._navigating = False

    def _stop_threads(self):
        if hasattr(self, "translation_timer") and self.translation_timer.isActive():
            self.translation_timer.stop()

        for thread_attr in ("sign_language_thread", "video_thread"):
            thread = getattr(self, thread_attr, None)
            if thread is None:
                continue
            try:
                thread.update_frame.disconnect()
                thread.update_text.disconnect()
            except Exception:
                pass
            thread.running = False
            thread.stop()
            for _ in range(10):
                if not thread.isRunning():
                    break
                self._msleep(100)
            if thread.isRunning():
                thread.terminate()
            setattr(self, thread_attr, None)

    def _msleep(self, ms: int):
        deadline = QTime.currentTime().addMSecs(ms)
        while QTime.currentTime() < deadline:
            QApplication.processEvents(QApplication.ExclusiveUserInputEvents)

    def showEvent(self, event):
        super().showEvent(event)
        if not self.preloaded:
            QTimer.singleShot(100, self._setup_video_stream)
            self.video_placeholder.setText("Initializing camera...")
            self.video_placeholder.setStyleSheet(
                "QLabel{background-color:#000;color:#fff;font-size:18px;"
                "qproperty-alignment:AlignCenter;}"
            )
            QApplication.processEvents()

    def closeEvent(self, event):
        self._stop_threads()
        self.messages.clear()
        if hasattr(self, "translation_box"):
            self.translation_box.clear()
        if hasattr(self, "sign_display_layout"):
            self._clear_sign_display()
        gc.collect()
        event.accept()

    def hideEvent(self, event):
        if not self._navigating:
            self._stop_threads()
            gc.collect()
        super().hideEvent(event)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    app = QApplication(sys.argv)
    win = TranslationModule()
    win.showFullScreen()
    sys.exit(app.exec_())
