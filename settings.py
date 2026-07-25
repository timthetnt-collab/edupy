# settings.py

import tkinter as tk
import os

# ---------- SOUND DIRECTORY ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOUNDS_DIR = os.path.join(BASE_DIR, "sounds")

# ---------- WINDOW ----------
WIDTH, HEIGHT = 1280, 720
TITLE = "edupy"

# ---------- FONTS ----------
FONT_TITLE = ("Segoe UI", 30, "bold")
FONT_SUBTITLE = ("Segoe UI", 17, "bold")
FONT_TEXT = ("Segoe UI", 12)
FONT_BUTTON = ("Segoe UI", 12, "bold")

# ---------- BASE THEMES ----------
THEMES = {
    "Default": {
        "bg": "#0B1020",
        "fg": "#F7F9FF",
        "muted": "#9AA8C5",
        "panel": "#141B2F",
        "panel_alt": "#1B2540",
        "accent": "#6EA8FF",
        "accent_soft": "#203A68",
        "border": "#2B3857",
        "input_bg": "#10182B",
        "success": "#45D49B",
        "warning": "#FFC857",
        "danger": "#FF718B",
        "button_bg": "#315FAD",
        "button_fg": "#FFFFFF",
        "button_hover_bg": "#4274C8",
    },
    "Ocean": {
        "bg": "#001F3F",
        "fg": "#E0F7FA",
        "muted": "#91CBD0",
        "panel": "#073451",
        "panel_alt": "#0A4560",
        "accent": "#00BCD4",
        "button_bg": "#006064",
        "button_fg": "#E0F7FA",
        "button_hover_bg": "#00727A",
        "accent_soft": "#07566A", "border": "#17677A", "input_bg": "#062D48", "success": "#55D6A8", "warning": "#FFD166", "danger": "#FF718B",
    },
    "Sunset": {
        "bg": "#2C1B2F",
        "fg": "#FFE0B2",
        "muted": "#D6B5A2",
        "panel": "#40243D",
        "panel_alt": "#55304A",
        "accent": "#FF7043",
        "button_bg": "#B52F0B",
        "button_fg": "#FFE0B2",
        "button_hover_bg": "#8F2608",
        "accent_soft": "#6E354F", "border": "#704459", "input_bg": "#351F35", "success": "#65D6A5", "warning": "#FFD166", "danger": "#FF718B",
    },
    "Matrix": {
        "bg": "#000000",
        "fg": "#00FF00",
        "muted": "#70B870",
        "panel": "#071507",
        "panel_alt": "#0B250B",
        "accent": "#00CC00",
        "button_bg": "#003300",
        "button_fg": "#00FF00",
        "button_hover_bg": "#005500",
        "accent_soft": "#063806", "border": "#126012", "input_bg": "#041004", "success": "#00FF66", "warning": "#D7FF00", "danger": "#FF5B5B",
    },
    "Neon": {
        "bg": "#050014",
        "fg": "#F8F8FF",
        "muted": "#BDB3D8",
        "panel": "#16052D",
        "panel_alt": "#25084A",
        "accent": "#FF00FF",
        "button_bg": "#3A0070",
        "button_fg": "#F8F8FF",
        "button_hover_bg": "#5A00A0",
        "accent_soft": "#4B1468", "border": "#57217A", "input_bg": "#120528", "success": "#43E6A0", "warning": "#FFD166", "danger": "#FF5D8F",
    },
    "Study Paper": {
        "bg": "#F4F7FC", "fg": "#17233C", "muted": "#5F6F89",
        "panel": "#FFFFFF", "panel_alt": "#EDF2FA", "accent": "#1267E5",
        "accent_soft": "#DCEAFF", "border": "#D6DFEC", "input_bg": "#FFFFFF",
        "success": "#168A5B", "warning": "#B76B00", "danger": "#C33A52",
        "button_bg": "#1267E5", "button_fg": "#FFFFFF", "button_hover_bg": "#0B55C6",
    },
    "Academy": {
        "bg": "#F8F5EC", "fg": "#1B2945", "muted": "#667087",
        "panel": "#FFFDF7", "panel_alt": "#EEE8D8", "accent": "#2456A6",
        "accent_soft": "#DFE8F8", "border": "#D8D0BD", "input_bg": "#FFFFFF",
        "success": "#267A55", "warning": "#A76500", "danger": "#B53B4F",
        "button_bg": "#243E70", "button_fg": "#FFFFFF", "button_hover_bg": "#31558F",
    },
    "Focus Mint": {
        "bg": "#ECF8F4", "fg": "#173A35", "muted": "#55756F",
        "panel": "#FFFFFF", "panel_alt": "#DCF1EA", "accent": "#168C76",
        "accent_soft": "#CDEDE4", "border": "#C2DED6", "input_bg": "#F9FFFD",
        "success": "#168C5A", "warning": "#A66A00", "danger": "#B83B54",
        "button_bg": "#147563", "button_fg": "#FFFFFF", "button_hover_bg": "#0F5E50",
    },
}

# ---------- CURRENT THEME ----------
THEME = THEMES["Default"].copy()

# settings.py (patch)
def set_theme(name: str):
    """
    Set THEME to a copy of the named theme and return it.
    Call this before rebuilding UI so new widgets pick up THEME values.
    """
    # Mutate the shared dictionary instead of rebinding it.  Several modules
    # import THEME directly, so rebinding left those screens using old colours.
    selected = THEMES.get(name, THEMES["Default"])
    THEME.clear()
    THEME.update(selected)
    return THEME

# ---------- DIFFICULTY LEVELS ----------
DIFFICULTY_LEVELS = {
    "Year 7": 7,
    "Year 8": 8,
    "Year 9": 9,
    "Year 10": 10,
    "Year 11": 11,
}

# ---------- OPTIONAL: ROOT CONFIG HELPER ----------
def apply_theme_to_root(root: tk.Tk):
    root.configure(bg=THEME["bg"])
