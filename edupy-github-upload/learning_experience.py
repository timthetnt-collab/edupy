"""Student diagnostics, lessons, Today dashboard, revision and safety UI."""

import datetime
import tkinter as tk
from tkinter import ttk

import assignments
import platform_features
import curriculum
import curriculum_ui
import english
import maths
import save_system
import ui
from settings import THEME, FONT_TITLE, FONT_SUBTITLE, FONT_TEXT, set_theme
from ui import clear, make_action_tile, make_button, make_card, make_label, make_page_header, make_scrollable, make_section_header, make_stat, show_popup, style_notebook


DIAGNOSTIC_BANK = {
    7: [
        ("Maths", "number", "What is -7 + 12?", ["3", "5", "19", "-19"], "5"),
        ("Maths", "fractions", "Which decimal equals 3/4?", ["0.34", "0.5", "0.75", "1.25"], "0.75"),
        ("Maths", "algebra", "Solve 3x + 5 = 20.", ["3", "5", "8", "15"], "5"),
        ("Maths", "geometry", "Two angles in a triangle are 50° and 60°. Find the third.", ["60°", "70°", "80°", "110°"], "70°"),
        ("English", "retrieval", "Which answer is retrieval?", ["A fact stated directly", "A hidden meaning", "A personal opinion", "A prediction"], "A fact stated directly"),
        ("English", "inference", "An inference is best described as…", ["Copying a sentence", "A conclusion supported by clues", "Counting paragraphs", "Correcting spelling"], "A conclusion supported by clues"),
        ("English", "language", "Which phrase is a simile?", ["The moon was a lamp", "The moon shone", "The moon was like a lamp", "Bright moon"], "The moon was like a lamp"),
        ("English", "grammar", "Which joins two related complete clauses correctly?", ["It rained; we stayed inside.", "It; rained we stayed.", "It rained; because cold.", "It, rained;"], "It rained; we stayed inside."),
    ],
    8: [
        ("Maths", "power_notation", "What is 2⁵?", ["10", "16", "25", "32"], "32"),
        ("Maths", "linear_equations_one_side", "Solve 4x - 7 = 21.", ["3.5", "7", "14", "28"], "7"),
        ("Maths", "mutually_exclusive", "A fair die is rolled. P(even) is…", ["1/6", "1/3", "1/2", "2/3"], "1/2"),
        ("Maths", "translations", "A reflection changes a shape's…", ["Size only", "Orientation and position", "Area", "Side lengths"], "Orientation and position"),
        ("English", "language", "A metaphor…", ["Uses like or as", "States one thing is another", "Repeats a sound", "Asks a question"], "States one thing is another"),
        ("English", "structure", "A shift in focus is mainly a feature of…", ["Structure", "Spelling", "Vocabulary", "Handwriting"], "Structure"),
        ("English", "viewpoint", "A rhetorical question is normally used to…", ["Request an answer", "Influence the audience", "Give a date", "Introduce a character"], "Influence the audience"),
        ("English", "comparison", "The strongest comparison begins with…", ["A clear similarity or difference", "A list of words", "One text only", "The conclusion"], "A clear similarity or difference"),
    ],
    9: [
        ("Maths", "algebra", "Expand (x + 3)(x + 2).", ["x² + 5x + 6", "x² + 6", "x² + 3x + 2", "2x + 5"], "x² + 5x + 6"),
        ("Maths", "number", "Write 0.00042 in standard form.", ["4.2 × 10⁻⁴", "42 × 10⁻⁴", "4.2 × 10⁴", "0.42 × 10⁻³"], "4.2 × 10⁻⁴"),
        ("Maths", "geometry", "A right triangle has shorter sides 6 and 8. Its hypotenuse is…", ["10", "12", "14", "100"], "10"),
        ("Maths", "statistics", "Positive correlation means…", ["Both variables tend to increase together", "One always causes the other", "No pattern", "Values are equal"], "Both variables tend to increase together"),
        ("English", "analysis", "An analytical paragraph should connect evidence to…", ["The writer's method and effect", "The page number only", "A plot summary", "The title only"], "The writer's method and effect"),
        ("English", "structure", "A cyclical structure…", ["Returns to an opening idea", "Has no paragraphs", "Uses only dialogue", "Lists facts"], "Returns to an opening idea"),
        ("English", "comparison", "Which word signals contrast?", ["Similarly", "Moreover", "Whereas", "Therefore"], "Whereas"),
        ("English", "transactional", "Transactional writing must be shaped for…", ["Audience and purpose", "The writer only", "Rhyme", "A fictional narrator"], "Audience and purpose"),
    ],
    10: [
        ("Maths", "algebra", "Solve x² - 5x + 6 = 0.", ["x = 2 or 3", "x = -2 or -3", "x = 1 or 6", "x = 5 or 6"], "x = 2 or 3"),
        ("Maths", "graphs", "The gradient of y = 3x - 4 is…", ["-4", "3", "4", "7"], "3"),
        ("Maths", "geometry", "In a right triangle, sin θ equals…", ["adjacent/hypotenuse", "opposite/hypotenuse", "opposite/adjacent", "hypotenuse/opposite"], "opposite/hypotenuse"),
        ("Maths", "statistics", "The median is…", ["The most frequent value", "The middle ordered value", "The range", "The total"], "The middle ordered value"),
        ("English", "ao1", "AO1 primarily rewards…", ["Selecting information and making inferences", "Spelling only", "Comparing writers", "Creative vocabulary"], "Selecting information and making inferences"),
        ("English", "ao2", "AO2 asks you to analyse…", ["Language and structure", "Dates and facts", "Only opinions", "Handwriting"], "Language and structure"),
        ("English", "ao4", "A strong evaluation includes…", ["A judgement supported by evidence", "A technique list", "No quotations", "Plot summary only"], "A judgement supported by evidence"),
        ("English", "accuracy", "A sentence fragment is…", ["An incomplete sentence", "A long paragraph", "A rhetorical question", "A quotation"], "An incomplete sentence"),
    ],
    11: [
        ("Maths", "algebra", "Factorise x² - 9.", ["(x - 3)(x + 3)", "(x - 9)(x + 1)", "x(x - 9)", "(x - 3)²"], "(x - 3)(x + 3)"),
        ("Maths", "proportion", "£200 grows by 5%. The new value is…", ["£205", "£210", "£215", "£250"], "£210"),
        ("Maths", "geometry", "A vector describes…", ["Magnitude and direction", "Area only", "An angle only", "Probability"], "Magnitude and direction"),
        ("Maths", "probability", "Conditional probability considers…", ["Information that an event has occurred", "Only fair dice", "Impossible events", "Averages"], "Information that an event has occurred"),
        ("English", "ao3", "AO3 comparison should explore…", ["Ideas and perspectives across texts", "One text only", "Spelling", "Paragraph length"], "Ideas and perspectives across texts"),
        ("English", "ao4", "Perceptive evaluation means…", ["A developed, evidence-based judgement", "Agreeing completely", "Listing techniques", "Retelling content"], "A developed, evidence-based judgement"),
        ("English", "transactional", "A counterargument helps by…", ["Addressing another viewpoint", "Changing the topic", "Removing structure", "Avoiding evidence"], "Addressing another viewpoint"),
        ("English", "revision", "The best first comparison step is…", ["Form a comparative idea", "Copy both openings", "List punctuation", "Write two separate summaries"], "Form a comparative idea"),
    ],
}


MATHS_GUIDES = {
    "number": ("Number work is about representing values accurately and choosing efficient operations.", "Write the values clearly, choose an operation, estimate, calculate, then check the size of the answer.", "For 3.2 × 10⁴, move the decimal four places: 32,000.", "Ignoring negative signs or place value.", "integer, operation, place value, estimate"),
    "fractions": ("Fractions, decimals and percentages are different ways to describe parts of a whole.", "Convert to a common form before comparing or calculating.", "3/4 = 0.75 = 75%.", "Adding denominators when adding fractions.", "numerator, denominator, equivalent, percentage"),
    "algebra": ("Algebra uses symbols to represent numbers and relationships.", "Simplify, perform inverse operations, and keep both sides balanced.", "3x + 5 = 20 → 3x = 15 → x = 5.", "Changing one side of an equation without changing the other.", "expression, equation, coefficient, factor"),
    "ratio": ("A ratio compares quantities multiplicatively.", "Find the total number of parts, find one part, then scale.", "2:3 has 5 parts; £25 gives £10 and £15.", "Treating a ratio like subtraction.", "ratio, part, scale, proportion"),
    "proportion": ("Proportion describes quantities that change in a linked way.", "Find a unit value or multiplier, then apply it consistently.", "If 4 items cost £6, one costs £1.50 and 10 cost £15.", "Using additive change when the relationship is multiplicative.", "unit rate, multiplier, direct, inverse"),
    "geometry": ("Geometry uses properties, measurements and logical relationships between shapes.", "Draw and label the diagram, select the correct property, calculate, and include units.", "In a triangle, the angles total 180°.", "Using a rule without checking the shape or units.", "angle, parallel, congruent, area"),
    "statistics": ("Statistics turns data into useful summaries while recognising variation.", "Check the data type, choose a suitable measure, calculate, then interpret in context.", "For 2, 4, 4, 10 the median is 4 and the mean is 5.", "Giving a number without explaining what it means.", "mean, median, range, distribution"),
    "probability": ("Probability measures how likely an event is from 0 to 1.", "List outcomes, identify favourable outcomes, divide, and simplify.", "Three even results on a fair die gives 3/6 = 1/2.", "Counting outcomes that are not equally likely as though they are.", "outcome, event, sample space, conditional"),
    "graphs": ("Graphs show relationships between variables.", "Identify axes and scale, plot accurately, then interpret gradient and intercept.", "In y = 3x - 4, gradient = 3 and intercept = -4.", "Confusing the gradient with the intercept.", "coordinate, gradient, intercept, function"),
    "reasoning": ("Multi-step reasoning combines several mathematical ideas.", "Underline what is known, decide intermediate steps, show working, and check reasonableness.", "Convert units before substituting into a formula.", "Starting calculations before planning the route.", "justify, derive, estimate, verify"),
}


ENGLISH_GUIDES = {
    "retrieval": ("Retrieval means finding information the writer states directly.", "Underline the key words in the question, scan for the same idea, then copy only the precise evidence needed.", "If asked where a character waits, locate the place named in the text and answer in a short phrase.", "Adding an inference when the question only asks for a stated fact.", "retrieve, explicit, evidence, scan"),
    "inference": ("Inference is a conclusion built from clues in the text rather than a guess.", "Make a clear inference, select a short quotation, then explain exactly which word supports it.", "‘He checked the lock twice’ suggests he feels anxious because repeating the check shows he is not reassured.", "Making a plausible claim without linking it to textual evidence.", "infer, implicit, clue, suggest"),
    "language": ("Language analysis explains how a writer's precise choices shape meaning and response.", "Choose a short quotation, zoom in on one word or image, explore its associations, then connect back to the question.", "Calling the street a ‘maze’ suggests confusion and entrapment, making the setting feel difficult to escape.", "Naming a technique and moving on without analysing the words.", "connotation, imagery, metaphor, tone"),
    "structure": ("Structure is how information is ordered, revealed and connected across a whole text.", "Track the opening, shifts in focus or time, pace, and ending; explain why the writer places each part there.", "A shift from the crowded platform to one silent character narrows the focus and increases tension.", "Writing about a single word when the question asks how the whole text is organised.", "focus, shift, contrast, pace, cyclical"),
    "comparison": ("Comparison explores meaningful similarities and differences between writers' ideas and methods.", "Start with a comparative idea, use evidence from both texts, analyse each method, then explain the important difference.", "Both writers present isolation, but one treats it as freedom whereas the other presents it as frightening.", "Writing two separate mini-essays without connecting the texts.", "similarly, whereas, perspective, contrast"),
    "viewpoint": ("Viewpoint writing uses deliberate choices to influence a particular audience.", "Clarify audience and purpose, form a position, sequence three developed reasons, address a counterargument, and finish decisively.", "A school speech might combine direct address, a real example and a clear call to action.", "Using lots of techniques without a logical argument.", "audience, purpose, rhetoric, counterargument"),
    "transactional": ("Transactional writing communicates a clear viewpoint in a real-world form such as an article, letter or speech.", "Match the form, establish your position, develop connected arguments, vary sentences for emphasis, and proofread.", "An article needs an engaging headline and opening, developed paragraphs, and a memorable conclusion.", "Forgetting the conventions of the requested form.", "form, register, cohesion, discourse marker"),
    "analysis": ("Analytical writing makes a focused argument about how a writer creates meaning.", "Write a precise point, embed brief evidence, analyse a method and key word, then develop an alternative or deeper interpretation.", "The verb ‘clutched’ conveys desperation; it may also suggest the object has become a source of security.", "Retelling what happens instead of explaining how meaning is created.", "thesis, evidence, method, interpretation"),
    "ao1": ("AO1 rewards accurate understanding, well-chosen references and supported inference.", "Answer the exact focus, choose concise evidence from across the relevant section, and explain the inference each detail supports.", "Combine two details only when they support the same clear inference.", "Copying large sections without selecting or interpreting them.", "select, synthesise, reference, inference"),
    "ao2": ("AO2 rewards analysis of how language and structure create effects and meanings.", "Use a conceptual point, concise evidence, close word analysis, structural context, and a developed effect.", "Explore both what an image suggests and why it appears at that moment in the text.", "Technique spotting or claiming every device simply ‘engages the reader’.", "method, effect, connotation, structural shift"),
    "ao3": ("AO3 rewards comparison of writers' ideas and perspectives and how they convey them.", "Build each paragraph around a comparison, move between both texts, and connect method to viewpoint.", "One writer's nostalgic imagery contrasts with the other's blunt criticism, revealing different attitudes to change.", "Comparing only subject matter and ignoring the writers' perspectives.", "perspective, attitude, synthesis, contrast"),
    "ao4": ("AO4 evaluation requires a convincing judgement supported by careful evidence and analysis.", "State how far you agree, select evidence, analyse how it supports or complicates the statement, then refine your judgement.", "‘Largely convincing’ is stronger when followed by why one moment supports the claim and another qualifies it.", "Repeating ‘I agree’ without evaluating the writer's choices.", "evaluate, judgement, convincing, qualify"),
    "creative": ("Creative writing controls viewpoint, detail, structure and accuracy to create a deliberate effect.", "Plan one central change, choose a viewpoint, open with a precise image, vary pace, and craft a purposeful ending.", "Zoom from a wide setting to one small object, then let that object trigger the change in the scene.", "Adding endless events instead of developing a controlled moment.", "viewpoint, motif, pace, sensory detail"),
    "narrative": ("Narrative writing shapes a sequence of events around a character, change or discovery.", "Give the character a clear want, introduce a problem, slow down the key moment, then show what has changed.", "A lost key becomes interesting when it forces the character to make a difficult choice.", "Starting every sentence the same way or rushing the turning point.", "character, conflict, turning point, resolution"),
    "grammar": ("Grammar and punctuation make relationships between ideas clear.", "Identify the sentence's main clause, add detail deliberately, and choose punctuation according to its job.", "A semicolon can join two closely related main clauses: The gate was open; nobody moved.", "Choosing punctuation because it looks dramatic rather than because it fits the sentence.", "clause, conjunction, modifier, punctuation"),
    "accuracy": ("Accuracy includes controlled sentences, precise vocabulary, secure spelling and purposeful punctuation.", "Draft for meaning first, then check sentence boundaries, verb agreement, commonly confused words and punctuation.", "Read each sentence alone: if it cannot stand independently, join or reshape the fragment.", "Using unnecessarily complicated words that make the meaning less precise.", "syntax, agreement, fragment, register"),
    "revision": ("Strong exam revision combines recall, timed application and careful review.", "Recall the method from memory, practise one focused question, compare against success criteria, then record one improvement.", "After a timed paragraph, highlight the point, evidence and analysis in different colours to find gaps.", "Rereading notes repeatedly without testing whether you can apply them.", "retrieval practice, timing, reflection, transfer"),
}


def lesson_guide(year, subject, topic_id):
    title = curriculum.topic_title(year, subject, topic_id)
    if subject == "Maths":
        if year == 8:
            import year8_maths
            base = year8_maths.guide(topic_id) or MATHS_GUIDES.get("reasoning")
        else:
            family = curriculum.question_family(year, subject, topic_id)
            base = MATHS_GUIDES.get(family, MATHS_GUIDES.get("reasoning"))
    else:
        family = curriculum.question_family(year, subject, topic_id)
        base = ENGLISH_GUIDES.get(family, (
            f"{title} develops careful reading or purposeful writing. Strong responses make a clear point and support it precisely.",
            "Read the question, identify the focus, choose precise evidence or ideas, explain the method and effect, then review your response.",
            "Point: the writer creates tension. Evidence: choose a short quotation. Explain how one word shapes the reader's response.",
            "Naming a technique without explaining its effect, or retelling instead of analysing.",
            "evidence, inference, method, structure, effect, audience, purpose",
        ))
    return {"title": title, "explanation": base[0], "steps": base[1], "example": base[2], "mistake": base[3], "vocabulary": base[4]}


def learning_plan(data, username, limit=5):
    user = save_system.get_user(data, username) or {}
    year = user.get("selected_year", 7)
    items = []
    for subject in ("Maths", "English"):
        for order, (topic_id, title) in enumerate(curriculum.topics_for(year, subject)):
            record = user.get("mastery", {}).get(subject, {}).get(topic_id, {})
            attempts = int(record.get("attempts", 0)); score = curriculum.mastery_percent(user, subject, topic_id)
            priority = (0 if attempts and score < 50 else 1 if attempts == 0 else 2, score, order)
            items.append({"subject": subject, "topic": topic_id, "title": title, "mastery": score, "attempts": attempts, "priority": priority})
    return sorted(items, key=lambda item: item["priority"])[:limit]


def _mastery_for_unit(user, unit):
    return curriculum.mastery_percent(user, unit["subject"], unit["id"])


def diagnostic_summary(results):
    """Build a friendly, non-judgemental summary of a diagnostic attempt."""
    by_subject = {}
    for item in results or []:
        earned, possible = float(item.get("earned", 0)), max(1.0, float(item.get("possible", 1)))
        subject = item.get("subject", "Other")
        totals = by_subject.setdefault(subject, {"earned": 0.0, "possible": 0.0})
        totals["earned"] += earned; totals["possible"] += possible
    return {
        subject: round(values["earned"] / values["possible"] * 100)
        for subject, values in by_subject.items()
    }


def show_diagnostic(root, app):
    year = app.difficulty_value; questions = DIAGNOSTIC_BANK[year]
    state = {"index": 0, "results": []}
    def render():
        clear(root); index = state["index"]
        if index >= len(questions):
            app.experience_store.record_diagnostic(app.current_user, year, state["results"])
            for result in state["results"]:
                curriculum.record_mastery(app.save_data, app.current_user, result["subject"], result["topic"], result["earned"], result["possible"])
            body = make_page_header(root, "Starting Check Complete", "EduPy has created your first personalised learning path.", app.main_menu)
            correct = sum(result["earned"] for result in state["results"])
            make_stat(body, f"{int(correct)}/{len(questions)}", "Starting score", THEME["accent"]).pack(pady=20)
            for item in learning_plan(app.save_data, app.current_user, 3):
                make_card(body, item["title"], f"{item['subject']} • Recommended next", "#58D68D").pack(fill="x", padx=80, pady=6)
            make_button(body, "Open My Today Page", app.main_menu, wide=True); return
        subject, topic, prompt, choices, answer = questions[index]
        body = make_page_header(root, "Starting Check", f"Question {index + 1} of {len(questions)} • This does not affect a school mark.", app.main_menu)
        card = make_card(body, prompt, f"{subject} • {curriculum.topic_title(year, subject, topic)}", THEME["accent"], padding=24); card.pack(fill="both", expand=True, padx=100, pady=25)
        selected = tk.StringVar()
        for choice in choices:
            tk.Radiobutton(card, text=choice, value=choice, variable=selected, font=FONT_TEXT, bg=card["bg"], fg=THEME["fg"], selectcolor=THEME.get("panel_alt", card["bg"])).pack(anchor="w", pady=7)
        def submit():
            if not selected.get(): show_popup(app, "Choose an answer first."); return
            state["results"].append({"subject": subject, "topic": topic, "earned": int(selected.get() == answer), "possible": 1})
            state["index"] += 1; render()
        make_button(card, "Next", submit, wide=True)
    render()


def show_lesson(root, app, subject, topic_id):
    app.experience_store.record_lesson_view(app.current_user, subject, topic_id)
    guide = lesson_guide(app.difficulty_value, subject, topic_id)
    clear(root); body = make_page_header(root, guide["title"], f"{subject} • Year {app.difficulty_value} lesson", app.subject_menu); body = make_scrollable(body)
    unit = curriculum.topic_details(app.difficulty_value, subject, topic_id) or {}
    prerequisite_titles = []
    for prerequisite in unit.get("prerequisites", []):
        detail = curriculum.topic_details(app.difficulty_value, subject, prerequisite)
        if detail: prerequisite_titles.append(detail["title"])
    prior = "You are ready to begin. Use the starting check if you are unsure." if not prerequisite_titles else "Before this lesson, review: " + ", ".join(prerequisite_titles)
    make_card(body, "Prior knowledge", prior, "#FFB84D").pack(fill="x", padx=35, pady=7)
    for title, content, accent in (
        ("What you need to know", guide["explanation"], THEME["accent"]),
        ("A reliable method", guide["steps"], "#58D68D"),
        ("Worked example", guide["example"], "#4EA3FF"),
        ("Common mistake", guide["mistake"], "#FFB84D"),
        ("Key vocabulary", guide["vocabulary"], "#B56BFF"),
    ):
        make_card(body, title, content, accent).pack(fill="x", padx=35, pady=7)
    if unit.get("subskills"):
        make_card(body, "Success criteria", "By the end, you should be able to:\n• " + "\n• ".join(unit["subskills"]), "#58D68D").pack(fill="x", padx=35, pady=7)
    if subject == "Maths":
        import maths as maths_module, maths_diagrams
        example = maths_module.generate_question_data(app.difficulty_value, topic_id, difficulty=2, category="Applied")
        interactive = make_card(body, "Interactive example", example["prompt"], "#4EA3FF"); interactive.pack(fill="x", padx=35, pady=7)
        response = tk.StringVar()
        visual = maths_diagrams.render_diagram(interactive, example.get("diagram"), response)
        if visual: visual.pack(fill="x", pady=8)
        make_button(interactive, "Reveal Worked Answer", lambda q=example: show_popup(app, f"Answer: {q['answer']}\n\n{q['explanation']}"))
    else:
        make_card(body, "Interactive example", "Highlight one precise piece of evidence, explain the method or choice, then connect it directly to the question. Use the practice activity to test and refine the response.", "#4EA3FF").pack(fill="x", padx=35, pady=7)
    def practise():
        app.experience_store.record_lesson_view(app.current_user, subject, topic_id, completed=True)
        if subject == "Maths": maths.show_maths_screen(root, app, topic_id)
        else: english.show_english_screen(root, app, topic=topic_id)
    make_button(body, "I Understand — Start Practice", practise, wide=True)
    make_button(body, "Take Topic Assessment", lambda: curriculum_ui.show_topic_assessment(root, app, app.difficulty_value, subject, topic_id, "end"), wide=True, kind="secondary")


def show_today(root, app):
    clear(root); user = save_system.get_user(app.save_data, app.current_user) or {}; prefs = app.experience_store.preferences(app.current_user)
    body = make_page_header(root, f"Today for {app.current_user}", f"Year {app.difficulty_value} • One clear step at a time"); body = make_scrollable(body)
    diagnostic = app.experience_store.latest_diagnostic(app.current_user)
    if not diagnostic:
        card = make_card(body, "Start with a short check", "Eight questions help EduPy choose the right starting topics. It is not a test grade.", "#FFB84D"); card.pack(fill="x", pady=8); make_button(card, "Take Starting Check", lambda: show_diagnostic(root, app), wide=True)
    else:
        scores = diagnostic_summary(diagnostic)
        details = " • ".join(f"{subject} {score}%" for subject, score in scores.items())
        card = make_card(body, "Your starting check", f"{details} • Used only to personalise recommendations.", THEME["accent"]); card.pack(fill="x", pady=8)
        make_button(card, "Retake Check", lambda: show_diagnostic(root, app))
    due = [item for item in assignments.assignments_for_student(app.save_data, app.current_user) if assignments.assignment_state(item, app.current_user) in ("To do", "Overdue")]
    plan = learning_plan(app.save_data, app.current_user, 3)
    revision = app.experience_store.revision_plan(app.current_user)
    tasks = [task for task in (revision or {}).get("tasks", []) if not task["completed"]][:3]
    recent_lessons = app.experience_store.recent_lessons(app.current_user, 1)
    stats = tk.Frame(body, bg=THEME["bg"]); stats.pack(fill="x", pady=8)
    make_stat(stats, len(due), "Assignments to do", "#FF7043").pack(side="left", fill="x", expand=True, padx=4)
    make_stat(stats, len(tasks), "Revision tasks", "#4EA3FF").pack(side="left", fill="x", expand=True, padx=4)
    if not prefs.get("focus_mode"):
        make_stat(stats, user.get("tokens", 0), "Learning tokens", "#FFB84D").pack(side="left", fill="x", expand=True, padx=4)
    active_pathways = app.experience_store.active_pathways(app.current_user)
    if active_pathways:
        path = next((item for item in curriculum.pathways() if item["id"] == active_pathways[0]), None)
        units = curriculum.pathway_units(active_pathways[0]) if path else []
        next_unit = next((unit for unit in units if _mastery_for_unit(user, unit) < 75), None)
        if next_unit:
            card = make_card(body, f"Continue pathway: {path['title']}", f"Next unit: {next_unit['title']} · Year {next_unit['year']} {next_unit['subject']}", "#B56BFF"); card.pack(fill="x", pady=8)
            make_button(card, "Continue Pathway", lambda u=next_unit: curriculum_ui._open_unit(root, app, u, False))
            make_button(card, "View Full Pathway", lambda p=path: curriculum_ui.show_pathway(root, app, p["id"]))
    retention = app.experience_store.retention_due(app.current_user)
    if retention:
        item = retention[0]; unit = curriculum.topic_details(item["year"], item["subject"], item["topic"])
        if unit:
            card = make_card(body, "Ready for a retention check", f"See what you still remember from {unit['title']}.", "#FFB84D"); card.pack(fill="x", pady=8)
            make_button(card, "Start Retention Check", lambda u=unit: curriculum_ui.show_topic_assessment(root, app, u["year"], u["subject"], u["id"], "retention"))
    if recent_lessons:
        recent = recent_lessons[0]
        title = curriculum.topic_title(app.difficulty_value, recent["subject"], recent["topic"])
        card = make_card(body, f"Continue: {title}", f"{recent['subject']} • Pick up from your most recent lesson.", "#4EA3FF"); card.pack(fill="x", pady=8)
        make_button(card, "Continue Lesson", lambda r=recent: show_lesson(root, app, r["subject"], r["topic"]), wide=True)
    make_section_header(body, "Recommended next", "A small set of activities chosen from your recent progress.")
    for item in plan:
        card = make_card(body, item["title"], f"{item['subject']} • Mastery {item['mastery']}%", "#58D68D"); card.pack(fill="x", pady=5)
        make_button(card, "Learn First", lambda i=item: show_lesson(root, app, i["subject"], i["topic"]))
        make_button(card, "Practise Now", lambda i=item: maths.show_maths_screen(root, app, i["topic"]) if i["subject"] == "Maths" else english.show_english_screen(root, app, topic=i["topic"]))
    if due:
        card = make_card(body, "Assignments", f"{len(due)} item(s) need your attention.", "#FF7043"); card.pack(fill="x", pady=8); make_button(card, "Open Assignments", lambda: assignments.show_student_assignments(root, app), wide=True)
    make_section_header(body, "Explore EduPy", "Jump straight to the part of your learning day you need.")
    nav = tk.Frame(body, bg=THEME["bg"]); nav.pack(fill="x", pady=(0, 12))
    for column in range(3): nav.grid_columnconfigure(column, weight=1, uniform="today_nav")
    destinations = (
        ("Curriculum", "Search every unit and follow guided pathways.", lambda: curriculum_ui.show_curriculum_explorer(root, app), "#4EA3FF"),
        ("My Toolkit", "Mock exams, portfolio, certificates and mistake review.", lambda: platform_features.show_student_toolkit(root, app), "#5EC7C2"),
        ("Revision", "Build and follow a manageable study plan.", lambda: show_revision_planner(root, app), "#B56BFF"),
        ("Classes", "See teachers, classmates and assigned work.", lambda: __import__('classes').show_student_classes(root, app), "#58D68D"),
        ("Rewards", "Use tokens earned through real learning.", app.open_shop, "#FFB84D"),
        ("Progress", "Review mastery, activity and achievements.", app.open_progress, "#4EA3FF"),
        ("Safety & Settings", "Accessibility, privacy and support.", lambda: show_safety_centre(root, app), "#FF7AA2"),
    )
    for index, (title, description, command, accent) in enumerate(destinations):
        make_action_tile(nav, title, description, command, accent).grid(row=index // 3, column=index % 3, sticky="nsew", padx=5, pady=5)
    logout_bar = tk.Frame(body, bg=THEME["bg"]); logout_bar.pack(fill="x", pady=(2, 8))
    make_button(logout_bar, "Log out", app.logout, wide=True, kind="secondary")
    make_button(logout_bar, "Quit EduPy", app.quit_app, wide=True, kind="secondary")


def generate_revision_tasks(data, username, exam_date, count=10):
    start = datetime.date.today(); end = datetime.date.fromisoformat(exam_date)
    if end <= start: raise ValueError("Choose a future assessment date.")
    topics = learning_plan(data, username, max(count, 6)); days = (end - start).days
    tasks = []
    for index in range(count):
        item = topics[index % len(topics)]
        due = start + datetime.timedelta(days=max(1, round((index + 1) * days / (count + 1))))
        tasks.append({"subject": item["subject"], "topic": item["topic"], "due_date": due.isoformat()})
    return tasks


def show_revision_planner(root, app):
    clear(root); body = make_page_header(root, "Revision Planner", "Build a manageable plan that adapts to your weakest topics.", app.main_menu); body = make_scrollable(body)
    plan = app.experience_store.revision_plan(app.current_user)
    if not plan:
        card = make_card(body, "Create your plan", "Choose an assessment name and date. EduPy will build a manageable calendar around your weakest topics.", THEME["accent"]); card.pack(fill="x", padx=50, pady=15)
        title = tk.Entry(card, font=FONT_TEXT); title.insert(0, "Next assessment"); title.pack(fill="x", pady=5)
        exam = tk.Entry(card, font=FONT_TEXT); exam.insert(0, (datetime.date.today()+datetime.timedelta(days=28)).isoformat()); exam.pack(fill="x", pady=5)
        def create():
            try:
                days=(datetime.date.fromisoformat(exam.get())-datetime.date.today()).days
                tasks = generate_revision_tasks(app.save_data, app.current_user, exam.get(), min(18,max(6,days//3)))
            except ValueError as error: show_popup(app, str(error)); return
            app.experience_store.create_revision_plan(app.current_user, title.get(), exam.get(), tasks); show_revision_planner(root, app)
        make_button(card, "Create Revision Plan", create, wide=True); return
    summary = make_card(body, plan["title"], f"Assessment date: {plan['exam_date']} • {sum(task['completed'] for task in plan['tasks'])}/{len(plan['tasks'])} sessions complete", THEME["accent"]); summary.pack(fill="x", pady=8)
    def replace_plan():
        app.experience_store.delete_revision_plan(app.current_user)
        show_revision_planner(root, app)
    make_button(summary, "Create a New Plan", replace_plan)
    weeks={}
    for task in plan["tasks"]:
        date=datetime.date.fromisoformat(task["due_date"]);week_start=date-datetime.timedelta(days=date.weekday());weeks.setdefault(week_start,[]).append(task)
    calendar=tk.Frame(body,bg=THEME["bg"]);calendar.pack(fill="x",pady=8)
    for column in range(min(4,max(1,len(weeks)))):calendar.grid_columnconfigure(column,weight=1,uniform="revision_weeks")
    for index,(week_start,items) in enumerate(sorted(weeks.items())):
        complete=sum(item["completed"] for item in items)
        make_card(calendar,f"Week of {week_start.strftime('%d %b')}",f"{complete}/{len(items)} sessions complete","#58D68D" if complete==len(items) else "#4EA3FF").grid(row=index//4,column=index%4,sticky="nsew",padx=4,pady=4)
    today = datetime.date.today().isoformat()
    for task in plan["tasks"]:
        title = curriculum.topic_title(app.difficulty_value, task["subject"], task["topic"])
        timing = "Complete" if task["completed"] else "Due today" if task["due_date"] == today else "Overdue" if task["due_date"] < today else f"Planned for {task['due_date']}"
        colour = "#58D68D" if task["completed"] else "#FF7043" if task["due_date"] < today else "#4EA3FF"
        card = make_card(body, ("✓ " if task["completed"] else "") + title, f"{task['subject']} • {timing}", colour); card.pack(fill="x", pady=5)
        if not task["completed"]:
            make_button(card, "Study This Topic", lambda t=task: show_lesson(root, app, t["subject"], t["topic"]))
            make_button(card, "Mark Complete", lambda i=task["id"]: (app.experience_store.set_revision_task(app.current_user, i), show_revision_planner(root, app)))


def show_safety_centre(root, app):
    clear(root); user = save_system.get_user(app.save_data, app.current_user) or {}; role = user.get("role", "student")
    body = make_page_header(root, "Safety, Privacy & Accessibility", "Control your experience or report a concern.", app.main_menu)
    style_notebook(root); notebook = ttk.Notebook(body, style="Edu.TNotebook"); notebook.pack(fill="both", expand=True)
    settings_frame = tk.Frame(notebook, bg=THEME["bg"]); report_frame = tk.Frame(notebook, bg=THEME["bg"]); privacy_frame = tk.Frame(notebook, bg=THEME["bg"])
    notebook.add(settings_frame, text="Accessibility"); notebook.add(report_frame, text="Report Concern"); notebook.add(privacy_frame, text="Privacy")
    settings_tab = make_scrollable(settings_frame); report_tab = make_scrollable(report_frame); privacy_tab = make_scrollable(privacy_frame)
    prefs = app.experience_store.preferences(app.current_user)
    contrast_report = ui.theme_accessibility_report()
    make_card(settings_tab, "Keyboard & screen-reader support",
        "Use Tab and Shift+Tab to move between controls, Enter or Space to activate buttons, and the mouse wheel or arrow keys to move through long pages. "
        f"Current theme contrast: {'AA checks passed' if contrast_report['passes_aa'] else 'use High contrast for stronger readability'}.",
        "#58D68D" if contrast_report["passes_aa"] else "#FFB84D").pack(fill="x", padx=24, pady=8)
    reduced = tk.BooleanVar(value=prefs["reduced_motion"]); contrast = tk.BooleanVar(value=prefs["high_contrast"]); focus = tk.BooleanVar(value=prefs["focus_mode"])
    dyslexia = tk.BooleanVar(value=prefs.get("dyslexia_friendly",False)); ruler = tk.BooleanVar(value=prefs.get("reading_ruler",False)); spacing = tk.BooleanVar(value=prefs.get("generous_spacing",False)); calm = tk.BooleanVar(value=prefs.get("calm_palette",False))
    font_scale = tk.StringVar(value=str(prefs["font_scale"])); extra = tk.StringVar(value=str(prefs["extra_time_percent"]))
    for text, variable in (("Reduce animations", reduced), ("High contrast", contrast), ("Focus mode (hide reward totals on Today)", focus)):
        tk.Checkbutton(settings_tab, text=text, variable=variable, font=FONT_TEXT, bg=THEME["bg"], fg=THEME["fg"], selectcolor=THEME.get("panel_alt", THEME["bg"])).pack(anchor="w", padx=30, pady=6)
    make_label(settings_tab, "Reading profile", FONT_SUBTITLE).pack(anchor="w", padx=30, pady=(14,4))
    for text, variable in (("Dyslexia-friendly typeface",dyslexia),("Mouse-following reading ruler",ruler),("More generous spacing",spacing),("Calm colour overlay",calm)):
        tk.Checkbutton(settings_tab,text=text,variable=variable,font=FONT_TEXT,bg=THEME["bg"],fg=THEME["fg"],selectcolor=THEME.get("panel_alt",THEME["bg"])).pack(anchor="w",padx=30,pady=6)
    make_label(settings_tab, "Text size", FONT_TEXT).pack(anchor="w", padx=30); ttk.Combobox(settings_tab, values=["90","100","110","120","130","140"], textvariable=font_scale, state="readonly").pack(anchor="w", padx=30)
    make_label(settings_tab, "Recorded additional working time (%)", FONT_TEXT).pack(anchor="w", padx=30); ttk.Combobox(settings_tab, values=["0","10","25","50","100"], textvariable=extra, state="readonly").pack(anchor="w", padx=30)
    make_label(settings_tab, "EduPy records this support preference for future timed activities. Current practice is untimed.", FONT_TEXT).pack(anchor="w", padx=30, pady=(2, 10))
    def save_prefs():
        app.experience_store.update_preferences(app.current_user, reduced_motion=reduced.get(), high_contrast=contrast.get(), focus_mode=focus.get(), font_scale=font_scale.get(), extra_time_percent=extra.get())
        app.experience_store.update_accessibility_profile(app.current_user,dyslexia_friendly=dyslexia.get(),reading_ruler=ruler.get(),generous_spacing=spacing.get(),calm_palette=calm.get())
        set_theme(user.get("current_theme", "Default")); ui.apply_accessibility(root, app.experience_store.preferences(app.current_user)); root.configure(bg=THEME["bg"])
        show_safety_centre(root, app); show_popup(app, "Accessibility settings saved and applied.")
    make_button(settings_tab, "Save Accessibility Settings", save_prefs, wide=True)
    make_label(report_tab, "Tell a trusted adult immediately if anyone is in danger.", FONT_SUBTITLE).pack(pady=12)
    category = tk.StringVar(value="Content concern"); ttk.Combobox(report_tab, values=["Content concern","Account concern","Bullying or behaviour","Technical safety","Other"], textvariable=category, state="readonly").pack(pady=5)
    description = tk.Text(report_tab, height=8, font=FONT_TEXT); description.pack(fill="x", padx=35, pady=8)
    def report():
        if app.experience_store.submit_safety_report(app.current_user, category.get(), description.get("1.0","end")): description.delete("1.0","end"); show_safety_centre(root, app); show_popup(app,"Your concern has been recorded for an administrator.")
        else: show_popup(app,"Please explain the concern in at least ten characters.")
    make_button(report_tab, "Submit Concern", report, wide=True)
    concerns = app.experience_store.my_safety_reports(app.current_user, 5)
    if concerns:
        make_label(report_tab, "My recent reports", FONT_SUBTITLE).pack(anchor="w", padx=25, pady=(14, 4))
        for item in concerns:
            colour = "#58D68D" if item["status"] == "resolved" else "#FFB84D"
            make_card(report_tab, item["category"], f"{item['created_at'][:10]} • {item['status'].title()}", colour).pack(fill="x", padx=25, pady=4)
    make_card(privacy_tab, "What EduPy stores", "Account role, classes, assignments, submitted work, marks, progress, rewards, preferences, and safety records. EduPy does not need home addresses, phone numbers, location, or payment details.", THEME["accent"]).pack(fill="x", padx=25, pady=12)
    for label, request_type in (("Request a copy of my data","export"),("Request a correction","correction"),("Request account deletion review","deletion")):
        def request(r=request_type):
            created = app.experience_store.create_privacy_request(app.current_user, r)
            if created: show_safety_centre(root, app)
            show_popup(app, "Request recorded." if created else "That request is already open.")
        make_button(privacy_tab, label, request, wide=True)
    requests = app.experience_store.my_privacy_requests(app.current_user, 5)
    if requests:
        make_label(privacy_tab, "My recent requests", FONT_SUBTITLE).pack(anchor="w", padx=25, pady=(14, 4))
        for item in requests:
            colour = "#58D68D" if item["status"] == "resolved" else "#4EA3FF"
            make_card(privacy_tab, item["request_type"].replace("_", " ").title(), f"{item['created_at'][:10]} • {item['status'].title()}", colour).pack(fill="x", padx=25, pady=4)
    if role == "admin":
        admin_frame = tk.Frame(notebook, bg=THEME["bg"]); notebook.add(admin_frame, text="Admin Reports"); admin_tab = make_scrollable(admin_frame)
        reports = app.experience_store.safety_reports(app.current_user)
        for item in reports:
            card = make_card(admin_tab, item["category"], f"Reported by {item['reporter']} • {item['created_at'][:16]}\n{item['description']}", "#FF7043"); card.pack(fill="x", padx=20, pady=6)
            make_button(card, "Mark Resolved", lambda i=item["id"]: (app.experience_store.resolve_safety_report(app.current_user, i), show_safety_centre(root, app)))
        requests = app.experience_store.privacy_requests(app.current_user)
        for item in requests:
            card = make_card(admin_tab, "Privacy request", f"{item['username']} • {item['request_type'].title()} • {item['created_at'][:16]}", "#4EA3FF"); card.pack(fill="x", padx=20, pady=6)
            make_button(card, "Mark Reviewed", lambda i=item["id"]: (app.experience_store.resolve_privacy_request(app.current_user, i), show_safety_centre(root, app)))
