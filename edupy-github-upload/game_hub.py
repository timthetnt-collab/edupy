"""The student-facing Questoria game home screen."""

import tkinter as tk

import assignments
import classes
import curriculum
import curriculum_ui
import english
import game_state
import learning_experience
import maths
import minigames
import platform_features
import save_system
from settings import THEME
from ui import (
    clear,
    make_button,
    make_card,
    make_page_header,
    make_progress_bar,
    make_scrollable,
    make_section_header,
    make_stat,
    show_popup,
)


WORLD_ZONES = (
    ("Number Meadows", "Maths", 1, "Train your number powers through guided battles.", "#4EA3FF"),
    ("Wordwood Forest", "English", 1, "Decode texts and forge stronger writing skills.", "#B56BFF"),
    ("Puzzle Peaks", "Mini-Games", 2, "Take on quick challenges for fluency and memory.", "#58D68D"),
    ("Scholar's Citadel", "Curriculum", 4, "Choose advanced paths and conquer whole units.", "#FFB84D"),
)


def _open_zone(root, app, zone):
    if zone == "Maths":
        maths.show_maths_screen(root, app)
    elif zone == "English":
        english.show_english_screen(root, app)
    elif zone == "Mini-Games":
        minigames.show_minigames_menu(root, app)
    else:
        curriculum_ui.show_curriculum_explorer(root, app)


def show_game_hub(root, app):
    clear(root)
    user = save_system.get_user(app.save_data, app.current_user) or {}
    state = game_state.ensure_game_state(user)
    level = int(user.get("level", 1))
    xp = int(user.get("xp", 0))
    required = max(100, level * 100)

    body = make_page_header(
        root,
        "QUESTORIA",
        f"{game_state.hero_title(level)} {app.current_user} - Year {app.difficulty_value}",
    )
    body = make_scrollable(body, padx=22, pady=10)

    hero = make_card(
        body,
        f"Adventure Rank {level}",
        "Every lesson is a mission. Every correct answer powers up your hero.",
        THEME["accent"],
        padding=22,
    )
    hero.pack(fill="x", pady=(0, 10))
    stats = tk.Frame(hero, bg=hero["bg"])
    stats.pack(fill="x", pady=(14, 8))
    make_stat(stats, state.get("stars", 0), "Quest Stars", "#FFB84D").pack(side="left", fill="x", expand=True, padx=4)
    make_stat(stats, user.get("tokens", 0), "Gold Tokens", "#58D68D").pack(side="left", fill="x", expand=True, padx=4)
    make_stat(stats, user.get("questions_answered", 0), "Challenges", "#4EA3FF").pack(side="left", fill="x", expand=True, padx=4)
    make_progress_bar(hero, xp / required * 100, THEME["accent"]).pack(fill="x", pady=(6, 2))
    tk.Label(
        hero,
        text=f"{xp}/{required} XP until Adventure Rank {level + 1}",
        bg=hero["bg"],
        fg=THEME.get("muted", THEME["fg"]),
    ).pack(anchor="w")

    diagnostic = app.experience_store.latest_diagnostic(app.current_user)
    recommendation = curriculum.recommend_next(app.save_data, app.current_user)
    if not diagnostic:
        main_quest = make_card(
            body,
            "PROLOGUE: Discover Your Powers",
            "Complete an 8-question starting challenge so the world can adapt to you. This is not a grade.",
            "#FFB84D",
            padding=20,
        )
        main_quest.pack(fill="x", pady=8)
        make_button(main_quest, "Begin Prologue", lambda: learning_experience.show_diagnostic(root, app), wide=True)
    elif recommendation:
        main_quest = make_card(
            body,
            f"MAIN QUEST: {recommendation['title']}",
            f"{recommendation['subject']} mission - {recommendation['reason']}",
            "#58D68D",
            padding=20,
        )
        main_quest.pack(fill="x", pady=8)

        def start_main(item=recommendation):
            if item["subject"] == "Maths":
                maths.show_maths_screen(root, app, item["topic"])
            else:
                english.show_english_screen(root, app, topic=item["topic"])

        make_button(main_quest, "Start Main Quest", start_main, wide=True)

    make_section_header(body, "Today's quests", "Complete all three for stars and gold tokens.")
    quest_grid = tk.Frame(body, bg=THEME["bg"])
    quest_grid.pack(fill="x", pady=(0, 8))
    for column in range(3):
        quest_grid.grid_columnconfigure(column, weight=1, uniform="daily_quests")
    for index, quest in enumerate(game_state.DAILY_QUESTS):
        current, target = game_state.quest_progress(user, quest)
        claimed = quest["id"] in state["daily"].get("claimed", [])
        complete = current >= target
        accent = "#58D68D" if complete else "#4EA3FF"
        card = make_card(
            quest_grid,
            ("CLAIMED - " if claimed else "") + quest["title"],
            f"{quest['description']}\nReward: {quest['stars']} star(s) + {quest['tokens']} tokens",
            accent,
        )
        card.grid(row=0, column=index, sticky="nsew", padx=5, pady=5)
        make_progress_bar(card, current / target * 100, accent).pack(fill="x", pady=(10, 4))

        def claim(quest_id=quest["id"]):
            _, message = game_state.claim_quest(app, quest_id)
            show_popup(app, message)
            show_game_hub(root, app)

        make_button(card, "Claim Reward" if complete and not claimed else f"Progress {current}/{target}", claim, wide=True)

    make_section_header(body, "Adventure map", "Choose a realm. New regions unlock as your adventure rank grows.")
    world = tk.Frame(body, bg=THEME["bg"])
    world.pack(fill="x", pady=(0, 8))
    for column in range(2):
        world.grid_columnconfigure(column, weight=1, uniform="world_zones")
    for index, (title, zone, unlock_level, description, colour) in enumerate(WORLD_ZONES):
        unlocked = level >= unlock_level
        status = "READY" if unlocked else f"LOCKED - Rank {unlock_level}"
        card = make_card(world, f"{status}: {title}", description, colour if unlocked else THEME.get("border", "#777777"))
        card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=6, pady=6)
        if unlocked:
            make_button(card, "Enter Realm", lambda z=zone: _open_zone(root, app, z), wide=True)

    due = [
        item for item in assignments.assignments_for_student(app.save_data, app.current_user)
        if assignments.assignment_state(item, app.current_user) in ("To do", "Overdue")
    ]
    make_section_header(body, "Base camp", "Manage your adventure, gear, guild, and player settings.")
    camp = tk.Frame(body, bg=THEME["bg"])
    camp.pack(fill="x", pady=(0, 12))
    for column in range(3):
        camp.grid_columnconfigure(column, weight=1, uniform="camp")
    actions = (
        ("Quest Log", f"{len(due)} guild assignment(s) waiting", lambda: assignments.show_student_assignments(root, app), "#FF7043"),
        ("Guild Hall", "Classes, teachers, and teammates", lambda: classes.show_student_classes(root, app), "#58D68D"),
        ("Hero Progress", "Ranks, mastery, and achievements", app.open_progress, "#4EA3FF"),
        ("Rewards Locker", "Spend earned tokens on themes", app.open_shop, "#FFB84D"),
        ("Adventurer's Toolkit", "Revision, mock exams, and portfolio", lambda: platform_features.show_student_toolkit(root, app), "#5EC7C2"),
        ("Player Settings", "Accessibility, privacy, and safety", lambda: learning_experience.show_safety_centre(root, app), "#FF7AA2"),
    )
    for index, (title, description, command, colour) in enumerate(actions):
        card = make_card(camp, title, description, colour)
        card.grid(row=index // 3, column=index % 3, sticky="nsew", padx=5, pady=5)
        make_button(card, "Open", command, wide=True)

    footer = tk.Frame(body, bg=THEME["bg"])
    footer.pack(fill="x", pady=(4, 10))
    make_button(footer, "Change Year", app.difficulty_menu, kind="secondary")
    make_button(footer, "Log Out", app.logout, kind="secondary")
    make_button(footer, "Quit Game", app.quit_app, kind="secondary")
