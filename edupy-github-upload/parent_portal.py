"""Read-only family progress views and administrator-managed student links."""

import tkinter as tk
from tkinter import ttk

import account_service
import assignments
import curriculum
import save_system
from settings import FONT_SUBTITLE, FONT_TEXT, THEME
from ui import clear, make_button, make_card, make_label, make_page_header, make_progress_bar, make_scrollable, make_section_header, make_stat, show_popup


def _linked_students(app):
    return [item["student"] for item in app.experience_store.family_links(app.current_user)
            if item["parent"] == app.current_user]


def _assignment_summary(data, username):
    visible = []
    for item in assignments.ensure_assignments_root(data).values():
        cls = data.get("classes", {}).get(item.get("class_id"), {})
        if username in cls.get("student_usernames", []) and assignments.assignment_is_available(item):
            visible.append(item)
    submitted = sum(username in item.get("submissions", {}) for item in visible)
    marked = sum(item.get("submissions", {}).get(username, {}).get("grade") is not None for item in visible)
    return visible, submitted, marked


def _mastery_summary(profile):
    records = []
    for subject, topics in profile.get("mastery", {}).items():
        for topic, record in topics.items():
            possible = float(record.get("possible", 0) or 0)
            if possible > 0:
                records.append((subject, topic, round(float(record.get("earned", 0)) / possible * 100)))
    average = round(sum(item[2] for item in records) / len(records)) if records else 0
    return average, sorted(records, key=lambda item: item[2])


def show_parent_dashboard(root, app):
    profile = save_system.get_user(app.save_data, app.current_user) or {}
    if profile.get("role") != "parent":
        app.main_menu(); return
    clear(root)
    body = make_page_header(root, "Family Progress", "A read-only view of linked learners. Private wellbeing and safeguarding records are never shown.")
    body = make_scrollable(body)
    students = _linked_students(app)
    if not students:
        make_card(body, "No learner linked yet", "Ask an EduPy administrator to connect this family account to a student.", THEME["accent"]).pack(fill="x", pady=12)
    for username in students:
        learner = app.save_data.get("users", {}).get(username, {})
        work, submitted, marked = _assignment_summary(app.save_data, username)
        average, topic_scores = _mastery_summary(learner)
        goals = app.experience_store.goals(username, False, app.current_user)
        make_section_header(body, username, f"Year {learner.get('selected_year', 7)} learning overview")
        stats = tk.Frame(body, bg=THEME["bg"]); stats.pack(fill="x", pady=5)
        make_stat(stats, f"{submitted}/{len(work)}", "Assignments submitted", "#4EA3FF").pack(side="left", fill="x", expand=True, padx=4)
        make_stat(stats, marked, "Marked pieces", "#58D68D").pack(side="left", fill="x", expand=True, padx=4)
        make_stat(stats, f"{average}%", "Recorded mastery", "#B56BFF").pack(side="left", fill="x", expand=True, padx=4)
        make_stat(stats, len(goals), "Active goals", "#FFB84D").pack(side="left", fill="x", expand=True, padx=4)
        due = [item for item in work if username not in item.get("submissions", {})][:5]
        card = make_card(body, "Current work", "\n".join(
            f"• {item['title']} — {assignments.deadline_label(item, username)}" for item in due
        ) or "No outstanding published assignments.", "#4EA3FF")
        card.pack(fill="x", pady=5)
        if topic_scores:
            focus = topic_scores[:3]
            make_card(body, "Suggested conversation starters", "\n".join(
                f"• Ask how {curriculum.topic_title(learner.get('selected_year', 7), subject, topic)} is going ({score}% recorded mastery)."
                for subject, topic, score in focus
            ), "#FFB84D").pack(fill="x", pady=5)
        if goals:
            make_card(body, "Learner goals", "\n".join(
                f"• {goal['title']}" + (f" — target {goal['target_date']}" if goal.get("target_date") else "")
                for goal in goals[:5]
            ), "#58D68D").pack(fill="x", pady=5)
    footer = tk.Frame(body, bg=THEME["bg"]); footer.pack(fill="x", pady=14)
    make_button(footer, "Refresh", lambda: show_parent_dashboard(root, app))
    make_button(footer, "Logout", app.logout, kind="secondary")
    make_button(footer, "Quit EduPy", app.quit_app, kind="secondary")


def show_family_link_manager(root, app):
    actor = app.account_db.get_account(app.current_user)
    if not actor or actor.role != "admin":
        app.main_menu(); return
    clear(root)
    body = make_page_header(root, "Family Account Links", "Connect a parent or carer account to the learner records they may view.", app.main_menu)
    body = make_scrollable(body)
    records = account_service.account_summaries(app.account_db)
    parents = [item["username"] for item in records if item["role"] == "parent" and item["active"]]
    students = [item["username"] for item in records if item["role"] == "student" and item["active"]]
    form = make_card(body, "Create a family link", "Only administrators can add or remove these links.", THEME["accent"]); form.pack(fill="x", pady=6)
    parent = tk.StringVar(value=parents[0] if parents else ""); student = tk.StringVar(value=students[0] if students else "")
    ttk.Combobox(form, values=parents, textvariable=parent, state="readonly").pack(fill="x", pady=4)
    ttk.Combobox(form, values=students, textvariable=student, state="readonly").pack(fill="x", pady=4)

    def save_link(linked=True, parent_name=None, student_name=None):
        parent_name, student_name = parent_name or parent.get(), student_name or student.get()
        if not app.experience_store.set_family_link(app.current_user, parent_name, student_name, linked):
            show_popup(app, "Choose an active parent account and student account."); return
        profile = app.save_data.setdefault("users", {}).setdefault(parent_name, save_system.default_user("parent"))
        linked_students = profile.setdefault("linked_accounts", [])
        if linked and student_name not in linked_students: linked_students.append(student_name)
        if not linked: profile["linked_accounts"] = [name for name in linked_students if name != student_name]
        save_system.append_audit(app.save_data, admin=app.current_user,
            action="link_family_account" if linked else "unlink_family_account",
            target=parent_name, details={"student": student_name})
        save_system.save_save(app.save_data); show_family_link_manager(root, app)

    make_button(form, "Link Account", save_link, wide=True)
    make_section_header(body, "Current family access", "Parent accounts can only see the learners listed here.")
    links = app.experience_store.family_links(app.current_user)
    for link in links:
        card = make_card(body, link["parent"], f"Read-only access to {link['student']}", "#58D68D"); card.pack(fill="x", pady=4)
        make_button(card, "Remove Link", lambda item=link: save_link(False, item["parent"], item["student"]), kind="secondary")
    if not links:
        make_label(body, "No family links have been created.", FONT_SUBTITLE).pack(pady=20)
