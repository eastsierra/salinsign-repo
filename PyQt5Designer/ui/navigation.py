"""
Centralized navigation manager.

Handles all window transitions so that individual modules never need to
import each other directly, breaking the circular-import cycle that plagued
the original codebase.
"""

import gc
import logging

from PyQt5.QtWidgets import QMainWindow

log = logging.getLogger(__name__)


class NavigationManager:
    """Singleton that owns all top-level window transitions."""

    _instance: "NavigationManager | None" = None

    @classmethod
    def instance(cls) -> "NavigationManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        self._current_window: QMainWindow | None = None

    def go_to_main_menu(self) -> None:
        from ui.main_menu import MainMenuWindow

        self._close_current()
        window = MainMenuWindow()
        window.showFullScreen()
        self._current_window = window

    def go_to_translation(self, preloaded: bool = False) -> None:
        from ui.translation import TranslationModule

        self._close_current()
        window = TranslationModule()
        window.preloaded = preloaded
        window.showFullScreen()
        self._current_window = window

    def go_to_sign_library(self) -> None:
        from ui.sign_library import SignLanguageLibrary

        self._close_current()
        window = SignLanguageLibrary()
        window.showFullScreen()
        self._current_window = window

    def go_to_user_guide(self) -> None:
        from ui.user_guide import UserGuideModule

        self._close_current()
        window = UserGuideModule()
        window.showFullScreen()
        self._current_window = window

    def _close_current(self) -> None:
        if self._current_window is not None:
            try:
                self._current_window.close()
            except Exception:
                log.exception("Error closing current window")
            self._current_window = None
        gc.collect()
