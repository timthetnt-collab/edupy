"""Assessment, intervention, resource, revision-paper and learner-goal tools."""

import datetime
import os
import tkinter as tk
from tkinter import filedialog, ttk

import assignments
import classes
import curriculum
import curriculum_ui
import maths
import save_system
from settings import FONT_SUBTITLE, FONT_TEXT, THEME
from ui import clear, make_action_tile, make_button, make_card, make_label, make_page_header, make_progress_bar, make_scrollable, make_section_header, make_stat, show_popup


def _profile(app, username=None):
    return save_system.get_user(app.save_data, username or app.current_user) or {}


def _owned_classes(app):
    role = _profile(app).get("role", "student")
    return classes.get_classes(app.save_data, app.current_user, role)


def generate_assessment_questions(year, subject, topics, count=10, difficulty=2):
    """Build a balanced, serialisable paper from one or more curriculum topics."""
    try:
        year, count, difficulty = int(year), int(count), int(difficulty)
    except (TypeError, ValueError):
        return []
    topics = [str(topic).strip() for topic in topics if str(topic).strip()]
    if not 7 <= year <= 11 or subject not in ("Maths", "English") or not topics:
        return []
    questions = []
    for index in range(max(1, min(40, count))):
        topic = topics[index % len(topics)]
        if subject == "Maths":
            item = maths.generate_question_data(year, topic, difficulty=max(1, min(4, difficulty)),
                category=("Fluency", "Applied", "Reasoning", "Exam-style")[index % 4])
            prompt, answer = item.get("prompt", ""), item.get("answer", "")
            marks = 2 if item.get("category") in ("Reasoning", "Exam-style") else 1
        else:
            item = curriculum_ui._english_assessment_question(year, topic, index)
            prompt, answer = item.get("prompt", ""), item.get("answer", "")
            marks = int(item.get("max_score", 1))
        if str(prompt).strip() and str(answer).strip():
            questions.append({"prompt": str(prompt), "answer": str(answer), "marks": marks,
                "topic": topic, "choices": list(item.get("choices", []))})
    return questions


def paper_text(paper, answers=False):
    heading = f"{paper['title']}\nYear {paper['year']} {paper['subject']} • {paper['duration']} minutes\n"
    total = sum(int(item.get("marks", 1)) for item in paper["questions"])
    lines = [heading, f"Total marks: {total}", ""]
    for index, question in enumerate(paper["questions"], 1):
        lines.append(f"{index}. {question['prompt']} [{question.get('marks', 1)}]")
        if question.get("choices"): lines.append("   " + " | ".join(question["choices"]))
        if answers: lines.append(f"   Answer: {question['answer']}")
        else: lines.extend(["", "   ______________________________________________", ""])
    return "\n".join(lines)


def _save_paper_file(app, paper, answers=False):
    suffix = "mark-scheme" if answers else "student-paper"
    path = filedialog.asksaveasfilename(
        title="Save revision paper", defaultextension=".txt",
        initialfile=f"{paper['title'].replace(' ', '-')}-{suffix}.txt",
        filetypes=[("Text document", "*.txt")],
    )
    if not path: return
    try:
        with open(path, "w", encoding="utf-8") as file: file.write(paper_text(paper, answers))
        show_popup(app, f"Saved {os.path.basename(path)}")
    except OSError as error:
        show_popup(app, f"The paper could not be saved: {error}")


def show_assessment_builder(root, app):
    if _profile(app).get("role") not in ("teacher", "admin"):
        app.main_menu(); return
    clear(root)
    body = make_page_header(root, "Assessment & Revision Paper Builder", "Create balanced topic papers, preview answers and assign them to a class.", app.open_teacher_hub)
    body = make_scrollable(body)
    form = make_card(body, "Paper setup", "Choose a year, subject and several topics. EduPy rotates questions across them.", THEME["accent"]); form.pack(fill="x", pady=6)
    title = tk.StringVar(value="End of unit assessment"); year = tk.StringVar(value="8"); subject = tk.StringVar(value="Maths")
    count = tk.StringVar(value="10"); difficulty = tk.StringVar(value="2"); duration = tk.StringVar(value="45")
    tk.Entry(form, textvariable=title, font=FONT_TEXT).pack(fill="x", ipady=5, pady=3)
    controls = tk.Frame(form, bg=form["bg"]); controls.pack(fill="x", pady=3)
    for values, variable, width in (([str(x) for x in range(7, 12)], year, 8), (["Maths", "English"], subject, 10),
            (["5", "10", "15", "20"], count, 8), (["1", "2", "3", "4"], difficulty, 8),
            (["20", "30", "45", "60", "90"], duration, 8)):
        ttk.Combobox(controls, values=values, textvariable=variable, state="readonly", width=width).pack(side="left", padx=3)
    make_label(form, "Topics (select one or more)", FONT_TEXT).pack(anchor="w")
    topic_list = tk.Listbox(form, selectmode="extended", height=9, exportselection=False, font=FONT_TEXT)
    topic_list.pack(fill="x", pady=4); topic_ids = []

    def rebuild_topics(*_):
        topic_list.delete(0, "end"); topic_ids.clear()
        for topic_id, name in curriculum.topics_for(int(year.get()), subject.get()):
            topic_ids.append(topic_id); topic_list.insert("end", name)
        if topic_ids: topic_list.selection_set(0)
    year.trace_add("write", rebuild_topics); subject.trace_add("write", rebuild_topics); rebuild_topics()
    def build():
        selected = [topic_ids[index] for index in topic_list.curselection()]
        questions = generate_assessment_questions(year.get(), subject.get(), selected, count.get(), difficulty.get())
        paper_id = app.experience_store.create_assessment_paper(app.current_user, title.get(), year.get(), subject.get(), duration.get(), selected, questions)
        if not paper_id:
            show_popup(app, "Add a title and select at least one topic."); return
        show_assessment_builder(root, app)
    make_button(form, "Generate & Save Paper", build, wide=True)
    make_section_header(body, "Saved papers", "Export student and mark-scheme copies or create a linked assignment.")
    owned = _owned_classes(app); class_map = {item["id"]: item for item in owned}
    for paper in app.experience_store.assessment_papers(app.current_user):
        total = sum(item.get("marks", 1) for item in paper["questions"])
        card = make_card(body, paper["title"], f"Year {paper['year']} {paper['subject']} • {len(paper['questions'])} questions • {total} marks • {paper['duration']} minutes", "#4EA3FF")
        card.pack(fill="x", pady=5)
        selected_class = tk.StringVar(value=owned[0]["id"] if owned else "")
        if owned: ttk.Combobox(card, values=list(class_map), textvariable=selected_class, state="readonly").pack(fill="x", pady=3)
        actions = tk.Frame(card, bg=card["bg"]); actions.pack(fill="x")
        make_button(actions, "Student Copy", lambda item=paper: _save_paper_file(app, item), kind="secondary")
        make_button(actions, "Mark Scheme", lambda item=paper: _save_paper_file(app, item, True), kind="secondary")
        def assign(item=paper, selected=selected_class):
            cls = class_map.get(selected.get())
            if not cls: show_popup(app, "Choose a class first."); return
            assignment_id = assignments.create_assignment(
                app.save_data, item["title"], cls["id"], pack_id=f"assessment:{item['id']}",
                instructions=f"Complete the attached EduPy paper: {len(item['questions'])} questions, {item['duration']} minutes. Your teacher can provide the exported student copy.",
                subject=item["subject"], max_marks=sum(q.get("marks", 1) for q in item["questions"]),
                reward_tokens=5, created_by=app.current_user,
            )
            if assignment_id: save_system.save_save(app.save_data); show_popup(app, "Assessment assigned to the class.")
            else: show_popup(app, "The assignment could not be created.")
        make_button(actions, "Assign to Class", assign)


def intervention_rows(data, school_classes):
    """Produce explainable support prompts, never labels or automated decisions."""
    students = sorted({name for cls in school_classes for name in cls.get("student_usernames", [])})
    rows = []
    for username in students:
        profile = data.get("users", {}).get(username, {})
        assigned = [item for item in data.get("assignments", {}).values()
            if username in data.get("classes", {}).get(item.get("class_id"), {}).get("student_usernames", [])
            and assignments.assignment_is_available(item)]
        submitted = sum(username in item.get("submissions", {}) for item in assigned)
        completion = round(submitted / len(assigned) * 100) if assigned else 100
        scores = []
        for topics in profile.get("mastery", {}).values():
            for record in topics.values():
                possible = float(record.get("possible", 0) or 0)
                if possible: scores.append(float(record.get("earned", 0)) / possible * 100)
        mastery = round(sum(scores) / len(scores)) if scores else None
        reasons = []
        if len(assigned) >= 2 and completion < 50: reasons.append(f"{completion}% of published assignments submitted")
        if mastery is not None and mastery < 50: reasons.append(f"{mastery}% average recorded topic mastery")
        if not profile.get("recent_topics") and assigned: reasons.append("no independent topic practice recorded yet")
        if reasons:
            rows.append({"student": username, "completion": completion, "mastery": mastery,
                "reasons": reasons, "suggestion": "Check in, confirm access to the work, then agree one small next step."})
    return rows


def show_intervention_dashboard(root, app):
    if _profile(app).get("role") not in ("teacher", "admin"):
        app.main_menu(); return
    clear(root); body = make_page_header(root, "Intervention Dashboard", "Explainable prompts for teacher review—not automatic judgements about children.", app.open_teacher_hub)
    body = make_scrollable(body); owned = _owned_classes(app); rows = intervention_rows(app.save_data, owned)
    make_card(body, "How this works", "EduPy highlights incomplete work, low recorded mastery and missing practice evidence. Teachers decide what the evidence means and what support is appropriate.", THEME["accent"]).pack(fill="x", pady=6)
    make_section_header(body, f"{len(rows)} learner(s) to review", "Start with a supportive conversation and check the context.")
    for item in rows:
        card = make_card(body, item["student"], "\n".join(f"• {reason}" for reason in item["reasons"]) + f"\nSuggested response: {item['suggestion']}", "#FFB84D")
        card.pack(fill="x", pady=5)
        goals = app.experience_store.goals(item["student"], False, app.current_user)
        if goals: make_label(card, "Active goals: " + " • ".join(goal["title"] for goal in goals[:3]), FONT_TEXT).pack(anchor="w")
    if not rows: make_card(body, "No current prompts", "Available assignment and mastery evidence does not show an obvious support pattern.", "#58D68D").pack(fill="x", pady=8)


def show_content_studio(root, app):
    if _profile(app).get("role") not in ("teacher", "admin"):
        app.main_menu(); return
    clear(root); body = make_page_header(root, "Teacher Content Studio", "Build reusable lesson explanations connected to exact curriculum topics.", app.open_teacher_hub)
    body = make_scrollable(body)
    form = make_card(body, "New lesson resource", "Include an explanation, worked example, common mistake and practice instruction.", THEME["accent"]); form.pack(fill="x", pady=6)
    title = tk.StringVar(); year = tk.StringVar(value="8"); subject = tk.StringVar(value="Maths"); topic = tk.StringVar(); summary = tk.StringVar()
    tk.Entry(form, textvariable=title, font=FONT_TEXT).pack(fill="x", ipady=5, pady=3)
    row = tk.Frame(form, bg=form["bg"]); row.pack(fill="x")
    ttk.Combobox(row, values=[str(x) for x in range(7, 12)], textvariable=year, state="readonly", width=8).pack(side="left", padx=3)
    ttk.Combobox(row, values=["Maths", "English"], textvariable=subject, state="readonly", width=10).pack(side="left", padx=3)
    topic_combo = ttk.Combobox(form, textvariable=topic, state="readonly"); topic_combo.pack(fill="x", pady=3); topic_map = {}
    def topics(*_):
        topic_map.clear()
        for topic_id, name in curriculum.topics_for(int(year.get()), subject.get()): topic_map[name] = topic_id
        topic_combo["values"] = list(topic_map)
        if topic.get() not in topic_map and topic_map: topic.set(next(iter(topic_map)))
    year.trace_add("write", topics); subject.trace_add("write", topics); topics()
    tk.Entry(form, textvariable=summary, font=FONT_TEXT).pack(fill="x", ipady=5, pady=3)
    content = tk.Text(form, height=12, font=FONT_TEXT); content.pack(fill="x", pady=4)
    content.insert("1.0", "Explanation:\n\nWorked example:\n\nCommon mistake:\n\nTry it yourself:")
    def save_resource(publish):
        result = app.experience_store.create_teacher_resource(app.current_user, title.get(), year.get(), subject.get(), topic_map.get(topic.get(), ""), summary.get(), content.get("1.0", "end"), publish)
        if result: show_content_studio(root, app)
        else: show_popup(app, "Add a title, topic and at least a short lesson explanation.")
    make_button(form, "Save Draft", lambda: save_resource(False)); make_button(form, "Publish Resource", lambda: save_resource(True))
    make_section_header(body, "Resource library", "Published resources are available to learners; drafts remain private.")
    for item in app.experience_store.teacher_resources(app.current_user):
        make_card(body, item["title"], f"Year {item['year']} {item['subject']} • {item['status'].title()}\n{item['summary']}\n\n{item['content'][:500]}", "#58D68D" if item["status"] == "published" else "#FFB84D").pack(fill="x", pady=5)


def show_student_goals(root, app):
    if _profile(app).get("role") != "student":
        app.main_menu(); return
    clear(root); body = make_page_header(root, "My Learning Goals", "Choose one manageable target, practise it and reflect on what helped.", app.main_menu)
    body = make_scrollable(body)
    form = make_card(body, "Set a goal", "Make it specific: what will you be able to do, and by when?", THEME["accent"]); form.pack(fill="x", pady=6)
    title = tk.StringVar(); subject = tk.StringVar(value="General"); target = tk.StringVar()
    tk.Entry(form, textvariable=title, font=FONT_TEXT).pack(fill="x", ipady=5, pady=3)
    ttk.Combobox(form, values=["General", "Maths", "English"], textvariable=subject, state="readonly").pack(fill="x", pady=3)
    tk.Entry(form, textvariable=target, font=FONT_TEXT).pack(fill="x", ipady=5, pady=3)
    make_label(form, "Optional target date: YYYY-MM-DD", FONT_TEXT).pack(anchor="w")
    def create():
        goal = app.experience_store.create_goal(app.current_user, title.get(), subject.get(), target.get().strip() or None)
        if goal: show_student_goals(root, app)
        else: show_popup(app, "Write a clear goal of at least five characters and check the date.")
    make_button(form, "Create Goal", create, wide=True)
    goals = app.experience_store.goals(app.current_user)
    make_section_header(body, "Your goals", f"{sum(goal['status'] == 'active' for goal in goals)} active")
    for goal in goals:
        detail = f"{goal['subject']}" + (f" • Target {goal['target_date']}" if goal.get("target_date") else "")
        if goal["reflection"]: detail += f"\nReflection: {goal['reflection']}"
        card = make_card(body, goal["title"], detail, "#58D68D" if goal["status"] == "completed" else "#FFB84D"); card.pack(fill="x", pady=5)
        if goal["status"] == "active":
            reflection = tk.StringVar(); tk.Entry(card, textvariable=reflection, font=FONT_TEXT).pack(fill="x", ipady=5, pady=3)
            make_button(card, "Complete & Reflect", lambda item=goal, text=reflection: (app.experience_store.complete_goal(app.current_user, item["id"], text.get()), show_student_goals(root, app)))


def show_published_resources(root, app):
    clear(root); body = make_page_header(root, "Teacher Resource Library", "Reusable explanations and examples published by your teachers.", app.main_menu)
    body = make_scrollable(body); resources = [item for item in app.experience_store.teacher_resources(app.current_user, True) if item["year"] == app.difficulty_value]
    for item in resources:
        make_card(body, item["title"], f"{item['subject']} • {item['summary']}\n\n{item['content']}", "#58D68D").pack(fill="x", pady=6)
    if not resources: make_card(body, "No published resources yet", "Teacher-created lesson resources for your year will appear here.").pack(fill="x", pady=8)
