# progress.py

import tkinter as tk
from ui import clear, make_label, make_button, make_card, make_page_header, make_progress_bar, make_scrollable, make_section_header, make_stat
from settings import THEME, FONT_SUBTITLE, FONT_TEXT
import audio
import save_system
import curriculum
import game_state


# ============================================================
# XP + LEVEL SYSTEM
# ============================================================

def get_user_data(app):
    """Return the save data for the current user."""
    username = app.current_user
    if username not in app.save_data["users"]:
        raise RuntimeError("The signed-in account is missing its learning profile.")
    return save_system.ensure_user_schema(app.save_data["users"][username])


def add_xp(app, amount, questions=1):
    """Add XP once and optionally count answered questions."""
    user = get_user_data(app)

    amount = max(0, int(amount))
    user["xp"] += amount
    user["total_xp"] = user.get("total_xp", 0) + amount
    user["questions_answered"] += max(0, int(questions))
    if amount > 0 and questions:
        game_state.record_event(user, "correct_answers", questions)

    # Level-up threshold formula
    required = user["level"] * 100

    leveled_up = False
    while user["xp"] >= required:
        user["xp"] -= required
        user["level"] += 1
        required = user["level"] * 100
        leveled_up = True

    save_system.save_save(app.save_data)

    if leveled_up:
        audio.play_level_up()


def record_answer(app):
    """Count an answered question when it earns no XP."""
    user = get_user_data(app)
    user["questions_answered"] += 1
    save_system.save_save(app.save_data)


# ============================================================
# PROGRESS SCREEN
# ============================================================

def show_progress_screen(root, app):
    clear(root)
    body = make_page_header(root, "Your Progress", "See what you have practised and choose a useful next step.", app.main_menu)
    content = make_scrollable(body, padx=20, pady=10)
    user = get_user_data(app)
    stats = tk.Frame(content, bg=THEME["bg"]); stats.pack(fill="x", pady=(0, 12))
    for value, label, colour in (
        (user["level"], "Level", THEME["accent"]),
        (user.get("total_xp", user["xp"]), "Total XP", "#58D68D"),
        (user["questions_answered"], "Questions", "#4EA3FF"),
        (user["maths_completed"] + user["english_completed"], "Activities", "#B56BFF"),
    ):
        make_stat(stats, value, label, colour).pack(side="left", fill="x", expand=True, padx=4)
    level_card = make_card(content, "Next level", f"{user['xp']} of {user['level'] * 100} XP earned", THEME["accent"]); level_card.pack(fill="x", pady=6)
    make_progress_bar(level_card, user["xp"] / max(1, user["level"] * 100) * 100, THEME["accent"]).pack(fill="x", pady=(12, 2))
    make_section_header(content, "Topic confidence", "Confidence is based only on topics you have actually practised.")
    year = user.get("selected_year", 7)
    subjects = tk.Frame(content, bg=THEME["bg"]); subjects.pack(fill="x")
    for column in range(2): subjects.grid_columnconfigure(column, weight=1, uniform="progress_subjects")
    for index, (subject, colour) in enumerate((("Maths", "#4EA3FF"), ("English", "#B56BFF"))):
        scores = curriculum.subject_mastery(user, year, subject)
        attempted = [score for topic, score in scores.items() if user.get("mastery", {}).get(subject, {}).get(topic, {}).get("attempts", 0)]
        average = round(sum(attempted) / len(attempted)) if attempted else 0
        detail = f"{average}% average across {len(attempted)} practised topic(s)" if attempted else "No topic evidence yet — start with a lesson or the Starting Check."
        card = make_card(subjects, subject, detail, colour); card.grid(row=0, column=index, sticky="nsew", padx=5, pady=5)
        make_progress_bar(card, average, colour).pack(fill="x", pady=(10, 2))
        make_button(card, "Open Subject", app.start_maths if subject == "Maths" else app.start_english)
    recent = list(reversed(user.get("recent_topics", [])[-6:]))
    make_label(content, "Recent practice", FONT_SUBTITLE).pack(anchor="w", pady=(14, 4))
    if not recent:
        make_card(content, "Nothing recorded yet", "Your latest practice scores will appear here.").pack(fill="x", pady=5)
    for item in recent:
        title = curriculum.topic_title(year, item.get("subject", "Maths"), item.get("topic", ""))
        make_card(content, title, f"{item.get('subject', '')} • {item.get('score', 0)}% • {item.get('date', '')}", "#58D68D" if item.get("score", 0) >= 70 else "#FFB84D").pack(fill="x", pady=4)


# ============================================================
# SESSION COMPLETION HELPERS
# ============================================================

def maths_completed(app):
    """Call when a maths session is completed."""
    user = get_user_data(app)
    user["maths_completed"] += 1
    game_state.record_event(user, "learning_sessions")
    save_system.award_tokens(app.save_data, app.current_user, 3, "Completed a maths session")


def english_completed(app):
    """Call when an English text is completed."""
    user = get_user_data(app)
    user["english_completed"] += 1
    game_state.record_event(user, "learning_sessions")
    save_system.award_tokens(app.save_data, app.current_user, 3, "Completed an English activity")
