"""Earned rewards and cosmetic themes. No payments or subscriptions."""

import datetime
import tkinter as tk
from tkinter import ttk

import achievements
import save_system
from settings import THEME, THEMES, FONT_SUBTITLE, FONT_TEXT, set_theme
from ui import apply_accessibility, apply_theme_to_root, clear, configure_root, make_button, make_card, make_label, make_page_header, make_scrollable, make_section_header, make_stat, show_popup, style_notebook


THEME_COSTS = {
    "Default": 0, "Study Paper": 10, "Academy": 20, "Focus Mint": 20,
    "Ocean": 25, "Sunset": 35, "Matrix": 50, "Neon": 60,
}


def get_user_data(app, username=None):
    username = username or app.current_user
    user = save_system.get_user(app.save_data, username)
    if user is None:
        raise RuntimeError("The signed-in account is missing its learning profile.")
    return user


def save(app):
    save_system.save_save(app.save_data)


def claim_daily_reward(app):
    user = get_user_data(app)
    today = datetime.date.today()
    if user.get("last_daily_claim") == today.isoformat():
        return 0
    if user.get("token_earn_day") != today.isoformat() or int(user.get("tokens_earned_today", 0)) <= 0:
        return 0
    yesterday = (today - datetime.timedelta(days=1)).isoformat()
    streak = int(user.get("daily_reward_streak", 0)) + 1 if user.get("last_daily_claim") == yesterday else 1
    user["daily_reward_streak"] = streak
    user["last_daily_claim"] = today.isoformat()
    amount = 2 + min(3, streak - 1)
    save_system.award_tokens(
        app.save_data,
        app.current_user,
        amount,
        f"Daily reward (day {streak})",
        daily_cap=None,
        count_toward_cap=False,
        event_id=f"daily:{app.current_user}:{today.isoformat()}",
    )
    return amount


def buy_theme(root, app, theme_name, price):
    user = get_user_data(app)
    if theme_name not in THEMES:
        return False
    if theme_name in user.get("themes_unlocked", []):
        apply_theme(root, app, theme_name)
        return True
    if user.get("tokens", 0) < price:
        show_popup(app, f"You need {price - user.get('tokens', 0)} more tokens. Complete learning activities to earn them.")
        return False
    if not save_system.purchase_theme(app.save_data, app.current_user, theme_name, price):
        return False
    show_popup(app, f"{theme_name} unlocked!")
    show_shop_screen(root, app)
    return True


def apply_theme(root, app, theme_name):
    if theme_name not in get_user_data(app).get("themes_unlocked", ["Default"]):
        return False
    set_theme(theme_name)
    if hasattr(app, "experience_store"):
        apply_accessibility(root, app.experience_store.preferences(app.current_user))
    configure_root(root); style_notebook(root)
    get_user_data(app)["current_theme"] = theme_name
    save(app)
    root.configure(bg=THEME["bg"])
    apply_theme_to_root(root)
    show_shop_screen(root, app)
    return True


def _build_rewards_tab(parent, root, app):
    user = get_user_data(app)
    stats = tk.Frame(parent, bg=THEME["bg"]); stats.pack(fill="x", padx=10, pady=12)
    make_stat(stats, user.get("tokens", 0), "Tokens", THEME["accent"]).pack(side="left", fill="x", expand=True, padx=5)
    make_stat(stats, user.get("daily_reward_streak", 0), "Daily streak", "#FFB84D").pack(side="left", fill="x", expand=True, padx=5)
    make_stat(stats, user.get("tokens_earned_today", 0), "Activity tokens today", "#58D68D").pack(side="left", fill="x", expand=True, padx=5)
    eligible = user.get("token_earn_day") == datetime.date.today().isoformat() and int(user.get("tokens_earned_today", 0)) > 0
    daily = make_card(parent, "Learning streak bonus", "Complete a learning activity, then claim 2 bonus tokens. Consecutive active days gradually increase this to 5.", "#FFB84D"); daily.pack(fill="x", padx=14, pady=7)
    claimed = user.get("last_daily_claim") == datetime.date.today().isoformat()
    def claim():
        amount = claim_daily_reward(app)
        message = f"You earned {amount} bonus tokens!" if amount else "Complete a learning activity first, or come back tomorrow if today's bonus is already claimed."
        show_popup(app, message)
        show_shop_screen(root, app)
    make_button(daily, "Claimed Today" if claimed else "Claim Learning Bonus" if eligible else "Complete Learning to Unlock", claim)
    ways = make_card(parent, "How to earn tokens", "Maths session: 3 • English activity: 3 • Marked assignment: up to 15\nActivity rewards are capped at 20 per day so progress stays balanced.", THEME["accent"]); ways.pack(fill="x", padx=14, pady=7)
    history = make_card(parent, "Recent activity", accent=THEME.get("panel_alt", THEME["accent"])); history.pack(fill="both", expand=True, padx=14, pady=7)
    entries = list(reversed(user.get("reward_history", [])[-8:]))
    if not entries: make_label(history, "No rewards earned yet — complete an activity to begin.", FONT_TEXT).pack(anchor="w")
    for entry in entries:
        amount = int(entry.get("amount", 0)); colour = "#58D68D" if amount >= 0 else "#FF8A80"
        row = tk.Frame(history, bg=history["bg"]); row.pack(fill="x", pady=3)
        tk.Label(row, text=entry.get("reason", "Reward"), font=FONT_TEXT, bg=row["bg"], fg=THEME["fg"]).pack(side="left")
        tk.Label(row, text=f"{amount:+d}", font=FONT_SUBTITLE, bg=row["bg"], fg=colour).pack(side="right")


def _build_themes_tab(parent, root, app):
    user = get_user_data(app)
    make_section_header(parent, "Choose your look", "Themes use learning tokens only and never affect access to lessons.")
    grid = tk.Frame(parent, bg=THEME["bg"]); grid.pack(fill="both", expand=True, padx=8)
    for column in range(2): grid.grid_columnconfigure(column, weight=1, uniform="theme_cards")
    for index, (theme_name, cost) in enumerate(THEME_COSTS.items()):
        palette = THEMES[theme_name]; owned = theme_name in user.get("themes_unlocked", ["Default"]); active = user.get("current_theme") == theme_name
        card = make_card(grid, theme_name, f"{cost} tokens" if not owned else ("Currently active" if active else "Unlocked"), palette["accent"]); card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=6, pady=6)
        swatches = tk.Frame(card, bg=card["bg"]); swatches.pack(fill="x", pady=(12, 4))
        for colour in (palette["bg"], palette["accent"], palette["button_bg"]): tk.Frame(swatches, bg=colour, width=38, height=24).pack(side="left", padx=3)
        if not active: make_button(card, "Use" if owned else f"Unlock • {cost}", lambda n=theme_name, c=cost: (apply_theme(root, app, n) if n in get_user_data(app).get("themes_unlocked", []) else buy_theme(root, app, n, c)))


def _build_achievements_tab(parent, app):
    achievements.check_unlocks(app)
    user = get_user_data(app)
    make_section_header(parent, "Achievements", "Milestones recognise real activity and steady progress.")
    grid = tk.Frame(parent, bg=THEME["bg"]); grid.pack(fill="both", expand=True, padx=8)
    for column in range(2): grid.grid_columnconfigure(column, weight=1, uniform="achievement_cards")
    for index, achievement in enumerate(achievements.get_all_achievements()):
        unlocked = achievement["id"] in user.get("achievements_unlocked", [])
        card = make_card(grid, ("✓ " if unlocked else "○ ") + achievement["title"], achievement["desc"], "#58D68D" if unlocked else THEME.get("panel_alt", THEME["accent"])); card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=6, pady=6)


def show_shop_screen(root, app):
    clear(root)
    body = make_page_header(root, "Rewards Locker", "Everything here is earned by learning — there are no payments.", app.main_menu)
    style_notebook(root)
    notebook = ttk.Notebook(body, style="Edu.TNotebook"); notebook.pack(fill="both", expand=True)
    rewards = tk.Frame(notebook, bg=THEME["bg"]); themes = tk.Frame(notebook, bg=THEME["bg"]); achievement_tab = tk.Frame(notebook, bg=THEME["bg"])
    notebook.add(rewards, text="Rewards"); notebook.add(themes, text="Themes"); notebook.add(achievement_tab, text="Achievements")
    _build_rewards_tab(make_scrollable(rewards), root, app)
    _build_themes_tab(make_scrollable(themes), root, app)
    _build_achievements_tab(make_scrollable(achievement_tab), app)
