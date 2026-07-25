# main.py

import tkinter as tk
import os
import sqlite3
from tkinter import messagebox, ttk
from ui import clear, make_action_tile, make_button, make_card, make_label, make_page_header, make_scrollable, make_section_header, make_stat, show_popup
from settings import THEME, FONT_BUTTON, FONT_TITLE, FONT_SUBTITLE, FONT_TEXT, set_theme
import shop
import english
import maths
import progress
import save_system
import minigames
import assignments
import classes
import teacher_dashboard
import audio
import curriculum
import curriculum_ui
import platform_features
import admin_dashboard
import parent_portal
import account_service
import education_service
import progress_service
from experience_store import ExperienceStore
import learning_experience
import ui
import backup_service
import game_hub


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Questoria - Learn. Play. Level Up.")
        ui.configure_root(self.root)
        ui.style_notebook(self.root)

        self.fullscreen = True
        try:
            self.root.attributes("-fullscreen", True)
        except Exception:
            pass
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))
        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

        # Load or create save data
        self.save_data = save_system.load_save()
        self.account_db = account_service.create_default_database()
        self.account_migration = account_service.migrate_legacy_accounts(self.save_data, self.account_db)
        self.account_profile_repairs = account_service.sync_profile_roles(self.save_data, self.account_db)
        self.education_store, self.education_migration = education_service.activate_education_database(self.save_data, self.account_db)
        self.progress_store, self.progress_migration = progress_service.activate_progress_database(self.save_data, self.account_db)
        self.experience_store = ExperienceStore(self.account_db.engine)
        self.backup_status = None
        self.backup_error = None
        try:
            self.backup_status = backup_service.create_daily_backup(
                self.account_db.path, save_system.SAVE_FILE,
                os.path.join(save_system.BASE_DIR, "backups"),
            )
        except (OSError, ValueError, sqlite3.Error) as error:
            # A backup problem should not lock learners out of the application.
            self.backup_error = str(error)
        self.current_user = None
        audio.init_audio()

        # The platform is designed for secondary-school learners.
        self.difficulty_name = "Year 7"
        self.difficulty_value = 7
        self.gcse_mode = False

        # Start UI
        self.show_login_screen()
        self.root.mainloop()

    # -------------------------
    # Navigation wrappers used by ui.py
    # -------------------------
    def open_shop(self):
        """Open the earned-rewards area."""
        shop.show_shop_screen(self.root, self)

    def open_progress(self):
        progress.show_progress_screen(self.root, self)

    def start_english(self):
        english.show_english_screen(self.root, self)

    def start_maths(self):
        maths.show_maths_screen(self.root, self)

    def start_minigames(self):
        minigames.show_minigames_menu(self.root, self)

    # -------------------------
    # Basic app utilities
    # -------------------------
    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        try:
            self.root.attributes("-fullscreen", self.fullscreen)
        except Exception:
            pass

    def quit_app(self):
        """Save local progress and close Questoria after confirmation."""
        if not messagebox.askyesno(
            "Leave Questoria",
            "Leave the adventure for now?\n\nYour quest progress will be saved.",
            parent=self.root,
        ):
            return
        try:
            save_system.save_save(self.save_data)
        finally:
            self.root.destroy()

    # -------------------------
    # Login / account screens
    # -------------------------
    def show_login_screen(self):
        clear(self.root)
        shell = tk.Frame(self.root, bg=THEME["bg"])
        shell.pack(fill="both", expand=True, padx=70, pady=48)
        brand = tk.Frame(shell, bg=THEME.get("panel", THEME["bg"]), padx=44, pady=42, highlightthickness=1, highlightbackground=THEME.get("border", THEME["accent"]))
        brand.pack(side="left", fill="both", expand=True, padx=(0, 12))
        tk.Label(brand, text="QUESTORIA", font=("Segoe UI", 11, "bold"), bg=brand["bg"], fg=THEME["accent"]).pack(anchor="w")
        tk.Label(brand, text="Learn. Play.\nLevel up.", font=("Segoe UI", 36, "bold"), bg=brand["bg"], fg=THEME["fg"], justify="left").pack(anchor="w", pady=(14, 15))
        tk.Label(brand, text="Enter a world where every lesson is a mission and knowledge is your strongest power.", font=FONT_TEXT, bg=brand["bg"], fg=THEME.get("muted", THEME["fg"]), justify="left", wraplength=390).pack(anchor="w", pady=(0, 24))
        for number, title, detail in (("01", "Explore", "Travel through Maths and English realms"), ("02", "Battle", "Beat challenges with skill and strategy"), ("03", "Level Up", "Earn ranks, quest stars, and rewards")):
            row = tk.Frame(brand, bg=brand["bg"]); row.pack(fill="x", pady=7)
            tk.Label(row, text=number, font=("Segoe UI", 10, "bold"), bg=THEME.get("accent_soft", brand["bg"]), fg=THEME["accent"], padx=9, pady=5).pack(side="left", padx=(0, 12))
            copy = tk.Frame(row, bg=brand["bg"]); copy.pack(side="left", fill="x", expand=True)
            tk.Label(copy, text=title, font=FONT_BUTTON, bg=brand["bg"], fg=THEME["fg"], anchor="w").pack(fill="x")
            tk.Label(copy, text=detail, font=("Segoe UI", 10), bg=brand["bg"], fg=THEME.get("muted", THEME["fg"]), anchor="w").pack(fill="x")
        form = make_card(shell, "Welcome back", "Sign in to continue where you left off.", THEME["accent"], padding=32)
        form.pack(side="right", fill="both", expand=True, padx=(12, 0))
        make_label(form, "Username", FONT_TEXT).pack(anchor="w", pady=(22, 3))
        username_entry = tk.Entry(form, font=("Segoe UI", 14), relief="flat", bg=THEME.get("input_bg", THEME["panel_alt"]), fg=THEME["fg"], insertbackground=THEME["fg"])
        username_entry.pack(fill="x", ipady=8)
        username_entry.focus()
        make_label(form, "Password", FONT_TEXT).pack(anchor="w", pady=(16, 3))
        password_entry = tk.Entry(form, font=("Segoe UI", 14), show="•", relief="flat", bg=THEME.get("input_bg", THEME["panel_alt"]), fg=THEME["fg"], insertbackground=THEME["fg"])
        password_entry.pack(fill="x", ipady=8)
        show_password = tk.BooleanVar(value=False)
        tk.Checkbutton(form, text="Show password", variable=show_password, command=lambda: password_entry.config(show="" if show_password.get() else "•"), font=FONT_TEXT, bg=form["bg"], fg=THEME["fg"], selectcolor=THEME.get("panel_alt", form["bg"])).pack(anchor="w", pady=(5, 0))

        def login():
            username = username_entry.get().strip()
            password = password_entry.get()

            if username == "" or password == "":
                show_popup(self, "Please enter both username and password.")
                return

            account = account_service.authenticate(self.account_db, username, password)
            if account is None:
                show_popup(self, "The username or password is incorrect.")
                return

            users = self.save_data.setdefault("users", {})
            if username not in users:
                show_popup(self, "This account is missing its learning profile. Ask an administrator for help.")
                return
            if account.force_password_change:
                self.show_change_password_screen(account)
                return
            self.complete_login(account)

        username_entry.bind("<Return>", lambda event: password_entry.focus())
        password_entry.bind("<Return>", lambda event: login())
        make_button(form, "Sign In", login, wide=True)
        make_button(form, "Create Student Account", self.show_create_account_screen, wide=True, kind="secondary")
        make_button(form, "Leave Questoria", self.quit_app, wide=True, kind="secondary")

    def complete_login(self, account):
        """Apply trusted database details and open the correct home screen."""
        self.current_user = account.username
        user = self.save_data["users"][account.username]
        changed = user.get("role") != account.role or user.get("selected_year") != account.year_group
        user["role"] = account.role
        user["admin"] = account.role == "admin"
        user["selected_year"] = account.year_group
        if changed:
            save_system.save_save(self.save_data)

        self.difficulty_value = min(11, max(7, int(account.year_group)))
        self.difficulty_name = f"Year {self.difficulty_value}"
        self.gcse_mode = self.difficulty_value >= 10
        try:
            set_theme(user.get("current_theme", "Default"))
            ui.apply_accessibility(self.root, self.experience_store.preferences(account.username))
            ui.configure_root(self.root)
            ui.style_notebook(self.root)
            self.root.configure(bg=THEME["bg"])
        except Exception:
            pass
        self.main_menu()

    def show_change_password_screen(self, account):
        clear(self.root)
        body = make_page_header(
            self.root,
            "Choose Your Own Password",
            "Your temporary password worked. Replace it before continuing.",
            self.show_login_screen,
        )
        form = make_card(body, "Secure your account", "Use at least 8 characters and keep it private.", THEME["accent"], padding=24)
        form.pack(fill="both", expand=True, padx=170, pady=25)
        make_label(form, "New password", FONT_TEXT).pack(anchor="w", pady=(12, 2))
        new_password = tk.Entry(form, font=("Segoe UI", 13), show="•", bg=THEME.get("input_bg", THEME["panel_alt"]), fg=THEME["fg"], insertbackground=THEME["fg"], relief="flat")
        new_password.pack(fill="x", ipady=6)
        make_label(form, "Type it again", FONT_TEXT).pack(anchor="w", pady=(12, 2))
        confirmation = tk.Entry(form, font=("Segoe UI", 13), show="•", bg=THEME.get("input_bg", THEME["panel_alt"]), fg=THEME["fg"], insertbackground=THEME["fg"], relief="flat")
        confirmation.pack(fill="x", ipady=6)
        reveal = tk.BooleanVar(value=False)
        def reveal_passwords():
            symbol = "" if reveal.get() else "•"; new_password.config(show=symbol); confirmation.config(show=symbol)
        tk.Checkbutton(form, text="Show passwords", variable=reveal, command=reveal_passwords, font=FONT_TEXT, bg=form["bg"], fg=THEME["fg"], selectcolor=THEME.get("panel_alt", form["bg"])).pack(anchor="w", pady=5)

        def save_password():
            if new_password.get() != confirmation.get():
                show_popup(self, "The two passwords do not match.")
                return
            ok, message = account_service.change_password(self.account_db, account.username, new_password.get())
            if not ok:
                show_popup(self, message)
                return
            show_popup(self, message)
            self.complete_login(self.account_db.get_account(account.username))

        new_password.focus()
        new_password.bind("<Return>", lambda event: confirmation.focus())
        confirmation.bind("<Return>", lambda event: save_password())
        make_button(form, "Save New Password", save_password, wide=True)

    def show_create_account_screen(self):
        clear(self.root)
        body = make_page_header(self.root, "Create Student Account", "Teachers can create managed accounts from Class Management.", self.show_login_screen)
        body = make_scrollable(body)
        form = make_card(body, "Your details", "Choose a username, secure password, and current year group.", THEME["accent"], padding=24)
        form.pack(fill="both", expand=True, padx=170, pady=15)
        make_label(form, "Username", FONT_TEXT).pack(anchor="w", pady=(12, 2))
        username_entry = tk.Entry(form, font=("Segoe UI", 13), bg=THEME.get("input_bg", THEME["panel_alt"]), fg=THEME["fg"], insertbackground=THEME["fg"], relief="flat"); username_entry.pack(fill="x", ipady=7)
        make_label(form, "Password (at least 8 characters)", FONT_TEXT).pack(anchor="w", pady=(12, 2))
        password_entry = tk.Entry(form, font=("Segoe UI", 13), show="•", bg=THEME.get("input_bg", THEME["panel_alt"]), fg=THEME["fg"], insertbackground=THEME["fg"], relief="flat"); password_entry.pack(fill="x", ipady=7)
        make_label(form, "Type the password again", FONT_TEXT).pack(anchor="w", pady=(12, 2))
        confirmation_entry = tk.Entry(form, font=("Segoe UI", 13), show="•", bg=THEME.get("input_bg", THEME["panel_alt"]), fg=THEME["fg"], insertbackground=THEME["fg"], relief="flat"); confirmation_entry.pack(fill="x", ipady=7)
        reveal = tk.BooleanVar(value=False)
        def reveal_passwords():
            symbol = "" if reveal.get() else "•"; password_entry.config(show=symbol); confirmation_entry.config(show=symbol)
        tk.Checkbutton(form, text="Show passwords", variable=reveal, command=reveal_passwords, font=FONT_TEXT, bg=form["bg"], fg=THEME["fg"], selectcolor=THEME.get("panel_alt", form["bg"])).pack(anchor="w", pady=5)
        make_label(form, "Year Group", FONT_TEXT).pack(anchor="w", pady=(12, 2))
        year_var = tk.StringVar(value="Year 7")
        ttk.Combobox(
            form,
            values=[f"Year {year}" for year in range(7, 12)],
            textvariable=year_var,
            state="readonly",
            font=FONT_TEXT,
            width=18,
        ).pack(fill="x", ipady=5)

        def create():
            username = username_entry.get().strip()
            password = password_entry.get()

            if password != confirmation_entry.get():
                show_popup(self, "The two passwords do not match.")
                return

            ok, message = account_service.create_account(
                self.save_data,
                self.account_db,
                username,
                password,
                role="student",
                year_group=int(year_var.get().split()[-1]),
            )
            if not ok:
                show_popup(self, message)
                return
            show_popup(self, message)
            self.show_login_screen()

        make_button(form, "Create Account", create, wide=True)

    # -------------------------
    # Main menu and navigation
    # -------------------------
    def main_menu(self):
        clear(self.root)

        user = save_system.get_user(self.save_data, self.current_user) or {}
        role = user.get("role", "student")
        if role == "student":
            game_hub.show_game_hub(self.root, self)
            return
        if role == "admin":
            admin_dashboard.show_admin_dashboard(self.root, self)
            return
        if role == "parent":
            parent_portal.show_parent_dashboard(self.root, self)
            return
        level = user.get("level", 1)
        xp = user.get("xp", 0)

        body = make_page_header(self.root, f"Welcome back, {self.current_user}", f"{self.difficulty_name} • {role.title()} workspace")
        body = make_scrollable(body)
        stats = tk.Frame(body, bg=THEME["bg"]); stats.pack(fill="x", pady=(0, 14))
        make_stat(stats, level, "Level", THEME["accent"]).pack(side="left", fill="x", expand=True, padx=5)
        make_stat(stats, f"{xp}/{level * 100}", "XP to next level", "#58D68D").pack(side="left", fill="x", expand=True, padx=5)
        make_stat(stats, user.get("tokens", 0), "Tokens", "#FFB84D").pack(side="left", fill="x", expand=True, padx=5)
        if role == "student":
            recommendation = curriculum.recommend_next(self.save_data, self.current_user)
            if recommendation:
                rec = make_card(body, f"Recommended next: {recommendation['title']}", f"{recommendation['subject']} • {recommendation['reason']}", "#58D68D"); rec.pack(fill="x", padx=6, pady=(0, 8))
                def start_recommendation(item=recommendation):
                    if item["subject"] == "Maths": maths.show_maths_screen(self.root, self, item["topic"])
                    else: english.show_english_screen(self.root, self, topic=item["topic"])
                make_button(rec, "Start Recommended Activity", start_recommendation)
        grid = tk.Frame(body, bg=THEME["bg"]); grid.pack(fill="both", expand=True)
        for column in range(2): grid.grid_columnconfigure(column, weight=1, uniform="menu")
        actions = [("Learn", "Maths, English, and focused mini games.", self.subject_menu)]
        if role == "student":
            actions.extend([("Assignments", "View due work, submit answers, and read feedback.", lambda: assignments.show_student_assignments(self.root, self)), ("My Classes", "Join classes and see your teachers.", lambda: classes.show_student_classes(self.root, self))])
        if role in ("teacher", "admin"):
            actions.append(("Teacher Hub", "Manage classes, assignments, marking, and progress.", self.open_teacher_hub))
        actions.extend([("Rewards", "Earn tokens through learning and unlock themes.", lambda: shop.show_shop_screen(self.root, self)), ("Progress", "Review your XP, sessions, and achievements.", lambda: progress.show_progress_screen(self.root, self)), ("Safety & Settings", "Accessibility, privacy requests, and safeguarding reports.", lambda: learning_experience.show_safety_centre(self.root, self)), ("Year Group", f"Currently set to {self.difficulty_name}.", self.difficulty_menu)])
        for index, (title, description, command) in enumerate(actions):
            card = make_card(grid, title, description, THEME["accent"]); card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=7, pady=7)
            make_button(card, "Open", command, wide=True)
        footer = tk.Frame(body, bg=THEME["bg"]); footer.pack(fill="x", pady=(10, 0))
        make_button(footer, "Toggle Fullscreen (F11)", self.toggle_fullscreen)
        make_button(footer, "Logout", self.logout)
        make_button(footer, "Leave Questoria", self.quit_app, kind="secondary")

    def logout(self):
        self.current_user = None
        self.show_login_screen()

    def open_teacher_hub(self):
        teacher_dashboard.show_teacher_hub(self.root, self)

    def subject_menu(self):
        clear(self.root)
        body = make_page_header(self.root, "Choose a Subject", f"Activities are tuned for {self.difficulty_name}.", self.main_menu)
        body = make_scrollable(body)
        make_section_header(body, "Pick a learning space", "You can switch subjects whenever you want.")
        grid = tk.Frame(body, bg=THEME["bg"]); grid.pack(fill="both", expand=True)
        for column in range(3): grid.grid_columnconfigure(column, weight=1, uniform="subjects")
        options = [("Maths", "Worked examples, guided methods and adaptive practice.", lambda: maths.show_maths_screen(self.root, self), "#4EA3FF"), ("English", "Reading, analysis and writing for your current year.", lambda: english.show_english_screen(self.root, self), "#B56BFF"), ("Curriculum Explorer", "Search all years, follow pathways and save useful units.", lambda: curriculum_ui.show_curriculum_explorer(self.root, self), "#FFB84D"), ("Mini-Games", "Short, balanced challenges for fluency and memory.", lambda: minigames.show_minigames_menu(self.root, self), "#58D68D")]
        for index, (title, description, command, accent) in enumerate(options):
            make_action_tile(grid, title, description, command, accent).grid(row=index // 3, column=index % 3, sticky="nsew", padx=7, pady=7)

    def difficulty_menu(self):
        clear(self.root)
        body = make_page_header(self.root, "Choose Your Year Group", "Questions, texts and recommendations will match this level.", self.main_menu)
        content = make_scrollable(body)

        def set_diff(name, value):
            self.difficulty_name = name
            self.difficulty_value = value
            self.gcse_mode = value >= 10
            user = save_system.get_user(self.save_data, self.current_user)
            if user is not None:
                user["selected_year"] = value
                self.account_db.update_account(self.current_user, year_group=value)
                save_system.save_save(self.save_data)
            self.subject_menu()

        grid = tk.Frame(content, bg=THEME["bg"]); grid.pack(fill="both", expand=True, pady=12)
        for column in range(3): grid.grid_columnconfigure(column, weight=1, uniform="years")
        for index, (label, value, detail) in enumerate((("Year 7",7,"Build strong secondary foundations"),("Year 8",8,"Develop fluency and deeper analysis"),("Year 9",9,"Prepare for GCSE-style thinking"),("Year 10",10,"GCSE knowledge and application"),("Year 11",11,"Exam readiness and final revision"))):
            make_action_tile(grid, label, detail, lambda n=label, v=value: set_diff(n, v), "#4EA3FF" if value < 10 else "#B56BFF").grid(row=index//3, column=index%3, sticky="nsew", padx=7, pady=7)

    # -------------------------
    # Admin menu and helpers
    # -------------------------
    def admin_menu(self):
        clear(self.root)
        make_label(self.root, "Admin Mode", FONT_TITLE).pack(pady=20)

        make_button(self.root, "Toggle School Safe Mode", self.toggle_school_safe, wide=True)
        make_button(self.root, "Back", self.main_menu, wide=True)

    def toggle_school_safe(self):
        if not self.current_user:
            show_popup(self, "No user logged in.")
            return
        users = self.save_data.setdefault("users", {})
        user = users.get(self.current_user, {})
        user["school_safe_mode"] = not user.get("school_safe_mode", False)
        save_system.save_save(self.save_data)
        show_popup(self, f"School Safe Mode: {user['school_safe_mode']}")

    # -------------------------
    # Learning access
    # -------------------------
    def check_time(self):
        # Learning is always available. Rewards are earned through participation.
        return True


if __name__ == "__main__":
    App()
