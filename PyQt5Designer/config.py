"""
Centralized configuration for the SalinSign application.

All hardcoded values, paths, colors, model parameters, and constants
are defined here for easy maintenance and modification.
"""

import logging
import os
import sys

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_LEVEL = logging.INFO


def setup_logging() -> None:
    """Configure the root logger for the application."""
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        stream=sys.stdout,
    )


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
IMAGES_DIR = os.path.join(BASE_DIR, "images")
SIGN_IMAGES_DIR = os.path.join(IMAGES_DIR, "signimages")
USER_GUIDE_ASSETS_DIR = os.path.join(IMAGES_DIR, "userguideassets")
HELP_ASSETS_DIR = os.path.join(IMAGES_DIR, "helpassets")
MODEL_PATH = os.path.join(BASE_DIR, "model.p")
STYLESHEET_PATH = os.path.join(BASE_DIR, "resources", "translation_style.qss")


def asset(filename: str) -> str:
    """Return the full path to an image asset."""
    return os.path.join(IMAGES_DIR, filename)


# ---------------------------------------------------------------------------
# Window defaults
# ---------------------------------------------------------------------------
WINDOW_SIZE = (1920, 1080)
WINDOW_MIN_SIZE = (360, 640)
LIBRARY_MIN_SIZE = (600, 400)
MOBILE_BREAKPOINT = 768
REFERENCE_WIDTH = 1920
REFERENCE_HEIGHT = 1080

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
CAMERA_RESOLUTION = (640, 480)
MAX_CAMERA_SCAN = 10

# ---------------------------------------------------------------------------
# Model / Inference
# ---------------------------------------------------------------------------
NUM_FEATURES = 84
CONFIDENCE_THRESHOLD = 0.4
MIN_DETECTION_CONFIDENCE = 0.3
STABLE_PREDICTIONS_REQUIRED = 3
FINGERTIP_INDICES = [4, 8, 12, 16, 20]
WRIST_INDEX = 0

LABELS = {
    0: "Pain", 1: "Sick", 2: "Headache", 3: "Dizzy", 4: "Vomit",
    5: "Diarrhea", 6: "Cough", 7: "Allergy", 8: "Strong", 9: "Weak",
    10: "Stomachache", 11: "Sore Throat", 12: "Sore Throat", 13: "Injury",
    14: "Breathing Difficulty", 15: "Food Poisoning", 16: "Wound", 17: "Stress",
    18: "Conditions", 19: "Fever", 20: "Diabetes", 21: "Back Pain",
    22: "Back Pain", 23: "Colds", 24: "Stroke", 25: "Blood Pressure",
    26: "Heartache", 27: "A", 28: "B", 29: "C", 30: "D", 31: "E",
    32: "F", 33: "G", 34: "H", 35: "I", 36: "J", 37: "K", 38: "L",
    39: "M", 40: "N", 41: "O", 42: "P", 43: "Q", 44: "R", 45: "S",
    46: "T", 47: "U", 48: "V", 49: "W", 50: "X", 51: "Y", 52: "Z",
    53: "Hello", 54: "Good Morning", 55: "Good Afternoon",
    56: "Good Evening", 57: "Thank You", 58: "Good Bye",
    59: "3", 60: "4", 61: "5", 62: "7", 63: "8", 64: "9", 65: "10",
}

# ---------------------------------------------------------------------------
# Timing (milliseconds)
# ---------------------------------------------------------------------------
SIGN_INTERVAL_MS = 1500
SIGN_HOLD_MS = 700
TRANSLATION_TIMEOUT_MS = 5000
THREAD_STOP_TIMEOUT_MS = 300
PRELOAD_DELAY_MS = 500

# ---------------------------------------------------------------------------
# User Guide
# ---------------------------------------------------------------------------
TOTAL_SLIDES = 17

# ---------------------------------------------------------------------------
# Doctor predefined phrases
# ---------------------------------------------------------------------------
DOCTOR_QUICK_PHRASES = [
    "Where does it hurt?",
    "How long have you felt this?",
    "I'll check your vital signs now.",
    "You need medicine \u2014 I'll give you instructions.",
    "Any questions before we finish?",
]

DOCTOR_AUTOCOMPLETE_PHRASES = [
    "How are you feeling today?",
    "Do you have any allergies?",
    "Are you currently taking any medications?",
    "Stay hydrated and get enough rest",
    "Contact me if your symptoms worsen",
    "Was this a problem before?",
    "Let me know if you feel dizzy or nauseous.",
    "I'm going to prescribe something to help.",
    "Make sure to take your medication on time.",
    "Very important to monitor your progress closely.",
]

# ---------------------------------------------------------------------------
# Sign Library catalog data
# ---------------------------------------------------------------------------
ALPHABET_ITEMS = sorted(f"Letter {c}" for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ")

NUMBER_ITEMS = sorted(
    [f"Number {n}" for n in range(1, 11)],
    key=lambda x: int(x.split()[-1]),
)

GREETING_ITEMS = sorted([
    "Good afternoon", "Good evening", "Good morning",
    "Goodbye", "Hello", "Thank you",
])

MEDICAL_ITEMS = sorted([
    "Allergy", "Back pain", "Blood Pressure", "Cold", "Conditions",
    "Cough", "Diabetes", "Diarrhea", "Dizzy", "Fever", "Food Poisoning",
    "Headache", "Heartache", "Injury", "Pain", "Sick", "Sore throat",
    "Stomachache", "Stress", "Stroke", "Strong", "Vomit", "Weak",
    "Wound", "Breathing Difficulty",
])

# ---------------------------------------------------------------------------
# Color schemes
# ---------------------------------------------------------------------------
MAIN_MENU_COLORS = {
    "button_bg": "#97cee8",
    "button_hover": "#a2defa",
}

CHAT_COLORS = {
    "patient_bg": "#00c29d",
    "doctor_bg": "#0084ff",
    "text": "white",
}

POPUP_COLORS = {
    "green": "#4CAF50",
    "green_hover": "#45a049",
    "blue": "#2196F3",
    "blue_hover": "#0b7dda",
    "red": "#f44336",
    "red_hover": "#d32f2f",
}

LIBRARY_COLORS = {
    "primary": "#4FB0AA",
    "background": "#f8f9fa",
    "surface": "#ffffff",
    "border": "#e0e0e0",
    "hover": "#f0f0f0",
    "active": "#e0e0e0",
    "text": "#333333",
    "tab_background": "#F0F0F0",
}

LIBRARY_TAB_COLORS = {
    "alphabet": {
        "primary": "#4FB0AA",
        "hover": "#E6F7F6",
        "item_bg": "#E6F7F6",
        "item_selected": "#4FB0AA",
        "item_hover": "#D0EFED",
        "text_color": "#2A6762",
    },
    "numbers": {
        "primary": "#5B6ABB",
        "hover": "#E6E9F7",
        "item_bg": "#E6E9F7",
        "item_selected": "#5B6ABB",
        "item_hover": "#D0D6EF",
        "text_color": "#344380",
    },
    "greetings": {
        "primary": "#E67E22",
        "hover": "#FBF1E6",
        "item_bg": "#FBF1E6",
        "item_selected": "#E67E22",
        "item_hover": "#F7E0C9",
        "text_color": "#A05816",
    },
    "medical": {
        "primary": "#E74C3C",
        "hover": "#FCE9E7",
        "item_bg": "#FCE9E7",
        "item_selected": "#E74C3C",
        "item_hover": "#F8D4D0",
        "text_color": "#A03529",
    },
}

POPUP_SIZE = (800, 650)
