"""
Main menu screen -- the application hub.

Provides navigation buttons to the Translation, Sign Library, and User Guide
modules.  Pre-loads the Translation module in the background for faster access.
"""

import gc
import logging

from PyQt5 import QtCore, QtGui, QtWidgets

import config

log = logging.getLogger(__name__)


class MainMenuWindow(QtWidgets.QMainWindow):
    """Full-screen main menu with three navigation buttons."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("MainWindow")
        self.resize(*config.WINDOW_SIZE)
        self.setMinimumSize(*config.WINDOW_MIN_SIZE)
        font = QtGui.QFont("Comic Sans MS")
        self.setFont(font)
        self.setAcceptDrops(False)
        self.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.showFullScreen()

        self._translation_preloaded = None

        try:
            self._setup_ui()
            QtCore.QTimer.singleShot(config.PRELOAD_DELAY_MS, self._preload_translation)
        except Exception:
            log.exception("Error during MainMenu setup")
            self._create_fallback_ui()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setStyleSheet("background-color:rgb(255,255,255);")

        self.background_label = QtWidgets.QLabel(self.centralwidget)
        self.background_label.setGeometry(QtCore.QRect(0, 0, *config.WINDOW_SIZE))
        self.background_label.setPixmap(QtGui.QPixmap(config.asset("RevampedMainDesign.png")))
        self.background_label.setScaledContents(True)
        self.background_label.lower()

        btn_style = self._button_style()

        self.translation_button = self._make_button(
            self.centralwidget, QtCore.QRect(824, 550, 271, 51),
            config.asset("TranslateButtonIcon.png"), btn_style,
        )
        self.library_button = self._make_button(
            self.centralwidget, QtCore.QRect(824, 620, 271, 51),
            config.asset("SignLibraryButtonIcon.png"), btn_style,
        )
        self.guide_button = self._make_button(
            self.centralwidget, QtCore.QRect(824, 690, 271, 51),
            config.asset("UserGuideButtonIcon.png"), btn_style,
        )

        self.setCentralWidget(self.centralwidget)
        self.setMenuBar(None)
        self.setStatusBar(None)
        self.setWindowTitle("SalinSign")

        self.translation_button.clicked.connect(self._open_translation)
        self.library_button.clicked.connect(self._open_library)
        self.guide_button.clicked.connect(self._open_guide)

        self.resizeEvent = self._handle_resize

    def _create_fallback_ui(self) -> None:
        cw = QtWidgets.QWidget(self)
        self.setCentralWidget(cw)
        layout = QtWidgets.QVBoxLayout(cw)

        err = QtWidgets.QLabel("An error occurred during startup. Please restart.")
        err.setStyleSheet("color:red;font-size:16px;")
        layout.addWidget(err)

        for label, slot in [
            ("Translation", self._open_translation),
            ("Sign Library", self._open_library),
            ("User Guide", self._open_guide),
            ("Exit", self.close),
        ]:
            btn = QtWidgets.QPushButton(label)
            btn.clicked.connect(slot)
            layout.addWidget(btn)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _button_style() -> str:
        c = config.MAIN_MENU_COLORS
        return (
            f"QPushButton{{border-radius:25px;border:none;"
            f"background-color:{c['button_bg']};color:black;}}"
            f"QPushButton:hover{{background-color:{c['button_hover']};}}"
        )

    @staticmethod
    def _make_button(parent, rect, icon_path, style) -> QtWidgets.QPushButton:
        btn = QtWidgets.QPushButton(parent)
        btn.setGeometry(rect)
        font = QtGui.QFont()
        font.setPointSize(18)
        btn.setFont(font)
        btn.setStyleSheet(style)
        btn.setText("")
        icon = QtGui.QIcon(QtGui.QPixmap(icon_path))
        btn.setIcon(icon)
        btn.setIconSize(QtCore.QSize(200, 130))
        return btn

    # ------------------------------------------------------------------
    # Resize
    # ------------------------------------------------------------------

    def _handle_resize(self, event) -> None:
        w, h = event.size().width(), event.size().height()
        if hasattr(self, "background_label"):
            self.background_label.setGeometry(QtCore.QRect(0, 0, w, h))

        scale = min(w / config.REFERENCE_WIDTH, h / config.REFERENCE_HEIGHT)
        if w < config.MOBILE_BREAKPOINT:
            scale *= 1.2

        btn_w = int(271 * scale)
        btn_h = int(51 * scale)
        radius = btn_h // 2
        c = config.MAIN_MENU_COLORS
        style = (
            f"QPushButton{{border-radius:{radius}px;border:none;"
            f"background-color:{c['button_bg']};color:black;cursor:pointer;}}"
            f"QPushButton:hover{{background-color:{c['button_hover']};}}"
        )
        cx = (w - btn_w) // 2
        spacing = int(70 * scale)
        start_y = int(h * 0.5)

        for i, btn in enumerate([self.translation_button, self.library_button, self.guide_button]):
            btn.setStyleSheet(style)
            btn.setGeometry(QtCore.QRect(cx, start_y + spacing * i, btn_w, btn_h))
            icon_w = int(200 * scale)
            icon_h = int(130 * scale)
            btn.setIconSize(QtCore.QSize(icon_w, icon_h))

    # ------------------------------------------------------------------
    # Pre-loading
    # ------------------------------------------------------------------

    def _preload_translation(self) -> None:
        try:
            from ui.translation import TranslationModule
            self._translation_preloaded = TranslationModule()
            self._translation_preloaded.preloaded = True
        except Exception:
            log.exception("Error preloading Translation module")
            self._translation_preloaded = None

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _open_translation(self) -> None:
        gc.collect()
        try:
            if self._translation_preloaded is not None:
                self._translation_preloaded.preloaded = False
                self._translation_preloaded.showFullScreen()
                self.hide()
            else:
                from ui.navigation import NavigationManager
                self.hide()
                NavigationManager.instance().go_to_translation()
        except Exception as e:
            log.exception("Error opening Translation")
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def _open_library(self) -> None:
        gc.collect()
        try:
            from ui.navigation import NavigationManager
            self.hide()
            NavigationManager.instance().go_to_sign_library()
        except Exception as e:
            log.exception("Error opening Sign Library")
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def _open_guide(self) -> None:
        gc.collect()
        try:
            from ui.navigation import NavigationManager
            self.hide()
            NavigationManager.instance().go_to_user_guide()
        except Exception as e:
            log.exception("Error opening User Guide")
            QtWidgets.QMessageBox.critical(self, "Error", str(e))


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    app = QtWidgets.QApplication(sys.argv)
    win = MainMenuWindow()
    win.show()
    sys.exit(app.exec_())
