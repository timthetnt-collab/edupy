"""Teacher-friendly assignments, submissions, marking, and student task views."""

import datetime
import csv
import tkinter as tk
import uuid
from tkinter import filedialog, messagebox, ttk

import classes
import curriculum
import curriculum_ui
import save_system
from settings import THEME, FONT_SUBTITLE, FONT_TEXT
from ui import clear, make_button, make_card, make_label, make_page_header, make_scrollable, show_popup, style_notebook


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def curriculum_target(pack_id):
    if not str(pack_id or "").startswith("curriculum:"):
        return None
    try:
        _, year, subject, topic = pack_id.split(":", 3)
        return curriculum.topic_details(int(year), subject, topic)
    except (ValueError, TypeError):
        return None


def ensure_assignments_root(data):
    data.setdefault("assignments", {})
    for assignment_id, item in data["assignments"].items():
        item.setdefault("id", assignment_id)
        item.setdefault("title", "Untitled assignment")
        item.setdefault("class_id", "")
        item.setdefault("subject", "General")
        item.setdefault("instructions", "")
        item.setdefault("created_by", "")
        item.setdefault("created_at", _now())
        item.setdefault("due_date", None)
        item.setdefault("max_marks", 100)
        item.setdefault("reward_tokens", 5)
        item.setdefault("status", "published")
        item.setdefault("publish_at", None)
        item.setdefault("allow_late", True)
        item.setdefault("resubmissions_allowed", True)
        item.setdefault("rubric", [])
        item.setdefault("extensions", {})
        item.setdefault("private_comments", {})
        item.setdefault("auto_grade", {})
        item.setdefault("submissions", {})
    return data["assignments"]


def _normalise_due_date(value):
    if not value:
        return None
    try:
        return datetime.date.fromisoformat(str(value)).isoformat()
    except ValueError:
        return None


def create_assignment(data, title, class_id, pack_id=None, instructions="", due_date=None,
                      auto_grade=None, subject="General", max_marks=100, reward_tokens=5,
                      created_by=None, status="published", publish_at=None, allow_late=True,
                      resubmissions_allowed=True, rubric=None):
    ensure_assignments_root(data)
    cls = classes.get_class(data, class_id)
    if not title.strip() or not cls:
        return None
    if created_by:
        creator = save_system.get_user(data, created_by)
        if not creator or (creator.get("role") != "admin" and created_by not in cls.get("teacher_usernames", [])):
            return None
    due_date = _normalise_due_date(due_date)
    publish_at = _normalise_due_date(publish_at)
    if status == "scheduled" and (not publish_at or (due_date and publish_at > due_date)):
        return None
    try:
        max_marks = min(1000, max(1, int(max_marks)))
        reward_tokens = min(15, max(0, int(reward_tokens)))
    except (TypeError, ValueError):
        return None
    clean_rubric = []
    try:
        for row in rubric or []:
            name, marks = str(row.get("name", "")).strip(), int(row.get("marks", 0))
            if not name or marks < 0:
                return None
            clean_rubric.append({"name": name, "marks": marks})
    except (AttributeError, TypeError, ValueError):
        return None
    if clean_rubric and sum(row["marks"] for row in clean_rubric) != max_marks:
        return None
    assignment_id = str(uuid.uuid4())
    data["assignments"][assignment_id] = {
        "id": assignment_id,
        "title": title.strip(),
        "class_id": class_id,
        "pack_id": pack_id,
        "subject": subject.strip() or "General",
        "instructions": instructions.strip(),
        "created_by": created_by or "",
        "created_at": _now(),
        "due_date": due_date,
        "max_marks": max_marks,
        "reward_tokens": reward_tokens,
        "status": status if status in ("draft", "published", "scheduled") else "draft",
        "publish_at": publish_at,
        "allow_late": bool(allow_late),
        "resubmissions_allowed": bool(resubmissions_allowed),
        "rubric": clean_rubric,
        "extensions": {},
        "private_comments": {},
        "auto_grade": auto_grade or {},
        "submissions": {},
    }
    save_system.append_audit(data, admin=created_by, action="create_assignment", target=assignment_id, details={"class": class_id, "title": title})
    return assignment_id


def save_template(data, name, assignment_fields, owner):
    if not name.strip(): return None
    template_id = str(uuid.uuid4())
    data.setdefault("assignment_templates", {})[template_id] = {
        "id": template_id, "name": name.strip(), "owner": owner, "created_at": _now(),
        "fields": {key: value for key, value in assignment_fields.items() if key not in ("class_id", "due_date", "publish_at")},
    }
    save_system.save_save(data)
    return template_id


def templates_for(data, owner):
    return sorted((item for item in data.get("assignment_templates", {}).values() if item.get("owner") in (owner, "shared")), key=lambda item: (item.get("name", "").lower(), item.get("created_at", "")))


def delete_template(data, template_id, actor):
    template = data.get("assignment_templates", {}).get(template_id)
    profile = save_system.get_user(data, actor)
    if not template or not profile or (profile.get("role") != "admin" and template.get("owner") != actor):
        return False
    del data["assignment_templates"][template_id]
    save_system.append_audit(data, admin=actor, action="delete_assignment_template", target=template_id)
    return True


def assignment_is_available(assignment, on_date=None):
    on_date = on_date or datetime.date.today().isoformat()
    if assignment.get("status") == "published": return True
    return assignment.get("status") == "scheduled" and bool(assignment.get("publish_at")) and assignment["publish_at"] <= on_date


def effective_due_date(assignment, username):
    return assignment.get("extensions", {}).get(username) or assignment.get("due_date")


def deadline_label(assignment, username=None, today=None):
    """Describe a deadline in language that makes urgency easy to scan."""
    due = _normalise_due_date(effective_due_date(assignment, username))
    if not due:
        return "No deadline"
    today_date = datetime.date.fromisoformat(today) if isinstance(today, str) else (today or datetime.date.today())
    due_date = datetime.date.fromisoformat(due)
    days = (due_date - today_date).days
    if days < 0:
        return f"Overdue by {abs(days)} day{'s' if days != -1 else ''}"
    if days == 0:
        return "Due today"
    if days == 1:
        return "Due tomorrow"
    if days <= 7:
        return f"Due in {days} days"
    return f"Due {due}"


def update_assignment_status(data, assignment_id, status, actor=None):
    item = ensure_assignments_root(data).get(assignment_id)
    if not item or status not in ("draft", "published", "archived"):
        return False
    if actor is not None:
        cls = classes.get_class(data, item.get("class_id"))
        profile = save_system.get_user(data, actor)
        if not profile or (profile.get("role") != "admin" and actor not in (cls or {}).get("teacher_usernames", [])):
            return False
    item["status"] = status
    save_system.save_save(data)
    return True


def update_assignment_details(data, assignment_id, actor, **changes):
    """Update safe assignment fields while preserving submissions and audit history."""
    item = ensure_assignments_root(data).get(assignment_id)
    cls = classes.get_class(data, item.get("class_id")) if item else None
    profile = save_system.get_user(data, actor)
    if not item or not profile or (profile.get("role") != "admin" and actor not in (cls or {}).get("teacher_usernames", [])):
        return False
    title = str(changes.get("title", item["title"])).strip()
    due_date = changes.get("due_date", item.get("due_date"))
    if not title or (due_date and not _normalise_due_date(due_date)):
        return False
    try:
        max_marks = min(1000, max(1, int(changes.get("max_marks", item["max_marks"]))))
        reward_tokens = min(15, max(0, int(changes.get("reward_tokens", item["reward_tokens"]))))
    except (TypeError, ValueError):
        return False
    existing_grades = [submission.get("grade") for submission in item.get("submissions", {}).values() if submission.get("grade") is not None]
    if existing_grades and max_marks < max(existing_grades):
        return False
    item.update({
        "title": title,
        "subject": str(changes.get("subject", item["subject"])).strip() or "General",
        "instructions": str(changes.get("instructions", item["instructions"])).strip(),
        "due_date": _normalise_due_date(due_date),
        "max_marks": max_marks,
        "reward_tokens": reward_tokens,
        "allow_late": bool(changes.get("allow_late", item["allow_late"])),
        "resubmissions_allowed": bool(changes.get("resubmissions_allowed", item["resubmissions_allowed"])),
    })
    save_system.append_audit(data, admin=actor, action="update_assignment", target=assignment_id, details={"title": title})
    return True


def duplicate_assignment(data, assignment_id, actor):
    """Create a clean draft copy without carrying over student work."""
    source = ensure_assignments_root(data).get(assignment_id)
    cls = classes.get_class(data, source.get("class_id")) if source else None
    profile = save_system.get_user(data, actor)
    if not source or not profile or (profile.get("role") != "admin" and actor not in (cls or {}).get("teacher_usernames", [])):
        return None
    return create_assignment(
        data, f"Copy of {source['title']}", source["class_id"], pack_id=source.get("pack_id"),
        instructions=source.get("instructions", ""), subject=source.get("subject", "General"),
        max_marks=source.get("max_marks", 100), reward_tokens=source.get("reward_tokens", 5),
        auto_grade=dict(source.get("auto_grade") or {}), created_by=actor, status="draft",
        allow_late=source.get("allow_late", True),
        resubmissions_allowed=source.get("resubmissions_allowed", True),
        rubric=[dict(row) for row in source.get("rubric", [])],
    )


def assignment_state(assignment, username=None):
    submission = assignment.get("submissions", {}).get(username) if username else None
    if submission and submission.get("grade") is not None:
        return "Marked"
    if submission:
        return "Submitted"
    if not assignment_is_available(assignment): return "Scheduled"
    due = _normalise_due_date(effective_due_date(assignment, username))
    if due and due < datetime.date.today().isoformat():
        return "Overdue"
    return "To do"


def submit_assignment(data, assignment_id, username, answer_text=None, attachment_path=None):
    assignment = ensure_assignments_root(data).get(assignment_id)
    cls = classes.get_class(data, assignment.get("class_id")) if assignment else None
    if not assignment or not assignment_is_available(assignment) or not cls or username not in cls.get("student_usernames", []):
        return False
    previous = assignment["submissions"].get(username, {})
    if previous and not assignment.get("resubmissions_allowed", True): return False
    due = effective_due_date(assignment, username)
    if due and due < datetime.date.today().isoformat() and not assignment.get("allow_late", True): return False
    assignment["submissions"][username] = {
        "submitted_at": _now(),
        "answer": (answer_text or "").strip(),
        "attachment": attachment_path,
        "grade": None,
        "feedback": None,
        "auto_graded": False,
        "reward_awarded": previous.get("reward_awarded", False),
        "late": bool(due and due < datetime.date.today().isoformat()),
    }
    submission = assignment["submissions"][username]
    grade, feedback = auto_grade_submission(assignment, submission)
    if grade is not None:
        submission.update({"grade": grade, "feedback": feedback, "auto_graded": True})
        _award_assignment_tokens(data, assignment, username, submission)
    save_system.append_audit(data, admin=None, action="submit_assignment", target=assignment_id, details={"student": username})
    return True


def auto_grade_submission(assignment, submission):
    rule = assignment.get("auto_grade") or {}
    answer = (submission.get("answer") or "").strip()
    if rule.get("type") == "keywords":
        keywords = [word.strip().lower() for word in rule.get("keywords", []) if word.strip()]
        if not keywords:
            return None, None
        hits = sum(word in answer.lower() for word in keywords)
        return round(hits / len(keywords) * assignment.get("max_marks", 100)), f"Included {hits} of {len(keywords)} key ideas."
    if rule.get("type") == "exact":
        expected = str(rule.get("expected", "")).strip().lower()
        return (assignment.get("max_marks", 100) if answer.lower() == expected else 0), "Automatically checked against the expected answer."
    if rule.get("type") == "numeric":
        try:
            correct = abs(float(answer) - float(rule.get("expected"))) <= float(rule.get("tolerance", 0.01))
            return (assignment.get("max_marks", 100) if correct else 0), "Automatically checked as a number."
        except (TypeError, ValueError):
            return None, None
    return None, None


def _award_assignment_tokens(data, assignment, username, submission):
    max_marks = max(1, int(assignment.get("max_marks", 100)))
    if submission.get("reward_awarded") or submission.get("grade") is None or submission["grade"] / max_marks < 0.5:
        return 0
    reward = min(15, max(0, int(assignment.get("reward_tokens", 5))))
    user = save_system.get_user(data, username)
    if not user:
        return 0
    reward = save_system.award_tokens(
        data,
        username,
        reward,
        f"Completed: {assignment['title']}",
        event_id=f"assignment:{assignment['id']}:{username}",
    )
    submission["reward_awarded"] = True
    return reward


def grade_submission(data, assignment_id, username, grade, feedback, teacher):
    assignment = ensure_assignments_root(data).get(assignment_id)
    submission = assignment.get("submissions", {}).get(username) if assignment else None
    cls = classes.get_class(data, assignment.get("class_id")) if assignment else None
    marker = save_system.get_user(data, teacher)
    if not submission or not marker or (marker.get("role") != "admin" and teacher not in (cls or {}).get("teacher_usernames", [])):
        return False
    try:
        grade = float(grade)
    except (TypeError, ValueError):
        return False
    submission["grade"] = min(float(assignment.get("max_marks", 100)), max(0, grade))
    submission["feedback"] = feedback.strip()
    submission["marked_by"] = teacher
    submission["marked_at"] = _now()
    _award_assignment_tokens(data, assignment, username, submission)
    save_system.append_audit(data, admin=teacher, action="grade_submission", target=assignment_id, details={"student": username, "grade": grade})
    return True


def structured_feedback(what_went_well="", next_step="", corrected_example="", follow_up="", general=""):
    """Format consistent, actionable feedback while preserving free-form teacher notes."""
    sections = (
        ("What went well", what_went_well),
        ("Your next step", next_step),
        ("Corrected example", corrected_example),
        ("Try this next", follow_up),
        ("Teacher note", general),
    )
    return "\n\n".join(f"{heading}:\n{str(value).strip()}" for heading, value in sections if str(value).strip())


def add_private_comment(data, assignment_id, username, comment, teacher):
    assignment = ensure_assignments_root(data).get(assignment_id)
    cls = classes.get_class(data, assignment.get("class_id")) if assignment else None
    marker = save_system.get_user(data, teacher)
    if not assignment or not marker or (marker.get("role") != "admin" and teacher not in (cls or {}).get("teacher_usernames", [])): return False
    assignment.setdefault("private_comments", {})[username] = comment.strip()
    save_system.save_save(data); return True


def set_extension(data, assignment_id, username, due_date, teacher):
    assignment = ensure_assignments_root(data).get(assignment_id)
    cls = classes.get_class(data, assignment.get("class_id")) if assignment else None
    if not assignment or not _normalise_due_date(due_date) or username not in (cls or {}).get("student_usernames", []): return False
    if teacher not in cls.get("teacher_usernames", []) and (save_system.get_user(data, teacher) or {}).get("role") != "admin": return False
    assignment.setdefault("extensions", {})[username] = _normalise_due_date(due_date); save_system.save_save(data); return True


def bulk_mark(data, assignment_id, marks, feedback, teacher, only_unmarked=True):
    assignment = ensure_assignments_root(data).get(assignment_id); count = 0
    if not assignment: return 0
    for username, mark in marks.items():
        submission = assignment.get("submissions", {}).get(username)
        if submission and (not only_unmarked or submission.get("grade") is None):
            count += bool(grade_submission(data, assignment_id, username, mark, feedback, teacher))
    return count


def export_assignment_report(data, assignment_id, path):
    assignment = ensure_assignments_root(data).get(assignment_id)
    cls = classes.get_class(data, assignment.get("class_id")) if assignment else None
    if not assignment or not cls: return False
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file); writer.writerow(["student", "status", "submitted_at", "late", "mark", "max_marks", "feedback"])
        for username in cls.get("student_usernames", []):
            sub = assignment.get("submissions", {}).get(username, {})
            writer.writerow([username, assignment_state(assignment, username), sub.get("submitted_at", ""), sub.get("late", False), sub.get("grade", ""), assignment.get("max_marks", 100), sub.get("feedback", "")])
    return True


def assignments_for_teacher(data, username, role="teacher"):
    allowed = {c["id"] for c in (classes.get_classes(data) if role == "admin" else classes.get_classes(data, username, "teacher"))}
    return sorted((a for a in ensure_assignments_root(data).values() if a.get("class_id") in allowed), key=lambda a: a.get("created_at", ""), reverse=True)


def assignments_for_student(data, username):
    allowed = {c["id"] for c in classes.get_classes(data, username, "student")}
    return sorted((a for a in ensure_assignments_root(data).values() if a.get("class_id") in allowed and assignment_is_available(a)), key=lambda a: (a.get("due_date") or "9999", a.get("title", "")))


def awaiting_marking(data, username, role="teacher", class_id=None, late_only=False):
    queue = []
    for assignment in assignments_for_teacher(data, username, role):
        if class_id and assignment.get("class_id") != class_id:
            continue
        for student, submission in assignment.get("submissions", {}).items():
            if submission.get("grade") is None and (not late_only or submission.get("late")):
                queue.append({"assignment": assignment, "student": student, "submission": submission})
    return sorted(queue, key=lambda item: item["submission"].get("submitted_at", ""))


def show_marking_inbox(root, app):
    clear(root); user = save_system.get_user(app.save_data, app.current_user) or {}
    body = make_page_header(root, "Marking Inbox", "Every submitted response waiting for teacher feedback.", app.open_teacher_hub); body = make_scrollable(body)
    all_queue = awaiting_marking(app.save_data, app.current_user, user.get("role", "teacher"))
    owned = classes.get_classes(app.save_data) if user.get("role") == "admin" else classes.get_classes(app.save_data, app.current_user, "teacher")
    class_options = {"All classes": None, **{f"{cls['title']} • Year {cls['year_group']} • {cls['id']}": cls["id"] for cls in owned}}
    class_var = tk.StringVar(value="All classes"); late_var = tk.BooleanVar(value=False)
    stats = tk.Frame(body, bg=THEME["bg"]); stats.pack(fill="x", pady=10)
    make_card(stats, str(len(all_queue)), "Waiting to be marked", "#FF8A80").pack(side="left", fill="x", expand=True, padx=5)
    make_card(stats, str(sum(item["submission"].get("late", False) for item in all_queue)), "Late submissions", "#FFB84D").pack(side="left", fill="x", expand=True, padx=5)
    filters = tk.Frame(body, bg=THEME["bg"]); filters.pack(fill="x", padx=10, pady=6)
    make_label(filters, "Show", FONT_TEXT).pack(side="left", padx=(0, 6))
    ttk.Combobox(filters, values=list(class_options), textvariable=class_var, state="readonly", width=28).pack(side="left")
    tk.Checkbutton(filters, text="Late only", variable=late_var, font=FONT_TEXT, bg=THEME["bg"], fg=THEME["fg"], selectcolor=THEME.get("panel_alt", THEME["bg"])).pack(side="left", padx=12)
    results = tk.Frame(body, bg=THEME["bg"]); results.pack(fill="both", expand=True)
    def rebuild(*_):
        for child in results.winfo_children(): child.destroy()
        queue = awaiting_marking(app.save_data, app.current_user, user.get("role", "teacher"), class_options[class_var.get()], late_var.get())
        if not queue:
            make_label(results, "Nothing matches these filters — you are up to date.", FONT_SUBTITLE).pack(pady=40)
        for item in queue:
            assignment = item["assignment"]; cls = classes.get_class(app.save_data, assignment["class_id"]) or {}
            detail = f"{item['student']} • {cls.get('title', assignment['class_id'])} • Submitted {item['submission'].get('submitted_at','')[:16].replace('T',' ')}"
            if item["submission"].get("late"): detail += " • LATE"
            card = make_card(results, assignment["title"], detail, "#FF7043" if item["submission"].get("late") else THEME["accent"]); card.pack(fill="x", padx=10, pady=6)
            make_button(card, "Review This Student", lambda a=assignment, s=item["student"]: _review_window_v2(root, app, a, lambda: show_marking_inbox(root, app), s))
    class_var.trace_add("write", rebuild); late_var.trace_add("write", rebuild); rebuild()


def _create_form(parent, app, on_created):
    user = save_system.get_user(app.save_data, app.current_user) or {}
    owned = classes.get_classes(app.save_data) if user.get("role") == "admin" else classes.get_classes(app.save_data, app.current_user, "teacher")
    if not owned:
        make_label(parent, "Create a class before assigning work.", FONT_SUBTITLE).pack(pady=30)
        return
    form = make_card(parent, "Create an assignment", "Choose a class, explain the task, then publish immediately or keep a draft.", THEME["accent"])
    form.pack(fill="both", expand=True, padx=12, pady=12)
    class_map = {f"{c['title']} • Year {c['year_group']}": c["id"] for c in owned}
    class_var = tk.StringVar(value=next(iter(class_map)))
    subject_var = tk.StringVar(value=owned[0].get("subject", "General")); due_var = tk.StringVar(value=(datetime.date.today() + datetime.timedelta(days=7)).isoformat())
    marks_var = tk.StringVar(value="20"); reward_var = tk.StringVar(value="5"); marking_var = tk.StringVar(value="Teacher marks")
    title_entry = tk.Entry(form, font=FONT_SUBTITLE)
    controls = (("Class", ttk.Combobox(form, values=list(class_map), textvariable=class_var, state="readonly")), ("Title", title_entry), ("Subject", tk.Entry(form, textvariable=subject_var, font=FONT_TEXT)), ("Due date (YYYY-MM-DD)", tk.Entry(form, textvariable=due_var, font=FONT_TEXT)), ("Maximum marks", tk.Entry(form, textvariable=marks_var, font=FONT_TEXT)), ("Completion reward (0-15 tokens)", tk.Entry(form, textvariable=reward_var, font=FONT_TEXT)))
    for label, widget in controls:
        make_label(form, label, FONT_TEXT).pack(anchor="w", pady=(7, 1)); widget.pack(fill="x")
    make_label(form, "Instructions", FONT_TEXT).pack(anchor="w", pady=(7, 1)); instructions = tk.Text(form, height=5, font=FONT_TEXT, bg=THEME.get("panel_alt", THEME["bg"]), fg=THEME["fg"], insertbackground=THEME["fg"]); instructions.pack(fill="x")
    make_label(form, "Marking", FONT_TEXT).pack(anchor="w", pady=(7, 1)); ttk.Combobox(form, values=["Teacher marks", "Key ideas", "Exact answer", "Numeric answer"], textvariable=marking_var, state="readonly").pack(fill="x")
    answer_entry = tk.Entry(form, font=FONT_TEXT); answer_entry.pack(fill="x", pady=5); answer_entry.insert(0, "For auto-marking: comma-separated key ideas or the expected answer")
    def create(status):
        try: marks = int(marks_var.get()); reward = int(reward_var.get())
        except ValueError: show_popup(app, "Marks and rewards must be whole numbers."); return
        if due_var.get() and not _normalise_due_date(due_var.get()): show_popup(app, "Use a valid due date such as 2026-09-18."); return
        mode = marking_var.get(); raw = answer_entry.get().strip(); rule = {}
        if mode == "Key ideas": rule = {"type": "keywords", "keywords": [x.strip() for x in raw.split(",") if x.strip()]}
        elif mode == "Exact answer": rule = {"type": "exact", "expected": raw}
        elif mode == "Numeric answer": rule = {"type": "numeric", "expected": raw, "tolerance": 0.01}
        assignment_id = create_assignment(app.save_data, title_entry.get(), class_map[class_var.get()], instructions=instructions.get("1.0", "end"), due_date=due_var.get(), auto_grade=rule, subject=subject_var.get(), max_marks=marks, reward_tokens=reward, created_by=app.current_user, status=status)
        if not assignment_id: show_popup(app, "Add a title and select a valid class."); return
        show_popup(app, "Assignment published." if status == "published" else "Draft saved."); on_created()
    buttons = tk.Frame(form, bg=form["bg"]); buttons.pack(fill="x", pady=8)
    make_button(buttons, "Publish", lambda: create("published")); make_button(buttons, "Save Draft", lambda: create("draft"))


def _create_form_v2(parent, app, on_created):
    user = save_system.get_user(app.save_data, app.current_user) or {}
    owned = classes.get_classes(app.save_data) if user.get("role") == "admin" else classes.get_classes(app.save_data, app.current_user, "teacher")
    if not owned:
        make_label(parent, "Create a class before assigning work.", FONT_SUBTITLE).pack(pady=30); return
    seed = getattr(app, "curriculum_assignment_seed", None)
    if hasattr(app, "curriculum_assignment_seed"): delattr(app, "curriculum_assignment_seed")
    pack_id = f"curriculum:{seed['year']}:{seed['subject']}:{seed['topic']}" if seed else None
    form = make_card(parent, "Create an assignment", "Use a reusable template, then publish now, schedule, or save a draft.", THEME["accent"]); form.pack(fill="both", expand=True, padx=12, pady=10)
    class_map = {f"{c['title']} • Year {c['year_group']} • {c['id']}": c["id"] for c in owned}
    class_details = {c["id"]: c for c in owned}
    class_var = tk.StringVar(value=next(iter(class_map))); subject_var = tk.StringVar(value=owned[0].get("subject", "General"))
    due_var = tk.StringVar(value=(datetime.date.today()+datetime.timedelta(days=7)).isoformat()); publish_var = tk.StringVar(value=datetime.date.today().isoformat())
    marks_var = tk.StringVar(value="20"); reward_var = tk.StringVar(value="5"); marking_var = tk.StringVar(value="Teacher marks")
    allow_late = tk.BooleanVar(value=True); allow_resubmit = tk.BooleanVar(value=True); rubric_var = tk.StringVar(value="Understanding:10, Evidence:5, Accuracy:5")
    template_map = {f"{item['name']} • {item['id'][:6]}": item for item in templates_for(app.save_data, app.current_user)}; template_var = tk.StringVar(value="Blank assignment")
    template_row = tk.Frame(form, bg=form["bg"]); template_row.pack(fill="x", pady=4); make_label(template_row, "Template", FONT_TEXT).pack(side="left"); ttk.Combobox(template_row, values=["Blank assignment", *template_map], textvariable=template_var, state="readonly", width=28).pack(side="left", padx=8)
    advanced_visible = {"value": False}
    columns = tk.Frame(form, bg=form["bg"]); columns.pack(fill="both", expand=True); left = tk.Frame(columns, bg=form["bg"]); right = tk.Frame(columns, bg=form["bg"]); left.pack(side="left", fill="both", expand=True, padx=(0,8))
    def toggle_advanced():
        advanced_visible["value"] = not advanced_visible["value"]
        if advanced_visible["value"]: right.pack(side="left", fill="both", expand=True, padx=(8,0))
        else: right.pack_forget()
        advanced_button.config(text="Hide Advanced Options" if advanced_visible["value"] else "Show Advanced Options")
    advanced_button = make_button(form, "Show Advanced Options", toggle_advanced)
    title_entry = tk.Entry(left, font=FONT_SUBTITLE)
    for label, widget in (("Class", ttk.Combobox(left, values=list(class_map), textvariable=class_var, state="readonly")), ("Title", title_entry), ("Subject", tk.Entry(left, textvariable=subject_var, font=FONT_TEXT)), ("Due date", tk.Entry(left, textvariable=due_var, font=FONT_TEXT))):
        make_label(left, label, FONT_TEXT).pack(anchor="w"); widget.pack(fill="x", pady=(0,4))
    make_label(left, "Instructions", FONT_TEXT).pack(anchor="w"); instructions = tk.Text(left, height=6, font=FONT_TEXT, bg=THEME.get("panel_alt",THEME["bg"]), fg=THEME["fg"], insertbackground=THEME["fg"]); instructions.pack(fill="both", expand=True)
    if seed:
        title_entry.insert(0, seed["title"])
        subject_var.set(seed["subject"])
        instructions.insert("1.0", f"Complete the EduPy unit: {seed['title']}.\nFocus: {', '.join(seed['subskills'])}\nOpen the linked lesson before submitting your response.")
    for label, variable in (("Maximum marks",marks_var),("Reward tokens (0-15)",reward_var),("Publish/schedule date",publish_var),("Rubric (criterion:marks, ...)",rubric_var)):
        make_label(right,label,FONT_TEXT).pack(anchor="w"); tk.Entry(right,textvariable=variable,font=FONT_TEXT).pack(fill="x",pady=(0,4))
    make_label(right,"Marking",FONT_TEXT).pack(anchor="w"); ttk.Combobox(right,values=["Teacher marks","Key ideas","Exact answer","Numeric answer"],textvariable=marking_var,state="readonly").pack(fill="x")
    answer_entry=tk.Entry(right,font=FONT_TEXT); answer_entry.pack(fill="x",pady=4); answer_entry.insert(0,"Auto-mark answer or comma-separated key ideas")
    tk.Checkbutton(right,text="Accept late work",variable=allow_late,bg=right["bg"],fg=THEME["fg"],selectcolor=THEME.get("panel_alt",THEME["bg"])).pack(anchor="w")
    tk.Checkbutton(right,text="Allow resubmissions",variable=allow_resubmit,bg=right["bg"],fg=THEME["fg"],selectcolor=THEME.get("panel_alt",THEME["bg"])).pack(anchor="w")
    def sync_class_subject(*_):
        selected = class_details.get(class_map.get(class_var.get()))
        if selected: subject_var.set(selected.get("subject", "General"))
    class_var.trace_add("write", sync_class_subject)
    def read_fields():
        try:
            rubric=[]
            for part in rubric_var.get().split(","):
                if part.strip(): name,value=part.rsplit(":",1); rubric.append({"name":name.strip(),"marks":int(value)})
            return {"title":title_entry.get(),"instructions":instructions.get("1.0","end"),"subject":subject_var.get(),"max_marks":int(marks_var.get()),"reward_tokens":int(reward_var.get()),"rubric":rubric,"allow_late":allow_late.get(),"resubmissions_allowed":allow_resubmit.get()}
        except ValueError: raise ValueError("Use whole numbers and rubric entries such as Analysis:10, Evidence:5.")
    def apply_template(*_):
        template=template_map.get(template_var.get())
        if not template:return
        fields=template.get("fields",{}); title_entry.delete(0,"end"); title_entry.insert(0,fields.get("title","")); subject_var.set(fields.get("subject","General")); marks_var.set(str(fields.get("max_marks",20))); reward_var.set(str(fields.get("reward_tokens",5))); rubric_var.set(", ".join(f"{r['name']}:{r['marks']}" for r in fields.get("rubric",[]))); instructions.delete("1.0","end"); instructions.insert("1.0",fields.get("instructions",""))
    template_var.trace_add("write",apply_template)
    def create(status):
        try: values=read_fields()
        except ValueError as error: show_popup(app,str(error));return
        if due_var.get() and not _normalise_due_date(due_var.get()): show_popup(app,"Choose a valid due date.");return
        if status=="scheduled" and not _normalise_due_date(publish_var.get()): show_popup(app,"Choose a valid publish date.");return
        if status=="scheduled" and due_var.get() and publish_var.get() > due_var.get(): show_popup(app,"The publish date must be on or before the due date.");return
        if values["rubric"] and sum(row["marks"] for row in values["rubric"]) != values["max_marks"]: show_popup(app,"Rubric marks must add up to the maximum marks.");return
        raw=answer_entry.get().strip(); mode=marking_var.get(); rule={}
        if mode != "Teacher marks" and (not raw or raw.startswith("Auto-mark answer")): show_popup(app,"Add the expected answer or key ideas for auto-marking.");return
        if mode=="Key ideas":rule={"type":"keywords","keywords":[x.strip() for x in raw.split(",") if x.strip()]}
        elif mode=="Exact answer":rule={"type":"exact","expected":raw}
        elif mode=="Numeric answer":rule={"type":"numeric","expected":raw,"tolerance":0.01}
        title=values.pop("title"); assignment_id=create_assignment(app.save_data,title,class_map[class_var.get()],pack_id=pack_id,due_date=due_var.get(),auto_grade=rule,created_by=app.current_user,status=status,publish_at=publish_var.get() if status=="scheduled" else None,**values)
        if not assignment_id:show_popup(app,"Add a title and select a valid class.");return
        show_popup(app,{"published":"Assignment published.","scheduled":"Assignment scheduled.","draft":"Draft saved."}[status]);on_created()
    def save_current_template():
        try:values=read_fields()
        except ValueError as error:show_popup(app,str(error));return
        save_template(app.save_data,title_entry.get().strip() or "Reusable assignment",values,app.current_user);show_popup(app,"Template saved.");on_created()
    buttons=tk.Frame(form,bg=form["bg"]);buttons.pack(fill="x",pady=6)
    for label, command in (("Publish Now",lambda:create("published")),("Schedule",lambda:create("scheduled")),("Save Draft",lambda:create("draft")),("Save as Template",save_current_template)):
        button=make_button(buttons,label,command);button.master.pack_configure(side="left",fill="x",expand=True,padx=3)
    if template_map:
        make_label(form, "Saved templates", FONT_SUBTITLE).pack(anchor="w", pady=(12, 3))
        for label, template in template_map.items():
            row = make_card(form, template["name"], f"Created {template.get('created_at', '')[:10]}"); row.pack(fill="x", pady=3)
            if template.get("owner") == app.current_user or user.get("role") == "admin":
                make_button(row, "Delete Template", lambda i=template["id"]: (delete_template(app.save_data, i, app.current_user), on_created()))


def show_teacher_assignments(root, app):
    clear(root); user = save_system.get_user(app.save_data, app.current_user) or {}
    body = make_page_header(root, "Assignment Centre", "Create work in a simple form, track hand-ins, and return feedback.", app.open_teacher_hub if hasattr(app, "open_teacher_hub") else app.main_menu)
    style_notebook(root); notebook = ttk.Notebook(body, style="Edu.TNotebook"); notebook.pack(fill="both", expand=True)
    create_tab = tk.Frame(notebook, bg=THEME["bg"]); manage_tab = tk.Frame(notebook, bg=THEME["bg"])
    notebook.add(create_tab, text="Create"); notebook.add(manage_tab, text="Manage & Mark")
    create_content = make_scrollable(create_tab); manage_content = make_scrollable(manage_tab)
    def rebuild():
        for child in create_content.winfo_children(): child.destroy()
        for child in manage_content.winfo_children(): child.destroy()
        _create_form_v2(create_content, app, rebuild)
        items = assignments_for_teacher(app.save_data, app.current_user, user.get("role", "teacher"))
        if not items: make_label(manage_content, "No assignments yet.", FONT_SUBTITLE).pack(pady=30); return
        for item in items:
            cls = classes.get_class(app.save_data, item["class_id"]) or {}
            submitted = len(item.get("submissions", {})); total = len(cls.get("student_usernames", []))
            card = make_card(manage_content, item["title"], f"{cls.get('title', item['class_id'])} • Due {item.get('due_date') or 'any time'} • {submitted}/{total} submitted • {item['status'].title()}", THEME["accent"]); card.pack(fill="x", padx=10, pady=6)
            make_button(card, "Review", lambda a=item: _review_window_v2(root, app, a, rebuild))
            make_button(card, "Edit", lambda a=item: _edit_assignment_window(root, app, a, rebuild))
            make_button(card, "Duplicate as Draft", lambda a=item: (duplicate_assignment(app.save_data, a["id"], app.current_user), rebuild()))
            make_button(card, "Export Report", lambda a=item: _export_report_dialog(app, a))
            make_button(card, "Archive" if item["status"] != "archived" else "Publish", lambda a=item: (update_assignment_status(app.save_data, a["id"], "archived" if a["status"] != "archived" else "published", app.current_user), rebuild()))
    rebuild()


def _edit_assignment_window(root, app, assignment, on_done):
    win = tk.Toplevel(root); win.title(f"Edit - {assignment['title']}"); win.geometry("720x690"); win.configure(bg=THEME["bg"]); win.grab_set()
    content = make_scrollable(win, padx=24, pady=16)
    make_label(content, "Edit Assignment", FONT_SUBTITLE).pack(pady=(0, 8))
    fields = {}
    for key, label, value in (
        ("title", "Title", assignment.get("title", "")),
        ("subject", "Subject", assignment.get("subject", "General")),
        ("due_date", "Due date (YYYY-MM-DD, or leave blank)", assignment.get("due_date") or ""),
        ("max_marks", "Maximum marks", assignment.get("max_marks", 100)),
        ("reward_tokens", "Completion reward (0-15 tokens)", assignment.get("reward_tokens", 5)),
    ):
        make_label(content, label, FONT_TEXT).pack(anchor="w")
        entry = tk.Entry(content, font=FONT_TEXT); entry.insert(0, str(value)); entry.pack(fill="x", pady=(0, 7)); fields[key] = entry
    make_label(content, "Instructions", FONT_TEXT).pack(anchor="w")
    instructions = tk.Text(content, height=7, font=FONT_TEXT, bg=THEME.get("panel_alt", THEME["bg"]), fg=THEME["fg"], insertbackground=THEME["fg"])
    instructions.insert("1.0", assignment.get("instructions", "")); instructions.pack(fill="x", pady=(0, 7))
    allow_late = tk.BooleanVar(value=assignment.get("allow_late", True)); resubmit = tk.BooleanVar(value=assignment.get("resubmissions_allowed", True))
    for label, variable in (("Accept late work", allow_late), ("Allow resubmissions", resubmit)):
        tk.Checkbutton(content, text=label, variable=variable, font=FONT_TEXT, bg=THEME["bg"], fg=THEME["fg"], selectcolor=THEME.get("panel_alt", THEME["bg"])).pack(anchor="w", pady=3)
    def save():
        ok = update_assignment_details(
            app.save_data, assignment["id"], app.current_user,
            title=fields["title"].get(), subject=fields["subject"].get(), due_date=fields["due_date"].get(),
            max_marks=fields["max_marks"].get(), reward_tokens=fields["reward_tokens"].get(),
            instructions=instructions.get("1.0", "end"), allow_late=allow_late.get(), resubmissions_allowed=resubmit.get(),
        )
        if not ok: show_popup(app, "Check the title, date, marks, and reward values."); return
        win.destroy(); show_popup(app, "Assignment updated."); on_done()
    make_button(content, "Save Changes", save, wide=True); make_button(content, "Cancel", win.destroy, wide=True)


def _export_report_dialog(app, assignment):
    path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV report", "*.csv")], initialfile=f"{assignment['title']}-report.csv")
    if path and export_assignment_report(app.save_data, assignment["id"], path):
        show_popup(app, "Assignment report exported.")


def _review_window_v2(root, app, assignment, on_done, initial_student=None):
    win=tk.Toplevel(root);win.title(f"Review - {assignment['title']}");win.geometry("820x680");win.configure(bg=THEME["bg"]);win.grab_set()
    cls=classes.get_class(app.save_data,assignment["class_id"]) or {};students=cls.get("student_usernames",[])
    make_label(win,assignment["title"],FONT_SUBTITLE).pack(pady=10);toolbar=tk.Frame(win,bg=THEME["bg"]);toolbar.pack(fill="x",padx=20)
    first_student = initial_student if initial_student in students else (students or [""])[0]
    student_var=tk.StringVar(value=first_student);ttk.Combobox(toolbar,values=students,textvariable=student_var,state="readonly").pack(side="left")
    content=make_scrollable(win,padx=20,pady=8)
    def bulk_dialog():
        dialog=tk.Toplevel(win);dialog.title("Bulk mark");dialog.configure(bg=THEME["bg"]);dialog.grab_set();make_label(dialog,"Mark all unmarked submissions",FONT_SUBTITLE).pack(padx=20,pady=10);mark=tk.Entry(dialog,font=FONT_TEXT);mark.pack(padx=20,pady=5);feedback=tk.Entry(dialog,font=FONT_TEXT,width=45);feedback.pack(padx=20,pady=5);feedback.insert(0,"Shared feedback")
        def apply():
            try:value=float(mark.get())
            except ValueError:show_popup(app,"Enter a valid mark.");return
            if not messagebox.askyesno("Bulk mark","Apply this mark to every currently unmarked submission?"):return
            count=bulk_mark(app.save_data,assignment["id"],{u:value for u in students},feedback.get(),app.current_user);dialog.destroy();show_popup(app,f"Marked {count} submission(s).");display();on_done()
        make_button(dialog,"Apply to Unmarked",apply,wide=True);make_button(dialog,"Cancel",dialog.destroy,wide=True)
    make_button(toolbar,"Bulk Mark",bulk_dialog)
    def display(*_):
        for child in content.winfo_children():child.destroy()
        username=student_var.get();submission=assignment.get("submissions",{}).get(username)
        extension_row=tk.Frame(content,bg=THEME["bg"]);extension_row.pack(fill="x");make_label(extension_row,f"Due: {effective_due_date(assignment,username) or 'No deadline'}",FONT_TEXT).pack(side="left");extension=tk.Entry(extension_row,font=FONT_TEXT,width=14);extension.pack(side="left",padx=6);extension.insert(0,effective_due_date(assignment,username) or "")
        def save_extension():show_popup(app,"Extension saved." if set_extension(app.save_data,assignment["id"],username,extension.get(),app.current_user) else "Enter a valid date.")
        make_button(extension_row,"Set Extension",save_extension)
        if not submission:make_label(content,"This student has not submitted yet.",FONT_SUBTITLE).pack(pady=30);return
        make_card(content,"Student answer",submission.get("answer") or "(No written answer)").pack(fill="x",pady=6)
        if assignment.get("rubric"):make_label(content,"Rubric: "+" • ".join(f"{r['name']} ({r['marks']})" for r in assignment["rubric"]),FONT_TEXT).pack(anchor="w")
        make_label(content,f"Mark out of {assignment['max_marks']}",FONT_TEXT).pack(anchor="w");mark=tk.Entry(content,font=FONT_TEXT);mark.pack(fill="x");mark.insert(0,"" if submission.get("grade") is None else str(submission["grade"]))
        make_label(content,"Actionable feedback",FONT_SUBTITLE).pack(anchor="w",pady=(8,2))
        feedback_fields = {}
        for key, label in (("well", "What went well"), ("next", "Your next step"),
                           ("example", "Corrected example"), ("follow", "Try this next")):
            make_label(content,label,FONT_TEXT).pack(anchor="w")
            entry=tk.Entry(content,font=FONT_TEXT);entry.pack(fill="x",ipady=4,pady=(0,4));feedback_fields[key]=entry
        make_label(content,"Additional teacher note",FONT_TEXT).pack(anchor="w");feedback=tk.Text(content,height=4,font=FONT_TEXT);feedback.pack(fill="x");feedback.insert("1.0",submission.get("feedback") or "")
        make_label(content,"Private teacher note",FONT_TEXT).pack(anchor="w");private=tk.Entry(content,font=FONT_TEXT);private.pack(fill="x");private.insert(0,assignment.get("private_comments",{}).get(username,""))
        def save_mark():
            formatted = structured_feedback(feedback_fields["well"].get(), feedback_fields["next"].get(),
                feedback_fields["example"].get(), feedback_fields["follow"].get(), feedback.get("1.0","end"))
            if not grade_submission(app.save_data,assignment["id"],username,mark.get(),formatted,app.current_user):show_popup(app,"Enter a valid mark.");return
            app.experience_store.notify(username,"Assignment feedback ready",f"{assignment['title']} has been marked. Open Assignments to read it.","Feedback")
            add_private_comment(app.save_data,assignment["id"],username,private.get(),app.current_user);show_popup(app,"Mark, feedback, and private note saved.");display();on_done()
        make_button(content,"Save Mark & Feedback",save_mark,wide=True)
    student_var.trace_add("write",display);display();make_button(win,"Close",win.destroy,wide=True)


def show_create_assignment(root, app):
    show_teacher_assignments(root, app)


def show_student_assignments(root, app):
    clear(root); body = make_page_header(root, "My Assignments", "See what is due, submit your work, and read teacher feedback.", app.main_menu)
    style_notebook(root); notebook = ttk.Notebook(body, style="Edu.TNotebook"); notebook.pack(fill="both", expand=True)
    tab_frames = {name: tk.Frame(notebook, bg=THEME["bg"]) for name in ("To do", "Submitted", "Marked")}
    for name, frame in tab_frames.items(): notebook.add(frame, text=name)
    tabs = {name: make_scrollable(frame) for name, frame in tab_frames.items()}
    items = assignments_for_student(app.save_data, app.current_user)
    counts = {name: 0 for name in tabs}
    for item in items:
        state = assignment_state(item, app.current_user); tab_name = "To do" if state in ("To do", "Overdue") else state; counts[tab_name] += 1
        cls = classes.get_class(app.save_data, item["class_id"]) or {}; sub = item.get("submissions", {}).get(app.current_user); due_for_student = effective_due_date(item, app.current_user)
        detail = f"{cls.get('title', item['class_id'])} • {item['subject']} • {deadline_label(item, app.current_user)} • {item['max_marks']} marks"
        if state == "Overdue": detail += " • OVERDUE"
        card = make_card(tabs[tab_name], item["title"], detail, "#FF7043" if state == "Overdue" else THEME["accent"]); card.pack(fill="x", padx=10, pady=7)
        target = curriculum_target(item.get("pack_id"))
        if target:
            make_label(card, f"Linked unit: Year {target['year']} · {target['title']}", FONT_TEXT).pack(anchor="w", pady=(5, 0))
            make_button(card, "Open Linked Lesson", lambda u=target: curriculum_ui._open_unit(root, app, u, True))
        if item.get("instructions"): make_label(card, item["instructions"], FONT_TEXT).pack(anchor="w")
        if sub and sub.get("grade") is not None:
            make_label(card, f"Mark: {sub['grade']}/{item['max_marks']}\nFeedback: {sub.get('feedback') or 'No feedback added.'}", FONT_TEXT).pack(anchor="w", pady=5)
        elif sub: make_label(card, "Submitted - waiting for your teacher.", FONT_TEXT).pack(anchor="w", pady=5)
        deadline_open = not due_for_student or due_for_student >= datetime.date.today().isoformat() or item.get("allow_late", True)
        can_resubmit = not sub or item.get("resubmissions_allowed", True)
        if deadline_open and can_resubmit:
            make_button(card, "Submit Work" if not sub else "Update Submission", lambda a=item: _submission_window(root, app, a))
        elif sub:
            make_label(card, "Resubmissions are closed.", FONT_TEXT).pack(anchor="w")
        else:
            make_label(card, "The submission deadline has passed.", FONT_TEXT).pack(anchor="w")
    for name, count in counts.items():
        notebook.tab(tab_frames[name], text=f"{name} ({count})")
        if not count: make_label(tabs[name], f"Nothing in {name.lower()}.", FONT_SUBTITLE).pack(pady=40)


def _submission_window(root, app, assignment):
    if str(assignment.get("pack_id", "")).startswith("assessment:"):
        paper_id = assignment["pack_id"].split(":", 1)[1]
        paper = next((item for item in app.experience_store.assessment_papers_for_student(app.current_user)
                      if item["id"] == paper_id), None)
        if paper:
            _assessment_submission_window(root, app, assignment, paper)
            return
    win = tk.Toplevel(root); win.title(assignment["title"]); win.geometry("700x520"); win.configure(bg=THEME["bg"]); win.grab_set()
    make_label(win, assignment["title"], FONT_SUBTITLE).pack(pady=10); make_label(win, assignment.get("instructions") or "Write your answer below.", FONT_TEXT).pack(padx=20)
    answer = tk.Text(win, height=14, font=FONT_TEXT, bg=THEME.get("panel", THEME["bg"]), fg=THEME["fg"], insertbackground=THEME["fg"]); answer.pack(fill="both", expand=True, padx=20, pady=(12, 4))
    old = assignment.get("submissions", {}).get(app.current_user, {}); answer.insert("1.0", old.get("answer") or "")
    count_label = make_label(win, "0 words", FONT_TEXT); count_label.pack(anchor="e", padx=20, pady=(0, 4))
    def update_count(event=None):
        del event
        words = len(answer.get("1.0", "end").split()); count_label.config(text=f"{words} word{'s' if words != 1 else ''}")
    answer.bind("<KeyRelease>", update_count); update_count()
    def submit():
        if not answer.get("1.0", "end").strip(): show_popup(app, "Write an answer before submitting."); return
        if old and not messagebox.askyesno("Update submission", "Replace your earlier submission with this version?"):
            return
        if submit_assignment(app.save_data, assignment["id"], app.current_user, answer.get("1.0", "end")):
            win.destroy(); show_popup(app, "Work submitted successfully."); show_student_assignments(root, app)
        else: show_popup(app, "This assignment is no longer available.")
    make_button(win, "Update Submission" if old else "Submit Work", submit, wide=True); make_button(win, "Cancel", win.destroy, wide=True)


def _assessment_submission_window(root, app, assignment, paper):
    win = tk.Toplevel(root); win.title(paper["title"]); win.geometry("820x720"); win.configure(bg=THEME["bg"]); win.grab_set()
    body = make_scrollable(win, padx=20, pady=14)
    make_label(body, paper["title"], FONT_SUBTITLE).pack(pady=(0, 4))
    make_card(body, "Paper instructions",
        f"Year {paper['year']} {paper['subject']} • Suggested time {paper['duration']} minutes • "
        f"{sum(item.get('marks', 1) for item in paper['questions'])} marks\nAnswer every question, then submit the complete paper.",
        THEME["accent"]).pack(fill="x", pady=5)
    responses = []
    for index, question in enumerate(paper["questions"], 1):
        card = make_card(body, f"Question {index}", f"{question['prompt']} [{question.get('marks', 1)}]", "#4EA3FF")
        card.pack(fill="x", pady=5)
        response = tk.Text(card, height=3, font=FONT_TEXT); response.pack(fill="x", pady=4)
        responses.append(response)
    old = assignment.get("submissions", {}).get(app.current_user, {})
    if old and old.get("answer"):
        make_card(body, "Previous submitted version", old["answer"], "#FFB84D").pack(fill="x", pady=6)

    def submit():
        values = [field.get("1.0", "end").strip() for field in responses]
        if any(not value for value in values):
            show_popup(app, "Answer every question before submitting the paper."); return
        if old and not messagebox.askyesno("Update assessment", "Replace your earlier assessment submission?"):
            return
        combined = "\n\n".join(f"Question {index}:\n{value}" for index, value in enumerate(values, 1))
        if submit_assignment(app.save_data, assignment["id"], app.current_user, combined):
            win.destroy(); show_popup(app, "Assessment submitted successfully."); show_student_assignments(root, app)
        else: show_popup(app, "This assessment is no longer available.")
    make_button(body, "Submit Complete Paper", submit, wide=True)
    make_button(body, "Cancel", win.destroy, wide=True, kind="secondary")
