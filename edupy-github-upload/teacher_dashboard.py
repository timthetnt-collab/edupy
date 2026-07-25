"""A dedicated teacher workspace for classes, assignments, and pupil progress."""

import statistics
import datetime
import tkinter as tk
from tkinter import ttk

import assignments
import classes
import curriculum
import curriculum_ui
import platform_features
import save_system
from settings import THEME, FONT_SUBTITLE, FONT_TEXT
from ui import clear, make_action_tile, make_button, make_card, make_label, make_page_header, make_scrollable, make_section_header, make_stat, style_notebook


def teacher_classes(data, username, role="teacher"):
    return classes.get_classes(data) if role == "admin" else classes.get_classes(data, username, "teacher")


def compute_class_metrics(data, class_id):
    cls = classes.get_class(data, class_id)
    if not cls:
        return {}
    students = cls.get("student_usernames", [])
    users = [data.get("users", {}).get(name, {}) for name in students]
    work = [a for a in assignments.ensure_assignments_root(data).values() if a.get("class_id") == class_id and a.get("status") == "published"]
    possible = len(students) * len(work)
    submitted = sum(len(a.get("submissions", {})) for a in work)
    grades = [sub["grade"] / max(1, a.get("max_marks", 100)) * 100 for a in work for sub in a.get("submissions", {}).values() if sub.get("grade") is not None]
    return {
        "students": len(students),
        "assignments": len(work),
        "submission_rate": round(submitted / possible * 100) if possible else 0,
        "average_grade": round(statistics.mean(grades)) if grades else None,
        "average_level": round(statistics.mean([u.get("level", 1) for u in users]), 1) if users else 0,
    }


def student_snapshot(data, username, owned):
    profile = data.get("users", {}).get(username, {})
    class_ids = {item["id"] for item in owned if username in item.get("student_usernames", [])}
    work = [item for item in assignments.ensure_assignments_root(data).values() if item.get("class_id") in class_ids and item.get("status") == "published"]
    submissions = [(item, item.get("submissions", {}).get(username)) for item in work]
    grades = [submission["grade"] / max(1, item.get("max_marks", 100)) * 100 for item, submission in submissions if submission and submission.get("grade") is not None]
    today = datetime.date.today().isoformat()
    missing_overdue = sum(1 for item, submission in submissions if not submission and item.get("due_date") and item["due_date"] < today)
    topics = []
    for subject, subject_topics in profile.get("mastery", {}).items():
        for topic_id, record in subject_topics.items():
            if record.get("attempts", 0):
                topics.append({"subject": subject, "topic": topic_id, "score": curriculum.mastery_percent(profile, subject, topic_id), "attempts": record.get("attempts", 0)})
    topics.sort(key=lambda item: (item["score"], -item["attempts"]))
    return {
        "classes": len(class_ids), "assignments": len(work),
        "submitted": sum(bool(submission) for _, submission in submissions),
        "missing_overdue": missing_overdue,
        "average_grade": round(statistics.mean(grades)) if grades else None,
        "weakest_topics": topics[:5],
    }


def _overview_tab(parent, app, owned):
    all_students = {student for cls in owned for student in cls.get("student_usernames", [])}
    all_work = [a for a in assignments.assignments_for_teacher(app.save_data, app.current_user, (save_system.get_user(app.save_data, app.current_user) or {}).get("role", "teacher")) if a.get("status") == "published"]
    awaiting = sum(1 for a in all_work for s in a.get("submissions", {}).values() if s.get("grade") is None)
    stats = tk.Frame(parent, bg=THEME["bg"]); stats.pack(fill="x", padx=8, pady=12)
    for value, label, colour in ((len(owned), "Classes", THEME["accent"]), (len(all_students), "Students", "#58D68D"), (len(all_work), "Live assignments", "#FFB84D"), (awaiting, "Awaiting marks", "#FF8A80")):
        make_stat(stats, value, label, colour).pack(side="left", fill="x", expand=True, padx=4)
    make_label(parent, "Class snapshot", FONT_SUBTITLE).pack(anchor="w", padx=12, pady=(8, 2))
    if not owned:
        make_card(parent, "Welcome", "Create your first class, then add student accounts and assignments.", THEME["accent"]).pack(fill="x", padx=12, pady=8)
    for cls in owned:
        metric = compute_class_metrics(app.save_data, cls["id"])
        grade = "No marks yet" if metric["average_grade"] is None else f"Average mark {metric['average_grade']}%"
        make_card(parent, cls["title"], f"{cls['subject']} • Year {cls['year_group']} • {metric['students']} students\n{metric['submission_rate']}% submitted • {grade}", THEME["accent"]).pack(fill="x", padx=12, pady=6)


def _classes_tab(parent, root, app, owned):
    intro = make_card(parent, "Class workspace", "Manage class codes, student rosters, co-teachers, and progress exports from one place.", THEME["accent"]); intro.pack(fill="x", padx=12, pady=12)
    make_button(intro, "Open Class Management", lambda: classes.show_class_management(root, app), wide=True)
    for cls in owned:
        make_card(parent, cls["title"], f"Join code: {cls['join_code']} • {len(cls['student_usernames'])} students • {len(cls['teacher_usernames'])} teachers").pack(fill="x", padx=12, pady=5)


def _assignments_tab(parent, root, app):
    intro = make_card(parent, "Assignment centre", "Create, publish, track, and mark work without writing configuration code.", THEME["accent"]); intro.pack(fill="x", padx=12, pady=12)
    make_button(intro, "Open Assignment Centre", lambda: assignments.show_teacher_assignments(root, app), wide=True)
    user = save_system.get_user(app.save_data, app.current_user) or {}
    for item in assignments.assignments_for_teacher(app.save_data, app.current_user, user.get("role", "teacher"))[:8]:
        make_card(parent, item["title"], f"Due {item.get('due_date') or 'any time'} • {len(item.get('submissions', {}))} hand-ins • {item['status'].title()}").pack(fill="x", padx=12, pady=5)


def _students_tab(parent, app, owned):
    students = sorted({student for cls in owned for student in cls.get("student_usernames", [])})
    if not students:
        make_label(parent, "No students have been added yet.", FONT_SUBTITLE).pack(pady=35)
    for username in students:
        user = app.save_data.get("users", {}).get(username, {})
        snapshot = student_snapshot(app.save_data, username, owned)
        recommendation = curriculum.recommend_next(app.save_data, username)
        next_step = f"Next focus: {recommendation['subject']} — {recommendation['title']}" if recommendation else "No recommendation yet"
        card = make_card(parent, username, f"Year {user.get('selected_year', 7)} • Level {user.get('level', 1)} • {user.get('total_xp', 0)} total XP\n{snapshot['submitted']}/{snapshot['assignments']} assignments submitted • {next_step}", "#58D68D"); card.pack(fill="x", padx=12, pady=6)
        make_button(card, "Open Student Snapshot", lambda u=username: _student_detail(parent, app, u, owned))


def _student_detail(parent, app, username, owned):
    win = tk.Toplevel(parent.winfo_toplevel()); win.title(f"Student snapshot - {username}"); win.geometry("760x680"); win.configure(bg=THEME["bg"]); win.grab_set()
    content = make_scrollable(win, padx=22, pady=16); profile = app.save_data.get("users", {}).get(username, {}); snapshot = student_snapshot(app.save_data, username, owned)
    make_label(content, username, FONT_SUBTITLE).pack(pady=(0, 8))
    stats = tk.Frame(content, bg=THEME["bg"]); stats.pack(fill="x", pady=8)
    grade = "—" if snapshot["average_grade"] is None else f"{snapshot['average_grade']}%"
    for value, label, colour in ((snapshot["submitted"], "Submitted", "#58D68D"), (snapshot["missing_overdue"], "Missing overdue", "#FF7043"), (grade, "Average mark", "#4EA3FF")):
        make_stat(stats, value, label, colour).pack(side="left", fill="x", expand=True, padx=4)
    recommendation = curriculum.recommend_next(app.save_data, username)
    if recommendation:
        make_card(content, "Suggested next focus", f"{recommendation['subject']} • {recommendation['title']}\n{recommendation['reason']}", THEME["accent"]).pack(fill="x", pady=7)
    make_label(content, "Topics that may need review", FONT_SUBTITLE).pack(anchor="w", pady=(14, 4))
    if not snapshot["weakest_topics"]:
        make_card(content, "No practice evidence yet", "The snapshot will update after the learner completes curriculum activities.").pack(fill="x", pady=5)
    for item in snapshot["weakest_topics"]:
        title = curriculum.topic_title(profile.get("selected_year", 7), item["subject"], item["topic"])
        make_card(content, title, f"{item['subject']} • {item['score']}% mastery • {item['attempts']} attempt(s)", "#FFB84D" if item["score"] < 50 else "#4EA3FF").pack(fill="x", pady=4)
    make_button(content, "Close", win.destroy, wide=True)


def class_insights(data, owned):
    insights = []
    today = datetime.date.today().isoformat()
    for cls in owned:
        students = cls.get("student_usernames", [])
        work = [item for item in assignments.ensure_assignments_root(data).values() if item.get("class_id") == cls["id"] and item.get("status") == "published"]
        overdue_missing = sum(1 for item in work if item.get("due_date") and item["due_date"] < today for student in students if student not in item.get("submissions", {}))
        low_marks = [(item, student) for item in work for student, submission in item.get("submissions", {}).items() if submission.get("grade") is not None and submission["grade"] / max(1, item.get("max_marks", 100)) < 0.5]
        if overdue_missing:
            insights.append(("Missing overdue work", f"{cls['title']} has {overdue_missing} overdue student task(s) without a submission.", "Check whether deadlines, access, or additional support need reviewing.", "#FF7043"))
        if low_marks:
            insights.append(("Review recent understanding", f"{len(low_marks)} marked response(s) in {cls['title']} are below 50%.", "Look for a shared misconception before assigning more practice.", "#FFB84D"))
        topic_scores = {}
        for student in students:
            profile = data.get("users", {}).get(student, {})
            for subject, topics in profile.get("mastery", {}).items():
                for topic_id in topics:
                    topic_scores.setdefault((subject, topic_id), []).append(curriculum.mastery_percent(profile, subject, topic_id))
        for (subject, topic_id), scores in topic_scores.items():
            if len(scores) >= max(1, len(students) // 2) and statistics.mean(scores) < 50:
                title = curriculum.topic_title(cls.get("year_group", 7), subject, topic_id)
                insights.append(("Possible class-wide gap", f"Average recorded mastery for {title} is {round(statistics.mean(scores))}% across {len(scores)} learner(s).", "Consider a worked example or short reteach before independent work.", "#B56BFF"))
    return insights


def _marking_tab(parent, root, app):
    role = (save_system.get_user(app.save_data, app.current_user) or {}).get("role", "teacher")
    queue = assignments.awaiting_marking(app.save_data, app.current_user, role)
    intro = make_card(parent, "Marking inbox", f"{len(queue)} submission(s) are waiting for feedback.", "#FF8A80"); intro.pack(fill="x", padx=12, pady=12)
    make_button(intro, "Open Marking Inbox", lambda: assignments.show_marking_inbox(root, app), wide=True)
    for item in queue[:10]:
        make_card(parent, item["assignment"]["title"], f"{item['student']} • Submitted {item['submission'].get('submitted_at','')[:10]}").pack(fill="x", padx=12, pady=5)


def _insights_tab(parent, app, owned):
    make_card(parent, "How to use insights", "These are prompts for teacher review, not automatic judgements about students.", THEME["accent"]).pack(fill="x", padx=12, pady=12)
    insights = class_insights(app.save_data, owned)
    if not insights:
        make_label(parent, "No urgent patterns found in the available evidence.", FONT_SUBTITLE).pack(pady=35)
    for title, evidence, suggestion, colour in insights:
        make_card(parent, title, f"{evidence}\nSuggested response: {suggestion}", colour).pack(fill="x", padx=12, pady=6)


def show_teacher_hub(root, app):
    clear(root)
    user = save_system.get_user(app.save_data, app.current_user) or {}
    if user.get("role") not in ("teacher", "admin"):
        app.main_menu(); return
    owned = teacher_classes(app.save_data, app.current_user, user.get("role"))
    body = make_page_header(root, "Teacher Hub", "Your classes, assignments, marking, and learner progress in one workspace.", app.main_menu)
    make_section_header(body, "Quick actions", "Open the jobs teachers use most often.")
    actions = tk.Frame(body, bg=THEME["bg"]); actions.pack(fill="x", pady=(0, 12))
    for column in range(3): actions.grid_columnconfigure(column, weight=1, uniform="teacher_actions")
    style_notebook(root); notebook = ttk.Notebook(body, style="Edu.TNotebook")
    quick_actions = (
        ("Manage classes", "Rosters, staff and join codes.", lambda: classes.show_class_management(root, app), "#4EA3FF"),
        ("Create work", "Build, schedule and publish assignments.", lambda: assignments.show_teacher_assignments(root, app), "#B56BFF"),
        ("Marking inbox", "Review work waiting for feedback.", lambda: assignments.show_marking_inbox(root, app), "#FF7A8A"),
        ("View insights", "Spot patterns that may need support.", lambda: notebook.select(tabs["Insights"]), "#58D68D"),
        ("Curriculum", "Preview, assign and review unit mastery.", lambda: curriculum_ui.show_curriculum_manager(root, app), "#FFB84D"),
        ("Platform Studio", "Questions, live activities, coverage and moderation.", lambda: platform_features.show_teacher_studio(root, app), "#5EC7C2"),
    )
    for index, (title, description, command, accent) in enumerate(quick_actions):
        make_action_tile(actions, title, description, command, accent).grid(row=index//3, column=index%3, sticky="nsew", padx=4, pady=4)
    notebook.pack(fill="both", expand=True)
    tabs = {name: tk.Frame(notebook, bg=THEME["bg"]) for name in ("Overview", "Classes", "Assignments", "Marking", "Insights", "Students")}
    for name, tab in tabs.items(): notebook.add(tab, text=name)
    _overview_tab(make_scrollable(tabs["Overview"]), app, owned)
    _classes_tab(make_scrollable(tabs["Classes"]), root, app, owned)
    _assignments_tab(make_scrollable(tabs["Assignments"]), root, app)
    _marking_tab(make_scrollable(tabs["Marking"]), root, app)
    _insights_tab(make_scrollable(tabs["Insights"]), app, owned)
    _students_tab(make_scrollable(tabs["Students"]), app, owned)


def show_dashboard(root, app):
    show_teacher_hub(root, app)


def show_class_detail(root, app, class_id):
    classes.show_class_management(root, app)
