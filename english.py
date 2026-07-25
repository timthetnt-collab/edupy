"""Year 7-11 English reading and writing aligned to KS3 and GCSE skills."""

import random
import re
import copy
import tkinter as tk

import audio
import curriculum
import progress
from english_bank import ADDITIONAL_TEXTS
from settings import THEME, FONT_SUBTITLE, FONT_TEXT
from ui import clear, make_action_tile, make_button, make_card, make_label, make_page_header, make_progress_bar, make_scrollable, make_section_header, make_stat


TEXTS = [
    {
        "year": 7, "topic": "inference", "title": "The Last Bus", "source": "Original fiction",
        "text": "Sam reached the stop just as the bus sighed away from the kerb. Its red lights shrank into the rain. He checked the blank timetable, then the dark road, and pulled his thin jacket tighter. Across the street, the bakery owner turned her sign to CLOSED but paused when she noticed him standing alone.",
        "questions": [
            {"type":"multiple_choice","topic":"retrieval","prompt":"Why does Sam pull his jacket tighter?","choices":["He is cold","He is hiding","He is excited","He is running"],"answer":"He is cold","max_score":1,"explanation":"The rain and thin jacket are explicit clues."},
            {"type":"short","topic":"inference","prompt":"What impression do you get of Sam's situation? Use one detail.","keywords":["alone","missed","bus","rain","dark","worried","cold"],"max_score":3,"explanation":"A strong inference combines an idea with evidence."},
            {"type":"short","topic":"language","prompt":"What does the verb “sighed” suggest about the bus as it leaves?","keywords":["tired","slow","reluctant","personification","sound"],"max_score":3,"explanation":"The personification gives the bus a tired, human quality."},
        ],
    },
    {
        "year": 8, "topic": "viewpoint", "title": "A Park Worth Protecting", "source": "Original speech",
        "text": "Some call the old park an empty patch of grass. They are wrong. It is our outdoor classroom, our football pitch and our quiet place after a difficult day. If we replace every tree with concrete, where will younger children explore? Where will birds nest? We do not need another car park; we need the courage to protect what cannot be replaced.",
        "questions": [
            {"type":"multiple_choice","topic":"viewpoint","prompt":"What is the writer's main viewpoint?","choices":["The park should be protected","Cars should be banned","The park is unsafe","Children dislike nature"],"answer":"The park should be protected","max_score":1,"explanation":"The argument repeatedly presents the park as valuable."},
            {"type":"short","topic":"language","prompt":"Identify one rhetorical method and explain its effect.","keywords":["question","rule of three","our","emotive","concrete","courage","persuade","reader"],"max_score":4,"explanation":"Name the method, quote it, then explain how it persuades."},
            {"type":"extended","topic":"structure","prompt":"How does the speech develop from beginning to end?","keywords":["dismisses","reframes","examples","questions","conclusion","call to action","protect"],"max_score":5,"explanation":"Track the sequence of ideas, not just individual words."},
        ],
    },
    {
        "year": 9, "topic": "comparison", "title": "Two Journeys", "source": "Original paired extracts",
        "text": "TEXT A — The train burst from the tunnel and the coast opened before us, bright and limitless. Passengers leaned towards the glass as if the sea had called their names.\n\nTEXT B — Our coach crawled through streets narrowed by traffic. Rain blurred the windows, and each red light seemed to hold us prisoner for another age. I watched the city repeat itself: shop, crossing, tower, stop.",
        "questions": [
            {"type":"short","topic":"analysis","prompt":"What is the main difference between the two journeys?","keywords":["freedom","exciting","bright","slow","trapped","boring","contrast"],"max_score":3,"explanation":"Establish a clear comparative idea first."},
            {"type":"extended","topic":"language","prompt":"Compare how language presents the travellers' experiences.","keywords":["burst","limitless","called","crawled","prisoner","repeat","metaphor","contrast","whereas"],"max_score":6,"explanation":"Compare methods and effects in both texts using evidence."},
            {"type":"writing","topic":"transactional","prompt":"Write the opening of a travel article describing a memorable journey.","max_score":6,"criteria":["clear viewpoint","varied vocabulary","sentence variety","accurate punctuation","paragraphing"],"explanation":"Shape the description for a reader rather than listing events."},
        ],
    },
    {
        "year": 10, "topic": "ao2", "title": "The House on Bell Street", "source": "Original 19th-century-style fiction",
        "text": "At the end of Bell Street stood a house which appeared to have withdrawn from its neighbours. While their windows shone warmly, its own stared black upon the road. Ivy had conquered the gate, twisting through the ironwork in thick ropes, and no footprint disturbed the pale dust of the path. Yet, as Clara passed, a curtain on the upper floor trembled—once, and then was still.",
        "questions": [
            {"type":"short","topic":"ao1","prompt":"List four details about the house.","keywords":["end","withdrawn","black","ivy","gate","dust","curtain","still"],"max_score":4,"explanation":"AO1 rewards precise information selected from the text."},
            {"type":"extended","topic":"ao2","prompt":"How does the writer use language to make the house seem threatening?","keywords":["withdrawn","stared","black","conquered","ropes","trembled","personification","verb","suggests","reader"],"max_score":8,"explanation":"Analyse specific choices, their connotations, and effects."},
            {"type":"extended","topic":"ao4","prompt":"A student said, “The ending makes the reader certain someone is inside.” Evaluate this view.","keywords":["agree","however","curtain","trembled","uncertain","suggests","evidence","reader"],"max_score":6,"explanation":"Give a clear judgement, use evidence, and consider an alternative."},
        ],
    },
    {
        "year": 11, "topic": "ao3", "title": "Facing the Mountain", "source": "Original paired non-fiction",
        "text": "TEXT A — I had imagined the summit as a prize waiting to be collected. By noon, the mountain had corrected me. Every step demanded attention, and the wind erased our voices before they reached one another. I felt wonderfully small.\n\nTEXT B — Why climb at all? From the valley, the peak offers everything a sensible traveller needs: beauty, distance and the comforting certainty of solid ground. Those who march upwards may call it courage. I call it an unnecessarily exhausting route to the same view.",
        "questions": [
            {"type":"extended","topic":"ao3","prompt":"Compare the writers' attitudes towards climbing the mountain.","keywords":["respect","humble","wonder","pointless","sensible","exhausting","whereas","both","attitude","method"],"max_score":8,"explanation":"Compare both attitudes and how each writer conveys them."},
            {"type":"extended","topic":"ao2","prompt":"How does Text A use language and structure to show a change in perspective?","keywords":["imagined","prize","corrected","demanded","erased","small","change","contrast","short","reader"],"max_score":8,"explanation":"Link the opening expectation to the later realisation."},
            {"type":"writing","topic":"transactional","prompt":"Write an article arguing whether difficult challenges are worth attempting.","max_score":10,"criteria":["convincing viewpoint","rhetorical methods","paragraphing","sentence variety","ambitious vocabulary","accurate punctuation"],"explanation":"Plan a clear argument, shape it for an audience, and finish decisively."},
        ],
    },
]

TEXTS.extend(ADDITIONAL_TEXTS)


EXTRA_QUESTIONS = {
    (7,"narrative"): {"type":"writing","topic":"narrative","prompt":"Continue Sam's story. Make the bakery owner's decision create a clear turning point.","max_score":6,"criteria":["clear sequence","description","sentence variety","paragraphing"],"explanation":"A turning point should change the direction or mood of the story."},
    (7,"grammar"): {"type":"multiple_choice","topic":"grammar","prompt":"Which sentence uses a semicolon correctly?","choices":["The bus left; Sam was stranded.","The bus; left Sam was stranded.","The bus left Sam; was stranded.","The; bus left, Sam was stranded."],"answer":"The bus left; Sam was stranded.","max_score":1,"explanation":"A semicolon can join two closely related independent clauses."},
    (8,"comparison"): {"type":"extended","topic":"comparison","prompt":"Compare the dismissive viewpoint in the opening with the determined viewpoint at the end.","keywords":["empty","wrong","courage","protect","change","contrast","whereas"],"max_score":5,"explanation":"Compare both viewpoints and support each with evidence."},
    (8,"inference"): {"type":"short","topic":"inference","prompt":"What can you infer about the writer's relationship with the park?","keywords":["values","personal","community","classroom","quiet","protect","evidence"],"max_score":4,"explanation":"Infer a relationship and support it with a precise detail."},
    (9,"comparison"): {"type":"extended","topic":"comparison","prompt":"Compare how the writers present the two journeys.","keywords":["freedom","bright","trapped","slow","whereas","both","language","contrast"],"max_score":6,"explanation":"Build the response around similarities or differences and analyse both texts."},
    (9,"structure"): {"type":"extended","topic":"structure","prompt":"How does the order of the two extracts sharpen the contrast between the journeys?","keywords":["first","then","freedom","trapped","contrast","shift","reader"],"max_score":5,"explanation":"Explain why the writer places the positive journey before the negative one."},
    (10,"creative"): {"type":"writing","topic":"creative","prompt":"Write the opening of a story in which a character notices something unexpected in a familiar place.","max_score":10,"criteria":["engaging opening","structure","imagery","sentence variety","accuracy"],"explanation":"Control the reveal and use detail selectively."},
    (10,"accuracy"): {"type":"multiple_choice","topic":"accuracy","prompt":"Which sentence is punctuated correctly?","choices":["Clara hesitated; the curtain moved again.","Clara hesitated the curtain; moved again.","Clara, hesitated; the curtain moved again", "Clara hesitated; Because the curtain moved."],"answer":"Clara hesitated; the curtain moved again.","max_score":1,"explanation":"The semicolon correctly joins two complete, related clauses."},
    (11,"ao4"): {"type":"extended","topic":"ao4","prompt":"“Text B is more convincing because its humour makes the viewpoint memorable.” Evaluate this statement.","keywords":["agree","humour","sensible","exhausting","however","evidence","convincing","reader"],"max_score":8,"explanation":"Make a judgement, evaluate methods, and consider an alternative."},
    (11,"revision"): {"type":"multiple_choice","topic":"revision","prompt":"What is the strongest first step for a comparison response?","choices":["State a clear connection or difference","List every technique","Copy both openings","Write about only one text"],"answer":"State a clear connection or difference","max_score":1,"explanation":"A comparison needs a clear comparative idea that both texts can support."},
}


def _representative_question(year, family):
    if (year, family) in EXTRA_QUESTIONS:
        return EXTRA_QUESTIONS[(year, family)]
    for text in TEXTS:
        if text.get("year") != year:
            continue
        for question in text.get("questions", []):
            if question.get("topic") == family:
                return question
    return {"type":"extended", "topic":family, "prompt":f"Complete a focused {family} response using clear evidence and explanation.", "keywords":[family,"evidence","explain"], "max_score":5, "explanation":"Answer the precise focus, support the idea and develop the explanation."}


# Every application and reasoning unit receives a focused question while
# retaining the age-appropriate source material and marking style of its family.
for _year in range(7, 12):
    for _topic, _ in curriculum.topics_for(_year, "English"):
        if (_year, _topic) in EXTRA_QUESTIONS:
            continue
        _unit = curriculum.topic_details(_year, "English", _topic) or {}
        _family = _unit.get("family", _topic)
        _question = copy.deepcopy(_representative_question(_year, _family))
        _question["topic"] = _topic
        _question["category"] = _unit.get("primary_category", "Fluency")
        _question["difficulty"] = {"foundation":1,"application":2,"reasoning":3}.get(_unit.get("stage"),2)
        EXTRA_QUESTIONS[(_year, _topic)] = _question


def texts_for_year(year, topic=None):
    pool = [item for item in TEXTS if item["year"] == min(11, max(7, int(year)))]
    if topic:
        matched = [item for item in pool if item.get("topic") == topic or any(q.get("topic") == topic for q in item["questions"])]
        if matched: return matched
    return pool


def _words(answer):
    return re.findall(r"[a-zA-Z’'-]+", answer.lower())


def _contains_term(answer, term):
    return bool(re.search(rf"(?<!\w){re.escape(term.lower())}(?!\w)", answer.lower()))


def mark_response(question, answer, year=7):
    answer = answer.strip(); max_score = int(question.get("max_score", 1))
    if not answer: return 0, max_score, "Write an answer before submitting."
    if question.get("type") == "multiple_choice":
        correct = answer.lower() == str(question.get("answer", "")).lower()
        return (max_score if correct else 0), max_score, (question["explanation"] if correct else f"The best answer is: {question['answer']}.")
    words = _words(answer)
    if question.get("type") == "writing":
        target = {7:45, 8:60, 9:80, 10:110, 11:140}.get(year, 80)
        labels = ["enough developed content", "several complete sentences", "clear paragraphing", "varied vocabulary", "purposeful punctuation"]
        features = [len(words) >= target, len(re.findall(r"[.!?]", answer)) >= 3, "\n" in answer.strip(),
                    len(set(words)) >= min(55, max(20, target//2)), bool(re.search(r"[;:—-]", answer))]
        score = round(sum(features) / len(features) * max_score)
        strengths = [label for label, met in zip(labels, features) if met]
        next_steps = [label for label, met in zip(labels, features) if not met]
        feedback = "Automated writing check. "
        feedback += ("Strengths: " + ", ".join(strengths[:2]) + ". ") if strengths else "Build the response further. "
        feedback += ("Next: " + ", ".join(next_steps[:2]) + ".") if next_steps else "Now proofread for precise meaning and accuracy."
        return score, max_score, feedback
    keywords = [word.lower() for word in question.get("keywords", [])]
    hits = sum(1 for keyword in keywords if _contains_term(answer, keyword))
    coverage = min(1.0, hits / max(1, min(len(keywords), 4)))
    evidence_bonus = 0.2 if ('"' in answer or "“" in answer or "‘" in answer) else (0.1 if hits else 0)
    development = min(0.25, len(words) / ({"short":80, "extended":140}.get(question.get("type"), 80)))
    score = min(max_score, round((coverage * 0.6 + evidence_bonus + development) * max_score))
    if score >= max_score * 0.75: feedback = "Strong response: you used relevant ideas and developed the explanation."
    elif score >= max_score * 0.4: feedback = "A sound start. Add a precise quotation and explain its effect in more detail."
    else: feedback = "Return to the text, choose precise evidence, and connect it directly to the question."
    return score, max_score, feedback


def mark_answer(user_answer, keywords, weight):
    """Compatibility wrapper for older content packs."""
    hits = sum(1 for keyword in keywords if _contains_term(user_answer, keyword))
    return hits, hits * weight


def highlight_keywords(text_widget, text, keywords=None):
    # Student-facing passages no longer reveal mark-scheme keywords.
    text_widget.config(state="normal"); text_widget.delete("1.0", tk.END); text_widget.insert("1.0", text); text_widget.config(state="disabled")


def _normalise_pack(pack, year):
    item = dict(pack); item.setdefault("title", "Teacher text"); item.setdefault("text", "")
    normalised = []
    for question in item.get("questions", []):
        if isinstance(question, str):
            normalised.append({"type":"extended", "topic":"analysis", "prompt":question, "keywords":[], "max_score":5, "explanation":"Use evidence and explain your ideas."})
        else:
            q = dict(question); q.setdefault("type", "extended"); q.setdefault("topic", "analysis"); q.setdefault("max_score", max(1, round(q.get("weight", 1)*3))); q.setdefault("explanation", "Use evidence and explain your ideas."); normalised.append(q)
    item["questions"] = normalised; item.setdefault("year", year); item.setdefault("source", "Teacher-created text")
    return item


def show_english_screen(root, app, pack=None, topic=None):
    if not app.check_time(): return
    if pack is None and topic is None: return show_english_topics(root, app)
    year = getattr(app, "difficulty_value", 7)
    family = curriculum.question_family(year, "English", topic) if topic else topic
    app.current_text = _normalise_pack(pack, year) if pack else copy.deepcopy(random.choice(texts_for_year(year, family)))
    if pack is None and topic and not any(question.get("topic") == topic for question in app.current_text["questions"]):
        app.current_text["questions"] = [EXTRA_QUESTIONS[(year, topic)]]
    categories = ["Fluency", "Applied", "Reasoning", "Exam-style"]
    user = app.save_data.get("users", {}).get(app.current_user, {})
    for index, question in enumerate(app.current_text["questions"]):
        question_topic = question.get("topic", topic or family)
        mastery = curriculum.mastery_percent(user, "English", question_topic)
        starting = 1 if mastery < 35 else 2 if mastery < 70 else 3
        adaptive = app.experience_store.adaptive_state(app.current_user, "English", question_topic, starting)
        question["difficulty"] = adaptive["difficulty"]
        question["category"] = question.get("category") or categories[min(3, index)]
    app.current_question_index = 0; app.english_total_score = 0; app.english_possible = 0; app.english_xp_earned = 0
    show_english_activity(root, app)


def show_english_topics(root, app):
    clear(root); year = getattr(app, "difficulty_value", 7)
    body = make_page_header(root, "English Curriculum", f"Choose a Year {year} skill or follow your recommendation.", app.subject_menu)
    body = make_scrollable(body)
    recommendation = curriculum.recommend_next(app.save_data, app.current_user, "English")
    if recommendation:
        card = make_card(body, f"Recommended: {recommendation['title']}", recommendation["reason"], "#58D68D"); card.pack(fill="x", pady=(0,10)); make_button(card, "Practise Next", lambda t=recommendation["topic"]: show_english_screen(root, app, topic=t))
    user = app.save_data["users"][app.current_user]
    chapters = curriculum.chapters_for(year, "English")
    if chapters:
        make_section_header(body, f"Year {year} English chapters", "Open a chapter for core knowledge, application and reasoning units.")
        grid = tk.Frame(body, bg=THEME["bg"]); grid.pack(fill="both", expand=True)
        for column in range(2): grid.grid_columnconfigure(column, weight=1, uniform="english_chapters")
        for index, chapter in enumerate(chapters):
            attempted = sum(bool(user.get("mastery", {}).get("English", {}).get(unit["id"], {}).get("attempts")) for unit in chapter["units"])
            make_action_tile(grid, chapter["title"], f"{len(chapter['units'])} units · {attempted} started", lambda c=chapter["id"]: show_english_chapter(root, app, c), "#B56BFF").grid(row=index // 2, column=index % 2, sticky="nsew", padx=5, pady=5)
        return
    make_section_header(body, "All English skills", "Read the guide, then build confidence through focused questions.")
    grid = tk.Frame(body, bg=THEME["bg"]); grid.pack(fill="both", expand=True)
    for column in range(2): grid.grid_columnconfigure(column, weight=1, uniform="english_topics")
    for index, (topic_id, title) in enumerate(curriculum.topics_for(year, "English")):
        mastery = curriculum.mastery_percent(user, "English", topic_id)
        card = make_card(grid, title, f"Mastery · {mastery}%", "#B56BFF"); card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=5, pady=5)
        make_progress_bar(card, mastery, "#B56BFF").pack(fill="x", pady=(10, 1))
        make_button(card, "Learn", lambda t=topic_id: __import__('learning_experience').show_lesson(root, app, "English", t))
        make_button(card, "Practise", lambda t=topic_id: show_english_screen(root, app, topic=t))


def show_english_chapter(root, app, chapter_id):
    year=getattr(app,"difficulty_value",7);chapter=next((item for item in curriculum.chapters_for(year,"English") if item["id"]==chapter_id),None)
    if not chapter:show_english_topics(root,app);return
    clear(root);body=make_page_header(root,chapter["title"],f"Year {year} English · {len(chapter['units'])} focused units",lambda:show_english_topics(root,app));body=make_scrollable(body);user=app.save_data["users"][app.current_user]
    make_section_header(body,"Choose a unit","Build the core skill, apply it to a text, then develop independent reasoning.")
    for unit in chapter["units"]:
        mastery=curriculum.mastery_percent(user,"English",unit["id"]);card=make_card(body,unit["title"],f"{', '.join(unit['subskills'])}\nMastery · {mastery}%","#B56BFF");card.pack(fill="x",pady=5);make_progress_bar(card,mastery,"#B56BFF").pack(fill="x",pady=(9,1));make_button(card,"Learn",lambda t=unit["id"]:__import__('learning_experience').show_lesson(root,app,"English",t));make_button(card,"Practise",lambda t=unit["id"]:show_english_screen(root,app,topic=t));make_button(card,"Assess",lambda t=unit["id"]:__import__('curriculum_ui').start_relevant_assessment(root,app,year,"English",t))


def show_english_activity(root, app):
    clear(root); item = app.current_text
    current = item["questions"][min(app.current_question_index, len(item["questions"])-1)]
    body = make_page_header(root, item["title"], f"{item.get('source', '')} • Question {app.current_question_index+1} of {len(item['questions'])} · {current.get('category','Practice')} · Adaptive level {current.get('difficulty',1)}", lambda: show_english_topics(root, app))
    body = make_scrollable(body)
    passage = tk.Text(body, wrap="word", height=10, font=FONT_TEXT, bg=THEME.get("panel", THEME["bg"]), fg=THEME["fg"], padx=15, pady=12, insertbackground=THEME["fg"])
    passage.pack(fill="x", padx=30, pady=(0,10)); highlight_keywords(passage, item["text"])
    ask_question(root, app, body)


def ask_question(root, app, parent=None):
    if app.current_question_index >= len(app.current_text["questions"]): return show_english_summary(root, app)
    parent = parent or root; question = app.current_text["questions"][app.current_question_index]
    card = make_card(parent, question["prompt"], accent="#B56BFF", padding=16); card.pack(fill="both", expand=True, padx=30, pady=5)
    response = tk.StringVar()
    if question.get("type") == "multiple_choice":
        for choice in question.get("choices", []):
            tk.Radiobutton(card, text=choice, variable=response, value=choice, font=FONT_TEXT, bg=card["bg"], fg=THEME["fg"], selectcolor=THEME.get("panel_alt", THEME["button_bg"])).pack(anchor="w", pady=3)
        get_answer = response.get
    else:
        height = 7 if question.get("type") in ("extended", "writing") else 3
        answer = tk.Text(card, height=height, font=FONT_TEXT, wrap="word", bg=THEME.get("panel_alt", THEME["bg"]), fg=THEME["fg"], insertbackground=THEME["fg"]); answer.pack(fill="both", expand=True, pady=8); answer.focus()
        get_answer = lambda: answer.get("1.0", "end")
        word_count = make_label(card, "0 words", FONT_TEXT); word_count.pack(anchor="e", pady=(0, 4))
        def update_word_count(event=None):
            del event
            count = len(_words(get_answer())); word_count.config(text=f"{count} word{'s' if count != 1 else ''}")
        answer.bind("<KeyRelease>", update_word_count)
    feedback = make_label(card, "", FONT_TEXT); feedback.pack()
    controls = tk.Frame(card, bg=card["bg"]); controls.pack(fill="x")
    def submit():
        score, possible, comment = mark_response(question, get_answer(), getattr(app, "difficulty_value", 7))
        if not get_answer().strip(): feedback.config(text=comment, fg="#FF8A80"); return
        app.english_total_score += score; app.english_possible += possible; earned = score * 4; app.english_xp_earned += earned
        if earned: progress.add_xp(app, earned)
        else: progress.record_answer(app)
        curriculum.record_mastery(app.save_data, app.current_user, "English", question.get("topic", "analysis"), score, possible)
        app.experience_store.record_adaptive_result(app.current_user, "English", question.get("topic", "analysis"), score >= possible/2, question.get("difficulty", 1))
        audio.play_correct() if score >= possible/2 else audio.play_incorrect(); feedback.config(text=f"{score}/{possible}. {comment} {question.get('explanation','')}", fg="#58D68D" if score >= possible/2 else "#FFB84D")
        app.current_question_index += 1
        for child in controls.winfo_children(): child.destroy()
        make_button(controls, "View Summary" if app.current_question_index >= len(app.current_text["questions"]) else "Next Question", lambda: show_english_summary(root, app) if app.current_question_index >= len(app.current_text["questions"]) else show_english_activity(root, app), wide=True)
    make_button(controls, "Submit Response", submit, wide=True)


def show_english_summary(root, app):
    clear(root); progress.english_completed(app); percentage = round(app.english_total_score / app.english_possible * 100) if app.english_possible else 0
    body = make_page_header(root, "English Summary", app.current_text["title"], app.subject_menu)
    body = make_scrollable(body)
    stats = tk.Frame(body, bg=THEME["bg"]); stats.pack(fill="x", pady=20)
    make_stat(stats, f"{app.english_total_score}/{app.english_possible}", "Marks", "#B56BFF").pack(side="left", fill="x", expand=True, padx=6)
    make_stat(stats, f"{percentage}%", "Performance", THEME["accent"]).pack(side="left", fill="x", expand=True, padx=6)
    make_stat(stats, app.english_xp_earned, "XP earned", "#FFB84D").pack(side="left", fill="x", expand=True, padx=6)
    recommendation = curriculum.recommend_next(app.save_data, app.current_user, "English")
    if recommendation:
        next_card = make_card(body, "Up next", f"{recommendation['title']} — {recommendation['reason']}", THEME["accent"]); next_card.pack(fill="x", pady=12)
        make_button(next_card, "Open Next Lesson", lambda r=recommendation: __import__('learning_experience').show_lesson(root, app, "English", r["topic"]))
    make_button(body, "Choose Another Skill", lambda: show_english_topics(root, app), wide=True)
