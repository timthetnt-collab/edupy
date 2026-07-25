# student_texts.py
"""
Student-facing text chooser:
- Shows two tabs: App Texts (built-in) and Teacher Texts (content_packs created by teachers)
- Student selects which pack to do; opens english flow with that pack
"""

import tkinter as tk
from tkinter import ttk
from ui import clear, make_label, make_button, make_scrollable, show_popup
from settings import THEME, FONT_TITLE, FONT_SUBTITLE, FONT_TEXT
import save_system
import english

def show_text_selector(root, app):
    clear(root)
    make_label(root, "Choose Texts", FONT_TITLE).pack(pady=12)

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=8, pady=8)

    # App texts: use english.TEXTS (built-in)
    app_tab = tk.Frame(notebook, bg=THEME["bg"])
    notebook.add(app_tab, text="App Texts")
    app_list = make_scrollable(app_tab)
    for t in english.TEXTS:
        frame = tk.Frame(app_list, bg=THEME["bg"])
        frame.pack(fill="x", padx=12, pady=6)
        make_label(frame, t["title"], FONT_SUBTITLE).pack(side="left")
        def start_pack(pack=t):
            # Open the full English screen with this built-in pack
            english.show_english_screen(root, app, pack=pack)
        make_button(frame, "Start", start_pack, wide=False)

    # Teacher texts: from save_data content_packs of type 'english'
    teacher_tab = tk.Frame(notebook, bg=THEME["bg"])
    notebook.add(teacher_tab, text="Teacher Texts")
    teacher_list = make_scrollable(teacher_tab)
    packs = save_system.get_content_packs(app.save_data, pack_type="english")
    if not packs:
        make_label(teacher_list, "No teacher texts available.", FONT_TEXT).pack(pady=12)
    else:
        for p in packs:
            frame = tk.Frame(teacher_list, bg=THEME["bg"])
            frame.pack(fill="x", padx=12, pady=6)
            make_label(frame, p.get("title", "Untitled"), FONT_SUBTITLE).pack(side="left")
            def start_pack2(pack=p):
                # Open the English screen with the teacher-created pack
                english.show_english_screen(root, app, pack=pack)
            make_button(frame, "Start", start_pack2, wide=False)

    make_button(root, "Back", app.subject_menu, wide=True)
