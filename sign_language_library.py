# Back button
self.back_button = QPushButton("Back", self)
self.back_button.setStyleSheet("""
    QPushButton {
        background-color: #97cee8;
        color: black;
        border-radius: 15px;
        padding: 10px;
        font-size: 16px;
    }
    QPushButton:hover {
        background-color: #a2defa;
    }
""")
self.back_button.setFixedSize(100, 40)
self.back_button.clicked.connect(self.go_back)
layout.addWidget(self.back_button, alignment=Qt.AlignLeft | Qt.AlignTop)

def go_back(self):
    from PyQt5Designer.MainMenu import Ui_MainWindow
    self.main_menu = Ui_MainWindow()
    self.main_menu.setupUi(self)
    self.main_menu.window.show()
    self.close() 