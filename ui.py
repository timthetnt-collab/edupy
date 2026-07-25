# ui.py
"""
UI helpers for the Learning Game.
Includes:
- clear, make_label, make_button, show_popup
- apply_theme_to_root to recolour widgets in place when theme changes
"""

import tkinter as tk
from settings import (
    THEME, FONT_TITLE, FONT_SUBTITLE, FONT_TEXT, FONT_BUTTON,
    DIFFICULTY_LEVELS
)
import audio


REDUCED_MOTION = False
_BASE_TK_SCALING = None


def configure_root(root):
    """Install the shared EduPy visual defaults for native Tk controls."""
    root.configure(bg=THEME["bg"])
    root.option_add("*Font", FONT_TEXT)
    root.option_add("*Entry.background", THEME.get("input_bg", THEME["panel_alt"]))
    root.option_add("*Entry.foreground", THEME["fg"])
    root.option_add("*Entry.insertBackground", THEME["fg"])
    root.option_add("*Entry.relief", "flat")
    root.option_add("*Text.background", THEME.get("input_bg", THEME["panel_alt"]))
    root.option_add("*Text.foreground", THEME["fg"])
    root.option_add("*Text.insertBackground", THEME["fg"])
    root.option_add("*Text.relief", "flat")
    root.option_add("*Checkbutton.background", THEME["bg"])
    root.option_add("*Checkbutton.foreground", THEME["fg"])
    root.option_add("*Radiobutton.background", THEME["bg"])
    root.option_add("*Radiobutton.foreground", THEME["fg"])
    root.option_add("*Button.takeFocus", True)
    root.option_add("*Entry.takeFocus", True)
    root.option_add("*Text.takeFocus", True)


def contrast_ratio(first, second):
    """Return the WCAG contrast ratio for two #RRGGBB colours."""
    def luminance(value):
        channels = [int(value[index:index + 2], 16) / 255 for index in (1, 3, 5)]
        channels = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
        return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]
    try:
        light, dark = sorted((luminance(first), luminance(second)), reverse=True)
        return round((light + 0.05) / (dark + 0.05), 2)
    except (TypeError, ValueError, IndexError):
        return 0.0


def theme_accessibility_report(theme=None):
    palette = theme or THEME
    checks = {
        "page_text": contrast_ratio(palette.get("fg"), palette.get("bg")),
        "panel_text": contrast_ratio(palette.get("fg"), palette.get("panel")),
        "button_text": contrast_ratio(palette.get("button_fg"), palette.get("button_bg")),
        "button_hover_text": contrast_ratio(palette.get("button_fg"), palette.get("button_hover_bg")),
    }
    return {"checks": checks, "passes_aa": all(value >= 4.5 for value in checks.values())}


def apply_accessibility(root, preferences):
    """Apply accessibility settings to current and future screens."""
    global REDUCED_MOTION, _BASE_TK_SCALING
    REDUCED_MOTION = bool(preferences.get("reduced_motion", False))
    try:
        if _BASE_TK_SCALING is None:
            _BASE_TK_SCALING = float(root.tk.call("tk", "scaling"))
        scale = min(140, max(90, int(preferences.get("font_scale", 100)))) / 100
        root.tk.call("tk", "scaling", _BASE_TK_SCALING * scale)
    except Exception:
        pass
    if preferences.get("high_contrast"):
        THEME.update({
            "bg": "#000000", "fg": "#FFFFFF", "panel": "#101010", "panel_alt": "#202020",
            "button_bg": "#FFD800", "button_fg": "#000000", "button_hover_bg": "#FFFFFF",
            "accent": "#00E5FF", "muted": "#E8E8E8",
            "accent_soft": "#003D45", "border": "#FFFFFF", "input_bg": "#101010",
            "success": "#60FF9B", "warning": "#FFE600", "danger": "#FF6B81",
        })
    elif preferences.get("calm_palette"):
        THEME.update({
            "bg":"#EDF7F3","fg":"#173A35","muted":"#55756F","panel":"#FFFFFF",
            "panel_alt":"#DCEFE8","accent":"#168C76","accent_soft":"#CDEDE4",
            "border":"#BDD9D1","input_bg":"#F9FFFD","button_bg":"#147563",
            "button_fg":"#FFFFFF","button_hover_bg":"#0F5E50",
        })
    try:
        family = "Comic Sans MS" if preferences.get("dyslexia_friendly") else "Segoe UI"
        root.option_add("*Font", (family, 12))
        root.option_add("*Label.padY", 4 if preferences.get("generous_spacing") else 0)
    except Exception:
        pass
    # A slim mouse-following line helps readers keep their place. It never
    # stores reading behaviour and can be switched off instantly.
    try:
        ruler = getattr(root, "_edupy_reading_ruler", None)
        if ruler:
            ruler.destroy(); root._edupy_reading_ruler = None
        old_binding = getattr(root, "_edupy_ruler_binding", None)
        if old_binding:
            root.unbind("<Motion>", old_binding)
        if preferences.get("reading_ruler"):
            ruler = tk.Frame(root, bg=THEME.get("warning", "#FFC857"), height=3)
            ruler._edupy_persistent = True
            root._edupy_reading_ruler = ruler
            def move(event):
                try:ruler.place(x=0,y=max(0,event.y_root-root.winfo_rooty()+18),relwidth=1);ruler.lift()
                except tk.TclError:pass
            root._edupy_ruler_binding = root.bind("<Motion>", move, add="+")
    except Exception:
        pass


# ============================================================
# CLEAR SCREEN
# ============================================================

def clear(root):
    for widget in root.winfo_children():
        if getattr(widget, "_edupy_persistent", False):
            continue
        widget.destroy()
    # A short fade makes screen changes feel intentional without delaying input.
    try:
        if REDUCED_MOTION:
            root.attributes("-alpha", 1.0)
            return
        root.attributes("-alpha", 0.94)
        def fade(step=0):
            root.attributes("-alpha", min(1.0, 0.94 + step * 0.012))
            if step < 5:
                root.after(18, fade, step + 1)
        fade()
    except Exception:
        pass


# ============================================================
# LABEL
# ============================================================

def make_label(root, text, font=FONT_TEXT, pady=10):
    return tk.Label(
        root,
        text=text,
        font=font,
        bg=THEME["bg"],
        fg=THEME["fg"],
        pady=pady,
        wraplength=820,
        justify="center"
    )


# ============================================================
# BUTTON (wide=True = full width, wide=False = 1/3 width)
# ============================================================

def make_button(root, text, command, wide=False, kind="primary"):
    """
    wide=False → 1/3 width medium-height button (menus)
    wide=True  → full-width medium-height button (login, back, logout)
    """

    # Shared hover behaviour
    def apply_hover(btn):
        def blend(start, end, amount):
            try:
                a = tuple(int(start[i:i + 2], 16) for i in (1, 3, 5))
                b = tuple(int(end[i:i + 2], 16) for i in (1, 3, 5))
                rgb = tuple(round(x + (y - x) * amount) for x, y in zip(a, b))
                return "#" + "".join(f"{value:02x}" for value in rgb)
            except Exception:
                return end

        def transition(target):
            if REDUCED_MOTION:
                btn.config(bg=target)
                return
            start = btn.cget("bg")
            for step in range(1, 5):
                btn.after(step * 18, lambda n=step: btn.config(bg=blend(start, target, n / 4)))
        try:
            normal = btn.cget("bg")
            hover = THEME["button_hover_bg"] if kind == "primary" else THEME.get("panel_alt", normal)
            btn.bind("<Enter>", lambda e: transition(hover))
            btn.bind("<Leave>", lambda e: transition(normal))
            btn.bind("<FocusIn>", lambda e: btn.config(highlightthickness=2, highlightbackground=THEME["accent"]))
            btn.bind("<FocusOut>", lambda e: btn.config(highlightthickness=0))
        except Exception:
            pass

    background = THEME["button_bg"] if kind == "primary" else THEME.get("panel_alt", THEME["button_bg"])
    foreground = THEME["button_fg"] if kind == "primary" else THEME["fg"]
    if wide:
        # FULL-WIDTH BUTTON (login, back, logout)
        btn = tk.Button(
            root,
            text=text,
            font=FONT_BUTTON,
            bg=background,
            fg=foreground,
            activebackground=THEME["button_hover_bg"],
            activeforeground=THEME["button_fg"],
            relief="flat",
            bd=0,
            padx=18,
            pady=10,
            cursor="hand2",
            takefocus=True,
            highlightthickness=1,
            highlightbackground=THEME.get("border", THEME["accent"]),
            highlightcolor=THEME["accent"],
            command=lambda: (audio.play_click(), command())
        )

        apply_hover(btn)
        btn.bind("<Return>", lambda event: btn.invoke())
        btn.pack(fill="x", pady=8, padx=12)
        return btn

    else:
        # 1/3 WIDTH BUTTON (main menu, subject menu, shop)
        parent_bg = root.cget("bg") if hasattr(root, "cget") else THEME["bg"]
        frame = tk.Frame(root, bg=parent_bg, height=42)
        if getattr(root, "_edupy_card", False):
            frame.pack(side="left", pady=(12, 0), padx=(0, 8))
            frame.configure(width=max(150, min(240, len(text) * 9 + 36)))
        else:
            frame.pack(pady=6)
            frame.configure(width=260)
        frame.pack_propagate(False)

        btn = tk.Button(
            frame,
            text=text,
            font=FONT_BUTTON,
            bg=background,
            fg=foreground,
            activebackground=THEME["button_hover_bg"],
            activeforeground=THEME["button_fg"],
            relief="flat",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            takefocus=True,
            highlightthickness=1,
            highlightbackground=THEME.get("border", THEME["accent"]),
            highlightcolor=THEME["accent"],
            command=lambda: (audio.play_click(), command())
        )

        apply_hover(btn)
        btn.bind("<Return>", lambda event: btn.invoke())
        btn.pack(fill="x")
        return btn


# ============================================================
# POPUP WINDOW
# ============================================================

def show_popup(app, message):
    popup = tk.Toplevel(app.root)
    popup.title("EduPy")
    popup.configure(bg=THEME["bg"])
    popup.geometry("520x260")
    popup.resizable(False, False)
    popup.transient(app.root)
    popup.grab_set()

    shell = tk.Frame(popup, bg=THEME.get("panel", THEME["bg"]), padx=28, pady=24, highlightthickness=1, highlightbackground=THEME.get("border", THEME["accent"]))
    shell.pack(fill="both", expand=True, padx=12, pady=12)
    tk.Label(shell, text="EDUPY", font=("Segoe UI", 9, "bold"), bg=shell["bg"], fg=THEME["accent"]).pack(anchor="w")
    label = tk.Label(shell, text=message, font=FONT_SUBTITLE, bg=shell["bg"], fg=THEME["fg"], wraplength=430, justify="left", anchor="w")
    label.pack(fill="both", expand=True, pady=(10, 14))
    button = make_button(shell, "OK", popup.destroy, wide=True)
    try:
        popup.update_idletasks()
        x = app.root.winfo_rootx() + max(0, (app.root.winfo_width() - popup.winfo_width()) // 2)
        y = app.root.winfo_rooty() + max(0, (app.root.winfo_height() - popup.winfo_height()) // 2)
        popup.geometry(f"+{x}+{y}")
    except tk.TclError:
        pass
    popup.bind("<Return>", lambda event: popup.destroy())
    popup.bind("<Escape>", lambda event: popup.destroy())
    button.focus_set()


# ============================================================
# LOADING SCREEN
# ============================================================

def show_loading_screen(root, callback):
    clear(root)

    frame = tk.Frame(root, bg=THEME["bg"])
    frame.pack(expand=True)

    title = make_label(frame, "Loading...", FONT_TITLE)
    title.pack(pady=20)

    dots_label = make_label(frame, "", FONT_SUBTITLE)
    dots_label.pack()

    def animate(i=0):
        dots = "." * (i % 4)
        dots_label.config(text=dots)
        if i < 40:
            root.after(100, animate, i + 1)
        else:
            callback()

    animate()


# ============================================================
# MAIN MENU
# ============================================================

def show_main_menu(root, app):
    clear(root)

    make_label(root, f"Hello, {app.current_user}!", FONT_TITLE).pack(pady=20)

    make_button(root, "Subjects", app.subject_menu)
    make_button(root, "Shop", lambda: app.open_shop())
    make_button(root, "Progress", lambda: app.open_progress())
    make_button(root, "Difficulty", app.difficulty_menu)
    make_button(root, "Toggle Fullscreen (F11)", app.toggle_fullscreen)

    make_button(root, "Logout", app.show_login_screen, wide=True)


# ============================================================
# SUBJECT MENU
# ============================================================

def show_subject_menu(root, app):
    clear(root)

    make_label(root, "Choose a Subject", FONT_TITLE).pack(pady=20)

    make_button(root, "English", lambda: app.start_english())
    make_button(root, "Maths", lambda: app.start_maths())
    # Hack removed intentionally

    make_button(root, "Back", app.main_menu, wide=True)


# ============================================================
# LOCK SCREEN
# ============================================================

def show_lock_screen(root):
    clear(root)

    make_label(root, "Time for a Short Break", FONT_TITLE).pack(pady=20)
    make_label(root, "Rest your eyes, stretch, and come back when you feel ready.", FONT_SUBTITLE).pack(pady=10)
    make_label(root, "EduPy lessons are not locked behind payments or time limits.", FONT_TEXT).pack(pady=10)


# ============================================================
# THEME RECOLOUR HELPER
# ============================================================

def apply_theme_to_root(root):
    """
    Walk the widget tree and update bg/fg/button colours using settings.THEME.
    This updates common Tk widgets in place so theme changes are visible immediately.
    """
    from settings import THEME  # import here to pick up updated THEME

    def walk(w):
        cls = w.winfo_class()
        try:
            # Frames and containers
            if cls in ("Frame", "TFrame"):
                w.configure(bg=THEME.get("bg", w.cget("bg")))
            # Labels
            elif cls in ("Label", "TLabel"):
                w.configure(bg=THEME.get("bg", w.cget("bg")), fg=THEME.get("fg", w.cget("fg")))
            # Buttons
            elif cls in ("Button", "TButton"):
                w.configure(
                    bg=THEME.get("button_bg", w.cget("bg")),
                    fg=THEME.get("button_fg", w.cget("fg")),
                    activebackground=THEME.get("button_hover_bg", w.cget("activebackground", THEME.get("button_bg"))),
                    activeforeground=THEME.get("button_fg", w.cget("activeforeground", THEME.get("button_fg")))
                )
            # Text widgets
            elif cls == "Text":
                w.configure(bg=THEME.get("bg", w.cget("bg")), fg=THEME.get("fg", w.cget("fg")))
            # Entry widgets
            elif cls == "Entry":
                w.configure(bg=THEME.get("bg", w.cget("bg")), fg=THEME.get("fg", w.cget("fg")), insertbackground=THEME.get("fg", w.cget("fg")))
            # Canvas
            elif cls == "Canvas":
                w.configure(bg=THEME.get("bg", w.cget("bg")))
        except Exception:
            pass

        for child in w.winfo_children():
            walk(child)

    walk(root)


def style_notebook(root):
    """Apply the active theme to ttk tabs and selectors."""
    from tkinter import ttk
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("Edu.TNotebook", background=THEME["bg"], borderwidth=0, tabmargins=(0, 8, 0, 0))
    style.configure(
        "Edu.TNotebook.Tab", background=THEME.get("panel", THEME["button_bg"]),
        foreground=THEME.get("muted", THEME["fg"]), padding=(18, 11), font=FONT_BUTTON, borderwidth=0,
    )
    style.map("Edu.TNotebook.Tab", background=[("selected", THEME.get("accent_soft", THEME["accent"]))], foreground=[("selected", THEME["fg"])])
    style.configure("Edu.TCombobox", padding=8, font=FONT_TEXT, fieldbackground=THEME.get("input_bg", THEME["panel_alt"]), foreground=THEME["fg"], arrowcolor=THEME["accent"])
    style.map("Edu.TCombobox", fieldbackground=[("readonly", THEME.get("input_bg", THEME["panel_alt"]))], foreground=[("readonly", THEME["fg"])])
    style.configure("TCombobox", padding=8, font=FONT_TEXT, fieldbackground=THEME.get("input_bg", THEME["panel_alt"]), foreground=THEME["fg"], arrowcolor=THEME["accent"])
    style.map("TCombobox", fieldbackground=[("readonly", THEME.get("input_bg", THEME["panel_alt"]))], foreground=[("readonly", THEME["fg"])])
    return style


def make_page_header(root, title, subtitle="", back_command=None):
    """Create a consistent page header and return its content container."""
    header = tk.Frame(root, bg=THEME.get("panel", THEME["bg"]), padx=30, pady=18)
    header.pack(fill="x")
    if back_command:
        back = tk.Button(
            header, text="←", command=lambda: (audio.play_click(), back_command()),
            font=("Segoe UI", 18, "bold"), bg=THEME.get("panel_alt", THEME["bg"]), fg=THEME["fg"],
            activebackground=THEME.get("panel_alt", THEME["button_bg"]),
            activeforeground=THEME["fg"], relief="flat", bd=0, cursor="hand2", padx=13, pady=6,
        )
        back.pack(side="left", padx=(0, 18))
    text = tk.Frame(header, bg=THEME.get("panel", THEME["bg"]))
    text.pack(side="left", fill="x", expand=True)
    tk.Label(text, text="EDUPY", font=("Segoe UI", 9, "bold"), bg=THEME.get("panel", THEME["bg"]), fg=THEME["accent"]).pack(anchor="w")
    tk.Label(text, text=title, font=("Segoe UI", 25, "bold"), bg=THEME.get("panel", THEME["bg"]), fg=THEME["fg"]).pack(anchor="w", pady=(1, 0))
    if subtitle:
        tk.Label(text, text=subtitle, font=FONT_TEXT, bg=THEME.get("panel", THEME["bg"]), fg=THEME.get("muted", THEME["fg"]), wraplength=900, justify="left").pack(anchor="w", pady=(4, 0))
    # The thin blue sweep mirrors the supplied curriculum reference while
    # giving page changes a clear sense of direction.
    divider = tk.Canvas(root, bg=THEME.get("border", THEME["accent"]), height=3, highlightthickness=0, bd=0)
    divider.pack(fill="x")
    def sweep(event=None, step=0):
        try:
            width=max(1,divider.winfo_width());divider.delete("all")
            progress=1 if REDUCED_MOTION else min(1,step/12)
            divider.create_rectangle(0,0,round(width*progress),3,fill=THEME["accent"],outline="")
            if progress<1:divider.after(16,sweep,None,step+1)
        except tk.TclError:pass
    divider.bind("<Configure>",lambda event:sweep(event,12 if REDUCED_MOTION else 0),add="+")
    body = tk.Frame(root, bg=THEME["bg"], padx=28, pady=20)
    body.pack(fill="both", expand=True)
    return body


def make_card(parent, title="", body="", accent=None, padding=14):
    """Create a reusable raised information card."""
    card = tk.Frame(
        parent, bg=THEME.get("panel", THEME["bg"]), padx=padding + 2, pady=padding,
        highlightbackground=THEME.get("border", accent or THEME["accent"]),
        highlightthickness=1, bd=0,
    )
    card._edupy_card = True
    tk.Frame(card, bg=accent or THEME["accent"], height=3).pack(fill="x", pady=(0, 11))
    if title:
        tk.Label(card, text=title, font=FONT_SUBTITLE, bg=card["bg"], fg=THEME["fg"], anchor="w").pack(fill="x")
    if body:
        tk.Label(card, text=body, font=FONT_TEXT, bg=card["bg"], fg=THEME.get("muted", THEME["fg"]), justify="left", anchor="w", wraplength=880).pack(fill="x", pady=(6, 0))
    def enter(event=None): card.configure(highlightbackground=accent or THEME["accent"])
    def leave(event=None): card.configure(highlightbackground=THEME.get("border", accent or THEME["accent"]))
    for widget in (card, *card.winfo_children()):
        widget.bind("<Enter>", enter, add="+"); widget.bind("<Leave>", leave, add="+")
    return card


def make_stat(parent, value, label, accent=None):
    card = make_card(parent, accent=accent or THEME["accent"], padding=12)
    tk.Label(card, text=str(value), font=("Segoe UI", 23, "bold"), bg=card["bg"], fg=accent or THEME["accent"]).pack()
    tk.Label(card, text=label, font=FONT_TEXT, bg=card["bg"], fg=THEME.get("muted", THEME["fg"])).pack()
    return card


def make_progress_bar(parent, percent, accent=None):
    """Create a compact responsive progress indicator."""
    value = min(100, max(0, int(percent or 0)))
    colour = accent or THEME["accent"]
    canvas = tk.Canvas(parent, height=8, bg=THEME.get("panel_alt", THEME["bg"]), highlightthickness=0, bd=0)
    animation={"step":12 if REDUCED_MOTION else 0}
    def draw(event=None):
        width = max(1, event.width if event else canvas.winfo_width())
        canvas.delete("all")
        canvas.create_rectangle(0, 0, width, 8, fill=THEME.get("panel_alt", THEME["bg"]), outline="")
        fraction=min(1,animation["step"]/12)
        canvas.create_rectangle(0, 0, round(width * value / 100*fraction), 8, fill=colour, outline="")
        if fraction<1:
            animation["step"]+=1
            canvas.after(18,draw)
    canvas.bind("<Configure>", draw)
    canvas.after_idle(draw)
    return canvas


def make_section_header(parent, title, subtitle=""):
    block = tk.Frame(parent, bg=THEME["bg"])
    block.pack(fill="x", pady=(18, 8))
    tk.Label(block, text=title, font=FONT_SUBTITLE, bg=THEME["bg"], fg=THEME["fg"], anchor="w").pack(fill="x")
    if subtitle:
        tk.Label(block, text=subtitle, font=FONT_TEXT, bg=THEME["bg"], fg=THEME.get("muted", THEME["fg"]), anchor="w").pack(fill="x", pady=(2, 0))
    return block


def make_action_tile(parent, title, subtitle, command, accent=None):
    """Create a whole-card navigation target for dashboards and menus."""
    accent = accent or THEME["accent"]
    tile = tk.Frame(parent, bg=THEME["panel"], padx=18, pady=16, highlightthickness=1, highlightbackground=THEME.get("border", accent), cursor="hand2")
    top = tk.Frame(tile, bg=tile["bg"]); top.pack(fill="x")
    tk.Label(top, text=title, font=FONT_SUBTITLE, bg=tile["bg"], fg=THEME["fg"], anchor="w", cursor="hand2").pack(side="left", fill="x", expand=True)
    tk.Label(top, text="↗", font=("Segoe UI", 15, "bold"), bg=tile["bg"], fg=accent, cursor="hand2").pack(side="right")
    tk.Label(tile, text=subtitle, font=FONT_TEXT, bg=tile["bg"], fg=THEME.get("muted", THEME["fg"]), justify="left", anchor="w", wraplength=320, cursor="hand2").pack(fill="x", pady=(8, 0))
    stripe = tk.Frame(tile, height=3, bg=accent)
    stripe._edupy_tile_accent = True
    stripe.pack(fill="x", pady=(14, 0))
    def open_tile(event=None): audio.play_click(); command()
    def recolour(widget, colour):
        for child in widget.winfo_children():
            if not getattr(child, "_edupy_tile_accent", False):
                try: child.configure(bg=colour)
                except tk.TclError: pass
                recolour(child, colour)
    def enter(event=None):
        colour = THEME.get("panel_alt", THEME["panel"])
        tile.configure(highlightbackground=accent, bg=colour)
        recolour(tile, colour)
    def leave(event=None):
        tile.configure(highlightbackground=THEME.get("border", accent), bg=THEME["panel"])
        recolour(tile, THEME["panel"])
    def bind_tree(widget):
        widget.bind("<Button-1>", open_tile); widget.bind("<Return>", open_tile); widget.bind("<Enter>", enter, add="+"); widget.bind("<Leave>", leave, add="+")
        for child in widget.winfo_children(): bind_tree(child)
    bind_tree(tile)
    tile.bind("<FocusIn>", enter, add="+")
    tile.bind("<FocusOut>", leave, add="+")
    tile.configure(takefocus=True)
    return tile


def scroll_units(delta=0, button_number=None):
    """Translate platform-specific wheel input into vertical scroll units."""
    if button_number == 4:
        return -3
    if button_number == 5:
        return 3
    if not delta:
        return 0
    return -max(-3, min(3, int(delta / 120)))


def make_scrollable(parent, padx=0, pady=0):
    """Create a responsive vertical scrolling area and return its inner frame.

    Mouse wheel, trackpad, arrow keys, Page Up/Down, Home and End are supported
    while the pointer is over the area.
    """
    container = tk.Frame(parent, bg=THEME["bg"])
    container.pack(fill="both", expand=True, padx=padx, pady=pady)
    canvas = tk.Canvas(container, bg=THEME["bg"], highlightthickness=0, bd=0)
    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview, relief="flat", bd=0, troughcolor=THEME["bg"], bg=THEME.get("panel_alt", THEME["panel"]), activebackground=THEME["accent"])
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    inner = tk.Frame(canvas, bg=THEME["bg"])
    window_id = canvas.create_window((0, 0), window=inner, anchor="nw")

    def update_region(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def fit_width(event):
        canvas.itemconfigure(window_id, width=event.width)

    def wheel(event):
        amount = scroll_units(getattr(event, "delta", 0), getattr(event, "num", None))
        if amount:
            canvas.yview_scroll(amount, "units")
        return "break"

    def key_scroll(event):
        actions = {
            "Up": (-1, "units"), "Down": (1, "units"),
            "Prior": (-1, "pages"), "Next": (1, "pages"),
        }
        if event.keysym == "Home": canvas.yview_moveto(0); return "break"
        if event.keysym == "End": canvas.yview_moveto(1); return "break"
        if event.keysym in actions:
            amount, unit = actions[event.keysym]; canvas.yview_scroll(amount, unit); return "break"

    def activate(event=None):
        canvas.focus_set()
        canvas.bind_all("<MouseWheel>", wheel)
        canvas.bind_all("<Button-4>", wheel)
        canvas.bind_all("<Button-5>", wheel)

    def deactivate(event=None):
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

    inner.bind("<Configure>", update_region)
    canvas.bind("<Configure>", fit_width)
    container.bind("<Enter>", activate)
    container.bind("<Leave>", deactivate)
    inner.bind("<Enter>", activate)
    canvas.bind("<Key>", key_scroll)
    inner._scroll_canvas = canvas
    inner._scroll_container = container
    return inner
