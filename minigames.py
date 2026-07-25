# minigames.py

import tkinter as tk
import random
import time

from ui import clear, make_action_tile, make_label, make_button, make_card, make_page_header, make_scrollable, make_section_header, make_stat
from settings import THEME, FONT_TITLE, FONT_SUBTITLE, FONT_TEXT
import audio
import progress
import game_state
import save_system


# ============================================================
# MAIN MINIGAME MENU
# ============================================================

def show_minigames_menu(root, app):
    clear(root)
    body = make_page_header(root, "Mini-Games", "Short brain breaks that reward effort without replacing lessons.", app.subject_menu)
    content = make_scrollable(body)
    make_section_header(content, "Choose a challenge", "Each game is quick, age-appropriate and keeps rewards balanced.")
    grid = tk.Frame(content, bg=THEME["bg"]); grid.pack(fill="both", expand=True)
    for column in range(3): grid.grid_columnconfigure(column, weight=1, uniform="games")
    for index, (title, description, colour, command) in enumerate((
        ("Quick Maths", "A short arithmetic sprint. Your accessibility time setting is applied.", "#4EA3FF", lambda: quick_maths(root, app)),
        ("Word Scramble", "Unscramble one age-appropriate vocabulary word.", "#B56BFF", lambda: word_scramble(root, app)),
        ("Memory Match", "Find six matching pairs with as few guesses as possible.", "#58D68D", lambda: memory_match(root, app)),
    )):
        make_action_tile(grid, title, description, command, colour).grid(row=0, column=index, sticky="nsew", padx=7, pady=7)


# ============================================================
# MINI‑GAME 1: QUICK MATHS
# ============================================================

def quick_maths_time_limit(app):
    try:
        extra = app.experience_store.preferences(app.current_user).get("extra_time_percent", 0)
    except (AttributeError, TypeError):
        extra = 0
    return round(30 * (1 + min(100, max(0, int(extra))) / 100))


def quick_maths(root, app):
    if not app.check_time():
        return

    clear(root); duration = quick_maths_time_limit(app); state = {"active": True, "answer": None, "finished": False}
    def leave(): state["active"] = False; show_minigames_menu(root, app)
    body = make_page_header(root, "Quick Maths", f"Answer as many as you can in {duration} seconds.", leave)

    score = {"value": 0}
    combo = {"value": 0}
    end_time = time.time() + duration

    # Timer bar frame
    timer_frame = tk.Frame(body, bg=THEME["bg"])
    timer_frame.pack(pady=10)

    timer_bar = tk.Frame(timer_frame, bg=THEME["accent"], width=400, height=20)
    timer_bar.pack()

    question_label = make_label(body, "", FONT_SUBTITLE)
    question_label.pack(pady=20)

    entry = tk.Entry(body, font=FONT_TEXT, width=20)
    entry.pack(pady=10)

    feedback = make_label(body, "", FONT_TEXT)
    feedback.pack(pady=10)

    # -----------------------------
    # TIMER BAR UPDATE
    # -----------------------------
    def update_timer():
        if not state["active"] or state["finished"]:
            return
        remaining = end_time - time.time()
        if remaining <= 0:
            state["finished"] = True; finish_quick_maths(root, app, score["value"])
            return

        # Scale bar width (max 400px)
        width = int((remaining / duration) * 400)
        timer_bar.config(width=width)

        root.after(100, update_timer)

    update_timer()

    # -----------------------------
    # NEW QUESTION
    # -----------------------------
    def new_question():
        if not state["active"] or state["finished"]: return

        a = random.randint(1, 10 * app.difficulty_value)
        b = random.randint(1, 10 * app.difficulty_value)
        op = random.choice(["+", "-", "×"])

        if op == "+":
            ans = a + b
        elif op == "-":
            ans = a - b
        else:
            ans = a * b

        state["answer"] = ans; question_label.config(text=f"{a} {op} {b} =")
        entry.delete(0, tk.END)
        feedback.config(text="")

    def submit():
        if not state["active"] or state["finished"]: return
        try: correct = float(entry.get()) == state["answer"]
        except ValueError:
            feedback.config(text="Enter a number.", fg="#FF8A80"); return
        if correct:
            score["value"] += 1; combo["value"] += 1; progress.add_xp(app, 3); audio.play_correct()
            feedback.config(text=f"Correct • streak {combo['value']}", fg="#58D68D")
        else:
            combo["value"] = 0; progress.record_answer(app); audio.play_incorrect()
            feedback.config(text=f"Not quite • answer {state['answer']}", fg="#FFB84D")
        new_question()

    entry.bind("<Return>", lambda event: submit()); make_button(body, "Submit", submit); new_question(); entry.focus()



def finish_quick_maths(root, app, score):
    clear(root)

    game_state.record_event(save_system.get_user(app.save_data, app.current_user), "minigames")
    save_system.save_save(app.save_data)

    make_label(root, "Time's Up!", FONT_TITLE).pack(pady=20)
    make_label(root, f"You scored {score}!", FONT_SUBTITLE).pack(pady=10)

    make_button(root, "Back to Mini-Games", app.start_minigames, wide=True)


# ============================================================
# MINI‑GAME 2: WORD SCRAMBLE
# ============================================================

WORDS_BY_YEAR = {
    7: ["planet", "forest", "library", "weather", "journey"],
    8: ["contrast", "transform", "persuade", "fraction", "evidence"],
    9: ["analysis", "correlation", "structure", "proportion", "evaluate"],
    10: ["quadratic", "inference", "rhetoric", "probability", "narrative"],
    11: ["synthesis", "conditional", "perspective", "cohesion", "interpret"],
}


def word_scramble(root, app):
    if not app.check_time():
        return

    clear(root)
    body = make_page_header(root, "Word Scramble", f"Year {app.difficulty_value} vocabulary", app.start_minigames)
    make_label(root, "Unscramble the word!", FONT_SUBTITLE).pack(pady=10)

    word = random.choice(WORDS_BY_YEAR.get(app.difficulty_value, WORDS_BY_YEAR[7]))
    scrambled = word
    while scrambled == word:
        scrambled = "".join(random.sample(word, len(word)))

    make_label(body, f"Scrambled: {scrambled}", FONT_SUBTITLE).pack(pady=20)

    entry = tk.Entry(body, font=FONT_TEXT, width=30)
    entry.pack(pady=10)

    feedback = make_label(body, "", FONT_TEXT)
    feedback.pack(pady=10)

    completed = {"value": False}
    def submit():
        if completed["value"]: return
        guess = entry.get().strip().lower()
        if not guess: feedback.config(text="Enter your answer first.", fg="#FF8A80"); return
        completed["value"] = True

        if guess == word:
            feedback.config(text="Correct!", fg="#58D68D")
            audio.play_correct()
            progress.add_xp(app, 15)
        else:
            feedback.config(text=f"The word was {word}.", fg="#FFB84D"); progress.record_answer(app)
            audio.play_incorrect()

        game_state.record_event(save_system.get_user(app.save_data, app.current_user), "minigames")
        save_system.save_save(app.save_data)

        make_button(body, "Play Again", lambda: word_scramble(root, app))
        make_button(body, "Back", app.start_minigames)

    make_button(body, "Submit", submit); entry.bind("<Return>", lambda event: submit()); entry.focus()


# ============================================================
# MINI‑GAME 3: MEMORY MATCH
# ============================================================

def memory_match(root, app):
    if not app.check_time():
        return

    clear(root); active = {"value": True}
    def leave(): active["value"] = False; app.start_minigames()
    body = make_page_header(root, "Memory Match", "Find six pairs in as few moves as possible.", leave)

    # Generate pairs
    letters = ["A", "B", "C", "D", "E", "F"]
    cards = letters + letters
    random.shuffle(cards)

    buttons = []
    revealed = []
    matched = set()
    moves = {"value": 0}; started = time.time()

    frame = tk.Frame(body, bg=THEME["bg"])
    frame.pack(pady=20)
    status = make_label(body, "0 moves • 0 of 6 pairs", FONT_TEXT); status.pack(pady=5)

    def reveal(i):
        if not active["value"] or i in matched or len(revealed) == 2:
            return

        buttons[i].config(text=cards[i], state="disabled")
        revealed.append(i)

        if len(revealed) == 2:
            root.after(700, check_match)

    def check_match():
        if not active["value"] or len(revealed) != 2:
            return
        i, j = revealed
        moves["value"] += 1
        if cards[i] == cards[j]:
            matched.add(i)
            matched.add(j)
            audio.play_correct()
        else:
            buttons[i].config(text="?", state="normal")
            buttons[j].config(text="?", state="normal")
            audio.play_incorrect()

        revealed.clear()
        status.config(text=f"{moves['value']} move{'s' if moves['value'] != 1 else ''} • {len(matched) // 2} of 6 pairs")

        if len(matched) == len(cards):
            active["value"] = False; finish_memory_match(root, app, moves["value"], round(time.time() - started))

    # Create card buttons
    for i in range(len(cards)):
        btn = tk.Button(
            frame,
            text="?",
            width=6,
            height=3,
            font=FONT_SUBTITLE,
            bg=THEME["button_bg"],
            fg=THEME["button_fg"],
            command=lambda i=i: reveal(i)
        )
        btn.grid(row=i // 4, column=i % 4, padx=10, pady=10)
        buttons.append(btn)


def memory_match_xp(moves):
    return 10 + max(0, 12 - max(6, int(moves)))


def finish_memory_match(root, app, moves, elapsed_seconds):
    clear(root)

    game_state.record_event(save_system.get_user(app.save_data, app.current_user), "minigames")

    make_label(root, "You matched all pairs!", FONT_TITLE).pack(pady=20)
    stats = tk.Frame(root, bg=THEME["bg"]); stats.pack(fill="x", padx=80, pady=12)
    reward = memory_match_xp(moves)
    make_stat(stats, moves, "Moves", "#4EA3FF").pack(side="left", fill="x", expand=True, padx=5)
    make_stat(stats, f"{elapsed_seconds}s", "Time", "#B56BFF").pack(side="left", fill="x", expand=True, padx=5)
    make_stat(stats, reward, "XP earned", "#58D68D").pack(side="left", fill="x", expand=True, padx=5)

    progress.add_xp(app, reward, questions=0)

    make_button(root, "Play Again", lambda: memory_match(root, app), wide=True)
    make_button(root, "Back", app.start_minigames, wide=True)
