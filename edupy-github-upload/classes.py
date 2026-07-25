"""Class membership, teacher ownership, rosters, and class-management UI."""

import csv
import datetime
import random
import string
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import save_system
import account_service
from settings import THEME, FONT_SUBTITLE, FONT_TEXT
from ui import clear, make_button, make_card, make_label, make_page_header, make_scrollable, show_popup, style_notebook


def ensure_classes_root(data):
    data.setdefault("classes", {})
    for class_id, cls in data["classes"].items():
        cls.setdefault("id", class_id)
        cls.setdefault("title", class_id)
        cls.setdefault("subject", "General")
        cls.setdefault("year_group", 7)
        cls.setdefault("teacher_usernames", [])
        cls.setdefault("student_usernames", [])
        cls.setdefault("join_code", _new_join_code(data))
        cls.setdefault("created_at", datetime.datetime.now(datetime.timezone.utc).isoformat())
        cls.setdefault("archived", False)
        cls.setdefault("metadata", {})
    return data["classes"]


def _new_join_code(data):
    existing = {c.get("join_code") for c in data.get("classes", {}).values()}
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = "".join(random.choice(alphabet) for _ in range(6))
        if code not in existing:
            return code


def generate_class_id(data, title):
    """Create a readable unique internal ID from a teacher-facing class name."""
    base = re.sub(r"[^a-z0-9]+", "-", title.strip().lower()).strip("-") or "class"
    existing = set(ensure_classes_root(data))
    candidate, number = base, 2
    while candidate in existing:
        candidate = f"{base}-{number}"; number += 1
    return candidate


def _valid_user(data, username, roles):
    user = data.get("users", {}).get(username)
    return bool(user and user.get("role", "student") in roles)


def _can_manage_class(data, cls, actor):
    if actor is None:
        return False
    profile = save_system.get_user(data, actor)
    return bool(profile and (profile.get("role") == "admin" or actor in cls.get("teacher_usernames", [])))


def create_class(data, class_id, title, teachers=None, students=None, subject="General", year_group=7, actor=None):
    ensure_classes_root(data)
    class_id = class_id.strip().lower().replace(" ", "-")
    if not class_id or not title.strip() or class_id in data["classes"]:
        return False
    valid_teachers = [u for u in dict.fromkeys(teachers or []) if _valid_user(data, u, ("teacher", "admin"))]
    valid_students = [u for u in dict.fromkeys(students or []) if _valid_user(data, u, ("student",))]
    if actor is None or not _valid_user(data, actor, ("teacher", "admin")) or actor not in valid_teachers:
        return False
    data["classes"][class_id] = {
        "id": class_id,
        "title": title.strip(),
        "subject": subject.strip() or "General",
        "year_group": min(11, max(7, int(year_group))),
        "teacher_usernames": valid_teachers,
        "student_usernames": valid_students,
        "join_code": _new_join_code(data),
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "archived": False,
        "metadata": {},
    }
    save_system.append_audit(data, admin=actor, action="create_class", target=class_id, details={"title": title})
    return True


def create_school_account(data, username, password, role="student", year_group=7, database=None):
    if database is None:
        # Creating only a JSON profile would leave a user who cannot securely
        # authenticate. Callers must provide the account database.
        return False
    ok, _message = account_service.create_account(
        data,
        database,
        username,
        password,
        role=role,
        year_group=year_group,
        force_password_change=True,
    )
    return ok


def delete_class(data, class_id, actor=None):
    ensure_classes_root(data)
    if class_id not in data["classes"]:
        return False
    if not _can_manage_class(data, data["classes"][class_id], actor):
        return False
    # Preserve the class and its relationships for school records.
    data["classes"][class_id]["archived"] = True
    for assignment in data.get("assignments", {}).values():
        if assignment.get("class_id") == class_id:
            assignment["status"] = "archived"
    save_system.append_audit(data, admin=actor, action="archive_class", target=class_id)
    return True


def restore_class(data, class_id, actor=None):
    cls = get_class(data, class_id)
    if not cls or not cls.get("archived") or not _can_manage_class(data, cls, actor):
        return False
    cls["archived"] = False
    save_system.append_audit(data, admin=actor, action="restore_class", target=class_id)
    return True


def update_class_details(data, class_id, title, subject, year_group, actor):
    cls = get_class(data, class_id)
    actor_profile = save_system.get_user(data, actor)
    if not cls or not actor_profile:
        return False
    if actor_profile.get("role") != "admin" and actor not in cls.get("teacher_usernames", []):
        return False
    title = title.strip()
    if not title:
        return False
    try:
        year = min(11, max(7, int(year_group)))
    except (TypeError, ValueError):
        return False
    cls["title"] = title
    cls["subject"] = subject.strip() or "General"
    cls["year_group"] = year
    save_system.append_audit(data, admin=actor, action="update_class", target=class_id)
    return True


def regenerate_join_code(data, class_id, actor):
    cls = get_class(data, class_id)
    actor_profile = save_system.get_user(data, actor)
    if not cls or not actor_profile:
        return False
    if actor_profile.get("role") != "admin" and actor not in cls.get("teacher_usernames", []):
        return False
    cls["join_code"] = _new_join_code(data)
    save_system.append_audit(data, admin=actor, action="regenerate_join_code", target=class_id)
    return True


def add_teacher_to_class(data, class_id, username, actor=None):
    cls = get_class(data, class_id)
    if not cls or not _can_manage_class(data, cls, actor) or not _valid_user(data, username, ("teacher", "admin")):
        return False
    if username not in cls["teacher_usernames"]:
        cls["teacher_usernames"].append(username)
        save_system.append_audit(data, admin=actor, action="add_teacher_to_class", target=class_id, details={"teacher": username})
    return True


def remove_teacher_from_class(data, class_id, username, actor=None):
    cls = get_class(data, class_id)
    if not cls or not _can_manage_class(data, cls, actor) or username not in cls["teacher_usernames"] or len(cls["teacher_usernames"]) <= 1:
        return False
    cls["teacher_usernames"].remove(username)
    save_system.append_audit(data, admin=actor, action="remove_teacher_from_class", target=class_id, details={"teacher": username})
    return True


def add_student_to_class(data, class_id, username, actor=None):
    cls = get_class(data, class_id)
    if not cls or not _can_manage_class(data, cls, actor) or not _valid_user(data, username, ("student",)):
        return False
    if username not in cls["student_usernames"]:
        cls["student_usernames"].append(username)
        save_system.append_audit(data, admin=actor, action="add_student_to_class", target=class_id, details={"student": username})
    return True


def remove_student_from_class(data, class_id, username, actor=None):
    cls = get_class(data, class_id)
    if not cls or not _can_manage_class(data, cls, actor) or username not in cls["student_usernames"]:
        return False
    cls["student_usernames"].remove(username)
    save_system.append_audit(data, admin=actor, action="remove_student_from_class", target=class_id, details={"student": username})
    return True


def join_class(data, username, join_code):
    if not _valid_user(data, username, ("student",)):
        return None
    for cls in get_classes(data):
        if cls.get("join_code", "").upper() == join_code.strip().upper():
            if username not in cls["student_usernames"]:
                cls["student_usernames"].append(username)
                save_system.append_audit(data, admin=None, action="join_class", target=cls["id"], details={"student": username})
            return cls
    return None


def get_classes(data, username=None, role=None, include_archived=False):
    classes = list(ensure_classes_root(data).values())
    if not include_archived:
        classes = [c for c in classes if not c.get("archived")]
    if username and role == "teacher":
        classes = [c for c in classes if username in c.get("teacher_usernames", [])]
    elif username and role == "student":
        classes = [c for c in classes if username in c.get("student_usernames", [])]
    return sorted(classes, key=lambda c: (c.get("year_group", 7), c.get("title", "").lower()))


def get_class(data, class_id):
    return ensure_classes_root(data).get(class_id)


def import_roster_from_csv(data, class_id, csv_path, database=None, actor=None):
    """Import student rows formatted as username,password,year_group."""
    created = added = 0
    with open(csv_path, newline="", encoding="utf-8-sig") as file:
        for row_number, row in enumerate(csv.reader(file)):
            if not row or row_number == 0 and row[0].strip().lower() == "username":
                continue
            username = row[0].strip()
            if not username:
                continue
            if username not in data.get("users", {}):
                password = row[1].strip() if len(row) > 1 and row[1].strip() else "changeme"
                year = min(11, max(7, int(row[2]))) if len(row) > 2 and row[2].strip().isdigit() else 7
                if database is None:
                    # Profile-only creation would produce an account that cannot
                    # authenticate through the secure login system.
                    continue
                ok, _message = account_service.create_account(
                    data, database, username, password, role="student",
                    year_group=year, force_password_change=True,
                )
                if not ok:
                    continue
                created += 1
            if add_student_to_class(data, class_id, username, actor):
                added += 1
    save_system.append_audit(data, admin=actor, action="import_roster", target=class_id, details={"created": created, "added": added})
    return created, added


def export_roster_to_csv(data, class_id, path):
    cls = get_class(data, class_id)
    if not cls:
        return False
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["username", "year_group", "level", "total_xp"])
        for username in cls["student_usernames"]:
            user = data["users"].get(username, {})
            writer.writerow([username, user.get("selected_year", 7), user.get("level", 1), user.get("total_xp", 0)])
    return True


def show_student_classes(root, app):
    clear(root)
    body = make_page_header(root, "My Classes", "Join a class with the code your teacher gives you.", app.main_menu)
    body = make_scrollable(body)
    mine = get_classes(app.save_data, app.current_user, "student")
    join_card = make_card(body, "Join a class")
    join_card.pack(fill="x", pady=(0, 14))
    code = tk.Entry(join_card, font=FONT_SUBTITLE, width=14, justify="center")
    code.pack(side="left", padx=(0, 12), pady=8)
    def join():
        cls = join_class(app.save_data, app.current_user, code.get())
        if cls:
            show_popup(app, f"You joined {cls['title']}.")
            show_student_classes(root, app)
        else:
            show_popup(app, "That class code was not found.")
    make_button(join_card, "Join", join)
    if not mine:
        make_label(body, "You have not joined a class yet.", FONT_SUBTITLE).pack(pady=30)
    for cls in mine:
        assignment_count = sum(1 for a in app.save_data.get("assignments", {}).values() if a.get("class_id") == cls["id"] and a.get("status", "published") == "published")
        card = make_card(body, cls["title"], f"{cls['subject']} • Year {cls['year_group']}\nTeachers: {', '.join(cls['teacher_usernames']) or 'Not assigned'} • {assignment_count} assignment(s)", THEME["accent"])
        card.pack(fill="x", pady=7)


def show_class_management(root, app):
    clear(root)
    user = save_system.get_user(app.save_data, app.current_user) or {}
    role = user.get("role", "student")
    if role not in ("teacher", "admin"):
        show_popup(app, "Class management is for teachers.")
        app.main_menu()
        return

    body = make_page_header(root, "Class Management", "Create classes, organise staff, and keep rosters accurate.", app.open_teacher_hub if hasattr(app, "open_teacher_hub") else app.main_menu)
    body = make_scrollable(body)
    style_notebook(root)
    top = tk.Frame(body, bg=THEME["bg"])
    top.pack(fill="x", pady=(0, 12))
    class_var = tk.StringVar()
    selector = ttk.Combobox(top, textvariable=class_var, state="readonly", style="Edu.TCombobox", width=34)
    selector.pack(side="left", padx=(0, 10))
    content = tk.Frame(body, bg=THEME["bg"])
    content.pack(fill="both", expand=True)

    def available():
        return get_classes(app.save_data) if role == "admin" else get_classes(app.save_data, app.current_user, "teacher")

    def selected_class():
        mapping = {f"{c['title']} ({c['id']})": c for c in available()}
        return mapping.get(class_var.get())

    def choose_user(title, candidates, callback):
        if not candidates:
            show_popup(app, "There are no suitable accounts available.")
            return
        win = tk.Toplevel(root); win.title(title); win.configure(bg=THEME["bg"]); win.grab_set()
        make_label(win, title, FONT_SUBTITLE).pack(padx=24, pady=12)
        value = tk.StringVar(value=candidates[0])
        ttk.Combobox(win, values=candidates, textvariable=value, state="readonly", width=28).pack(padx=24, pady=8)
        def done(): callback(value.get()); win.destroy(); refresh()
        make_button(win, "Confirm", done, wide=True); make_button(win, "Cancel", win.destroy, wide=True)

    def refresh(*_):
        classes_now = available()
        values = [f"{c['title']} ({c['id']})" for c in classes_now]
        selector["values"] = values
        if values and class_var.get() not in values:
            class_var.set(values[0])
        for widget in content.winfo_children(): widget.destroy()
        cls = selected_class()
        if not cls:
            make_label(content, "No classes yet. Create your first class to get started.", FONT_SUBTITLE).pack(pady=40)
            return
        summary = tk.Frame(content, bg=THEME["bg"]); summary.pack(fill="x")
        for value, label in ((len(cls["student_usernames"]), "Students"), (len(cls["teacher_usernames"]), "Teachers"), (cls["join_code"], "Join code")):
            card = make_card(summary, str(value), label, THEME["accent"]); card.pack(side="left", fill="x", expand=True, padx=5)
        tabs = ttk.Notebook(content, style="Edu.TNotebook"); tabs.pack(fill="both", expand=True, pady=(14, 0))
        overview = tk.Frame(tabs, bg=THEME["bg"]); roster = tk.Frame(tabs, bg=THEME["bg"]); staff = tk.Frame(tabs, bg=THEME["bg"])
        class_work = tk.Frame(tabs, bg=THEME["bg"]); activity = tk.Frame(tabs, bg=THEME["bg"]); class_settings = tk.Frame(tabs, bg=THEME["bg"])
        tabs.add(overview, text="Overview"); tabs.add(roster, text="Students"); tabs.add(staff, text="Teachers")
        tabs.add(class_work, text="Assignments"); tabs.add(activity, text="Activity"); tabs.add(class_settings, text="Settings")
        make_card(overview, cls["title"], f"{cls['subject']} • Year {cls['year_group']}\nClass ID: {cls['id']}\nStudents can join with code {cls['join_code']}", THEME["accent"]).pack(fill="x", padx=10, pady=12)
        def import_csv():
            path = filedialog.askopenfilename(filetypes=[("CSV roster", "*.csv")])
            if not path: return
            try:
                created, added = import_roster_from_csv(app.save_data, cls["id"], path, app.account_db, app.current_user)
            except (OSError, csv.Error, UnicodeError):
                show_popup(app, "That CSV could not be read. Use columns: username, password, year_group."); return
            refresh(); show_popup(app, f"Roster imported: {created} account(s) created and {added} student(s) added.")
        def export_csv():
            path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV roster", "*.csv")])
            if path: export_roster_to_csv(app.save_data, cls["id"], path); show_popup(app, "Roster exported without passwords.")
        make_button(overview, "Import Student CSV", import_csv); make_button(overview, "Export Progress CSV", export_csv)
        for username in cls["student_usernames"]:
            row = make_card(roster, username, f"Year {app.save_data['users'].get(username, {}).get('selected_year', 7)} • Level {app.save_data['users'].get(username, {}).get('level', 1)}")
            row.pack(fill="x", padx=10, pady=5)
            make_button(row, "Remove", lambda u=username: (remove_student_from_class(app.save_data, cls["id"], u, app.current_user), refresh()))
            def reset_password(student=username):
                win = tk.Toplevel(root); win.title(f"Reset password - {student}"); win.configure(bg=THEME["bg"]); win.grab_set()
                make_label(win, f"Temporary password for {student}", FONT_SUBTITLE).pack(padx=24, pady=12)
                make_label(win, "At least 8 characters. The student must replace it at next sign-in.", FONT_TEXT).pack(padx=24)
                first = tk.Entry(win, font=FONT_TEXT, show="•"); second = tk.Entry(win, font=FONT_TEXT, show="•")
                first.pack(fill="x", padx=24, pady=6); second.pack(fill="x", padx=24, pady=6)
                def save_password():
                    if first.get() != second.get(): show_popup(app, "The two passwords do not match."); return
                    ok, message = account_service.reset_managed_password(app.save_data, app.account_db, app.current_user, student, first.get())
                    if ok: win.destroy()
                    show_popup(app, message)
                make_button(win, "Save Temporary Password", save_password, wide=True); make_button(win, "Cancel", win.destroy, wide=True)
            make_button(row, "Reset Password", reset_password)
        student_candidates = [u for u, info in app.save_data.get("users", {}).items() if info.get("role", "student") == "student" and u not in cls["student_usernames"]]
        make_button(roster, "Add Existing Student", lambda: choose_user("Add student", student_candidates, lambda u: add_student_to_class(app.save_data, cls["id"], u, app.current_user)), wide=True)
        for username in cls["teacher_usernames"]:
            row = make_card(staff, username, "Teacher account"); row.pack(fill="x", padx=10, pady=5)
            if len(cls["teacher_usernames"]) > 1:
                make_button(row, "Remove", lambda u=username: (remove_teacher_from_class(app.save_data, cls["id"], u, app.current_user), refresh()))
        teacher_candidates = [u for u, info in app.save_data.get("users", {}).items() if info.get("role") in ("teacher", "admin") and u not in cls["teacher_usernames"]]
        make_button(staff, "Add Teacher", lambda: choose_user("Add teacher", teacher_candidates, lambda u: add_teacher_to_class(app.save_data, cls["id"], u, app.current_user)), wide=True)

        import assignments as assignment_tools
        work = [item for item in assignment_tools.ensure_assignments_root(app.save_data).values() if item.get("class_id") == cls["id"]]
        intro = make_card(class_work, "Class assignments", "Create work, review submissions, and manage deadlines from the Assignment Centre.", THEME["accent"])
        intro.pack(fill="x", padx=10, pady=10)
        make_button(intro, "Open Assignment Centre", lambda: assignment_tools.show_teacher_assignments(root, app), wide=True)
        if not work:
            make_label(class_work, "No assignments have been created for this class.", FONT_TEXT).pack(pady=20)
        for item in sorted(work, key=lambda value: value.get("created_at", ""), reverse=True):
            submitted = len(item.get("submissions", {}))
            make_card(
                class_work,
                item.get("title", "Untitled assignment"),
                f"{item.get('status', 'draft').title()} • Due {item.get('due_date') or 'any time'} • {submitted}/{len(cls['student_usernames'])} submitted",
            ).pack(fill="x", padx=10, pady=5)

        assignment_ids = {item.get("id") for item in work}
        events = [
            event for event in reversed(save_system.get_audit_log(app.save_data, 500))
            if event.get("target") == cls["id"]
            or event.get("target") in assignment_ids
            or (event.get("details") or {}).get("class") == cls["id"]
        ]
        if not events:
            make_label(activity, "No recorded class activity yet.", FONT_TEXT).pack(pady=25)
        for event in events[:50]:
            action = event.get("action", "activity").replace("_", " ").title()
            who = event.get("admin") or (event.get("details") or {}).get("student") or "EduPy"
            when = str(event.get("time", ""))[:16].replace("T", " ")
            make_card(activity, action, f"{who} • {when}").pack(fill="x", padx=10, pady=4)

        settings_card = make_card(class_settings, "Class details", "Update the name, subject, year group, or replace the join code.", THEME["accent"])
        settings_card.pack(fill="x", padx=10, pady=10)
        title_value = tk.StringVar(value=cls["title"]); subject_value = tk.StringVar(value=cls["subject"]); year_value = tk.StringVar(value=str(cls["year_group"]))
        for label, widget in (
            ("Class name", tk.Entry(settings_card, textvariable=title_value, font=FONT_TEXT)),
            ("Subject", tk.Entry(settings_card, textvariable=subject_value, font=FONT_TEXT)),
            ("Year group", ttk.Combobox(settings_card, values=[str(y) for y in range(7, 12)], textvariable=year_value, state="readonly")),
        ):
            make_label(settings_card, label, FONT_TEXT).pack(anchor="w", pady=(6, 1)); widget.pack(fill="x")
        def save_details():
            if update_class_details(app.save_data, cls["id"], title_value.get(), subject_value.get(), year_value.get(), app.current_user):
                show_popup(app, "Class details updated."); refresh()
            else:
                show_popup(app, "Check the class details and try again.")
        def new_join_code():
            if messagebox.askyesno("Replace join code", "The current join code will stop working. Continue?") and regenerate_join_code(app.save_data, cls["id"], app.current_user):
                show_popup(app, "A new join code was created."); refresh()
        make_button(settings_card, "Save Class Details", save_details, wide=True)
        make_button(settings_card, "Replace Join Code", new_join_code, wide=True)

    def create_dialog():
        win = tk.Toplevel(root); win.title("Create class"); win.configure(bg=THEME["bg"]); win.grab_set()
        fields = {}
        for label in ("Class name", "Subject"):
            make_label(win, label, FONT_TEXT).pack(anchor="w", padx=24); entry = tk.Entry(win, font=FONT_TEXT, width=34); entry.pack(padx=24, pady=(2, 8)); fields[label] = entry
        year = tk.StringVar(value="7"); make_label(win, "Year group", FONT_TEXT).pack(anchor="w", padx=24)
        ttk.Combobox(win, values=[str(y) for y in range(7, 12)], textvariable=year, state="readonly").pack(padx=24, pady=(2, 10))
        def create():
            class_id = generate_class_id(app.save_data, fields["Class name"].get())
            ok = create_class(app.save_data, class_id, fields["Class name"].get(), [app.current_user], subject=fields["Subject"].get(), year_group=year.get(), actor=app.current_user)
            if not ok: show_popup(app, "Add a class name and subject, then try again."); return
            win.destroy(); refresh()
        make_button(win, "Create Class", create, wide=True); make_button(win, "Cancel", win.destroy, wide=True)

    def account_dialog(account_role):
        win = tk.Toplevel(root); win.title(f"New {account_role} account"); win.configure(bg=THEME["bg"]); win.grab_set()
        make_label(win, f"Create {account_role.title()} Account", FONT_SUBTITLE).pack(padx=24, pady=12)
        make_label(win, "Username", FONT_TEXT).pack(anchor="w", padx=24); username = tk.Entry(win, font=FONT_TEXT); username.pack(padx=24, pady=(2, 8))
        make_label(win, "Temporary password (at least 8 characters)", FONT_TEXT).pack(anchor="w", padx=24); password = tk.Entry(win, font=FONT_TEXT, show="*"); password.pack(padx=24, pady=(2, 8))
        year = tk.StringVar(value="7")
        if account_role == "student":
            make_label(win, "Year group", FONT_TEXT).pack(anchor="w", padx=24); ttk.Combobox(win, values=[str(y) for y in range(7, 12)], textvariable=year, state="readonly").pack(padx=24, pady=(2, 8))
        def create_account():
            if not create_school_account(app.save_data, username.get(), password.get(), account_role, year.get(), app.account_db):
                show_popup(app, "Use a unique username and a password of at least 8 characters."); return
            win.destroy(); show_popup(app, f"{account_role.title()} account created."); refresh()
        make_button(win, "Create Account", create_account, wide=True); make_button(win, "Cancel", win.destroy, wide=True)

    make_button(top, "New Class", create_dialog)
    make_button(top, "New Student", lambda: account_dialog("student"))
    if role == "admin":
        make_button(top, "New Teacher", lambda: account_dialog("teacher"))
    def delete_selected():
        cls = selected_class()
        if cls and messagebox.askyesno("Archive class", f"Archive {cls['title']} and its assignments? You can restore the class later."):
            delete_class(app.save_data, cls["id"], app.current_user); class_var.set(""); refresh()
    def archived_dialog():
        archived = [item for item in get_classes(app.save_data, app.current_user, role, include_archived=True) if item.get("archived")]
        win = tk.Toplevel(root); win.title("Archived classes"); win.geometry("620x520"); win.configure(bg=THEME["bg"]); win.grab_set()
        content = make_scrollable(win, padx=20, pady=14); make_label(content, "Archived Classes", FONT_SUBTITLE).pack(pady=8)
        if not archived: make_label(content, "No archived classes.", FONT_TEXT).pack(pady=30)
        for item in archived:
            card = make_card(content, item["title"], f"{item['subject']} • Year {item['year_group']}"); card.pack(fill="x", pady=5)
            def restore(class_id=item["id"]):
                if restore_class(app.save_data, class_id, app.current_user): win.destroy(); refresh(); show_popup(app, "Class restored. Its old assignments remain archived until you republish them.")
            make_button(card, "Restore Class", restore)
        make_button(content, "Close", win.destroy, wide=True)
    make_button(top, "Archive Class", delete_selected)
    make_button(top, "Archived", archived_dialog)
    selector.bind("<<ComboboxSelected>>", refresh)
    refresh()
