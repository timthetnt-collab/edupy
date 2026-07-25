"""Year 7-11 Maths practice with curriculum topics and varied question types."""

import math
import random
import re
import tkinter as tk
from fractions import Fraction

import audio
import curriculum
import progress
import maths_diagrams
import year8_maths
from settings import THEME, FONT_SUBTITLE, FONT_TEXT
from ui import clear, make_action_tile, make_button, make_card, make_label, make_page_header, make_progress_bar, make_scrollable, make_section_header, make_stat


def _q(prompt, answer, topic, explanation, kind="numeric", choices=None, accepted=None):
    return {"prompt": prompt, "answer": answer, "topic": topic, "explanation": explanation,
            "type": kind, "choices": choices or [], "accepted": accepted or []}


def _year7(topic):
    if topic == "number":
        a, b = random.randint(-25, 15), random.randint(-20, 20)
        return _q(f"Work out {a} + ({b}).", a + b, topic, "When adding a negative, move left on the number line.")
    if topic == "fractions":
        if random.choice([True, False]):
            denominator = random.choice([4, 5, 8, 10]); a, b = random.randint(1, denominator - 1), random.randint(1, denominator - 1)
            answer = Fraction(a + b, denominator)
            return _q(f"Give {a}/{denominator} + {b}/{denominator} in its simplest form.", str(answer), topic, "Add the numerators, keep the denominator, then simplify.", "text")
        percent = random.choice([10, 20, 25, 50]); value = random.choice([40, 60, 80, 120, 200])
        return _q(f"Find {percent}% of {value}.", percent * value / 100, topic, "Convert the percentage to a fraction or decimal, then multiply.")
    if topic == "algebra":
        x = random.randint(2, 12); a = random.randint(2, 6); b = random.randint(1, 12)
        return _q(f"Solve {a}x + {b} = {a*x+b}.", x, topic, f"Subtract {b}, then divide by {a}.")
    if topic == "ratio":
        left, right = random.choice([(2, 3), (3, 5), (4, 7)]); unit = random.randint(2, 8); total = (left + right) * unit
        return _q(f"Share {total} in the ratio {left}:{right}. Give the smaller share.", min(left, right) * unit, topic, "Add the ratio parts, find one part, then multiply.")
    if topic == "geometry":
        angle = random.randint(35, 145)
        return _q(f"Angles on a straight line total 180°. One angle is {angle}°. Find the other.", 180-angle, topic, "Angles on a straight line add to 180°.")
    values = [random.randint(3, 15) for _ in range(5)]
    return _q(f"Find the mean of: {', '.join(map(str, values))}.", sum(values)/len(values), "statistics", "Add all values and divide by how many there are.")


def _year8(topic):
    if topic == "number":
        base, power = random.randint(2, 5), random.randint(2, 4)
        return _q(f"Work out {base}^{power}.", base**power, topic, "A power tells you how many times to multiply the base by itself.")
    if topic == "algebra":
        difference = random.randint(2, 8); start = random.randint(1, 10); position = random.randint(8, 15)
        return _q(f"The sequence starts {start}, {start+difference}, {start+2*difference}, ... Find term {position}.", start+(position-1)*difference, topic, "Use first term + (position − 1) × common difference.")
    if topic == "proportion":
        cost, count, wanted = random.randint(2, 6), random.randint(2, 5), random.randint(6, 12)
        return _q(f"{count} notebooks cost £{count*cost}. At the same rate, what do {wanted} cost? Enter the number of pounds.", wanted*cost, topic, "Find the cost of one, then scale up.")
    if topic == "geometry":
        return _q("Which transformation turns a shape around a fixed point?", "rotation", topic, "A rotation turns every point through the same angle around a centre.", "multiple_choice", ["Reflection", "Rotation", "Translation", "Enlargement"])
    if topic == "probability":
        red, total = random.randint(1, 5), random.randint(6, 12)
        return _q(f"A bag has {red} red counters out of {total}. Give P(red) as a simplified fraction.", str(Fraction(red, total)), topic, "Probability = favourable outcomes ÷ total outcomes.", "text")
    values = [random.randint(5, 20) for _ in range(6)]
    return _q(f"Find the range of: {', '.join(map(str, values))}.", max(values)-min(values), "statistics", "Range = largest value − smallest value.")


def _year9(topic):
    if topic == "algebra":
        a, b = random.randint(2, 7), random.randint(1, 9)
        return _q(f"Expand {a}(x + {b}).", f"{a}x+{a*b}", topic, "Multiply every term inside the bracket.", "text", accepted=[f"{a*b}+{a}x"])
    if topic == "number":
        value = random.randint(1001, 9999)
        return _q(f"Round {value} to 2 significant figures.", round(value, -2), topic, "Keep the first two significant digits and use the next digit to round.")
    if topic == "geometry":
        a, b = random.choice([(3,4), (5,12), (8,15), (7,24)])
        return _q(f"A right-angled triangle has shorter sides {a} cm and {b} cm. Find the hypotenuse.", math.hypot(a,b), topic, "Use a² + b² = c².")
    if topic == "proportion":
        speed, hours = random.randint(35, 70), random.randint(2, 5)
        return _q(f"A car travels at {speed} mph for {hours} hours. How far does it travel?", speed*hours, topic, "Distance = speed × time.")
    if topic == "probability":
        p = random.choice([0.2, 0.35, 0.6, 0.75])
        return _q(f"If P(win) = {p}, what is P(not win)?", 1-p, topic, "Probabilities of complementary outcomes total 1.")
    return _q("A scatter graph slopes down from left to right. What type of correlation is shown?", "negative", "statistics", "As one variable rises, the other tends to fall: negative correlation.", "multiple_choice", ["Positive", "Negative", "No correlation"])


def _year10(topic):
    if topic == "number":
        coefficient, power = random.randint(12, 89)/10, random.randint(3, 6)
        return _q(f"Write {coefficient} × 10^{power} as an ordinary number.", coefficient*(10**power), topic, "Move the decimal point right for a positive power.")
    if topic == "algebra":
        r1 = random.randint(1, 6); r2 = random.choice([value for value in range(1, 7) if value != r1])
        return _q(f"Solve x² − {r1+r2}x + {r1*r2} = 0. Give both roots separated by a comma.", f"{r1},{r2}", topic, "Factorise into two brackets and set each bracket equal to zero.", "roots")
    if topic == "graphs":
        gradient = random.randint(-4, 5); intercept = random.randint(-5, 5)
        return _q(f"For y = {gradient}x + {intercept}, state the gradient.", gradient, topic, "In y = mx + c, m is the gradient.")
    if topic == "geometry":
        adjacent, angle = random.randint(5, 14), random.choice([30, 35, 40, 45, 50, 60])
        answer = round(adjacent*math.tan(math.radians(angle)), 1)
        return _q(f"A right triangle has angle {angle}° and adjacent side {adjacent} cm. Find the opposite side to 1 d.p.", answer, topic, "Use tan θ = opposite ÷ adjacent.")
    if topic == "probability":
        p, trials = random.choice([(0.2,150),(0.35,200),(0.6,250)])
        return _q(f"A result has probability {p}. Estimate how often it occurs in {trials} trials.", p*trials, topic, "Expected frequency = probability × number of trials.")
    frequency, width = random.randint(10, 40), random.choice([2,5,10])
    return _q(f"A histogram class has frequency {frequency} and class width {width}. Find its frequency density.", frequency/width, "statistics", "Frequency density = frequency ÷ class width.")


def _year11(topic):
    if topic == "algebra":
        x, y = random.randint(1, 7), random.randint(1, 7)
        return _q(f"Solve simultaneously: x + y = {x+y} and 2x + y = {2*x+y}. Enter x,y.", f"{x},{y}", topic, "Subtract the first equation from the second to find x, then substitute.", "pair")
    if topic == "graphs":
        root = random.randint(-4, 4)
        bracket = f"x + {abs(root)}" if root < 0 else f"x − {root}"
        return _q(f"The graph y = ({bracket})² has its turning point at ({root}, k). Find k.", 0, topic, "A squared expression is smallest when the bracket equals zero.")
    if topic == "geometry":
        angle = random.randint(35, 75)
        return _q(f"An angle at the circumference is {angle}°. Find the angle at the centre standing on the same arc.", angle*2, topic, "The angle at the centre is twice the angle at the circumference.")
    if topic == "proportion":
        principal, rate = random.choice([(500,4),(800,5),(1200,3)])
        return _q(f"£{principal} grows by {rate}% each year. Find its value after 2 years to the nearest penny.", round(principal*(1+rate/100)**2,2), topic, "Use the multiplier (1 + rate) once for each year.")
    if topic == "probability":
        both, first = random.choice([(0.18,0.6),(0.2,0.5),(0.12,0.4)])
        return _q(f"P(A and B) = {both} and P(A) = {first}. Given A, find P(B).", both/first, topic, "Conditional probability here is P(A and B) ÷ P(A).")
    price, discount, quantity = random.randint(20,60), random.choice([10,15,20]), random.randint(2,5)
    return _q(f"A club buys {quantity} items at £{price} each and receives {discount}% off the total. Find the final cost.", quantity*price*(1-discount/100), "reasoning", "Find the total, calculate the discount, then subtract it.")


def generate_question_data(year, topic=None, difficulty=None, category=None):
    year = min(11, max(7, int(year)))
    valid = [topic_id for topic_id, _ in curriculum.topics_for(year, "Maths")]
    topic = topic if topic in valid else random.choice(valid)
    if year == 8:
        question = year8_maths.generate(topic)
    else:
        family = curriculum.question_family(year, "Maths", topic)
        question = {7:_year7, 9:_year9, 10:_year10, 11:_year11}[year](family)
        question["topic"] = topic
        question["diagram"] = maths_diagrams.diagram_for_family(family, question)
    unit = curriculum.topic_details(year, "Maths", topic) or {}
    stage_level = {"foundation":1,"application":2,"reasoning":3,"mixed":2}.get(unit.get("stage"),2)
    question["difficulty"] = min(4,max(1,int(difficulty or stage_level)))
    categories = unit.get("question_categories") or ["Fluency","Applied","Reasoning","Exam-style"]
    question["category"] = category if category in categories else categories[0]
    return question


def generate_question(app):
    question = generate_question_data(getattr(app, "difficulty_value", 7), getattr(app, "maths_topic", None))
    return question["prompt"], question["answer"]


def _normalise(value):
    text = str(value).lower().replace("×", "*").replace("·", "*").replace("π", "pi").replace("−", "-")
    for symbol, power in (("²","2"),("³","3"),("⁴","4"),("⁵","5"),("⁶","6"),("⁷","7"),("⁸","8"),("⁹","9")):
        text = text.replace(symbol, "^" + power)
    return re.sub(r"\s+", "", text)


def _fraction_value(value):
    text = str(value).strip()
    mixed = re.fullmatch(r"(-?\d+)\s+(\d+)\s*/\s*(\d+)", text)
    if mixed:
        whole, numerator, denominator = map(int, mixed.groups())
        sign = -1 if whole < 0 else 1
        return Fraction(whole, 1) + sign * Fraction(numerator, denominator)
    return Fraction(text)


def answer_is_correct(question, response):
    response = response.strip()
    if not response:
        return False
    if question["type"] in ("roots", "pair"):
        def numbers(value): return sorted(round(float(x), 6) for x in re.findall(r"-?\d+(?:\.\d+)?", str(value)))
        return numbers(response) == numbers(question["answer"])
    if question["type"] == "ordered_pair":
        def numbers(value): return [round(float(x), 6) for x in re.findall(r"-?\d+(?:\.\d+)?", str(value))]
        return numbers(response) == numbers(question["answer"])
    candidates = [question["answer"], *question.get("accepted", [])]
    for answer in candidates:
        try:
            if abs(float(response) - float(answer)) <= 0.011:
                return True
        except (ValueError, TypeError):
            pass
        try:
            if _fraction_value(response) == _fraction_value(answer):
                return True
        except (ValueError, ZeroDivisionError):
            pass
        if _normalise(response) == _normalise(answer):
            return True
    return False


def show_maths_screen(root, app, topic=None):
    if not app.check_time(): return
    if topic is None:
        return show_maths_topics(root, app)
    app.maths_topic = topic; app.maths_correct = 0; app.maths_total = 0; app.maths_best_streak = 0; app.maths_current_streak = 0; app.maths_xp_earned = 0
    app.maths_session_questions = 10
    user = app.save_data.get("users", {}).get(app.current_user, {})
    mastery = curriculum.mastery_percent(user, "Maths", topic)
    starting = 1 if mastery < 35 else 2 if mastery < 70 else 3
    adaptive = app.experience_store.adaptive_state(app.current_user, "Maths", topic, starting)
    app.maths_adaptive_level = adaptive["difficulty"]
    ask_maths_question(root, app)


def show_maths_topics(root, app):
    clear(root); year = getattr(app, "difficulty_value", 7)
    body = make_page_header(root, "Maths Curriculum", f"Choose a Year {year} topic or follow your recommendation.", app.subject_menu)
    body = make_scrollable(body)
    recommendation = curriculum.recommend_next(app.save_data, app.current_user, "Maths")
    if recommendation:
        card = make_card(body, f"Recommended: {recommendation['title']}", recommendation["reason"], "#58D68D"); card.pack(fill="x", pady=(0,10)); make_button(card, "Practise Next", lambda t=recommendation["topic"]: show_maths_screen(root, app, t))
    user = app.save_data["users"][app.current_user]
    chapters = curriculum.chapters_for(year, "Maths")
    if chapters:
        make_section_header(body, f"Year {year} chapters", "Open a chapter to see its units, prerequisites and mastery.")
        grid = tk.Frame(body, bg=THEME["bg"]); grid.pack(fill="both", expand=True)
        for column in range(2): grid.grid_columnconfigure(column, weight=1, uniform="maths_chapters")
        for index, chapter in enumerate(chapters):
            attempted = sum(bool(user.get("mastery", {}).get("Maths", {}).get(unit["id"], {}).get("attempts")) for unit in chapter["units"])
            make_action_tile(grid, chapter["title"], f"{len(chapter['units'])} units · {attempted} started", lambda c=chapter["id"]: show_maths_chapter(root, app, c), THEME["accent"]).grid(row=index // 2, column=index % 2, sticky="nsew", padx=5, pady=5)
        return


def show_year8_chapter(root, app, chapter_id):
    return show_maths_chapter(root, app, chapter_id)


def show_maths_chapter(root, app, chapter_id):
    year = getattr(app, "difficulty_value", 7)
    chapter = next((item for item in curriculum.chapters_for(year, "Maths") if item["id"] == chapter_id), None)
    if not chapter:
        show_maths_topics(root, app); return
    clear(root)
    body = make_page_header(root, chapter["title"], f"Year {year} · {len(chapter['units'])} focused units", lambda: show_maths_topics(root, app))
    body = make_scrollable(body); user = app.save_data["users"][app.current_user]
    make_section_header(body, "Choose a unit", "Follow prerequisites, learn the method, practise adaptively, then assess.")
    grid = tk.Frame(body, bg=THEME["bg"]); grid.pack(fill="both", expand=True)
    for column in range(2): grid.grid_columnconfigure(column, weight=1, uniform="maths_units")
    for index, unit in enumerate(chapter["units"]):
        mastery = curriculum.mastery_percent(user, "Maths", unit["id"])
        card = make_card(grid, unit["title"], f"{', '.join(unit['subskills'])}\nMastery · {mastery}%", THEME["accent"]); card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=5, pady=5)
        make_progress_bar(card, mastery, THEME["accent"]).pack(fill="x", pady=(10, 1))
        make_button(card, "Learn", lambda t=unit["id"]: __import__('learning_experience').show_lesson(root, app, "Maths", t))
        make_button(card, "Practise", lambda t=unit["id"]: show_maths_screen(root, app, t))
        make_button(card, "Assess", lambda t=unit["id"]: __import__('curriculum_ui').start_relevant_assessment(root, app, year, "Maths", t))


def ask_maths_question(root, app):
    clear(root); year = getattr(app, "difficulty_value", 7); title = curriculum.topic_title(year, "Maths", app.maths_topic)
    categories = ["Fluency", "Applied", "Reasoning", "Exam-style"]
    category = categories[min(3, app.maths_total * len(categories) // max(1, app.maths_session_questions))]
    question = generate_question_data(year, app.maths_topic, getattr(app, "maths_adaptive_level", 1), category); app.current_math_question = question
    body = make_page_header(root, "Maths Practice", f"{title} • Question {app.maths_total + 1} of {app.maths_session_questions} · {question['category']} · Adaptive level {question['difficulty']}", lambda: show_maths_topics(root, app))
    card = make_card(body, question["prompt"], accent=THEME["accent"], padding=22); card.pack(fill="both", expand=True, padx=80, pady=18)
    response = tk.StringVar()
    diagram = maths_diagrams.render_diagram(card, question.get("diagram"), response)
    if diagram: diagram.pack(fill="x", pady=(12, 4))
    if question["type"] == "multiple_choice":
        for choice in question["choices"]:
            tk.Radiobutton(card, text=choice, variable=response, value=choice, font=FONT_TEXT, bg=card["bg"], fg=THEME["fg"], selectcolor=THEME.get("panel_alt", THEME["button_bg"]), activebackground=card["bg"], activeforeground=THEME["fg"]).pack(anchor="w", pady=5)
    else:
        entry = tk.Entry(card, textvariable=response, font=FONT_SUBTITLE, width=32); entry.pack(pady=18, ipady=7); entry.focus(); entry.bind("<Return>", lambda event: submit())
    feedback = make_label(card, "", FONT_TEXT); feedback.pack(pady=8)
    controls = tk.Frame(card, bg=card["bg"]); controls.pack(fill="x", pady=8)
    def submit():
        if not response.get().strip(): feedback.config(text="Enter an answer first.", fg="#FF8A80"); return
        correct = answer_is_correct(question, response.get()); app.maths_total += 1
        adaptive = app.experience_store.record_adaptive_result(app.current_user, "Maths", question["topic"], correct, question.get("difficulty", 1))
        app.maths_adaptive_level = adaptive["difficulty"]
        curriculum.record_mastery(app.save_data, app.current_user, "Maths", question["topic"], 1 if correct else 0, 1)
        if correct:
            app.maths_correct += 1; app.maths_current_streak += 1; app.maths_best_streak = max(app.maths_best_streak, app.maths_current_streak); app.maths_xp_earned += 10
            progress.add_xp(app, 10); audio.play_correct(); feedback.config(text=f"Correct. {question['explanation']}", fg="#58D68D")
        else:
            app.maths_current_streak = 0; progress.record_answer(app); audio.play_incorrect(); feedback.config(text=f"Answer: {question['answer']}. {question['explanation']}", fg="#FF8A80")
        for child in controls.winfo_children(): child.destroy()
        if app.maths_total >= app.maths_session_questions: make_button(controls, "View Summary", lambda: show_maths_summary(root, app), wide=True)
        else: make_button(controls, "Next Question", lambda: ask_maths_question(root, app), wide=True)
    make_button(controls, "Check Answer", submit, wide=True)


def show_maths_summary(root, app):
    clear(root); correct, total, streak = app.maths_correct, app.maths_total, app.maths_best_streak
    bonus = streak * 2
    if bonus: progress.add_xp(app, bonus, questions=0)
    progress.maths_completed(app)
    body = make_page_header(root, "Maths Summary", curriculum.topic_title(app.difficulty_value, "Maths", app.maths_topic), app.subject_menu)
    body = make_scrollable(body)
    stats = tk.Frame(body, bg=THEME["bg"]); stats.pack(fill="x", pady=20)
    make_stat(stats, f"{correct}/{total}", "Correct", "#58D68D").pack(side="left", fill="x", expand=True, padx=6)
    make_stat(stats, f"{round(correct/total*100) if total else 0}%", "Accuracy", THEME["accent"]).pack(side="left", fill="x", expand=True, padx=6)
    make_stat(stats, app.maths_xp_earned + bonus, "XP earned", "#FFB84D").pack(side="left", fill="x", expand=True, padx=6)
    recommendation = curriculum.recommend_next(app.save_data, app.current_user, "Maths")
    if recommendation:
        next_card = make_card(body, "Up next", f"{recommendation['title']} — {recommendation['reason']}", THEME["accent"]); next_card.pack(fill="x", pady=12)
        make_button(next_card, "Open Next Lesson", lambda r=recommendation: __import__('learning_experience').show_lesson(root, app, "Maths", r["topic"]))
    make_button(body, "Practise This Topic Again", lambda: show_maths_screen(root, app, app.maths_topic), wide=True)
    make_button(body, "Choose Another Topic", lambda: show_maths_topics(root, app), wide=True)
