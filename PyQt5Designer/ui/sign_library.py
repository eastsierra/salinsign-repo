"""
Sign Language Library -- tabbed catalog of signs with search.
"""

import logging
import sys
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QScrollArea, QGridLayout,
    QFrame, QGraphicsDropShadowEffect, QLineEdit,
)
from PyQt5.QtGui import QPixmap, QIcon, QFont, QColor
from PyQt5.QtCore import Qt, QSize

import config
from ui.widgets.catalog import CatalogItem, CustomTabBar

log = logging.getLogger(__name__)


class SignLanguageLibrary(QMainWindow):
    """Full-screen catalog organized by Medical, Greetings, Alphabet, Numbers."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sign Language Library")
        self.setGeometry(100, 100, *config.WINDOW_SIZE)
        self.setMinimumSize(*config.LIBRARY_MIN_SIZE)
        self.showFullScreen()

        QApplication.setFont(QFont("Segoe UI", 10))

        self.colors = config.LIBRARY_COLORS
        self.tab_colors = config.LIBRARY_TAB_COLORS
        self.all_items: dict[str, list[dict]] = {}

        self._setup_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setup_ui(self):
        cw = QWidget()
        cw.setStyleSheet(f"background-color:{self.colors['background']};")
        self.setCentralWidget(cw)
        main_layout = QVBoxLayout(cw)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet(
            f"QFrame{{background-color:{self.colors['surface']};"
            f"border-bottom:1px solid {self.colors['border']};}}"
        )
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 10, 20, 10)

        back_btn = QPushButton()
        back_btn.setIcon(QIcon(config.asset("backbutton.png")))
        back_btn.setIconSize(QSize(40, 40))
        back_btn.setFixedSize(40, 40)
        back_btn.setStyleSheet(
            f"QPushButton{{background-color:{self.colors['surface']};"
            f"border:none;border-radius:20px;padding:5px;}}"
            f"QPushButton:hover{{background-color:{self.colors['hover']};}}"
        )
        back_btn.clicked.connect(self._go_back)

        title_lbl = QLabel()
        title_lbl.setPixmap(QPixmap(config.asset("signlibrary.png")))
        title_lbl.setAlignment(Qt.AlignCenter)

        hl.addWidget(back_btn)
        hl.addWidget(title_lbl)
        main_layout.addWidget(header)

        # Search bar
        search_frame = QFrame()
        search_frame.setStyleSheet(
            f"QFrame{{background-color:{self.colors['surface']};"
            f"border-bottom:1px solid {self.colors['border']};}}"
            f"QLineEdit{{border:1px solid {self.colors['border']};border-radius:20px;"
            f"padding:8px 15px;background-color:{self.colors['background']};}}"
            f"QPushButton{{background-color:{self.colors['primary']};color:white;"
            "border:none;border-radius:20px;padding:8px 20px;font-weight:bold;}"
            "QPushButton:hover{background-color:#45A29A;}"
        )
        sl = QHBoxLayout(search_frame)
        sl.setContentsMargins(20, 10, 20, 10)

        search_icon_lbl = QLabel()
        spx = QPixmap(config.asset("search_icon.png"))
        if spx.isNull():
            search_icon_lbl.setText("\U0001f50d")
        else:
            search_icon_lbl.setPixmap(spx.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        search_icon_lbl.setFixedSize(30, 30)
        search_icon_lbl.setAlignment(Qt.AlignCenter)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search sign language...")
        self.search_input.setMinimumWidth(300)
        self.search_input.returnPressed.connect(self._perform_search)

        clear_btn = QPushButton("\u00d7")
        clear_btn.setStyleSheet(
            "QPushButton{background-color:transparent;color:#666;font-size:18px;"
            "font-weight:bold;border:none;padding:5px;}"
            "QPushButton:hover{color:#333;}"
        )
        clear_btn.setFixedSize(30, 30)
        clear_btn.clicked.connect(self._clear_search)

        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._perform_search)

        sl.addWidget(search_icon_lbl)
        sl.addWidget(self.search_input)
        sl.addWidget(clear_btn)
        sl.addWidget(search_btn)
        main_layout.addWidget(search_frame)

        # Tab widget
        self.tab_widget = QTabWidget()
        tab_bar = CustomTabBar()
        self.tab_widget.setTabBar(tab_bar)
        tab_bar.set_tab_colors([
            self.tab_colors["medical"]["primary"],
            self.tab_colors["greetings"]["primary"],
            self.tab_colors["alphabet"]["primary"],
            self.tab_colors["numbers"]["primary"],
        ])
        self.tab_widget.setStyleSheet(self._tab_stylesheet())

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 2)
        self.tab_widget.setGraphicsEffect(shadow)

        self.tab_widget.addTab(
            self._catalog_tab("Medical", config.MEDICAL_ITEMS, self.tab_colors["medical"]), "Medical"
        )
        self.tab_widget.addTab(
            self._catalog_tab("Greetings", config.GREETING_ITEMS, self.tab_colors["greetings"]), "Greetings"
        )
        self.tab_widget.addTab(
            self._catalog_tab("Alphabet", config.ALPHABET_ITEMS, self.tab_colors["alphabet"]), "Alphabet"
        )
        self.tab_widget.addTab(
            self._catalog_tab("Numbers", config.NUMBER_ITEMS, self.tab_colors["numbers"]), "Numbers"
        )

        tab_container = QWidget()
        tcl = QVBoxLayout(tab_container)
        tcl.setContentsMargins(20, 20, 20, 20)
        tcl.addWidget(self.tab_widget)
        main_layout.addWidget(tab_container)

    # ------------------------------------------------------------------
    # Catalog tab builder
    # ------------------------------------------------------------------

    def _catalog_tab(self, category: str, items: list[str], colors: dict) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet(f"background-color:{colors['primary']};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background-color:{colors['primary']};")

        content = QWidget()
        content.setStyleSheet(f"background-color:{colors['primary']};")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(10, 10, 10, 10)
        cl.setSpacing(15)

        if category not in self.all_items:
            self.all_items[category] = []

        win_w = self.width()
        spacing = 15
        items_per_row = max(3, min(6, (win_w - 40) // (180 + spacing)))
        item_w = (win_w - 40 - (items_per_row - 1) * spacing) // items_per_row
        item_h = int(item_w * 1.1)

        row_widgets: list[CatalogItem] = []

        for text in items:
            img_path = self._image_path_for(text, category)
            self.all_items[category].append({
                "title": text, "image_path": img_path,
                "color_scheme": colors, "category": category,
            })
            ci = CatalogItem(text, img_path, colors, category)
            ci.setFixedSize(item_w, item_h)
            row_widgets.append(ci)

            if len(row_widgets) == items_per_row or text == items[-1]:
                rl = QHBoxLayout()
                rl.setSpacing(spacing)
                rl.setContentsMargins(0, 0, 0, 0)
                for w in row_widgets:
                    rl.addWidget(w)
                if len(row_widgets) < items_per_row and text == items[-1]:
                    for _ in range(items_per_row - len(row_widgets)):
                        s = QWidget()
                        s.setFixedSize(item_w, item_h)
                        rl.addWidget(s)
                cl.addLayout(rl)
                row_widgets = []

        scroll.setWidget(content)
        layout.addWidget(scroll)
        return tab

    @staticmethod
    def _image_path_for(text: str, category: str) -> str:
        if "Letter" in text:
            return config.asset(f"letter_{text.split()[-1].lower()}.png")
        if "Number" in text:
            return config.asset(f"number_{text.split()[-1]}.png")
        fname = text.lower().replace(" ", "_").replace("?", "").replace("!", "")
        return config.asset(f"{category.lower()}_{fname}.png")

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def _perform_search(self):
        query = self.search_input.text().lower().strip()
        if not query:
            return

        results = []
        for cat, items in self.all_items.items():
            for item in items:
                if query in item["title"].lower():
                    copy = item.copy()
                    copy["category"] = cat
                    results.append(copy)
        results.sort(key=lambda x: x["title"])

        for i in range(self.tab_widget.count()):
            if "Search Results" in self.tab_widget.tabText(i):
                self.tab_widget.removeTab(i)
                break

        tab = self._search_results_tab(results, query)
        self.tab_widget.addTab(tab, f"Search Results ({len(results)})")
        self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)

        tb = self.tab_widget.tabBar()
        if isinstance(tb, CustomTabBar):
            tb.set_tab_colors([
                self.tab_colors["medical"]["primary"],
                self.tab_colors["greetings"]["primary"],
                self.tab_colors["alphabet"]["primary"],
                self.tab_colors["numbers"]["primary"],
                self.colors["primary"],
            ])

    def _clear_search(self):
        self.search_input.clear()
        for i in range(self.tab_widget.count()):
            if "Search Results" in self.tab_widget.tabText(i):
                self.tab_widget.removeTab(i)
                break
        tb = self.tab_widget.tabBar()
        if isinstance(tb, CustomTabBar):
            tb.set_tab_colors([
                self.tab_colors["medical"]["primary"],
                self.tab_colors["greetings"]["primary"],
                self.tab_colors["alphabet"]["primary"],
                self.tab_colors["numbers"]["primary"],
            ])

    def _search_results_tab(self, results: list[dict], query: str) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet(f"background-color:{self.colors['primary']};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)

        header = QHBoxLayout()
        lbl = QLabel(f"Search results for: '{query}'")
        lbl.setStyleSheet("color:white;font-size:16px;font-weight:bold;")
        cb = QPushButton("Clear Search")
        cb.setStyleSheet(
            "QPushButton{background-color:white;color:#333;border:none;"
            "border-radius:15px;padding:5px 15px;font-weight:bold;}"
            "QPushButton:hover{background-color:#eee;}"
        )
        cb.clicked.connect(self._clear_search)
        header.addWidget(lbl)
        header.addStretch()
        header.addWidget(cb)
        layout.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background-color:{self.colors['primary']};")

        content = QWidget()
        content.setStyleSheet(f"background-color:{self.colors['primary']};")

        if not results:
            el = QVBoxLayout(content)
            el.setAlignment(Qt.AlignCenter)
            no = QLabel("No results found")
            no.setStyleSheet("color:white;font-size:18px;font-weight:bold;")
            no.setAlignment(Qt.AlignCenter)
            el.addWidget(no)
        else:
            grid = QGridLayout(content)
            grid.setContentsMargins(10, 10, 10, 10)
            grid.setSpacing(20)
            grid.setAlignment(Qt.AlignCenter)
            cols = 4
            for idx, item in enumerate(results):
                ci = CatalogItem(item["title"], item["image_path"], item["color_scheme"], item["category"])
                ci.setFixedSize(200, 220)
                r, c = divmod(idx, cols)
                grid.addWidget(ci, r, c)

        scroll.setWidget(content)
        layout.addWidget(scroll)
        return tab

    # ------------------------------------------------------------------
    # Stylesheet
    # ------------------------------------------------------------------

    def _tab_stylesheet(self) -> str:
        c = self.colors
        return (
            "QTabWidget{background-color:transparent;}"
            "QTabWidget::pane{border:none;background-color:transparent;padding:0;}"
            f"QTabBar::tab{{font-weight:bold;padding:12px 40px;margin-right:4px;"
            f"border-top-left-radius:8px;border-top-right-radius:8px;border:none;"
            f"min-width:120px;color:{c['text']};background:{c['tab_background']};}}"
            f"QScrollBar:vertical{{border:none;background:{c['background']};"
            "width:8px;border-radius:4px;}"
            "QScrollBar::handle:vertical{background:rgba(0,0,0,0.3);min-height:30px;border-radius:4px;}"
            "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{border:none;background:none;height:0;}"
            "QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{background:none;}"
            f"QScrollBar:horizontal{{border:none;background:{c['background']};"
            "height:8px;border-radius:4px;}"
            "QScrollBar::handle:horizontal{background:rgba(0,0,0,0.3);min-width:30px;border-radius:4px;}"
            "QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal{border:none;background:none;width:0;}"
            "QScrollBar::add-page:horizontal,QScrollBar::sub-page:horizontal{background:none;}"
        )

    # ------------------------------------------------------------------
    # Navigation / lifecycle
    # ------------------------------------------------------------------

    def _go_back(self):
        try:
            from ui.navigation import NavigationManager
            self.close()
            NavigationManager.instance().go_to_main_menu()
        except Exception as e:
            log.exception("Error navigating back")
            self.close()

    def resizeEvent(self, event):
        super().resizeEvent(event)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = SignLanguageLibrary()
    win.show()
    sys.exit(app.exec_())
