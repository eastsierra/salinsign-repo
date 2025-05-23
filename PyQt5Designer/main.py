"""
SalinSign – application entry point.

Run from the PyQt5Designer directory:
    python main.py
"""

import sys
import os

# Ensure the package root is on the path so all internal imports resolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication

from ui.navigation import NavigationManager


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    nav = NavigationManager.instance()
    nav.go_to_main_menu()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
