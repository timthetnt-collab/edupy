"""Secure whole-school administration workspace for EduPy."""

import tkinter as tk
from tkinter import ttk

import account_service
import classes
import parent_portal
import save_system
from settings import THEME, FONT_SUBTITLE, FONT_TEXT
from ui import (clear, make_action_tile, make_button, make_card, make_label,
                make_page_header, make_scrollable, make_section_header,
                make_stat, show_popup, style_notebook)


def _is_admin(app):
    account = app.account_db.get_account(app.current_user) if app.current_user else None
    return bool(account and account.role == "admin" and account.is_active)


def _reauthenticate(app, password):
    account = account_service.authenticate(app.account_db, app.current_user, password)
    return bool(account and account.role == "admin")


def _create_account_dialog(root, app):
    win = tk.Toplevel(root); win.title("Create managed account"); win.geometry("520x650")
    win.configure(bg=THEME["bg"]); win.grab_set()
    body = make_scrollable(win, padx=24, pady=18)
    make_label(body, "Create Managed Account", FONT_SUBTITLE).pack(pady=(0, 8))
    make_card(body, "Secure setup", "The temporary password must be replaced the first time this user signs in.", "#4EA3FF").pack(fill="x", pady=6)
    username = tk.StringVar(); temporary = tk.StringVar(); role = tk.StringVar(value="student")
    year = tk.StringVar(value="7"); admin_password = tk.StringVar()
    for label, variable, hidden in (
        ("Username", username, False), ("Temporary password", temporary, True),
    ):
        make_label(body, label, FONT_TEXT).pack(anchor="w", pady=(8, 1))
        tk.Entry(body, textvariable=variable, font=FONT_TEXT, show="*" if hidden else "").pack(fill="x", ipady=6)
    make_label(body, "Account role", FONT_TEXT).pack(anchor="w", pady=(8, 1))
    ttk.Combobox(body, values=["student", "teacher", "parent", "admin"], textvariable=role, state="readonly").pack(fill="x")
    make_label(body, "Year group", FONT_TEXT).pack(anchor="w", pady=(8, 1))
    ttk.Combobox(body, values=[str(year) for year in range(7, 12)], textvariable=year, state="readonly").pack(fill="x")
    make_label(body, "Confirm with your admin password", FONT_TEXT).pack(anchor="w", pady=(8, 1))
    tk.Entry(body, textvariable=admin_password, font=FONT_TEXT, show="*").pack(fill="x", ipady=6)

    def create():
        if not _reauthenticate(app, admin_password.get()):
            show_popup(app, "Your administrator password was not accepted."); return
        ok, message = account_service.create_account(
            app.save_data, app.account_db, username.get(), temporary.get(), role.get(), year.get(),
            force_password_change=True,
        )
        if not ok:
            show_popup(app, message); return
        save_system.append_audit(app.save_data, admin=app.current_user, action="admin_create_account",
                                 target=username.get(), details={"role": role.get()})
        save_system.save_save(app.save_data); win.destroy(); show_popup(app, "Managed account created.")
        show_admin_dashboard(root, app, "Accounts")

    make_button(body, "Create Account", create, wide=True)
    make_button(body, "Cancel", win.destroy, wide=True, kind="secondary")


def _manage_account_dialog(root, app, record):
    win = tk.Toplevel(root); win.title(f"Manage {record['username']}"); win.geometry("510x610")
    win.configure(bg=THEME["bg"]); win.grab_set()
    body = make_scrollable(win, padx=24, pady=18)
    make_label(body, record["username"], FONT_SUBTITLE).pack(pady=(0, 6))
    make_card(
        body, "Current access",
        f"Role: {record['role'].title()}\nLogin: {'Enabled' if record['active'] else 'Disabled'}\nYear {record['year_group']}",
        "#58D68D" if record["active"] else "#FF7043",
    ).pack(fill="x", pady=6)
    role = tk.StringVar(value=record["role"]); admin_password = tk.StringVar(); temporary = tk.StringVar()
    make_label(body, "New role", FONT_TEXT).pack(anchor="w", pady=(8, 1))
    ttk.Combobox(body, values=["student", "teacher", "parent", "admin"], textvariable=role, state="readonly").pack(fill="x")
    make_label(body, "Confirm with your admin password", FONT_TEXT).pack(anchor="w", pady=(8, 1))
    tk.Entry(body, textvariable=admin_password, font=FONT_TEXT, show="*").pack(fill="x", ipady=6)

    def authorised():
        if _reauthenticate(app, admin_password.get()): return True
        show_popup(app, "Your administrator password was not accepted."); return False

    def change_role():
        if not authorised(): return
        ok, message = account_service.change_managed_role(
            app.save_data, app.account_db, app.current_user, record["username"], role.get(),
        )
        show_popup(app, message)
        if not ok: return
        save_system.save_save(app.save_data); win.destroy()
        if record["username"] == app.current_user and role.get() != "admin": app.logout()
        else: show_admin_dashboard(root, app, "Accounts")

    def toggle_login():
        if not authorised(): return
        ok, message = account_service.set_managed_account_active(
            app.save_data, app.account_db, app.current_user, record["username"], not record["active"],
        )
        show_popup(app, message)
        if ok:
            save_system.save_save(app.save_data); win.destroy(); show_admin_dashboard(root, app, "Accounts")

    make_button(body, "Save Role", change_role, wide=True)
    make_button(body, "Enable Login" if not record["active"] else "Disable Login", toggle_login, wide=True, kind="secondary")
    if record["role"] != "admin" and record["username"] != app.current_user:
        make_label(body, "New temporary password", FONT_TEXT).pack(anchor="w", pady=(10, 1))
        tk.Entry(body, textvariable=temporary, font=FONT_TEXT, show="*").pack(fill="x", ipady=6)
        def reset_password():
            if not authorised(): return
            ok, message = account_service.reset_managed_password(
                app.save_data, app.account_db, app.current_user, record["username"], temporary.get(),
            )
            show_popup(app, message)
            if ok:
                save_system.save_save(app.save_data); win.destroy(); show_admin_dashboard(root, app, "Accounts")
        make_button(body, "Set Temporary Password", reset_password, wide=True, kind="secondary")
    make_button(body, "Cancel", win.destroy, wide=True, kind="secondary")


def _overview_tab(parent, root, app, notebook, tabs, accounts, school_classes, queues):
    body = make_scrollable(parent)
    make_section_header(body, "School at a glance", "Live information from secure accounts and school records.")
    active = [account for account in accounts if account["active"]]
    stats = tk.Frame(body, bg=THEME["bg"]); stats.pack(fill="x", pady=6)
    values = (
        (sum(item["role"] == "student" for item in active), "Active students", "#4EA3FF"),
        (sum(item["role"] == "teacher" for item in active), "Active teachers", "#B56BFF"),
        (len(school_classes), "Classes", "#58D68D"),
        (sum(len(items) for items in queues.values()), "Items to review", "#FFB84D"),
    )
    for value, label, colour in values:
        make_stat(stats, value, label, colour).pack(side="left", fill="x", expand=True, padx=4)
    grid = tk.Frame(body, bg=THEME["bg"]); grid.pack(fill="x", pady=8)
    for column in range(2): grid.grid_columnconfigure(column, weight=1, uniform="admin_alerts")
    alerts = (
        ("Safeguarding reports", len(queues["safety"]), "Safety & Privacy", "#FF7043"),
        ("Privacy requests", len(queues["privacy"]), "Safety & Privacy", "#4EA3FF"),
        ("Questions awaiting approval", len(queues["pending"]), "Moderation", "#FFB84D"),
        ("Reported content", len(queues["reports"]), "Moderation", "#B56BFF"),
    )
    for index, (title, count, target, colour) in enumerate(alerts):
        make_action_tile(grid, title, f"{count} item(s) currently need review.", lambda name=target: notebook.select(tabs[name]), colour).grid(
            row=index // 2, column=index % 2, sticky="nsew", padx=5, pady=5,
        )
    admin_count = sum(item["role"] == "admin" and item["active"] for item in accounts)
    disabled = sum(not item["active"] for item in accounts)
    make_card(
        body, "Security status",
        f"{admin_count} active administrator(s) · {disabled} disabled login(s)\n"
        "Passwords are hashed and never displayed. Account changes require administrator re-authentication.",
        "#58D68D",
    ).pack(fill="x", pady=7)
    actions = make_card(body, "Administrator tools", "Open the teacher workspace or manage the school configuration.", THEME["accent"])
    actions.pack(fill="x", pady=7)
    make_button(actions, "Teacher Workspace", lambda: __import__('platform_features').show_teacher_studio(root, app))
    make_button(actions, "Class Manager", lambda: classes.show_class_management(root, app), kind="secondary")


def _accounts_tab(parent, root, app):
    body = make_scrollable(parent)
    bar = make_card(body, "Account Directory", "Search accounts, change roles, reset passwords or disable access.", "#4EA3FF")
    bar.pack(fill="x", pady=6)
    query = tk.StringVar(); role = tk.StringVar(value="All roles"); status = tk.StringVar(value="All logins")
    row = tk.Frame(bar, bg=bar["bg"]); row.pack(fill="x", pady=5)
    tk.Entry(row, textvariable=query, font=FONT_TEXT).pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 5))
    ttk.Combobox(row, values=["All roles", "Student", "Teacher", "Parent", "Admin"], textvariable=role, state="readonly", width=12).pack(side="left", padx=4)
    ttk.Combobox(row, values=["All logins", "Enabled", "Disabled"], textvariable=status, state="readonly", width=12).pack(side="left", padx=4)
    make_button(bar, "Create Managed Account", lambda: _create_account_dialog(root, app), wide=True)
    make_button(bar, "Manage Family Links", lambda: parent_portal.show_family_link_manager(root, app), wide=True, kind="secondary")
    results = tk.Frame(body, bg=THEME["bg"]); results.pack(fill="x")

    def rebuild(*_):
        for child in results.winfo_children(): child.destroy()
        records = account_service.account_summaries(app.account_db); needle = query.get().strip().lower()
        if needle: records = [item for item in records if needle in item["username"].lower()]
        if role.get() != "All roles": records = [item for item in records if item["role"] == role.get().lower()]
        if status.get() != "All logins": records = [item for item in records if item["active"] == (status.get() == "Enabled")]
        make_section_header(results, f"{len(records)} account(s)", "Password hashes and private wellbeing notes are never shown.")
        for record in records:
            detail = f"{record['role'].title()} · Year {record['year_group']} · {'Login enabled' if record['active'] else 'Login disabled'}"
            if record["force_password_change"]: detail += " · Password change required"
            card = make_card(results, record["username"], detail, "#58D68D" if record["active"] else "#FF7043")
            card.pack(fill="x", pady=4)
            make_button(card, "Manage Access", lambda item=record: _manage_account_dialog(root, app, item))
    for variable in (query, role, status): variable.trace_add("write", rebuild)
    rebuild()


def _classes_tab(parent, root, app, school_classes):
    body = make_scrollable(parent)
    intro = make_card(body, "Class Administration", "Manage rosters, teachers, join codes, assignments and curriculum coverage.", "#58D68D")
    intro.pack(fill="x", pady=6)
    make_button(intro, "Open Full Class Manager", lambda: classes.show_class_management(root, app))
    make_button(intro, "Open Coverage Map", lambda: __import__('platform_features').show_coverage_map(root, app), kind="secondary")
    for item in school_classes:
        work = sum(assignment.get("class_id") == item["id"] for assignment in app.save_data.get("assignments", {}).values())
        make_card(
            body, item["title"],
            f"{item['subject']} · Year {item['year_group']} · {len(item.get('student_usernames', []))} students · "
            f"{len(item.get('teacher_usernames', []))} staff · {work} assignments",
            THEME["accent"],
        ).pack(fill="x", pady=4)
    if not school_classes:
        make_card(body, "No classes yet", "Use the Class Manager to create the first class.").pack(fill="x", pady=6)


def _moderation_tab(parent, root, app, pending, reports):
    body = make_scrollable(parent)
    make_section_header(body, "Questions awaiting approval", f"{len(pending)} pending")
    for item in pending:
        card = make_card(body, item["prompt"], f"By {item['owner']} · Year {item['year']} {item['subject']}\nExpected answer: {item['answer']}", "#FFB84D")
        card.pack(fill="x", pady=5)
        make_button(card, "Approve", lambda question=item["id"]: (
            app.experience_store.moderate_question(app.current_user, question, "approved", "Clear and suitable for the selected unit."),
            show_admin_dashboard(root, app, "Moderation"),
        ))
        make_button(card, "Return for Changes", lambda question=item["id"]: (
            app.experience_store.moderate_question(app.current_user, question, "rejected", "Please revise the wording or expected answer."),
            show_admin_dashboard(root, app, "Moderation"),
        ), kind="secondary")
    make_section_header(body, "Reported content", f"{len(reports)} open report(s)")
    for item in reports:
        card = make_card(body, f"Report from {item['reporter']}", f"Question reference: {item['question_id'] or 'General'}\n{item['reason']}", "#FF7043")
        card.pack(fill="x", pady=4)
        make_button(card, "Mark Reviewed", lambda report=item["id"]: (
            app.experience_store.content_reports(app.current_user, report), show_admin_dashboard(root, app, "Moderation"),
        ), kind="secondary")
    if not pending and not reports:
        make_card(body, "Moderation queue clear", "There are no questions or reports waiting for review.", "#58D68D").pack(fill="x", pady=6)


def _safety_tab(parent, root, app, safety, privacy):
    body = make_scrollable(parent)
    make_card(body, "Restricted records", "Only administrators can access this queue. Follow your school safeguarding policy.", "#FF7043").pack(fill="x", pady=6)
    make_section_header(body, "Safeguarding reports", f"{len(safety)} active")
    for item in safety:
        card = make_card(body, item["category"], f"Reported by {item['reporter']} · {item['created_at'][:16]} · {item['status'].replace('_', ' ').title()}\n{item['description']}", "#FF7043")
        card.pack(fill="x", pady=4)
        history = app.experience_store.safeguarding_actions(app.current_user, item["id"])
        if history:
            make_label(card, "Case history:\n" + "\n".join(
                f"• {row['created_at'][:16]} — {row['actor']}: {row['action'].title()}" + (f" — {row['note']}" if row['note'] else "")
                for row in history[-5:]
            ), FONT_TEXT).pack(anchor="w", pady=4)

        def case_action(report, action):
            win = tk.Toplevel(root); win.title("Safeguarding case action"); win.configure(bg=THEME["bg"]); win.grab_set()
            make_label(win, action.replace("_", " ").title(), FONT_SUBTITLE).pack(padx=24, pady=10)
            note = tk.Text(win, height=6, width=55, font=FONT_TEXT); note.pack(padx=24, pady=6)
            def save():
                if app.experience_store.add_safeguarding_action(app.current_user, report, action, note.get("1.0", "end")):
                    win.destroy(); show_admin_dashboard(root, app, "Safety & Privacy")
                else: show_popup(app, "The case action could not be saved.")
            make_button(win, "Save Restricted Case Action", save, wide=True)
            make_button(win, "Cancel", win.destroy, wide=True, kind="secondary")

        actions = tk.Frame(card, bg=card["bg"]); actions.pack(fill="x")
        make_button(actions, "Add Restricted Note", lambda report=item["id"]: case_action(report, "note"), kind="secondary")
        make_button(actions, "Assign / Start Review", lambda report=item["id"]: case_action(report, "assigned"))
        make_button(actions, "Escalate", lambda report=item["id"]: case_action(report, "escalated"), kind="secondary")
        make_button(actions, "Resolve", lambda report=item["id"]: case_action(report, "resolved"))
    make_section_header(body, "Privacy requests", f"{len(privacy)} open")
    for item in privacy:
        card = make_card(body, item["request_type"].replace("_", " ").title(), f"{item['username']} · {item['created_at'][:16]}", "#4EA3FF")
        card.pack(fill="x", pady=4)
        make_button(card, "Mark Reviewed", lambda request=item["id"]: (
            app.experience_store.resolve_privacy_request(app.current_user, request), show_admin_dashboard(root, app, "Safety & Privacy"),
        ))
    make_button(body, "Open Full Safety & Accessibility Centre", lambda: __import__('learning_experience').show_safety_centre(root, app), wide=True, kind="secondary")


def _audit_tab(parent, app):
    body = make_scrollable(parent); query = tk.StringVar()
    search = make_card(body, "Audit Trail", "Important account, class, assignment and moderation actions are recorded here.", "#B56BFF")
    search.pack(fill="x", pady=6); tk.Entry(search, textvariable=query, font=FONT_TEXT).pack(fill="x", ipady=6, pady=5)
    results = tk.Frame(body, bg=THEME["bg"]); results.pack(fill="x")
    def rebuild(*_):
        for child in results.winfo_children(): child.destroy()
        events = list(reversed(save_system.get_audit_log(app.save_data, 500))); needle = query.get().strip().lower()
        if needle: events = [event for event in events if needle in str(event).lower()]
        make_section_header(results, f"{len(events)} recorded action(s)", "Newest actions appear first.")
        for event in events[:150]:
            actor = event.get("admin") or "EduPy"; action = str(event.get("action", "activity")).replace("_", " ").title()
            target = event.get("target") or "School records"; details = event.get("details") or {}
            occurred = event.get("time") or event.get("timestamp") or ""
            make_card(results, action, f"By {actor} · Target: {target} · {str(occurred)[:19]}\n{details if details else ''}", "#B56BFF").pack(fill="x", pady=3)
    query.trace_add("write", rebuild); rebuild()


def show_admin_dashboard(root, app, selected_tab="Overview"):
    """Render the dedicated admin landing page and its permissioned tools."""
    if not _is_admin(app):
        app.logout(); return
    clear(root)
    body = make_page_header(root, "Admin Command Centre", f"Signed in securely as {app.current_user} · Whole-school controls")
    toolbar = tk.Frame(body, bg=THEME["bg"]); toolbar.pack(fill="x", pady=(0, 8))
    make_button(toolbar, "Teacher Workspace", lambda: __import__('platform_features').show_teacher_studio(root, app))
    make_button(toolbar, "Log Out", app.logout, kind="secondary")
    make_button(toolbar, "Quit EduPy", app.quit_app, kind="secondary")
    style_notebook(root); notebook = ttk.Notebook(body, style="Edu.TNotebook"); notebook.pack(fill="both", expand=True)
    names = ("Overview", "Accounts", "Classes", "Moderation", "Safety & Privacy", "Audit Log")
    tabs = {name: tk.Frame(notebook, bg=THEME["bg"]) for name in names}
    for name in names: notebook.add(tabs[name], text=name)

    accounts = account_service.account_summaries(app.account_db); school_classes = classes.get_classes(app.save_data)
    queues = {
        "pending": app.experience_store.custom_questions(app.current_user, status="pending"),
        "reports": app.experience_store.content_reports(app.current_user),
        "safety": app.experience_store.safety_reports(app.current_user, "active"),
        "privacy": app.experience_store.privacy_requests(app.current_user),
    }
    _overview_tab(tabs["Overview"], root, app, notebook, tabs, accounts, school_classes, queues)
    _accounts_tab(tabs["Accounts"], root, app)
    _classes_tab(tabs["Classes"], root, app, school_classes)
    _moderation_tab(tabs["Moderation"], root, app, queues["pending"], queues["reports"])
    _safety_tab(tabs["Safety & Privacy"], root, app, queues["safety"], queues["privacy"])
    _audit_tab(tabs["Audit Log"], app)
    if selected_tab in tabs: notebook.select(tabs[selected_tab])
