# editor.py
"""
Lesson editor UI for teachers.
Supports:
- Create / edit English text packs (title, tags, text, questions)
- Create / edit simple maths templates (title, template text)
- Save to save_data['content_packs'] via save_system.add_content_pack
"""

import tkinter as tk
from ui import clear, make_label, make_button, make_scrollable, show_popup
from settings import THEME, FONT_TITLE, FONT_SUBTITLE, FONT_TEXT
import save_system
import uuid
import json


def show_editor(root, app):
    clear(root)
    content = make_scrollable(root)

    make_label(content, "Lesson Editor", FONT_TITLE).pack(pady=12)

    make_button(content, "Create English Text", lambda: edit_english(root, app), wide=False)
    make_button(content, "Create Maths Template", lambda: edit_maths(root, app), wide=False)
    make_button(content, "Import JSON (paste)", lambda: import_json_editor(root, app), wide=False)
    make_button(content, "Back", app.open_teacher_hub if hasattr(app, "open_teacher_hub") else app.main_menu, wide=True)


def import_json_editor(root, app):
    clear(root)
    content = make_scrollable(root)
    make_label(content, "Paste JSON content pack", FONT_TITLE).pack(pady=12)
    txt = tk.Text(content, height=20, width=80, bg=THEME["bg"], fg=THEME["fg"])
    txt.pack(pady=8)
    def do_import():
        try:
            pack = json.loads(txt.get("1.0", tk.END))
            if not isinstance(pack, dict):
                show_popup(app, "Invalid JSON: expected an object")
                return
            if "id" not in pack:
                pack["id"] = str(uuid.uuid4())
            save_system.add_content_pack(app.save_data, pack)
            show_popup(app, "Imported content pack")
            show_editor(root, app)
        except Exception as e:
            show_popup(app, f"Import failed: {e}")
    make_button(content, "Import", do_import, wide=True)
    make_button(content, "Back", lambda: show_editor(root, app), wide=True)


# -------------------------
# English editor
# -------------------------

def edit_english(root, app, pack=None):
    clear(root)
    content = make_scrollable(root)
    if pack is None:
        pack = {"id": str(uuid.uuid4()), "type": "english", "title": "", "tags": [], "text": "", "questions": []}

    make_label(content, "English Text Editor", FONT_TITLE).pack(pady=8)

    make_label(content, "Title", FONT_SUBTITLE).pack(anchor="w", padx=12)
    title_entry = tk.Entry(content, font=FONT_TEXT, width=60)
    title_entry.insert(0, pack.get("title", ""))
    title_entry.pack(pady=6, padx=12)

    make_label(content, "Tags (comma separated)", FONT_SUBTITLE).pack(anchor="w", padx=12)
    tags_entry = tk.Entry(content, font=FONT_TEXT, width=60)
    tags_entry.insert(0, ",".join(pack.get("tags", [])))
    tags_entry.pack(pady=6, padx=12)

    make_label(content, "Text", FONT_SUBTITLE).pack(anchor="w", padx=12)
    text_box = tk.Text(content, height=10, width=80, bg=THEME["bg"], fg=THEME["fg"])
    text_box.insert("1.0", pack.get("text", ""))
    text_box.pack(pady=6, padx=12)

    # Questions area (simple JSON editor for questions)
    make_label(content, "Questions (JSON list)", FONT_SUBTITLE).pack(anchor="w", padx=12)
    qtxt = tk.Text(content, height=8, width=80, bg=THEME["bg"], fg=THEME["fg"])
    qtxt.insert("1.0", json.dumps(pack.get("questions", []), indent=2))
    qtxt.pack(pady=6, padx=12)

    def save_pack():
        title = title_entry.get().strip()
        tags = [t.strip() for t in tags_entry.get().split(",") if t.strip()]
        text = text_box.get("1.0", tk.END).strip()
        try:
            questions = json.loads(qtxt.get("1.0", tk.END))
            if not isinstance(questions, list):
                raise ValueError("Questions must be a list")
        except Exception as e:
            show_popup(app, f"Invalid questions JSON: {e}")
            return
        pack["title"] = title
        pack["tags"] = tags
        pack["text"] = text
        pack["questions"] = questions
        save_system.add_content_pack(app.save_data, pack)
        show_popup(app, "Saved English content pack")
        show_editor(root, app)

    make_button(content, "Save", save_pack, wide=True)
    make_button(content, "Back", lambda: show_editor(root, app), wide=True)


# -------------------------
# Maths editor (simple template)
# -------------------------

def edit_maths(root, app, pack=None):
    clear(root)
    content = make_scrollable(root)
    if pack is None:
        pack = {"id": str(uuid.uuid4()), "type": "maths", "title": "", "template": ""}

    make_label(content, "Maths Template Editor", FONT_TITLE).pack(pady=8)

    make_label(content, "Title", FONT_SUBTITLE).pack(anchor="w", padx=12)
    title_entry = tk.Entry(content, font=FONT_TEXT, width=60)
    title_entry.insert(0, pack.get("title", ""))
    title_entry.pack(pady=6, padx=12)

    make_label(content, "Template (use placeholders)", FONT_SUBTITLE).pack(anchor="w", padx=12)
    template_box = tk.Text(content, height=12, width=80, bg=THEME["bg"], fg=THEME["fg"])
    template_box.insert("1.0", pack.get("template", ""))
    template_box.pack(pady=6, padx=12)

    def save_pack():
        title = title_entry.get().strip()
        template = template_box.get("1.0", tk.END).strip()
        pack["title"] = title
        pack["template"] = template
        save_system.add_content_pack(app.save_data, pack)
        show_popup(app, "Saved Maths template")
        show_editor(root, app)

    make_button(content, "Save", save_pack, wide=True)
    make_button(content, "Back", lambda: show_editor(root, app), wide=True)
