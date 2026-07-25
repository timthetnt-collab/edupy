# import_export.py
"""
Content-pack import/export helpers.

Full-save replacement was retired when accounts, classes and progress moved to
the relational database. Replacing only the old JSON file would now create an
inconsistent or insecure installation.
"""

import tkinter as tk
from tkinter import filedialog
from ui import clear, make_label, make_button, show_popup
from settings import FONT_TITLE, FONT_SUBTITLE, FONT_TEXT
import json
import os


def show_import_export(root, app):
    clear(root)
    make_label(root, "Import / Export", FONT_TITLE).pack(pady=12)

    make_button(root, "Export content packs", lambda: export_packs_dialog(app), wide=False)
    make_label(root, "Full account backups are managed by EduPy. Old JSON save imports are disabled to protect secure accounts and class records.", FONT_TEXT).pack(pady=12)
    make_button(root, "Back", app.open_shop, wide=True)


def export_save_dialog(app):
    show_popup(app, "Full-save export is retired because secure data now spans multiple protected stores.")


def export_packs_dialog(app):
    path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    if not path:
        return
    try:
        packs = app.save_data.get("content_packs", [])
        with open(path, "w") as f:
            json.dump(packs, f, indent=2)
        show_popup(app, f"Exported {len(packs)} content packs")
    except Exception as e:
        show_popup(app, f"Export failed: {e}")


def import_save_dialog(app, replace=False):
    del replace
    show_popup(app, "Old full-save imports are disabled to protect accounts, classes, and progress.")
