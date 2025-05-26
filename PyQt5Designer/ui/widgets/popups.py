"""
Popup dialogs: onboarding tutorial flow and medical summary template.
"""

import logging

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QGroupBox, QFormLayout,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

import config

log = logging.getLogger(__name__)

_GREEN_BTN = (
    "QPushButton{background-color:%s;color:white;border:none;border-radius:5px;"
    "padding:10px 20px;font-size:14px;font-weight:bold;}"
    "QPushButton:hover{background-color:%s;}"
) % (config.POPUP_COLORS["green"], config.POPUP_COLORS["green_hover"])

_BLUE_BTN = (
    "QPushButton{background-color:%s;color:white;border:none;border-radius:5px;"
    "padding:10px 20px;font-size:14px;font-weight:bold;margin:0 10px;}"
    "QPushButton:hover{background-color:%s;}"
) % (config.POPUP_COLORS["blue"], config.POPUP_COLORS["blue_hover"])

_RED_BTN = (
    "QPushButton{background-color:%s;color:white;border:none;border-radius:5px;"
    "padding:10px 20px;font-size:14px;font-weight:bold;}"
    "QPushButton:hover{background-color:%s;}"
) % (config.POPUP_COLORS["red"], config.POPUP_COLORS["red_hover"])

_TUTORIAL_IMAGES = {
    "first":         config.asset("helpassets/both/welcomepopup.png"),
    "second":        config.asset("helpassets/both/beforepopup.png"),
    "final_shared":  config.asset("helpassets/both/seemorepopup.png"),
    "patient1":      config.asset("helpassets/patient/patientpopup1.png"),
    "patient2":      config.asset("helpassets/patient/patientpopup2.png"),
    "patient3":      config.asset("helpassets/patient/patientpopup3.png"),
    "patient4":      config.asset("helpassets/patient/patientpopup4.png"),
    "patient5":      config.asset("helpassets/patient/patientpopup5.png"),
    "doctor1":       config.asset("helpassets/doctor/doctorpopup1.png"),
    "doctor2":       config.asset("helpassets/doctor/doctorpopup2.png"),
    "doctor3":       config.asset("helpassets/doctor/doctorpopup3.png"),
    "doctor4":       config.asset("helpassets/doctor/doctorpopup4.png"),
    "doctor5":       config.asset("helpassets/doctor/doctorpopup5.png"),
}

_NEXT_POPUP = {
    "first":    "second",
    "patient1": "patient2",
    "patient2": "patient3",
    "patient3": "patient4",
    "patient4": "patient5",
    "patient5": "final_shared",
    "doctor1":  "doctor2",
    "doctor2":  "doctor3",
    "doctor3":  "doctor4",
    "doctor4":  "doctor5",
    "doctor5":  "final_shared",
}


class PopupWindow(QDialog):
    """Generic onboarding / tutorial popup with image content."""

    def __init__(self, parent=None, popup_type: str = "first") -> None:
        super().__init__(parent)
        if popup_type not in _TUTORIAL_IMAGES:
            log.warning("Unknown popup type '%s', defaulting to 'first'", popup_type)
            popup_type = "first"

        self.popup_type = popup_type
        w, h = config.POPUP_SIZE
        self.setWindowTitle("")
        self.setFixedSize(w, h)
        self.setStyleSheet("background-color:white;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        image_path = _TUTORIAL_IMAGES.get(popup_type)
        if image_path:
            img = QLabel()
            img.setPixmap(QPixmap(image_path).scaled(w, h - 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            img.setAlignment(Qt.AlignCenter)
            layout.addWidget(img)

        layout.addStretch()
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(20, 0, 20, 20)
        self._add_buttons(btn_layout)
        layout.addLayout(btn_layout)

    def _add_buttons(self, layout: QHBoxLayout) -> None:
        if self.popup_type == "first":
            btn = QPushButton("Let's Get Started")
            btn.setStyleSheet(_GREEN_BTN)
            btn.clicked.connect(lambda: self._advance("second"))
            layout.addWidget(btn)

        elif self.popup_type == "second":
            for label, style, role in [("Patient", _GREEN_BTN, "patient1"), ("Doctor", _BLUE_BTN, "doctor1")]:
                btn = QPushButton(label)
                btn.setStyleSheet(style)
                btn.clicked.connect(lambda _=False, r=role: self._advance(r))
                layout.addWidget(btn)

        elif self.popup_type == "final_shared":
            guide_btn = QPushButton("User Guide")
            guide_btn.setStyleSheet(_BLUE_BTN)
            guide_btn.clicked.connect(self._open_user_guide)
            layout.addWidget(guide_btn)

            close_btn = QPushButton("Close")
            close_btn.setStyleSheet(_GREEN_BTN)
            close_btn.clicked.connect(self.accept)
            layout.addWidget(close_btn)

        elif "patient" in self.popup_type or "doctor" in self.popup_type:
            is_last = self.popup_type.endswith("5")
            btn = QPushButton("Got it!" if is_last else "Next")
            btn.setStyleSheet(_GREEN_BTN)
            nxt = _NEXT_POPUP.get(self.popup_type)
            btn.clicked.connect(lambda: self._advance(nxt))
            layout.addWidget(btn)

        else:
            btn = QPushButton("Got it!")
            btn.setStyleSheet(_GREEN_BTN)
            btn.clicked.connect(self.accept)
            layout.addWidget(btn)

    def _advance(self, next_type: str | None) -> None:
        self.accept()
        if next_type:
            PopupWindow(self.parent(), next_type).exec_()

    def _open_user_guide(self) -> None:
        self.accept()
        from ui.navigation import NavigationManager
        nav = NavigationManager.instance()
        parent = self.parent()
        if isinstance(parent, QMainWindow):
            parent.close()
        nav.go_to_user_guide()


class MedicalSummaryTemplate(QDialog):
    """Dialog for composing a structured medical summary."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Medical Summary Template")
        self.setMinimumSize(600, 500)
        self.plain_summary = ""
        self.setStyleSheet(
            "QDialog{background-color:white;}"
            "QLabel{font-size:14px;font-weight:bold;color:#333;}"
            "QTextEdit,QLineEdit{border:1px solid #ddd;border-radius:5px;padding:10px;font-size:14px;background-color:#f9f9f9;}"
            "QPushButton{padding:10px 20px;background-color:#4CAF50;color:white;border:none;"
            "border-radius:5px;font-size:14px;font-weight:bold;}"
            "QPushButton:hover{background-color:#45a049;}"
            "QGroupBox{font-size:16px;font-weight:bold;border:1px solid #ddd;border-radius:5px;"
            "margin-top:20px;background-color:white;}"
            "QGroupBox::title{subcontrol-origin:margin;left:10px;padding:0 5px;}"
        )

        layout = QVBoxLayout(self)
        header = QLabel("Medical Summary")
        header.setStyleSheet("font-size:24px;color:#2a70a5;margin-bottom:15px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        self.symptoms_edit = self._add_group(layout, "Symptoms", "Enter patient symptoms here...")
        self.diagnosis_edit = self._add_group(layout, "Diagnosis", "Enter diagnosis here...")
        self.prescription_edit = self._add_group(layout, "Prescription", "Enter prescription details here...")

        btn_layout = QHBoxLayout()
        gen_btn = QPushButton("Generate Summary")
        gen_btn.clicked.connect(self._generate)
        btn_layout.addWidget(gen_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(_RED_BTN)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    @staticmethod
    def _add_group(parent_layout, title: str, placeholder: str) -> QTextEdit:
        group = QGroupBox(title)
        gl = QVBoxLayout()
        edit = QTextEdit()
        edit.setPlaceholderText(placeholder)
        edit.setMinimumHeight(100)
        gl.addWidget(edit)
        group.setLayout(gl)
        parent_layout.addWidget(group)
        return edit

    def _generate(self) -> None:
        symptoms = self.symptoms_edit.toPlainText().strip()
        diagnosis = self.diagnosis_edit.toPlainText().strip()
        prescription = self.prescription_edit.toPlainText().strip()

        if not all([symptoms, diagnosis, prescription]):
            self._show_error("Please fill in all fields to generate a summary.")
            return

        html = (
            "<div style='font-family:Arial,sans-serif;padding:10px;'>"
            "<h2 style='color:#2a70a5;text-align:center;'>Medical Summary</h2>"
            f"<div style='margin:15px 0;padding:10px;background-color:#f0f7ff;border-radius:5px;'>"
            f"<h3 style='color:#333;'>Symptoms:</h3><p style='margin-left:15px;'>{symptoms}</p></div>"
            f"<div style='margin:15px 0;padding:10px;background-color:#f0fff0;border-radius:5px;'>"
            f"<h3 style='color:#333;'>Diagnosis:</h3><p style='margin-left:15px;'>{diagnosis}</p></div>"
            f"<div style='margin:15px 0;padding:10px;background-color:#fff7f0;border-radius:5px;'>"
            f"<h3 style='color:#333;'>Prescription:</h3><p style='margin-left:15px;'>{prescription}</p></div>"
            "</div>"
        )

        self.plain_summary = (
            f"Medical Summary\nSymptoms:\n{symptoms}\n\n"
            f"Diagnosis:\n{diagnosis}\n\n"
            f"Prescription:\n{prescription}"
        )

        preview = QDialog(self)
        preview.setWindowTitle("Medical Summary Preview")
        preview.setMinimumSize(600, 500)
        pl = QVBoxLayout(preview)

        display = QTextEdit()
        display.setReadOnly(True)
        display.setHtml(html)
        pl.addWidget(display)

        pbl = QHBoxLayout()
        add_btn = QPushButton("Add to Chat")
        add_btn.setStyleSheet(_GREEN_BTN)
        add_btn.clicked.connect(lambda: [preview.accept(), self.accept()])
        pbl.addWidget(add_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(_RED_BTN)
        cancel_btn.clicked.connect(preview.reject)
        pbl.addWidget(cancel_btn)
        pl.addLayout(pbl)

        preview.exec_()

    def _show_error(self, message: str) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle("Error")
        dlg.setFixedSize(300, 150)
        lo = QVBoxLayout(dlg)
        lbl = QLabel(message)
        lbl.setStyleSheet("color:red;font-size:14px;")
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignCenter)
        lo.addWidget(lbl)
        ok = QPushButton("OK")
        ok.clicked.connect(dlg.accept)
        lo.addWidget(ok, alignment=Qt.AlignCenter)
        dlg.exec_()
